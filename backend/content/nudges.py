"""
Micro-sessions: when a vendor says "yes, send me one quick question tomorrow",
the question is prepared right away (content/pipeline.pause_conversation) and
this job delivers it in the morning: it adds the question to the conversation
and emails the vendor a link that opens straight to it.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from database.models import Conversation, ConversationStatus, Market, Message, Vendor, utcnow
from database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

MAX_NUDGES = 3


async def send_due_nudges() -> int:
    """Deliver every follow-up question that is due. Returns how many were sent."""
    from core.auth import new_vendor_magic_link
    from vendors.router import login_url, send_login_email

    sent = 0
    async with AsyncSessionLocal() as db:
        due = (await db.execute(
            select(Conversation).where(Conversation.status == ConversationStatus.OPEN,
                                       Conversation.resume_at.is_not(None), Conversation.resume_at <= utcnow())
        )).scalars().all()
        for conv in due:
            try:
                m = dict(conv.story_map or {})
                micro = m.get("micro") or {}
                question = micro.get("question")
                if not question or micro.get("sent") or (conv.nudge_count or 0) >= MAX_NUDGES:
                    conv.resume_at = None
                    await db.commit()
                    continue
                vendor = await db.get(Vendor, conv.vendor_id)
                market = await db.get(Market, vendor.market_id)
                db.add(Message(conversation_id=conv.id, role="agent", content=question, meta={"skill": "micro-session"}))
                micro["sent"] = True
                m["micro"] = micro
                conv.story_map = m
                conv.resume_at = None
                conv.nudge_count = (conv.nudge_count or 0) + 1
                token = await new_vendor_magic_link(db, vendor)
                await db.commit()
                await send_login_email(
                    db, vendor, market, login_url(token), subject=f"{vendor.name}: one quick question"[:140],
                    intro=f"One quick question, as promised: <b>{question}</b><br><br>Answer in a few words. It takes a minute.",
                )
                await db.commit()
                sent += 1
            except Exception as e:  # noqa: BLE001
                logger.error(f"[Nudges] {conv.id}: {e}")
                await db.rollback()
    return sent
