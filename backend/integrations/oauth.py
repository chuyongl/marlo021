from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx, secrets, os, uuid
from datetime import datetime
from database.session import get_db
from database.models import PlatformIntegration, Business
from auth.router import get_current_user
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

router = APIRouter(prefix="/integrations", tags=["integrations"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
APP_BASE = os.getenv("APP_BASE_URL", "http://localhost:8000")
FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:3000")

GOOGLE_SCOPES = " ".join([
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/business.manage",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "openid", "email"
])
META_SCOPES = "ads_management,ads_read,instagram_basic,instagram_content_publish,pages_read_engagement"

oauth_states: dict = {}  # Use Redis in production (Day 38)

@router.get("/connect/google")
async def connect_google(business_id: str):
    # No login required — link comes from onboarding email
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"business_id": business_id, "platform": "google"}
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={APP_BASE}/integrations/callback/google"
        f"&response_type=code&scope={GOOGLE_SCOPES}"
        f"&access_type=offline&prompt=consent&state={state}"
    )
    return RedirectResponse(auth_url)

@router.get("/callback/google")
async def google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    state_data = oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{APP_BASE}/integrations/callback/google",
                "grant_type": "authorization_code"
            }
        )
        tokens = response.json()

    if "error" in tokens:
        raise HTTPException(status_code=400, detail=f"OAuth error: {tokens['error']}")

    integration = PlatformIntegration(
        id=uuid.uuid4(),
        business_id=state_data["business_id"],
        platform="google_ads",
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        scopes=GOOGLE_SCOPES.split(),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(integration)

    # Update onboarding step
    from sqlalchemy import select, update
    await db.execute(
        update(Business)
        .where(Business.id == state_data["business_id"])
        .values(onboarding_step=2)
    )
    await db.commit()

    # Show a friendly success page — the user is on their phone/browser
    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">Google connected!</h2>
    <p style="color:#666">Check your email — Marlo is sending the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)

@router.get("/connect/meta")
async def connect_meta(business_id: str):
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"business_id": business_id, "platform": "meta"}
    meta_app_id = os.getenv("META_APP_ID")
    auth_url = (
        f"https://www.facebook.com/v21.0/dialog/oauth"
        f"?client_id={meta_app_id}"
        f"&redirect_uri={APP_BASE}/integrations/callback/meta"
        f"&scope={META_SCOPES}&state={state}"
    )
    return RedirectResponse(auth_url)

@router.get("/callback/meta")
async def meta_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    state_data = oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    meta_app_id = os.getenv("META_APP_ID")
    meta_app_secret = os.getenv("META_APP_SECRET")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.facebook.com/v21.0/oauth/access_token",
            params={
                "client_id": meta_app_id, "client_secret": meta_app_secret,
                "redirect_uri": f"{APP_BASE}/integrations/callback/meta",
                "code": code
            }
        )
        tokens = response.json()

    integration = PlatformIntegration(
        id=uuid.uuid4(),
        business_id=state_data["business_id"],
        platform="meta",
        access_token=tokens["access_token"],
        scopes=META_SCOPES.split(","),
        is_active=True, created_at=datetime.utcnow()
    )
    db.add(integration)
    from sqlalchemy import update
    await db.execute(
        update(Business)
        .where(Business.id == state_data["business_id"])
        .values(onboarding_step=3)
    )
    await db.commit()

    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2>Facebook & Instagram connected!</h2>
    <p style="color:#666">Check your email — Marlo is sending the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)