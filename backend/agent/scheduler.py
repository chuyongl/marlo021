"""
scheduler.py
Marlo background scheduler.

STATUS: Mid-pivot (Aug 2026).

All seven original jobs belonged to the Instagram-posting product and have
been removed along with the code they called (see backend/archive/).

The newsletter jobs are not written yet. Planned set, per docs/ARCHITECTURE.md:

    supply_monitor           every 6h    count material, report runway, escalate
    weekly_vendor_interview  hourly      ask each vendor one question
    interview_chase          daily       nudge non-responders
    assemble_issue           hourly      build the block pool
    request_block_approval   on assembly email vendors their block
    send_issue               hourly      send at market local time
    recompute_interests      daily       rebuild interest_vector
    reserve_health           weekly      report reserve depth

Starting with zero jobs is correct right now, not a bug. The startup log
says so explicitly so nobody has to wonder.

What survives from v1 (all still useful, all model-agnostic):
  - Sentry network-error suppression   (ADR-013)
  - Timezone helpers                   (markets have send_day/send_hour local)
  - Day-name / weekday mapping
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

ALL_DAYS_ORDERED = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"]

DAY_TO_WEEKDAY = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                  "Friday": 4, "Saturday": 5, "Sunday": 6}

DEFAULT_TZ = "America/Los_Angeles"


# ─── ERROR HANDLING (ADR-013) ─────────────────────────────────────────────────

def is_network_error(e: Exception) -> bool:
    """
    True for transient infrastructure errors that don't warrant a Sentry alert.
    Railway has occasional DNS blips; these resolve on their own and are not
    code bugs. Without this filter one outage produces dozens of alerts.
    """
    msg = str(e).lower()
    return any(keyword in msg for keyword in [
        "errno -3",
        "temporary failure in name resolution",
        "connection is closed",
        "connection refused",
        "connection reset",
        "timeout",
        "could not connect",
        "interface error",
        "network is unreachable",
    ])


def log_error(context: str, e: Exception, exc_info: bool = False):
    """
    Network errors → WARNING (Sentry ignores).
    Real bugs      → ERROR   (Sentry captures).
    """
    if is_network_error(e):
        logger.warning(
            f"[Scheduler] {context}: network issue (auto-recovering) — {type(e).__name__}"
        )
    else:
        logger.error(f"[Scheduler] {context}: {e}", exc_info=exc_info)


# ─── TIMEZONE HELPERS ─────────────────────────────────────────────────────────
# Written against any object exposing a `timezone` attribute — a market now,
# a vendor later. Deliberately not tied to a specific model.

def get_tz(obj) -> ZoneInfo:
    """Resolve an object's timezone, falling back safely."""
    tz_name = getattr(obj, "timezone", None) or DEFAULT_TZ
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo(DEFAULT_TZ)


def get_local_dt(obj, utc_now: datetime = None) -> datetime:
    """Convert UTC now into the object's local time."""
    utc_now = utc_now or datetime.now(timezone.utc)
    return utc_now.astimezone(get_tz(obj))


def get_local_hour(obj, utc_now: datetime = None) -> int:
    return get_local_dt(obj, utc_now).hour


def get_local_weekday(obj, utc_now: datetime = None) -> int:
    return get_local_dt(obj, utc_now).weekday()


def get_local_day_name(obj, utc_now: datetime = None) -> str:
    return get_local_dt(obj, utc_now).strftime("%A")


def is_send_window(market, utc_now: datetime = None) -> bool:
    """
    True when it's the market's configured send day and hour, local time.

    Jobs run hourly and check this rather than relying on cron, so a Railway
    restart can't cause a permanently missed send — the next hourly tick
    picks it up.
    """
    utc_now = utc_now or datetime.now(timezone.utc)
    target_weekday = DAY_TO_WEEKDAY.get(getattr(market, "send_day", None), 3)
    target_hour = getattr(market, "send_hour", 17)
    return (
        get_local_weekday(market, utc_now) == target_weekday
        and get_local_hour(market, utc_now) == target_hour
    )


# ─── JOB REGISTRATION ─────────────────────────────────────────────────────────

def start_scheduler():
    """
    Start APScheduler. No jobs are registered yet — the newsletter pipeline
    isn't built. Add jobs here as each module lands.

    Pattern for new jobs (keep these habits, they were learned the hard way):

        scheduler.add_job(
            supply_monitor,
            IntervalTrigger(hours=6),
            id="supply_monitor",
            name="Content supply monitor",
            replace_existing=True,
            misfire_grace_time=600,
        )

      - Import DB models and services INSIDE the job function, never at module
        top level. Avoids circular imports and keeps startup fast.
      - Open a fresh session inside the job:
            async with AsyncSessionLocal() as db:
        Never reuse a session created elsewhere — it will already be closed.
      - Wrap the body in try/except and route errors through log_error().
      - Use datetime.now(timezone.utc). Never datetime.utcnow() (ADR-005).
    """
    scheduler.start()

    jobs = scheduler.get_jobs()
    if not jobs:
        logger.info(
            "[Scheduler] Started with NO jobs registered. "
            "Expected during the newsletter pivot — see docs/ARCHITECTURE.md."
        )
        return

    logger.info(f"[Scheduler] Started with {len(jobs)} job(s).")
    for job in jobs:
        logger.info(f"  ✓ {job.name} — next: {job.next_run_time}")