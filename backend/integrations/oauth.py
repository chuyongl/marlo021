from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx, secrets, os, uuid, asyncio, urllib.parse
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

# Instagram Login App credentials (new Business-type app)
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")

GOOGLE_SCOPES = " ".join([
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/business.manage",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "openid", "email"
])

# Instagram Login scopes (graph.instagram.com — no Facebook Page required)
INSTAGRAM_SCOPES = "instagram_business_basic,instagram_business_content_publish,instagram_business_manage_insights"

# Legacy Facebook Login scopes — kept for reference, no longer used for new connections
META_SCOPES = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish,instagram_manage_insights"

oauth_states: dict = {}


# ── Google ────────────────────────────────────────────────────────────────────

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

@router.get("/skip-google")
async def skip_google(business_id: str):
    async def send_email_2():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step > 1:
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


# ── Instagram Login (NEW — replaces Facebook Login for Instagram) ─────────────
#
# Uses Instagram Login API (launched July 2024).
# No Facebook Page required — user logs in directly with Instagram credentials.
# OAuth host: www.instagram.com/oauth/authorize
# API host: graph.instagram.com
# Account ID comes from GET graph.instagram.com/me directly.
#
# IMPORTANT: Must use urllib.parse.urlencode to build the auth URL.
# f-string interpolation causes Instagram to encode commas in scope as "-",
# which breaks the OAuth flow with "Error validating verification code".

@router.get("/connect/instagram")
async def connect_instagram(business_id: str):
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"business_id": business_id, "platform": "instagram"}
    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": f"{APP_BASE}/integrations/callback/instagram",
        "response_type": "code",
        "scope": INSTAGRAM_SCOPES,
        "state": state,
    }
    auth_url = "https://www.instagram.com/oauth/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(auth_url)


@router.get("/callback/instagram")
async def instagram_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    error_code: str = None,
    error_message: str = None,
    db: AsyncSession = Depends(get_db)
):
    # User denied or error from Instagram
    if error or error_code:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
        <div style="font-size:48px">❌</div>
        <h2 style="color:#cc0000">Instagram connection failed</h2>
        <p style="color:#666">{error_message or error or 'Unknown error'}</p>
        <p style="color:#999;font-size:14px">Please close this tab and try again.</p>
        </body></html>
        """)

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    state_data = oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Step 1: Exchange code for short-lived access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": f"{APP_BASE}/integrations/callback/instagram",
                "code": code,
            }
        )
        tokens = response.json()

    if "error" in tokens or "access_token" not in tokens:
        error_msg = tokens.get("error_message") or tokens.get("error", {}).get("message", "Token exchange failed")
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
        <div style="font-size:48px">❌</div>
        <h2 style="color:#cc0000">Instagram connection failed</h2>
        <p style="color:#666">{error_msg}</p>
        <p style="color:#999;font-size:14px">Please close this tab and try again.</p>
        </body></html>
        """)

    short_lived_token = tokens["access_token"]
    ig_user_id = str(tokens.get("user_id", ""))

    # Step 2: Exchange for long-lived token (60 days)
    async with httpx.AsyncClient() as client:
        ll_response = await client.get(
            "https://graph.instagram.com/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": INSTAGRAM_APP_SECRET,
                "access_token": short_lived_token,
            }
        )
        ll_tokens = ll_response.json()

    long_lived_token = ll_tokens.get("access_token", short_lived_token)

    # Step 3: Get Instagram username from /me
    async with httpx.AsyncClient() as client:
        me_response = await client.get(
            "https://graph.instagram.com/me",
            params={
                "fields": "id,username",
                "access_token": long_lived_token,
            }
        )
        me_data = me_response.json()

    ig_account_id = me_data.get("id") or ig_user_id
    ig_username = me_data.get("username", "")
    print(f"[Instagram Login] Connected: @{ig_username} (ID: {ig_account_id})")

    from security.encryption import encrypt_token
    from sqlalchemy import select, update

    # Step 4: Upsert integration — store as platform="meta" for backward compat with executor
    existing_result = await db.execute(
        select(PlatformIntegration).where(
            PlatformIntegration.business_id == state_data["business_id"],
            PlatformIntegration.platform == "meta",
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.access_token = encrypt_token(long_lived_token)
        existing.platform_account_id = ig_account_id
        existing.scopes = INSTAGRAM_SCOPES.split(",")
        existing.is_active = True
    else:
        integration = PlatformIntegration(
            id=uuid.uuid4(),
            business_id=state_data["business_id"],
            platform="meta",
            access_token=encrypt_token(long_lived_token),
            platform_account_id=ig_account_id,
            scopes=INSTAGRAM_SCOPES.split(","),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(integration)

    # Step 5: Advance onboarding to step 3
    await db.execute(
        update(Business)
        .where(Business.id == state_data["business_id"])
        .values(onboarding_step=3)
    )
    await db.commit()

    # Step 6: Send onboarding email 3
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

    username_line = f'<p style="color:#15803D;font-size:14px;">Connected as @{ig_username} ✓</p>' if ig_username else ""

    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">Instagram connected!</h2>
    {username_line}
    <p style="color:#666">Check your email — Marlo is sending the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)


@router.get("/deauthorize/instagram")
async def instagram_deauthorize():
    """
    Called by Meta when a user removes the app from their Instagram account.
    Required for Meta app review. We mark the integration as inactive.
    """
    return HTMLResponse("OK", status_code=200)


@router.get("/delete/instagram")
async def instagram_data_deletion():
    """
    Called by Meta when a user requests data deletion.
    Required for Meta app review.
    """
    return {
        "url": f"{FRONTEND}/privacy",
        "confirmation_code": "marlo_data_deletion_confirmed"
    }


# ── Meta (Legacy Facebook Login — kept but no longer used for new connections) ─

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


async def _get_instagram_account_id(access_token: str) -> str | None:
    """
    Legacy helper for Facebook Login flow.
    Fetches Instagram Business Account ID from linked Facebook Page.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://graph.facebook.com/v21.0/me/accounts",
            params={
                "access_token": access_token,
                "fields": "id,name,instagram_business_account"
            }
        )
        data = resp.json()

        if "error" in data:
            print(f"[Meta OAuth] /me/accounts error: {data['error']}")
            return None

        pages = data.get("data", [])
        if not pages:
            print("[Meta OAuth] No Facebook Pages found")
            return None

        for page in pages:
            ig = page.get("instagram_business_account")
            if ig and ig.get("id"):
                print(f"[Meta OAuth] Found IG account ID: {ig['id']} (page: {page.get('name')})")
                return ig["id"]

        print("[Meta OAuth] No Instagram Business Account linked to any page")
        return None


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
                "client_id": meta_app_id,
                "client_secret": meta_app_secret,
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

    access_token = tokens["access_token"]
    ig_account_id = await _get_instagram_account_id(access_token)

    from security.encryption import encrypt_token
    from sqlalchemy import select, update

    existing_result = await db.execute(
        select(PlatformIntegration).where(
            PlatformIntegration.business_id == state_data["business_id"],
            PlatformIntegration.platform == "meta",
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.access_token = encrypt_token(access_token)
        existing.platform_account_id = ig_account_id
        existing.scopes = META_SCOPES.split(",")
        existing.is_active = True
    else:
        integration = PlatformIntegration(
            id=uuid.uuid4(),
            business_id=state_data["business_id"],
            platform="meta",
            access_token=encrypt_token(access_token),
            platform_account_id=ig_account_id,
            scopes=META_SCOPES.split(","),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(integration)

    await db.execute(
        update(Business)
        .where(Business.id == state_data["business_id"])
        .values(onboarding_step=3)
    )
    await db.commit()

    if ig_account_id:
        ig_line = f'<p style="color:#15803D;font-size:14px;">Instagram Business Account connected ✓ (ID: {ig_account_id})</p>'
    else:
        ig_line = '<p style="color:#D97706;font-size:13px;">⚠️ No Instagram Business Account found.</p>'

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

    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2>Facebook & Instagram connected!</h2>
    {ig_line}
    <p style="color:#666">Check your email — Marlo is sending the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)

@router.get("/skip-meta")
async def skip_meta(business_id: str):
    async def send_email_3():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step > 2:
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
    <p style="color:#666">You can connect Instagram anytime by replying to any Marlo email.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)


# ── Mailchimp ─────────────────────────────────────────────────────────────────

@router.get("/connect/mailchimp")
async def connect_mailchimp(business_id: str):
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

@router.get("/skip-mailchimp")
async def skip_mailchimp(business_id: str):
    async def send_email_4():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step > 3:
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
                        db=new_db,
                        skipped_platform="mailchimp"
                    )
    asyncio.create_task(send_email_4())
    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9">
    <div style="font-size:48px">✅</div>
    <h2 style="color:#1a1a1a">No problem!</h2>
    <p style="color:#666">Marlo has everything it needs to get started. Check your email for the next step.</p>
    <p style="color:#999;font-size:14px">You can close this tab.</p>
    </body></html>
    """)


# ── Shared helpers ────────────────────────────────────────────────────────────

async def _advance_to_step_4(business_id: str, skipped: bool = False, connected: bool = False):
    """Update onboarding step to 4 and send email 4."""
    async def send_email_4():
        from database.session import AsyncSessionLocal
        from email_system.sender import email_sender
        from sqlalchemy import select, update as sql_update
        async with AsyncSessionLocal() as new_db:
            biz_result = await new_db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz or biz.onboarding_step > 3:
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
    asyncio.create_task(_schedule_email4_reminder(business_id))

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


async def _schedule_email4_reminder(business_id: str):
    """Wait 72 hours. If still on step 4, send reminder."""
    await asyncio.sleep(72 * 60 * 60)

    from database.session import AsyncSessionLocal
    from email_system.sender import email_sender
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        biz = biz_result.scalar_one_or_none()
        if not biz or biz.onboarding_step != 4:
            return

        user_result = await db.execute(select(User).where(User.id == biz.owner_id))
        usr = user_result.scalar_one_or_none()
        if not usr:
            return

        first_name = (usr.full_name or "").split()[0] or "there"
        print(f"[Reminder] Sending email 4 reminder to {usr.email}")
        await email_sender.send_onboarding_step(
            step=4,
            business_id=business_id,
            user_email=usr.email,
            first_name=first_name,
            business_name=biz.name,
            db=db,
            extra_data={"is_reminder": True}
        )