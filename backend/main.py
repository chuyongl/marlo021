"""
main.py

Brown Bag API — FastAPI application entry point.

Brown Bag is the publication. Marlo is the backend system (this repo, this
API). No user-visible string should contain "Marlo".

STATUS: Build in progress (Aug 2026).
All v1 Instagram-era routers have been archived. The Brown Bag routers are
being built and will be registered here as each lands. See docs/TASKS.md.
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development"),
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Brown Bag API", version="0.3.0")

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
    # 1. Create tables from the models.
    #    Safe on every boot — create_all only adds what's missing. The old v1
    #    tables (businesses, agent_actions, platform_integrations) still exist
    #    in the database and are left untouched; nothing reads them.
    try:
        from database.session import engine
        from database.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(
            f"[Startup] Database ready — {len(Base.metadata.tables)} tables verified."
        )
    except Exception as e:
        logger.error(f"[Startup] DB check failed (non-fatal): {e}")

    # 2. Background scheduler.
    #    Currently registers zero jobs — correct during the build, not a bug.
    try:
        from agent.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"[Startup] Scheduler failed to start (non-fatal): {e}")


# ─── HEALTH ───────────────────────────────────────────────────────────────────

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.3.0"}


@app.get("/health/detailed")
async def detailed_health():
    import asyncpg

    health = {
        "api": "ok",
        "version": "0.3.0",
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

    try:
        from database.models import Base
        health["tables_defined"] = len(Base.metadata.tables)
    except Exception as e:
        health["tables_defined"] = f"error: {e}"

    return health


# ─── ROUTER REGISTRATION ──────────────────────────────────────────────────────

def include(module_path: str, attr: str = "router"):
    """
    Import and register a router, logging instead of crashing on failure.

    Modules are landing one at a time during the build. A router that isn't
    written yet should be a startup log line, not a dead API.
    """
    try:
        module = __import__(module_path, fromlist=[attr])
        app.include_router(getattr(module, attr))
        logger.info(f"[Routers] Loaded {module_path}")
    except ModuleNotFoundError:
        logger.info(f"[Routers] Not built yet: {module_path}")
    except Exception as e:
        logger.error(f"[Routers] FAILED {module_path} — {type(e).__name__}: {e}")


# --- Brown Bag routers. Uncomment as each is built (docs/TASKS.md) ---

# P0
# include("editors.router")          # login, review queue          — P0 #6
# include("subscribers.router")      # unsubscribe                  — P0 #10

# P1
# include("vendors.router")          # code signup, magic link      — P1 #11-13
# include("vendors.conversation")    # interviewer chat             — P1 #14

# P2
# include("subscribers.scan")        # GET /v/{scan_code}           — P2 #20
# include("vendors.workspace")       # drafts, library, corrections — P2 #22-23


# --- Archived. Do NOT re-add without a deliberate decision. ---
#   auth/                     → editors get their own auth
#   businesses/               → replaced by vendors/
#   agent/approval_router.py  → replaced by editors/review.py
#   agent/router.py           → v1 agent endpoints
#   agent/debug_router.py     → built around Instagram posting
#   email_system/inbound.py   → intake moved to the vendor web app
#   integrations/oauth.py, billing/