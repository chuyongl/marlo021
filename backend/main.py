"""
main.py

Brown Bag API — FastAPI application entry point.

Brown Bag is the publication. Marlo is the backend system (this repo, this
API). No user-visible string should contain "Marlo".

STATUS: Pilot build (Oct 2026). Public site, vendor app, editor app and the
weekly issue all run from this API. See docs/ARCHITECTURE.md.
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

VERSION = "0.5.0"
app = FastAPI(title="Brown Bag API", version=VERSION)

# Trust Railway's proxy headers so request.url uses https, not http
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=__import__("core.config", fromlist=["CORS_ORIGINS"]).CORS_ORIGINS,
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
        from database import migrate
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await migrate.run(conn)
        logger.info(
            f"[Startup] Database ready — {len(Base.metadata.tables)} tables verified."
        )
    except Exception as e:
        logger.error(f"[Startup] DB check failed (non-fatal): {e}")

    # 2. First-boot seed: Seattle market, venues, sample content.
    try:
        from database.session import AsyncSessionLocal
        from database.seed import seed_if_empty
        async with AsyncSessionLocal() as db:
            await seed_if_empty(db)
    except Exception as e:
        logger.error(f"[Startup] Seed failed (non-fatal): {e}")

    # 3. Background scheduler.
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
    return {"status": "ok", "version": VERSION}


@app.get("/health/detailed")
async def detailed_health():
    import asyncpg

    health = {
        "api": "ok",
        "version": VERSION,
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


# --- Brown Bag routers ---
include("public.router")    # website, QR landings, follow, share, report, clicks, media
include("vendors.router")   # vendor app: signup, magic link, interview, drafts, reach
include("editors.router")   # editor app: queue, vendors, codes, venues, issue, settings


# --- Archived. Do NOT re-add without a deliberate decision. ---
#   auth/                     → editors get their own auth
#   businesses/               → replaced by vendors/
#   agent/approval_router.py  → replaced by editors/review.py
#   agent/router.py           → v1 agent endpoints
#   agent/debug_router.py     → built around Instagram posting
#   email_system/inbound.py   → intake moved to the vendor web app
#   integrations/oauth.py, billing/