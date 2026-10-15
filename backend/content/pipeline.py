"""
The supply pipeline: conversation -> 素材 -> draft -> vendor preview -> editor.

Wires the pure agents (content/interviewer.py, content/writer.py) to the
database. Drafting runs in the background with its own session because the
writer and the guard together take a while.
"""

import logging
from datetime import timedelta

from sqlalchemy import select

from content import interviewer
from content.writer import write_checked
from core.util import short_id, slugify, week_start
from database.models import (
    Block, BlockClass, BlockStatus, Conversation, ConversationStatus, Message, Submission,
    SubmissionStatus, Vendor, utcnow,
)
from database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

UPDATE_SHELF_DAYS = 14


async def vendor_profile(db, vendor: Vendor) -> dict:
    past = (await db.execute(
        select(Block.headline).where(Block.vendor_id == vendor.id, Block.status == BlockStatus.APPROVED)
        .order_by(Block.created_at.desc()).limit(6)
    )).scalars().all()
    known = [vendor.description or ""]
    if vendor.schedule_note:
        known.append(f"Schedule: {vendor.schedule_note}")
    memory = (vendor.vendor_memory or {}).get("notes", [])
    known.extend(memory[-6:])
    return {
        "name": vendor.name,
        "business": vendor.name,
        "category": ", ".join(vendor.categories or []),
        "neighborhood": vendor.neighborhood or "",
        "products": vendor.description or "",
        "known_facts": "; ".join(k for k in known if k),
        "past_stories": [p for p in past if p],
    }


def transcript_of(conv: Conversation) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in conv.messages]


async def open_conversation(db, vendor: Vendor, force_new: bool = False) -> Conversation:
    """This week's conversation; creates one (with an opening question) if needed."""
    if not force_new:
        conv = (await db.execute(
            select(Conversation).where(Conversation.vendor_id == vendor.id)
            .order_by(Conversation.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        if conv and (conv.status == ConversationStatus.OPEN or conv.cycle_start == week_start()):
            await db.refresh(conv, ["messages"])
            return conv

    profile = await vendor_profile(db, vendor)
    try:
        question = await interviewer.opening_question(profile)
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Pipeline] opening question failed: {e}")
        question = "What's one thing that happened at your stall this week that surprised you?"
    conv = Conversation(vendor_id=vendor.id, cycle_start=week_start(), opening_question=question,
                        gaps_remaining=["origin", "moment", "people", "turn", "meaning"])
    db.add(conv)
    await db.flush()
    db.add(Message(conversation_id=conv.id, role="agent", content=question))
    await db.commit()
    await db.refresh(conv, ["messages"])
    return conv


async def vendor_says(db, vendor: Vendor, conv: Conversation, text: str) -> dict:
    """One vendor message in, one interviewer move out."""
    db.add(Message(conversation_id=conv.id, role="vendor", content=text.strip()))
    await db.flush()
    await db.refresh(conv, ["messages"])
    transcript = transcript_of(conv)

    profile = await vendor_profile(db, vendor)
    turn = await interviewer.next_turn(profile, transcript, conv.stalled_turns)

    conv.turns = (conv.turns or 0) + 1
    conv.stalled_turns = turn.stalled_turns
    conv.gaps_remaining = turn.gaps_remaining
    if turn.message:
        db.add(Message(conversation_id=conv.id, role="agent", content=turn.message))

    submission_id = None
    if turn.finished:
        submission_id = await _finish(db, vendor, conv, turn, transcript)
    await db.commit()
    await db.refresh(conv, ["messages"])
    return {"move": turn.move, "submission_id": submission_id, "reason": turn.reason, "have": turn.have}


async def _finish(db, vendor, conv, turn, transcript) -> str | None:
    notes = [f"{k}: {v}" for k, v in turn.have.items() if v]
    memory = dict(vendor.vendor_memory or {})
    memory["notes"] = (memory.get("notes", []) + [n for n in notes if not n.startswith("quote")])[-12:]
    vendor.vendor_memory = memory

    if turn.move == "nothing_here":
        conv.status = ConversationStatus.ABANDONED
        return None

    raw = "\n".join(("Interviewer: " if m["role"] == "agent" else "Vendor: ") + m["content"] for m in transcript)
    sensitive = turn.sensitive or turn.move == "escalate"
    sub = Submission(
        vendor_id=vendor.id, conversation_id=conv.id, raw_text=raw,
        perishable=turn.move == "finish_update", material_notes={**turn.have, "move": turn.move},
        sensitive=sensitive,
    )
    db.add(sub)
    conv.status = ConversationStatus.SUBMITTED
    vendor.last_submitted_at = utcnow()
    vendor.silent_cycles = 0
    if sensitive:
        conv.escalated_at = utcnow()
        conv.escalation_reason = "sensitive"
    await db.flush()
    return None if sensitive else str(sub.id)


async def draft_submission(submission_id: str, kind_override: str | None = None) -> None:
    """Background job: write + guard, then put the draft in front of the vendor."""
    async with AsyncSessionLocal() as db:
        sub = await db.get(Submission, submission_id)
        if not sub:
            return
        vendor = await db.get(Vendor, sub.vendor_id)
        conv = await db.get(Conversation, sub.conversation_id) if sub.conversation_id else None
        if conv:
            await db.refresh(conv, ["messages"])
            transcript = transcript_of(conv)
        else:
            transcript = [{"role": "vendor", "content": sub.raw_text}]
        move = (sub.material_notes or {}).get("move")
        kind = kind_override or ("update" if move == "finish_update" else "story")
        try:
            draft = await write_checked(kind, await vendor_profile(db, vendor), transcript)
        except Exception as e:  # noqa: BLE001
            logger.error(f"[Pipeline] drafting failed for {submission_id}: {e}")
            return
        is_update = kind == "update"
        guard = draft.get("guard", {})
        db.add(Block(
            market_id=vendor.market_id, vendor_id=vendor.id, submission_id=sub.id,
            block_class=BlockClass.UPDATE if is_update else BlockClass.STORY,
            status=BlockStatus.VENDOR_PREVIEW,
            headline=draft["title"][:120], body=draft["body"], word_count=draft["words"],
            categories=vendor.categories or [], perishable=is_update,
            expires_at=(utcnow() + timedelta(days=UPDATE_SHELF_DAYS)) if is_update else None,
            slug=f"{slugify(draft['title'])}-{short_id()}", guard_notes=guard,
            is_sample=vendor.is_sample,
        ))
        sub.status = SubmissionStatus.DRAFTED
        await db.commit()
