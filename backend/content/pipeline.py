"""
The supply pipeline: scout -> pick -> interview -> 素材 -> draft -> claims
check -> vendor -> editor.

Wires the pure agents (content/scout.py, content/interviewer.py,
content/writer.py) to the database. Drafting runs in the background with its
own session because the writing chain makes several model calls.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from content import interviewer, scout, skills, storymap
from content.writer import write_checked
from core.util import short_id, slugify, week_start
from database.models import (
    Block, BlockClass, BlockStatus, Conversation, ConversationStatus, Market, Media, Message, ReaderShare,
    Submission, SubmissionStatus, Vendor, utcnow,
)
from database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

UPDATE_SHELF_DAYS = 14
SCOUT_TIMEOUT_SECONDS = 20
DEFAULT_PROMPT = "Pick the story that's easiest to tell this week."


# ── What we know about a vendor ──────────────────────────────────────────────

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


async def scout_context(db, vendor: Vendor) -> dict:
    """Everything the story scout may use: season, history, updates, reader notes, the market's recent stories."""
    from database.models import Venue

    now = utcnow()
    recent_updates = (await db.execute(
        select(Block.body).where(Block.vendor_id == vendor.id, Block.block_class == BlockClass.UPDATE)
        .order_by(Block.created_at.desc()).limit(3))).scalars().all()
    past = (await db.execute(
        select(Block.headline).where(Block.vendor_id == vendor.id, Block.block_class == BlockClass.STORY)
        .order_by(Block.created_at.desc()).limit(8))).scalars().all()
    shares = (await db.execute(
        select(ReaderShare.text).where(ReaderShare.vendor_id == vendor.id, ReaderShare.status != "rejected")
        .order_by(ReaderShare.created_at.desc()).limit(3))).scalars().all()
    market_heads = (await db.execute(
        select(Block.headline).where(Block.market_id == vendor.market_id, Block.vendor_id != vendor.id,
                                     Block.block_class == BlockClass.STORY, Block.status == BlockStatus.APPROVED)
        .order_by(Block.created_at.desc()).limit(6))).scalars().all()
    venue = await db.get(Venue, vendor.venue_id) if vendor.venue_id else None
    return {
        "today": now.strftime("%A, %B %-d, %Y"),
        "schedule": vendor.schedule_note or "",
        "venue": venue.name if venue else "",
        "memory": ((vendor.vendor_memory or {}).get("notes", []))[-8:],
        "past_headlines": [h for h in past if h],
        "recent_updates": [(u or "")[:160] for u in recent_updates],
        "reader_notes": [(s or "")[:160] for s in shares],
        "market_headlines": [h for h in market_heads if h],
    }


def transcript_of(conv: Conversation) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in conv.messages]


# ── Opening a conversation and picking a story ───────────────────────────────

async def open_conversation(db, vendor: Vendor, force_new: bool = False) -> Conversation:
    """This week's conversation. A new one starts at the story menu (the scout's hooks plus the fixed menu)."""
    await skills.refresh(db)
    previous = (await db.execute(
        select(Conversation).where(Conversation.vendor_id == vendor.id)
        .order_by(Conversation.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not force_new and previous and (previous.status == ConversationStatus.OPEN or previous.cycle_start == week_start()):
        await db.refresh(previous, ["messages"])
        return previous

    # Reuse this week's hooks the vendor has not tried yet (saves a model call on "tell us something else").
    hooks: list[dict] = []
    if previous and previous.cycle_start == week_start() and previous.hooks:
        used = ((previous.story_map or {}).get("hook") or {}).get("id")
        hooks = [h for h in previous.hooks if h["id"] != used]
    if not hooks:
        try:
            profile = await vendor_profile(db, vendor)
            hooks = await asyncio.wait_for(scout.scout(profile, await scout_context(db, vendor)), SCOUT_TIMEOUT_SECONDS)
        except Exception as e:  # noqa: BLE001 - the menu works without the scout
            logger.error(f"[Pipeline] story scout failed: {e}")
            hooks = []

    m = storymap.new_map(None)
    m["stage"] = "choose"
    conv = Conversation(
        vendor_id=vendor.id, cycle_start=week_start(), hooks=hooks, story_map=m,
        opening_question=hooks[0]["bait"] if hooks else DEFAULT_PROMPT,
        gaps_remaining=[],
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv, ["messages"])
    return conv


def _agent_message(conv_id, text: str, meta: dict | None = None) -> Message:
    return Message(conversation_id=conv_id, role="agent", content=text, meta=meta)


async def start_conversation(db, vendor: Vendor, conv: Conversation, pick: str, *, text: str | None = None,
                             photo_url: str | None = None, caption: str | None = None) -> Conversation:
    """The vendor tapped a story. Write the opening question (or take their first words as the answer)."""
    await skills.refresh(db)
    hook = scout.hook_for(pick, conv.hooks or [])
    if not hook:
        raise ValueError("Pick one of the stories on the screen.")
    m = storymap.new_map({k: hook.get(k) for k in ("id", "title", "bait", "hint", "source", "why") if hook.get(k)})
    profile = await vendor_profile(db, vendor)

    photo = None
    if pick == "photo":
        media = await db.get(Media, _media_id(photo_url)) if photo_url else None
        if not media or media.uploaded_by != f"vendor:{vendor.id}":
            raise ValueError("Attach a photo first.")
        photo = (media.content_type, media.data)
        db.add(Message(conversation_id=conv.id, role="vendor", content=(caption or "").strip() or "(a photo)",
                       image_urls=[photo_url]))

    if text and text.strip() and pick != "photo":
        # They started talking instead of waiting for a question: their words are the first answer.
        conv.story_map = m
        await db.commit()
        await db.refresh(conv, ["messages"])
        return conv

    msg, problems = await interviewer.opening(profile, hook, photo, caption or "")
    db.add(_agent_message(conv.id, msg, {"skill": "opener", "problems": problems, "hook": hook.get("title")}))
    conv.story_map = m
    conv.opening_question = msg
    await db.commit()
    await db.refresh(conv, ["messages"])
    return conv


def _media_id(url: str | None):
    from core.util import as_uuid
    return as_uuid((url or "").rsplit("/", 1)[-1])


# ── The turns ────────────────────────────────────────────────────────────────

async def vendor_says(db, vendor: Vendor, conv: Conversation, text: str) -> dict:
    """One vendor message in, one interviewer move out."""
    await skills.refresh(db)
    db.add(Message(conversation_id=conv.id, role="vendor", content=text.strip()))
    await db.flush()
    await db.refresh(conv, ["messages"])
    transcript = transcript_of(conv)

    current = conv.story_map or {}
    if current.get("stage") == "choose" or "scene" not in current:
        current = storymap.new_map({"id": "free", "title": "(started talking)", "source": "free"})
    profile = await vendor_profile(db, vendor)
    turn = await interviewer.next_turn(profile, current, transcript)

    conv.story_map = turn.story_map
    conv.turns = (conv.turns or 0) + 1
    conv.gaps_remaining = turn.missing
    conv.resume_at = None
    if turn.message:
        db.add(_agent_message(conv.id, turn.message, turn.meta() | {"note": turn.note}))

    submission_id = None
    if turn.finished:
        submission_id = await _finish(db, vendor, conv, turn, transcript)
    await db.commit()
    await db.refresh(conv, ["messages"])
    return {"move": turn.move, "submission_id": submission_id, "reason": turn.reason}


async def _finish(db, vendor, conv, turn, transcript) -> str | None:
    m = turn.story_map
    memory = dict(vendor.vendor_memory or {})
    memory["notes"] = (memory.get("notes", []) + storymap.memory_notes(m))[-12:]
    vendor.vendor_memory = memory

    if turn.move == "nothing_here":
        conv.status = ConversationStatus.ABANDONED
        return None

    raw = "\n".join(("Interviewer: " if x["role"] == "agent" else "Vendor: ") + x["content"] for x in transcript)
    sensitive = bool(turn.sensitive or turn.move == "escalate")
    sub = Submission(
        vendor_id=vendor.id, conversation_id=conv.id, raw_text=raw,
        perishable=turn.move == "finish_update",
        material_notes={**storymap.prompt_view(m), "move": turn.move, "skills": m.get("skill_counts", {})},
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


# ── Micro-sessions ───────────────────────────────────────────────────────────

def _tomorrow_morning(market) -> datetime:
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(getattr(market, "timezone", None) or "America/Los_Angeles")
    t = datetime.now(tz) + timedelta(days=1)
    return t.replace(hour=9, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


async def pause_conversation(db, vendor: Vendor, conv: Conversation) -> Conversation:
    """The vendor said yes to one quick question tomorrow. Prepare it now, send it in the morning."""
    await skills.refresh(db)
    m = dict(conv.story_map or {})
    profile = await vendor_profile(db, vendor)
    question, problems = await interviewer.micro_question(profile, m, transcript_of(conv))
    m["pauses"] = int(m.get("pauses", 0)) + 1
    m["micro"] = {"question": question, "sent": False}
    conv.story_map = m
    market = await db.get(Market, vendor.market_id)
    conv.resume_at = _tomorrow_morning(market)
    db.add(_agent_message(conv.id, "Done. I'll send you one question tomorrow morning. Nothing to do until then.",
                          {"skill": "pause", "problems": problems}))
    await db.commit()
    await db.refresh(conv, ["messages"])
    return conv


# ── Drafting ─────────────────────────────────────────────────────────────────

async def transcript_for_submission(db, sub: Submission) -> tuple[list[dict], dict | None]:
    """The conversation a submission came from (or just its raw text), plus the story map if any."""
    conv = await db.get(Conversation, sub.conversation_id) if sub.conversation_id else None
    if conv:
        await db.refresh(conv, ["messages"])
        return transcript_of(conv), conv.story_map
    return [{"role": "vendor", "content": sub.raw_text}], None


async def draft_submission(submission_id: str, kind_override: str | None = None) -> None:
    """Background job: write the story through the chain, then put the draft in front of the vendor."""
    async with AsyncSessionLocal() as db:
        await skills.refresh(db)
        sub = await db.get(Submission, submission_id)
        if not sub:
            return
        vendor = await db.get(Vendor, sub.vendor_id)
        transcript, story_map = await transcript_for_submission(db, sub)
        move = (sub.material_notes or {}).get("move")
        kind = kind_override or ("update" if move == "finish_update" else "story")
        try:
            draft = await write_checked(kind, await vendor_profile(db, vendor), transcript, story_map)
        except Exception as e:  # noqa: BLE001
            logger.error(f"[Pipeline] drafting failed for {submission_id}: {e}")
            return
        is_update = kind == "update"
        db.add(Block(
            market_id=vendor.market_id, vendor_id=vendor.id, submission_id=sub.id,
            block_class=BlockClass.UPDATE if is_update else BlockClass.STORY,
            status=BlockStatus.VENDOR_PREVIEW,
            headline=draft["title"][:120], body=draft["body"], word_count=draft["words"],
            categories=vendor.categories or [], perishable=is_update,
            expires_at=(utcnow() + timedelta(days=UPDATE_SHELF_DAYS)) if is_update else None,
            slug=f"{slugify(draft['title'])}-{short_id()}", guard_notes=draft.get("guard"),
            claims=draft.get("claims"), story_plan=draft.get("plan"),
            is_sample=vendor.is_sample,
        ))
        sub.status = SubmissionStatus.DRAFTED
        await db.commit()
