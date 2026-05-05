"""
scheduler.py
Marlo background scheduler — all time-based jobs.

Weekly content flow (fully data-driven from business.posting_schedule):
  Sunday 9pm local  → generate all posts + send kickoff email (first post approval)
  Day before each post at 2pm local → send approval email, expire previous post
  Last post day 6pm local → expire if still pending

posting_schedule examples:
  ["Monday", "Wednesday", "Friday"]         ← default 3x/week
  ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]  ← daily weekdays
  ["Monday"]                                 ← once a week
  ["Monday", "Wednesday", "Friday", "Saturday", "Sunday"]   ← 5x/week

Other jobs:
  Every 30min → expire stale actions older than 3 days (safety net)
  Every 15min → execute approved posts whose scheduled_post_time has passed
  Every hour  → onboarding reminder (72h no reply to email 4)
  Monday 8am UTC → weekly performance report
  Daily  2am UTC → subscription health check
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


# ─── HELPERS ─────────────────────────────────────────────────────────────────

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
    return get_local_dt(biz, utc_now).strftime("%A")  # "Monday", "Tuesday" etc

def get_posting_schedule(biz) -> list:
    """
    Returns the ordered list of posting days for this business.
    Reads from biz.posting_schedule (JSON column), falls back to posts_per_week,
    falls back to ["Monday", "Wednesday", "Friday"].
    """
    # Try JSON column first
    schedule = biz.posting_schedule
    if schedule and isinstance(schedule, list) and len(schedule) > 0:
        # Validate all entries are real day names
        valid = [d for d in schedule if d in DAY_TO_WEEKDAY]
        if valid:
            # Return in week order
            return sorted(valid, key=lambda d: DAY_TO_WEEKDAY[d])

    # Fall back to posts_per_week
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
    """
    Build approval/expiry windows from a posting schedule.
    For each post day, the approval email goes out the day before at 2pm.
    That same window also expires the previous post.
    The last post expires at 6pm on its own day.

    Returns list of dicts:
    {
      "weekday": int,        # local weekday to fire on
      "hour": int,           # local hour to fire on
      "send_day": str|None,  # which post to send approval for
      "expire_day": str|None # which post to expire
    }
    """
    if not posting_schedule:
        return []

    windows = []
    for i, day in enumerate(posting_schedule):
        day_weekday = DAY_TO_WEEKDAY[day]

        # Approval email goes out day before at 2pm (except first post — that's in kickoff email)
        if i > 0:
            prev_day_weekday = (day_weekday - 1) % 7
            expire_day = posting_schedule[i - 1]  # expire the post before this one
            windows.append({
                "weekday": prev_day_weekday,
                "hour": 14,
                "send_day": day,
                "expire_day": expire_day,
            })

    # Last post expires at 6pm on its own day
    last_day = posting_schedule[-1]
    windows.append({
        "weekday": DAY_TO_WEEKDAY[last_day],
        "hour": 18,
        "send_day": None,
        "expire_day": last_day,
    })

    return windows

def build_scheduled_post_time(biz, day_name: str) -> datetime:
    """Build UTC datetime for when this post should go live."""
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


# ─── 1. WEEKLY CONTENT GENERATION (Sunday 9pm local) ─────────────────────────

async def weekly_content_generation():
    """
    Runs every hour. Fires for each business on Sunday between 21:00-21:59 local.
    - Reads posting_schedule from DB (fully data-driven)
    - Generates exactly len(posting_schedule) posts
    - Sends kickoff email with: last week stats + this week strategy + image guide + first post approval
    """
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

                    # Only fire Sunday (6) 21:00-21:59 local
                    if local_weekday != 6 or local_hour != 21:
                        continue

                    # Idempotency: skip if already generated this week
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

                    # Get this business's posting schedule
                    posting_schedule = get_posting_schedule(biz)
                    posts_count = len(posting_schedule)
                    logger.info(f"[Scheduler] {biz.name} posting schedule: {posting_schedule}")

                    # Connected platforms
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

                    # Generate exactly posts_count posts
                    posts = await content_pipeline.generate_week_of_content(
                        business_id=str(biz.id),
                        db=db,
                        platforms=platforms,
                    )
                    # Pad or trim to match schedule length
                    while len(posts) < posts_count:
                        posts.append(posts[-1].copy() if posts else {})
                    posts = posts[:posts_count]

                    for i, post in enumerate(posts):
                        post["scheduled_day"] = posting_schedule[i]

                    # Generate Google Ads if connected
                    google_campaign = None
                    if has_google:
                        strategy = await strategy_agent.decide(
                            "google_ads", {"business": business_dict}, str(biz.id)
                        )
                        google_campaign = await google_ads_agent.generate_campaign(
                            business=business_dict,
                            strategy=strategy,
                            business_id=str(biz.id),
                        )

                    # Store all as pending actions
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
                            created_at=datetime.now(timezone.utc),
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
                            created_at=datetime.now(timezone.utc),
                        )
                        db.add(ads_action)
                        stored_actions.append(ads_action)

                    await db.commit()

                    # Last week stats
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

                    # First post action (for kickoff email)
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
                            last_week_stats=last_week_stats,
                            db=db,
                        )
                        first_action.approval_email_sent = True
                        if ads_stored:
                            ads_stored.approval_email_sent = True
                        await db.commit()

                    logger.info(f"[Scheduler] Weekly kickoff sent for {biz.name} — {posts_count} posts: {posting_schedule}")

                except Exception as e:
                    logger.error(f"[Scheduler] Weekly gen error for {biz.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"[Scheduler] weekly_content_generation outer error: {e}", exc_info=True)


# ─── 2. POST APPROVAL EMAILS + EXPIRY (every hour) ───────────────────────────

async def post_approval_and_expiry():
    """
    Runs every hour. Fully data-driven from posting_schedule.
    For each business, computes approval windows dynamically and fires accordingly.
    """
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

                    # Build windows dynamically from this business's schedule
                    posting_schedule = get_posting_schedule(biz)
                    windows = get_approval_windows(posting_schedule)

                    for w in windows:
                        if local_weekday != w["weekday"] or local_hour != w["hour"]:
                            continue

                        # Expire previous post if still pending
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

                        # Send approval email for next post
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


# ─── 3. EXECUTE APPROVED POSTS (every 15min) ─────────────────────────────────

async def execute_approved_posts():
    """Find approved posts whose scheduled_post_time has passed and post them."""
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


# ─── 4. EXPIRE STALE ACTIONS — safety net (every 30min) ──────────────────────

async def expire_stale_actions():
    """Safety net: expire any pending action older than 3 days."""
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


# ─── 5. ONBOARDING REMINDER (every hour) ─────────────────────────────────────

async def onboarding_reminder():
    """Send email 4 reminder if business stuck on step 4 for 72h with no reply."""
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


# ─── 6. WEEKLY PERFORMANCE REPORT (Monday 8am UTC) ───────────────────────────

async def weekly_performance_report():
    """Monday 8am UTC: send last week's stats to all active businesses."""
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business, User, AgentAction
        from email_system.sender import email_sender
        from sqlalchemy import select

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(
                    Business.onboarding_completed == True,
                    Business.subscription_id != None,
                )
            )
            for biz in result.scalars().all():
                try:
                    actions_result = await db.execute(
                        select(AgentAction).where(
                            AgentAction.business_id == biz.id,
                            AgentAction.created_at >= week_ago,
                        )
                    )
                    actions = actions_result.scalars().all()
                    if not actions:
                        continue

                    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
                    user = user_result.scalar_one_or_none()
                    if not user:
                        continue

                    first_name = (user.full_name or "").split()[0] or "there"
                    await email_sender.send_weekly_report(
                        business_id=str(biz.id),
                        user_email=user.email,
                        first_name=first_name,
                        business_name=biz.name,
                        report_data={
                            "week_start":     week_ago.strftime("%b %d"),
                            "week_end":       datetime.now(timezone.utc).strftime("%b %d"),
                            "approved_count": len([a for a in actions if a.status == "executed"]),
                            "skipped_count":  len([a for a in actions if a.status == "rejected"]),
                            "expired_count":  len([a for a in actions if a.status == "expired"]),
                            "pending_count":  len([a for a in actions if a.status == "pending"]),
                            "total_count":    len(actions),
                        },
                        db=db,
                    )
                    logger.info(f"[Scheduler] Weekly report → {biz.name}")

                except Exception as e:
                    logger.error(f"[Scheduler] Weekly report error for {biz.id}: {e}")

    except Exception as e:
        logger.error(f"[Scheduler] weekly_performance_report outer error: {e}")


# ─── 7. SUBSCRIPTION HEALTH CHECK (daily 2am UTC) ────────────────────────────

async def subscription_health_check():
    """Daily 2am UTC: deactivate businesses with cancelled Stripe subscriptions."""
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
        id="weekly_content_generation", name="Weekly content gen (Sun 9pm local)",
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

    scheduler.add_job(weekly_performance_report,
        CronTrigger(day_of_week="mon", hour=8, minute=0, timezone="UTC"),
        id="weekly_performance_report", name="Weekly performance report",
        replace_existing=True, misfire_grace_time=3600)

    scheduler.add_job(subscription_health_check,
        CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="subscription_health_check", name="Subscription health check",
        replace_existing=True, misfire_grace_time=1800)

    scheduler.start()
    logger.info("[Scheduler] Started. Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  ✓ {job.name} — next: {job.next_run_time}")