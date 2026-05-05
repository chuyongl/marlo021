"""
scheduler.py
Marlo background scheduler — all time-based jobs.

Weekly content flow:
  Sunday  9pm local  → generate all content + send Sunday kickoff email (Monday post approval)
  Tuesday 2pm local  → send Wednesday post approval; expire Monday post if still pending
  Thursday 2pm local → send Friday post approval; expire Wednesday post if still pending
  Friday  6pm local  → expire Friday post if still pending

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


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_local_hour(biz, utc_now) -> int:
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(biz.preferred_post_timezone or biz.timezone or "America/New_York")
        return utc_now.astimezone(tz).hour
    except Exception:
        return utc_now.hour

def get_local_weekday(biz, utc_now) -> int:
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(biz.preferred_post_timezone or biz.timezone or "America/New_York")
        return utc_now.astimezone(tz).weekday()
    except Exception:
        return utc_now.weekday()

def build_scheduled_post_time(biz, day_name: str) -> datetime:
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(biz.preferred_post_timezone or biz.timezone or "America/New_York")
        now_local = datetime.now(tz)
        day_map = {"Monday": 0, "Wednesday": 2, "Friday": 4}
        target_weekday = day_map.get(day_name, 0)
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
    Runs every hour. For each business, fires only on Sunday between 21:00-21:59 local.
    Generates all posts for the week, stores as pending actions, sends Sunday kickoff email
    containing: last week's results + this week's strategy + image guide + Monday post approval.
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
                    platforms  = ["instagram"]  # default; extend when more platforms supported

                    business_dict = {
                        "name": biz.name,
                        "industry": biz.industry or "",
                        "description": biz.description or "",
                        "tone_of_voice": biz.tone_of_voice or "warm and authentic",
                        "target_audience": biz.target_audience or "local customers",
                        "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
                    }

                    posts_per_week = biz.posts_per_week or 3
                    all_days       = ["Monday", "Wednesday", "Friday"]
                    scheduled_days = all_days[:posts_per_week]

                    # Generate social posts
                    posts = await content_pipeline.generate_week_of_content(
                        business_id=str(biz.id),
                        db=db,
                        platforms=platforms,
                    )
                    posts = posts[:posts_per_week]
                    for i, post in enumerate(posts):
                        post["scheduled_day"] = scheduled_days[i]

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

                    # Store as pending actions
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
                            scheduled_day="Monday",
                            approval_email_sent=False,
                            created_at=datetime.now(timezone.utc),
                        )
                        db.add(ads_action)
                        stored_actions.append(ads_action)

                    await db.commit()

                    # Last week stats for kickoff email
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

                    # Send Sunday kickoff email (Monday post + ads + strategy + image guide)
                    monday_action = next((a for a in stored_actions if a.scheduled_day == "Monday" and a.action_type != "google_ads_campaign"), None)
                    ads_stored    = next((a for a in stored_actions if a.action_type == "google_ads_campaign"), None)

                    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
                    user = user_result.scalar_one_or_none()

                    if user and monday_action:
                        first_name = (user.full_name or "").split()[0] or "there"
                        await email_sender.send_weekly_kickoff(
                            business_id=str(biz.id),
                            user_email=user.email,
                            first_name=first_name,
                            business_name=biz.name,
                            monday_post=monday_action.action_parameters,
                            monday_approve_token=monday_action.approval_token,
                            monday_decline_token=monday_action.decline_token,
                            google_campaign=google_campaign,
                            ads_approve_token=ads_stored.approval_token if ads_stored else None,
                            ads_decline_token=ads_stored.decline_token if ads_stored else None,
                            scheduled_days=scheduled_days,
                            last_week_stats=last_week_stats,
                            db=db,
                        )
                        monday_action.approval_email_sent = True
                        if ads_stored:
                            ads_stored.approval_email_sent = True
                        await db.commit()

                    logger.info(f"[Scheduler] Weekly kickoff sent for {biz.name} ({len(posts)} posts)")

                except Exception as e:
                    logger.error(f"[Scheduler] Weekly gen error for {biz.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"[Scheduler] weekly_content_generation outer error: {e}", exc_info=True)


# ─── 2. POST APPROVAL EMAILS + EXPIRY (every hour) ───────────────────────────

async def post_approval_and_expiry():
    """
    Runs every hour. Per business local time:
    - Tuesday  2pm → expire Monday post, send Wednesday approval email
    - Thursday 2pm → expire Wednesday post, send Friday approval email
    - Friday   6pm → expire Friday post
    """
    try:
        from database.session import AsyncSessionLocal
        from database.models import Business, User, AgentAction
        from email_system.sender import email_sender
        from sqlalchemy import select

        utc_now = datetime.now(timezone.utc)

        WINDOWS = [
            {"weekday": 1, "hour": 14, "expire_day": "Monday",    "send_day": "Wednesday"},
            {"weekday": 3, "hour": 14, "expire_day": "Wednesday",  "send_day": "Friday"},
            {"weekday": 4, "hour": 18, "expire_day": "Friday",     "send_day": None},
        ]

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

                    for w in WINDOWS:
                        if local_weekday != w["weekday"] or local_hour != w["hour"]:
                            continue

                        # Expire previous post
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

                        # Send next post approval email
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
                            logger.info(f"[Scheduler] {w['send_day']} approval email sent to {biz.name}")

                except Exception as e:
                    logger.error(f"[Scheduler] post_approval_and_expiry error for {biz.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"[Scheduler] post_approval_and_expiry outer error: {e}", exc_info=True)


# ─── 3. EXECUTE APPROVED POSTS (every 15min) ─────────────────────────────────

async def execute_approved_posts():
    """Find approved posts whose scheduled_post_time has passed and actually post them."""
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
                    logger.info(f"[Scheduler] Posted action {action.id} ({action.action_type})")
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