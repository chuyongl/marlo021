from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from datetime import datetime
import os
import sentry_sdk

load_dotenv(dotenv_path="../.env")

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development")
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Marlo API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Auto-create any new tables on deploy (safe — won't drop existing tables)."""
    try:
        from database.session import engine
        from database.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables verified/created.")
    except Exception as e:
        print(f"Startup DB check error (non-fatal): {e}")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/health/detailed")
async def detailed_health():
    import redis.asyncio as aioredis
    import asyncpg

    health = {"api": "ok", "timestamp": datetime.utcnow().isoformat()}

    try:
        r = await aioredis.from_url(os.getenv("REDIS_URL"))
        await r.ping()
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"

    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL").replace("+asyncpg", ""))
        await conn.fetchval("SELECT 1")
        await conn.close()
        health["database"] = "ok"
    except Exception as e:
        health["database"] = f"error: {str(e)}"

    return health

from auth.router import router as auth_router
app.include_router(auth_router)

from businesses.router import router as businesses_router
from integrations.oauth import router as oauth_router
app.include_router(businesses_router)
app.include_router(oauth_router)

from agent.approval_router import router as approval_router
app.include_router(approval_router)

from email_system.inbound import router as inbound_router
app.include_router(inbound_router)

from agent.router import router as agent_router
app.include_router(agent_router)

from billing.billing_router import router as billing_router
app.include_router(billing_router)