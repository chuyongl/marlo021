"""
Sessions.

Editors: email + password, then a signed bearer token (30 days).
Vendors: magic link, then a session token stored in vendor_sessions (90 days).
Readers: no login. Their subscriber auth_token rides in links (unsubscribe,
share, follow from this device).
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from datetime import timedelta

import bcrypt
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import SECRET
from database.models import Editor, Vendor, VendorSession, utcnow
from database.session import get_db

EDITOR_TTL = 30 * 24 * 3600
VENDOR_SESSION_DAYS = 90
MAGIC_LINK_DAYS = 7


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(payload: dict, ttl: int) -> str:
    body = dict(payload, exp=int(time.time()) + ttl)
    raw = _b64(json.dumps(body, separators=(",", ":")).encode())
    mac = _b64(hmac.new(SECRET, raw.encode(), hashlib.sha256).digest()[:24])
    return f"{raw}.{mac}"


def verify(token: str) -> dict | None:
    try:
        raw, mac = token.split(".", 1)
        good = _b64(hmac.new(SECRET, raw.encode(), hashlib.sha256).digest()[:24])
        if not hmac.compare_digest(mac, good):
            return None
        body = json.loads(_unb64(raw))
        if body.get("exp", 0) < time.time():
            return None
        return body
    except Exception:
        return None


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def check_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def editor_token(editor: Editor) -> str:
    return sign({"t": "editor", "id": str(editor.id)}, EDITOR_TTL)


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Please sign in.")
    return authorization.split(" ", 1)[1].strip()


async def current_editor(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Editor:
    body = verify(_bearer(authorization))
    if not body or body.get("t") != "editor":
        raise HTTPException(401, "Your session ended. Please sign in again.")
    editor = await db.get(Editor, uuid.UUID(body["id"]))
    if not editor or not editor.is_active:
        raise HTTPException(401, "This editor account is not active.")
    return editor


async def new_vendor_magic_link(db: AsyncSession, vendor: Vendor) -> str:
    """Create a one-time login token. Returns the token (the caller builds the URL)."""
    now = utcnow()
    session = VendorSession(
        vendor_id=vendor.id,
        session_token=secrets.token_urlsafe(32),
        magic_token=secrets.token_urlsafe(24),
        magic_expires_at=now + timedelta(days=MAGIC_LINK_DAYS),
        expires_at=now + timedelta(days=VENDOR_SESSION_DAYS),
    )
    db.add(session)
    await db.flush()
    return session.magic_token


async def redeem_magic_link(db: AsyncSession, token: str) -> str | None:
    """Magic token -> session token. A link can be reused until it expires,
    so a vendor who opens it on two phones isn't locked out."""
    row = (await db.execute(
        select(VendorSession).where(VendorSession.magic_token == token)
    )).scalar_one_or_none()
    if not row or (row.magic_expires_at and row.magic_expires_at < utcnow()):
        return None
    row.magic_used_at = row.magic_used_at or utcnow()
    row.last_seen_at = utcnow()
    await db.commit()
    return row.session_token


async def current_vendor(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Vendor:
    token = _bearer(authorization)
    row = (await db.execute(
        select(VendorSession).where(VendorSession.session_token == token)
    )).scalar_one_or_none()
    if not row or row.expires_at < utcnow():
        raise HTTPException(401, "This login link has expired. Ask for a new one.")
    vendor = await db.get(Vendor, row.vendor_id)
    if not vendor or vendor.status == "removed":
        raise HTTPException(401, "This vendor account is not active.")
    row.last_seen_at = utcnow()
    return vendor
