from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx, secrets, os, uuid, asyncio
from datetime import datetime
from database.session import get_db
from database.models import PlatformIntegration, Business, User
from auth.router import get_current_user
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

router = APIRouter(prefix="/integrations", tags=["integrations"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
MAILCHIMP_CLIENT_ID = os.getenv("MAILCHIMP_CLIENT_ID")
MAILCHIMP_CLIENT_SECRET = os.getenv("MAILCHIMP_CLIENT_SECRET")
APP_BASE = os.getenv("APP_BASE_URL", "http://localhost:8000")
FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:3000")

GOOGLE_SCOPES = " ".join([
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/business.manage",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "openid", "email"
])
META_SCOPES = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish"

oauth_states: dict = {}  # Use Redis in production (Day 38)

@router.get("/connect/google")
async def connect_google(business_id: str):
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

    from security.encryption import encrypt_token
    integration = PlatformIntegration(
        id=uuid.uuid4(),
        business_id=state_data["business_id"],
        platform="google_ads",
        access_token=encrypt_token(tokens["access_token"]),
        refresh_token=encrypt_token(tokens.get("refresh_token", "")),
        scopes=GOOGLE_SCOPES.split(),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(integration)

    from sqlalchemy import select, update
    await db.execute(
        update(Business)
        .where(Business.id == state_data["business_id"])
        .values(onboarding_step=2)
    )
    await db.commit()

    business_id_copy = state_data["business_id"]
    async def send_email_2():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        async with AsyncSessionLocal() as new_db:
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id_copy))
            biz = biz_result.scalar_one_or_none()
            if biz:
                user_result = await new_db.execute(select(User).where(User.id == biz.owner_id))
                usr = user_result.scalar_one_or_none()
                if usr:
                    first_name = (usr.full_name or "").split()[0] or "there"
                    await email_sender.send_onboarding_step(
                        step=2,
                        business_id=business_id_copy,
                        user_email=usr.email,
                        first_name=first_name,
                        business_name=biz.name,
                        db=new_db
                    )
    asyncio.create_task(send_email_2())

    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">Google connected!</h2>
    <p style="color:#666">Check your email — Marlo is sending the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)

@router.get("/connect/mailchimp")
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
async def meta_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    error_code: str = None,
    error_message: str = None,
    db: AsyncSession = Depends(get_db)
):
    if error or error_code:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
        <div style="font-size:48px">❌</div>
        <h2 style="color:#cc0000">Connection failed</h2>
        <p style="color:#666">{error_message or error or 'Unknown error'}</p>
        <p style="color:#999;font-size:14px">Please close this tab and try again.</p>
        </body></html>
        """)

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

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

    if "error" in tokens:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
        <div style="font-size:48px">❌</div>
        <h2 style="color:#cc0000">Connection failed</h2>
        <p style="color:#666">{tokens['error'].get('message', 'Token exchange failed')}</p>
        <p style="color:#999;font-size:14px">Please close this tab and try again.</p>
        </body></html>
        """)

    from security.encryption import encrypt_token
    integration = PlatformIntegration(
        id=uuid.uuid4(),
        business_id=state_data["business_id"],
        platform="meta",
        access_token=encrypt_token(tokens["access_token"]),
        scopes=META_SCOPES.split(","),
        is_active=True, created_at=datetime.utcnow()
    )
    db.add(integration)

    from sqlalchemy import select, update
    await db.execute(
        update(Business)
        .where(Business.id == state_data["business_id"])
        .values(onboarding_step=3)
    )
    await db.commit()

    business_id_copy = state_data["business_id"]
    async def send_email_3():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        async with AsyncSessionLocal() as new_db:
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id_copy))
            biz = biz_result.scalar_one_or_none()
            if biz:
                user_result = await new_db.execute(select(User).where(User.id == biz.owner_id))
                usr = user_result.scalar_one_or_none()
                if usr:
                    first_name = (usr.full_name or "").split()[0] or "there"
                    await email_sender.send_onboarding_step(
                        step=3,
                        business_id=business_id_copy,
                        user_email=usr.email,
                        first_name=first_name,
                        business_name=biz.name,
                        db=new_db
                    )
    asyncio.create_task(send_email_3())

    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2>Facebook & Instagram connected!</h2>
    <p style="color:#666">Check your email — Marlo is sending the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)

@router.get("/connect/mailchimp")
async def connect_mailchimp(business_id: str):
    """Start Mailchimp OAuth — if no credentials configured, skip to step 4."""
    if not MAILCHIMP_CLIENT_ID:
        return await _advance_to_step_4(business_id, skipped=True)

    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"business_id": business_id, "platform": "mailchimp"}
    auth_url = (
        f"https://login.mailchimp.com/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={MAILCHIMP_CLIENT_ID}"
        f"&redirect_uri={APP_BASE}/integrations/callback/mailchimp"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)

@router.get("/callback/mailchimp")
async def mailchimp_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle Mailchimp OAuth callback."""
    if error or not code or not state:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
        <div style="font-size:48px">❌</div>
        <h2 style="color:#cc0000">Mailchimp connection failed</h2>
        <p style="color:#666">{error or 'Something went wrong.'}</p>
        <p style="color:#999;font-size:14px">Please close this tab and try again, or skip this step.</p>
        </body></html>
        """)

    state_data = oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://login.mailchimp.com/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": MAILCHIMP_CLIENT_ID,
                "client_secret": MAILCHIMP_CLIENT_SECRET,
                "redirect_uri": f"{APP_BASE}/integrations/callback/mailchimp",
                "code": code
            }
        )
        tokens = response.json()

    if "error" in tokens or "access_token" not in tokens:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
        <div style="font-size:48px">❌</div>
        <h2 style="color:#cc0000">Mailchimp connection failed</h2>
        <p style="color:#666">{tokens.get('error', 'Token exchange failed')}</p>
        <p style="color:#999;font-size:14px">Please close this tab and try again.</p>
        </body></html>
        """)

    from security.encryption import encrypt_token
    integration = PlatformIntegration(
        id=uuid.uuid4(),
        business_id=state_data["business_id"],
        platform="mailchimp",
        access_token=encrypt_token(tokens["access_token"]),
        scopes=["mailchimp"],
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(integration)
    await db.commit()

    return await _advance_to_step_4(state_data["business_id"], connected=True)

@router.get("/skip-google")
async def skip_google(business_id: str):
    """User chose to skip Google Ads — advance to step 2 and send email 2."""
    async def send_email_2():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            # Guard: only advance if still on step 1
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step != 1:
                return
            await new_db.execute(
                sql_update(Business)
                .where(Business.id == business_id)
                .values(onboarding_step=2)
            )
            await new_db.commit()
            biz_result2 = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result2.scalar_one_or_none()
            if biz:
                user_result = await new_db.execute(select(User).where(User.id == biz.owner_id))
                usr = user_result.scalar_one_or_none()
                if usr:
                    first_name = (usr.full_name or "").split()[0] or "there"
                    await email_sender.send_onboarding_step(
                        step=2,
                        business_id=business_id,
                        user_email=usr.email,
                        first_name=first_name,
                        business_name=biz.name,
                        db=new_db,
                        skipped_platform="google"
                    )
    asyncio.create_task(send_email_2())
    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">No problem!</h2>
    <p style="color:#666">Marlo will start with Instagram. You can connect Google Ads anytime by replying to any Marlo email.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)

@router.get("/skip-meta")
async def skip_meta(business_id: str):
    """User chose to skip Meta/Instagram — advance to step 3 and send email 3."""
    async def send_email_3():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            # Guard: only advance if still on step 2
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step != 2:
                return
            await new_db.execute(
                sql_update(Business)
                .where(Business.id == business_id)
                .values(onboarding_step=3)
            )
            await new_db.commit()
            biz_result2 = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result2.scalar_one_or_none()
            if biz:
                user_result = await new_db.execute(select(User).where(User.id == biz.owner_id))
                usr = user_result.scalar_one_or_none()
                if usr:
                    first_name = (usr.full_name or "").split()[0] or "there"
                    await email_sender.send_onboarding_step(
                        step=3,
                        business_id=business_id,
                        user_email=usr.email,
                        first_name=first_name,
                        business_name=biz.name,
                        db=new_db,
                        skipped_platform="meta"
                    )
    asyncio.create_task(send_email_3())
    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">No problem!</h2>
    <p style="color:#666">Marlo will start with Google Ads. You can connect Instagram anytime by replying to any Marlo email.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)

@router.get("/skip-mailchimp")
async def skip_mailchimp(business_id: str):
    """User chose to skip Mailchimp — advance to step 4."""
    return await _advance_to_step_4(business_id, skipped=True)

async def _advance_to_step_4(business_id: str, connected: bool = False, skipped: bool = False):
    """Update onboarding step to 4 and send email 4. Guard against duplicate triggers."""
    async def send_email_4():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            # Guard: only advance if still on step 3
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step != 3:
                return
            await new_db.execute(
                sql_update(Business)
                .where(Business.id == business_id)
                .values(onboarding_step=4)
            )
            await new_db.commit()
            biz_result2 = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result2.scalar_one_or_none()
            if biz:
                user_result = await new_db.execute(select(User).where(User.id == biz.owner_id))
                usr = user_result.scalar_one_or_none()
                if usr:
                    first_name = (usr.full_name or "").split()[0] or "there"
                    await email_sender.send_onboarding_step(
                        step=4,
                        business_id=business_id,
                        user_email=usr.email,
                        first_name=first_name,
                        business_name=biz.name,
                        db=new_db
                    )

    asyncio.create_task(send_email_4())

    if skipped:
        message = "No problem!"
        sub = "Marlo will work with Google and Facebook for now. You can connect Mailchimp anytime by replying to any Marlo email."
    else:
        message = "Mailchimp connected!"
        sub = "Check your email — Marlo is sending the next step."

    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">{message}</h2>
    <p style="color:#666">{sub}</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)