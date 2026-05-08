"""
scheduler.py
Marlo background scheduler — all time-based jobs.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

ALL_DAYS_ORDERED = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_TO_WEEKDAY  = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}


def get_biz_tz(biz):
    from zoneinfo import ZoneInfo
    tz_name = biz.preferred_post_timezone or biz.timezone or "America/New_York"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("America/New_York")

def get_local_dt(biz, utc_now) -> datetime:
    return utc_now.astimezone(get_biz_tz(biz))

def get_local_hour(biz, utc_now) -> int:
    return get_local_dt(biz, utc_now).hour

def get_local_weekday(biz, utc_now) -> int:
    return get_local_dt(biz, utc_now).weekday()

def get_local_day_name(biz, utc_now) -> str:
    return get_local_dt(biz, utc_now).strftime("%A")

def get_posting_schedule(biz) -> list:
    schedule = biz.posting_schedule
    if schedule and isinstance(schedule, list) and len(schedule) > 0:
        valid = [d for d in schedule if d in DAY_TO_WEEKDAY]
        if valid:
            return sorted(valid, key=lambda d: DAY_TO_WEEKDAY[d])
    n = biz.posts_per_week or 3
    defaults = {
        1: ["Monday"],
        2: ["Monday", "Thursday"],
        3: ["Monday", "Wednesday", "Friday"],
        4: ["Monday", "Tuesday", "Thursday", "Friday"],
        5: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        6: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        7: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    }
    return defaults.get(n, ["Monday", "Wednesday", "Friday"])

def get_approval_windows(posting_schedule: list) -> list:
    if not posting_schedule:
        return []
    windows = []
    for i, day in enumerate(posting_schedule):
        day_weekday = DAY_TO_WEEKDAY[day]
        if i > 0:
            prev_day_weekday = (day_weekday - 1) % 7
            expire_day = posting_schedule[i - 1]
            windows.append({"weekday": prev_day_weekday, "hour": 14, "send_day": day, "expire_day": expire_day})
    last_day = posting_schedule[-1]
    windows.append({"weekday": DAY_TO_WEEKDAY[last_day], "hour": 18, "send_day": None, "expire_day": last_day})
    return windows

def build_scheduled_post_time(biz, day_name: str) -> datetime:
    try:
        tz = get_biz_tz(biz)
        now_local = datetime.now(tz)
        target_weekday = DAY_TO_WEEKDAY.get(day_name, 0)
        days_ahead = (target_weekday - now_local.weekday()) % 7
        hour, minute = map(int, (biz.preferred_post_time or "09:00").split(":"))
        post_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        post_local = post_local + timedelta(days=days_ahead)
        return post_local.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc) + timedelta(days=1)


async def _build_image_guide(posts: list, business_dict: dict, strategy_summary: str = "") -> list:
    """Generate a high-level, human photo direction per post tied to the post's strategy."""
    from agent.brain import brain
    image_guide = []
    for post in posts:
        day = post.get("scheduled_day", "")
        caption = post.get("caption", "")
        platform = post.get("platform", "instagram")

        prompt = f"""You're helping a small business owner understand what kind of photo to take for a social media post.

This week's content strategy: {strategy_summary or "authentic, human content that builds trust"}

Post theme (for context): "{caption[:200]}"

Write ONE photo direction in 1 sentence that:
- Describes a real human moment, emotion, or scene — not a product shot
- Connects to the emotional theme or strategy of the post
- Gives creative freedom — suggest a feeling or situation, not exact staging
- Ends with a short reason why it works (e.g. "this builds trust", "this shows relatability")
- Sounds like advice from a creative director, not an AI prompt

Good examples:
- "Catch someone mid-laugh while working — joy is more magnetic than professionalism."
- "Show a quiet moment of focus at a messy desk — real work resonates more than polished setups."
- "Capture the before: stress, clutter, overwhelm — contrast makes the payoff land harder."

Return ONLY the one sentence, nothing else."""

        try:
            suggestion = await brain.generate_content(
                content_type="photo direction",
                business=business_dict,
                context={},
                instructions=prompt
            )
            description = suggestion.strip().strip('"')
        except Exception:
            description = f"Show a real, unposed moment from your business day — authenticity always outperforms polish."

        image_guide.append({"day": day, "description": description})

    return image_guide


# ─── 1. WEEKLY CONTENT GENERATION ────────────────────────────────────────────

async def weekly_content_generation():
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business, User, PlatformIntegration, AgentAction
        from agent.content_pipeline import content_pipeline
        from agent.google_ads_agent import google_ads_agent
        from agent.strategy_agent import strategy_agent
        from email_system.sender import email_sender
        from sqlalchemy import select
        import uuid as _uuid

        utc_now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(
                    Business.onboarding_completed == True,
                    Business.subscription_id != None,
                )
            )
            businesses = result.scalars().all()

            for biz in businesses:
                try:
                    local_hour    = get_local_hour(biz, utc_now)
                    local_weekday = get_local_weekday(biz, utc_now)

                    # Fire on user's chosen kickoff day at 9pm local, default Sunday
                    kickoff_day = biz.briefing_time or "Sunday"
                    kickoff_weekday = DAY_TO_WEEKDAY.get(kickoff_day, 6)
                    if local_weekday != kickoff_weekday or local_hour != 21:
                        continue

                    week_start = utc_now - timedelta(days=(utc_now.weekday() + 1) % 7)
                    existing = await db.execute(
                        select(AgentAction).where(
                            AgentAction.business_id == biz.id,
                            AgentAction.created_at >= week_start,
                            AgentAction.action_type.in_(["post_instagram", "post_facebook", "google_ads_campaign"])
                        )
                    )
                    if existing.scalars().first():
                        logger.info(f"[Scheduler] Already generated this week for {biz.name}, skipping.")
                        continue

                    posting_schedule = get_posting_schedule(biz)
                    posts_count = len(posting_schedule)

                    integrations_result = await db.execute(
                        select(PlatformIntegration).where(
                            PlatformIntegration.business_id == biz.id,
                            PlatformIntegration.is_active == True
                        )
                    )
                    integrations = integrations_result.scalars().all()
                    connected  = [p.platform for p in integrations]
                    has_google = "google" in connected
                    platforms  = ["instagram"]

                    business_dict = {
                        "name": biz.name,
                        "industry": biz.industry or "",
                        "description": biz.description or "",
                        "tone_of_voice": biz.tone_of_voice or "warm and authentic",
                        "target_audience": biz.target_audience or "local customers",
                        "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
                    }

                    try:
                        strategy = await strategy_agent.decide(
                            "weekly_content", {"business": business_dict}, str(biz.id)
                        )
                        strategy_summary = strategy.get("key_message", f"Building authentic content for {biz.name}.")
                    except Exception:
                        strategy = {}
                        strategy_summary = f"Building authentic content for {biz.name}."

                    posts = await content_pipeline.generate_week_of_content(
                        business_id=str(biz.id),
                        db=db,
                        platforms=platforms,
                    )
                    while len(posts) < posts_count:
                        posts.append(posts[-1].copy() if posts else {})
                    posts = posts[:posts_count]
                    for i, post in enumerate(posts):
                        post["scheduled_day"] = posting_schedule[i]

                    google_campaign = None
                    if has_google:
                        try:
                            ads_strategy = await strategy_agent.decide(
                                "google_ads", {"business": business_dict}, str(biz.id)
                            )
                            google_campaign = await google_ads_agent.generate_campaign(
                                business=business_dict,
                                strategy=ads_strategy,
                                business_id=str(biz.id),
                            )
                        except Exception as e:
                            logger.error(f"[Scheduler] Google Ads error: {e}")

                    stored_actions = []
                    for post in posts:
                        action = AgentAction(
                            id=_uuid.uuid4(),
                            business_id=biz.id,
                            action_type=f"post_{post.get('platform', 'instagram')}",
                            action_parameters=post,
                            approval_token=str(_uuid.uuid4()),
                            decline_token=str(_uuid.uuid4()),
                            status="pending",
                            requires_approval=True,
                            scheduled_post_time=build_scheduled_post_time(biz, post["scheduled_day"]),
                            scheduled_day=post["scheduled_day"],
                            approval_email_sent=False,
                            created_at=datetime.utcnow(),
                        )
                        db.add(action)
                        stored_actions.append(action)

                    if google_campaign:
                        ads_action = AgentAction(
                            id=_uuid.uuid4(),
                            business_id=biz.id,
                            action_type="google_ads_campaign",
                            action_parameters=google_campaign,
                            approval_token=str(_uuid.uuid4()),
                            decline_token=str(_uuid.uuid4()),
                            status="pending",
                            requires_approval=True,
                            scheduled_post_time=datetime.now(timezone.utc),
                            scheduled_day=posting_schedule[0],
                            approval_email_sent=False,
                            created_at=datetime.utcnow(),
                        )
                        db.add(ads_action)
                        stored_actions.append(ads_action)

                    await db.commit()

                    week_ago = utc_now - timedelta(days=7)
                    past_result = await db.execute(
                        select(AgentAction).where(
                            AgentAction.business_id == biz.id,
                            AgentAction.created_at >= week_ago,
                            AgentAction.created_at < utc_now - timedelta(days=1),
                        )
                    )
                    past = past_result.scalars().all()
                    last_week_stats = {
                        "approved": len([a for a in past if a.status == "executed"]),
                        "skipped":  len([a for a in past if a.status == "rejected"]),
                        "expired":  len([a for a in past if a.status == "expired"]),
                    }

                    image_guide = await _build_image_guide(posts, business_dict, strategy_summary)

                    first_day = posting_schedule[0]
                    first_action = next((a for a in stored_actions
                                        if a.scheduled_day == first_day
                                        and a.action_type != "google_ads_campaign"), None)
                    ads_stored = next((a for a in stored_actions
                                       if a.action_type == "google_ads_campaign"), None)

                    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
                    user = user_result.scalar_one_or_none()

                    if user and first_action:
                        first_name = (user.full_name or "").split()[0] or "there"
                        await email_sender.send_weekly_kickoff(
                            business_id=str(biz.id),
                            user_email=user.email,
                            first_name=first_name,
                            business_name=biz.name,
                            first_post=first_action.action_parameters,
                            first_post_day=first_day,
                            first_approve_token=first_action.approval_token,
                            first_decline_token=first_action.decline_token,
                            google_campaign=google_campaign,
                            ads_approve_token=ads_stored.approval_token if ads_stored else None,
                            ads_decline_token=ads_stored.decline_token if ads_stored else None,
                            posting_schedule=posting_schedule,
                            strategy_summary=strategy_summary,
                            image_guide=image_guide,
                            last_week_stats=last_week_stats,
                            db=db,
                        )
                        first_action.approval_email_sent = True
                        if ads_stored:
                            ads_stored.approval_email_sent = True
                        await db.commit()

                    logger.info(f"[Scheduler] Weekly kickoff sent for {biz.name} — {posts_count} posts: {posting_schedule} (kickoff day: {kickoff_day})")

                except Exception as e:
                    logger.error(f"[Scheduler] Weekly gen error for {biz.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"[Scheduler] weekly_content_generation outer error: {e}", exc_info=True)


# ─── 2. POST APPROVAL EMAILS + EXPIRY ────────────────────────────────────────

async def post_approval_and_expiry():
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business, User, AgentAction
        from email_system.sender import email_sender
        from sqlalchemy import select

        utc_now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(
                    Business.onboarding_completed == True,
                    Business.subscription_id != None,
                )
            )
            businesses = result.scalars().all()

            for biz in businesses:
                try:
                    local_hour    = get_local_hour(biz, utc_now)
                    local_weekday = get_local_weekday(biz, utc_now)
                    posting_schedule = get_posting_schedule(biz)
                    windows = get_approval_windows(posting_schedule)

                    for w in windows:
                        if local_weekday != w["weekday"] or local_hour != w["hour"]:
                            continue

                        if w["expire_day"]:
                            expire_result = await db.execute(
                                select(AgentAction).where(
                                    AgentAction.business_id == biz.id,
                                    AgentAction.scheduled_day == w["expire_day"],
                                    AgentAction.status == "pending",
                                )
                            )
                            for action in expire_result.scalars().all():
                                action.status = "expired"
                                logger.info(f"[Scheduler] Expired {w['expire_day']} post for {biz.name}")
                            await db.commit()

                        if w["send_day"]:
                            next_result = await db.execute(
                                select(AgentAction).where(
                                    AgentAction.business_id == biz.id,
                                    AgentAction.scheduled_day == w["send_day"],
                                    AgentAction.status == "pending",
                                    AgentAction.approval_email_sent == False,
                                )
                            )
                            next_action = next_result.scalars().first()
                            if not next_action:
                                continue

                            user_result = await db.execute(select(User).where(User.id == biz.owner_id))
                            user = user_result.scalar_one_or_none()
                            if not user:
                                continue

                            first_name = (user.full_name or "").split()[0] or "there"
                            await email_sender.send_post_approval(
                                business_id=str(biz.id),
                                user_email=user.email,
                                first_name=first_name,
                                business_name=biz.name,
                                post=next_action.action_parameters or {},
                                scheduled_day=w["send_day"],
                                approve_token=next_action.approval_token,
                                decline_token=next_action.decline_token,
                                db=db,
                            )
                            next_action.approval_email_sent = True
                            await db.commit()
                            logger.info(f"[Scheduler] {w['send_day']} approval email → {biz.name}")

                except Exception as e:
                    logger.error(f"[Scheduler] post_approval_and_expiry error for {biz.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"[Scheduler] post_approval_and_expiry outer error: {e}", exc_info=True)


# ─── 3. EXECUTE APPROVED POSTS ────────────────────────────────────────────────

async def execute_approved_posts():
    try:
        from database.session import AsyncSessionLocal
        from database.models import AgentAction
        from agent.executor import executor
        from sqlalchemy import select

        utc_now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentAction).where(
                    AgentAction.status == "executed",
                    AgentAction.executed_at == None,
                    AgentAction.scheduled_post_time <= utc_now,
                )
            )
            for action in result.scalars().all():
                try:
                    await executor.run(action, db)
                    action.executed_at = utc_now
                    await db.commit()
                    logger.info(f"[Scheduler] Posted {action.id} ({action.action_type})")
                except Exception as e:
                    logger.error(f"[Scheduler] Execute {action.id} error: {e}")

    except Exception as e:
        logger.error(f"[Scheduler] execute_approved_posts error: {e}")


# ─── 4. EXPIRE STALE ACTIONS ─────────────────────────────────────────────────

async def expire_stale_actions():
    try:
        from database.session import AsyncSessionLocal
        from database.models import AgentAction
        from sqlalchemy import update, and_

        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(AgentAction)
                .where(and_(AgentAction.status == "pending", AgentAction.created_at < cutoff))
                .values(status="expired")
                .returning(AgentAction.id)
            )
            expired = result.fetchall()
            await db.commit()
            if expired:
                logger.info(f"[Scheduler] Safety net expired {len(expired)} stale actions.")

    except Exception as e:
        logger.error(f"[Scheduler] expire_stale_actions error: {e}")


# ─── 5. ONBOARDING REMINDER ──────────────────────────────────────────────────

async def onboarding_reminder():
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business, User, EmailLog
        from email_system.sender import email_sender
        from sqlalchemy import select

        cutoff_72h = datetime.now(timezone.utc) - timedelta(hours=72)
        cutoff_96h = datetime.now(timezone.utc) - timedelta(hours=96)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(
                    Business.onboarding_step == 4,
                    Business.onboarding_completed == False,
                )
            )
            for biz in result.scalars().all():
                try:
                    log_result = await db.execute(
                        select(EmailLog).where(
                            EmailLog.business_id == biz.id,
                            EmailLog.email_type == "onboarding_4",
                        ).order_by(EmailLog.sent_at.asc())
                    )
                    original = log_result.scalars().first()
                    if not original:
                        continue

                    sent_at = original.sent_at
                    if sent_at.tzinfo is None:
                        sent_at = sent_at.replace(tzinfo=timezone.utc)
                    if not (cutoff_96h <= sent_at <= cutoff_72h):
                        continue

                    reminder_check = await db.execute(
                        select(EmailLog).where(
                            EmailLog.business_id == biz.id,
                            EmailLog.email_type == "onboarding_4_reminder",
                        )
                    )
                    if reminder_check.scalar_one_or_none():
                        continue

                    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
                    user = user_result.scalar_one_or_none()
                    if not user:
                        continue

                    first_name = (user.full_name or "").split()[0] or "there"
                    await email_sender.send_onboarding_step(
                        step=4, business_id=str(biz.id),
                        user_email=user.email, first_name=first_name,
                        business_name=biz.name, db=db,
                        extra_data={"is_reminder": True}
                    )
                    logger.info(f"[Scheduler] Onboarding reminder → {biz.name}")

                except Exception as e:
                    logger.error(f"[Scheduler] Onboarding reminder error for {biz.id}: {e}")

    except Exception as e:
        logger.error(f"[Scheduler] onboarding_reminder outer error: {e}")


# ─── 6. WEEKLY ANALYTICS (Friday 2pm local) ──────────────────────────────────

async def weekly_analytics():
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business, User
        from agent.analytics_agent import analytics_agent
        from email_system.sender import email_sender
        from sqlalchemy import select

        utc_now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(
                    Business.onboarding_completed == True,
                    Business.subscription_id != None,
                )
            )
            businesses = result.scalars().all()

            for biz in businesses:
                try:
                    local_hour    = get_local_hour(biz, utc_now)
                    local_weekday = get_local_weekday(biz, utc_now)

                    if local_weekday != 4 or local_hour != 14:
                        continue

                    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
                    user = user_result.scalar_one_or_none()
                    if not user:
                        continue

                    first_name = (user.full_name or "").split()[0] or "there"
                    insights = await analytics_agent.generate_weekly_insights(
                        business_id=str(biz.id), db=db,
                    )
                    await email_sender.send_weekly_analytics(
                        business_id=str(biz.id),
                        user_email=user.email,
                        first_name=first_name,
                        business_name=biz.name,
                        insights=insights,
                        db=db,
                    )
                    logger.info(f"[Scheduler] Weekly analytics sent → {biz.name}")

                except Exception as e:
                    logger.error(f"[Scheduler] Weekly analytics error for {biz.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"[Scheduler] weekly_analytics outer error: {e}", exc_info=True)


# ─── 7. SUBSCRIPTION HEALTH CHECK ────────────────────────────────────────────

async def subscription_health_check():
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business
        from billing.stripe_client import stripe_client
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(
                    Business.subscription_id != None,
                    Business.onboarding_completed == True,
                )
            )
            for biz in result.scalars().all():
                try:
                    sub = await stripe_client.get_subscription(biz.subscription_id)
                    if sub and sub.get("status") in ("canceled", "unpaid", "incomplete_expired"):
                        biz.subscription_id = None
                        await db.commit()
                        logger.info(f"[Scheduler] Deactivated {biz.name} (Stripe: {sub.get('status')})")
                except Exception as e:
                    logger.error(f"[Scheduler] Subscription health error for {biz.id}: {e}")

    except Exception as e:
        logger.error(f"[Scheduler] subscription_health_check outer error: {e}")


# ─── REGISTER & START ─────────────────────────────────────────────────────────

def start_scheduler():
    scheduler.add_job(weekly_content_generation, IntervalTrigger(hours=1),
        id="weekly_content_generation", name="Weekly content gen (user's kickoff day 9pm local)",
        replace_existing=True, misfire_grace_time=600)

    scheduler.add_job(post_approval_and_expiry, IntervalTrigger(hours=1),
        id="post_approval_and_expiry", name="Post approval emails + expiry",
        replace_existing=True, misfire_grace_time=600)

    scheduler.add_job(execute_approved_posts, IntervalTrigger(minutes=15),
        id="execute_approved_posts", name="Execute approved posts",
        replace_existing=True, misfire_grace_time=300)

    scheduler.add_job(expire_stale_actions, IntervalTrigger(minutes=30),
        id="expire_stale_actions", name="Expire stale actions (3-day net)",
        replace_existing=True, misfire_grace_time=300)

    scheduler.add_job(onboarding_reminder, IntervalTrigger(hours=1),
        id="onboarding_reminder", name="Onboarding 72h reminder",
        replace_existing=True, misfire_grace_time=600)

    scheduler.add_job(weekly_analytics, IntervalTrigger(hours=1),
        id="weekly_analytics", name="Weekly analytics (Fri 2pm local)",
        replace_existing=True, misfire_grace_time=600)

    scheduler.add_job(subscription_health_check,
        CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="subscription_health_check", name="Subscription health check",
        replace_existing=True, misfire_grace_time=1800)

    scheduler.start()
    logger.info("[Scheduler] Started. Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  ✓ {job.name} — next: {job.next_run_time}")