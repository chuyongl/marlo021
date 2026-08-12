"""
main.py
Marlo API — FastAPI application entry point.

STATUS: Mid-pivot (Aug 2026).
The Instagram-posting product has been archived to backend/archive/.
The newsletter product is not built yet. This file registers only the
routers that still exist and still make sense.

Router registration is deliberately fault-tolerant: during the pivot,
modules are in flux, and one broken import should not take the whole
API down. Failures are logged loudly at startup instead.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from datetime import datetime, timezone
import logging
import os
import sentry_sdk
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

load_dotenv(dotenv_path="../.env")

logger = logging.getLogger(__name__)

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development"),
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Marlo API", version="0.2.0")

# Trust Railway's proxy headers so request.url uses https, not http
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── STARTUP ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # 1. Auto-create DB tables from the models
    try:
        from database.session import engine
        from database.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[Startup] Database tables verified/created.")
    except Exception as e:
        logger.error(f"[Startup] DB check error (non-fatal): {e}")

    # 2. Incremental migrations — safe to run on every startup.
    #    NOTE: the newsletter schema (markets, subscribers, scan_events,
    #    content_items, issues, ...) is not written yet. When it is, the
    #    new tables come from create_all above; only ALTERs belong here.
    try:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
        conn = await asyncpg.connect(db_url)
        try:
            exists = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = 'businesses' AND column_name = 'user_memory'
            """)
            if not exists:
                await conn.execute(
                    "ALTER TABLE businesses ADD COLUMN user_memory JSONB DEFAULT NULL"
                )
                logger.info("[Startup] Migration: added user_memory column.")
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"[Startup] Migration error (non-fatal): {e}")

    # 3. Background scheduler
    try:
        from agent.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"[Startup] Scheduler startup error (non-fatal): {e}")


# ─── HEALTH ───────────────────────────────────────────────────────────────────

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/health/detailed")
async def detailed_health():
    import asyncpg

    health = {
        "api": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        conn = await asyncpg.connect(
            os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        health["database"] = "ok"
    except Exception as e:
        health["database"] = f"error: {e}"

    return health


# ─── ROUTER REGISTRATION ──────────────────────────────────────────────────────

def include(module_path: str, attr: str = "router", required: bool = False):
    """
    Import and register a router, logging instead of crashing on failure.

    During the pivot several modules are half-migrated. A broken import
    should surface as a startup warning, not a dead API.

    Set required=True for routers whose absence means the app is useless.
    """
    try:
        module = __import__(module_path, fromlist=[attr])
        app.include_router(getattr(module, attr))
        logger.info(f"[Routers] Loaded {module_path}")
    except Exception as e:
        level = logger.error if required else logger.warning
        level(f"[Routers] SKIPPED {module_path} — {type(e).__name__}: {e}")


# --- Active ---
include("auth.router")
include("email_system.inbound", required=True)   # content intake pipe
include("agent.approval_router")                 # to be repurposed: vendor block approval
include("businesses.router")                     # to be replaced by vendors/router.py

# --- Uncertain: may still import archived modules. Loaded defensively. ---
include("agent.router")
include("agent.debug_router")

# --- Archived, deliberately NOT registered ---
#   integrations.oauth        → backend/archive/oauth.py
#   billing.billing_router    → backend/archive/billing/
# Do not re-add without a deliberate decision. See docs/PRODUCT.md.

# --- Not built yet (newsletter product) ---
#   subscribers.router        → GET /v/{scan_code}, /subscribe, /unsubscribe
#   vendors.router            → /vendor/join, /vendor/qr/{id}
# See docs/API.md for the target surface.