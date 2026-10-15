"""
Outbound email through Resend. Every send is logged; failures are returned,
never raised, so the caller can show the editor what happened and fall back
to a copyable link.
"""

import asyncio
import logging
import os

import resend
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import FROM_EMAIL, FROM_NAME
from database.models import EmailLog, Market

logger = logging.getLogger(__name__)
resend.api_key = os.getenv("RESEND_API_KEY", "")


def sender_for(market: Market | None) -> str:
    if market and market.from_email and "@" in market.from_email:
        return f"{market.from_name or FROM_NAME} <{market.from_email}>"
    return f"{FROM_NAME} <{FROM_EMAIL}>"


async def send_email(
    db: AsyncSession | None,
    to: str,
    subject: str,
    html: str,
    email_type: str,
    market: Market | None = None,
    vendor_id=None,
    subscriber_id=None,
    reply_to: str | None = None,
    headers: dict | None = None,
) -> tuple[bool, str]:
    """Returns (ok, message_id_or_error)."""
    if not resend.api_key:
        return False, "Email isn't set up yet (RESEND_API_KEY is missing)."
    params = {"from": sender_for(market), "to": [to], "subject": subject, "html": html}
    if reply_to:
        params["reply_to"] = reply_to
    if headers:
        params["headers"] = headers
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        msg_id = (result or {}).get("id", "") if isinstance(result, dict) else getattr(result, "id", "")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Mail] send failed to {to}: {e}")
        return False, str(e)
    if db is not None:
        db.add(EmailLog(
            market_id=market.id if market else None,
            vendor_id=vendor_id,
            subscriber_id=subscriber_id,
            email_type=email_type,
            to_email=to,
            subject=subject,
            provider_id=msg_id,
        ))
    return True, msg_id
