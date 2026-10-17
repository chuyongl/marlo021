"""
Vendor app API: signup with a code, magic-link login, the weekly
conversation, drafts, quick updates, reach numbers and promotion material.
"""

import logging
from datetime import timedelta

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from content import scout, speech, storymap, writer
from content.pipeline import (
    draft_submission, open_conversation, pause_conversation, start_conversation, transcript_for_submission,
    vendor_profile, vendor_says,
)
from core.auth import current_vendor, new_vendor_magic_link, redeem_magic_link
from core.config import FRONTEND_URL
from core.mail import send_email
from core.util import CATEGORIES, CATEGORY_PAIRS, as_uuid, iso, scan_code, slugify
from database.models import (
    Block, BlockClass, BlockCorrection, BlockStatus, ConversationStatus, CorrectionStatus,
    InvitationCode, LinkClick, Market, Media, ReaderShare, ScanEvent, Submission, Vendor,
    VendorFollow, Venue, utcnow,
)
from database.session import get_db
from public.router import IMAGE_TYPES, MAX_UPLOAD, block_out, share_out, vendor_card

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendor")


def login_url(token: str) -> str:
    return f"{FRONTEND_URL}/vendor/auth?token={token}"


async def send_login_email(db, vendor: Vendor, market: Market | None, url: str, subject: str | None = None,
                           intro: str | None = None) -> tuple[bool, str]:
    pub = (market.publication_name if market else None) or "Brown Bag"
    body = f"""<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:520px;margin:auto;padding:24px;color:#2b2118">
<p style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#b07a45">{pub}</p>
<p style="font-size:17px;line-height:1.6">{intro or f"Here's your link to the {pub} vendor app."}</p>
<p><a href="{url}" style="display:inline-block;background:#2b2118;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none;font-size:16px">Open the vendor app</a></p>
<p style="font-size:13px;color:#7a6a58">The link works for 7 days and keeps you signed in on this phone for 90.</p></div>"""
    return await send_email(db, vendor.email, subject or f"Your {pub} vendor link", body, "vendor_login",
                            market, vendor_id=vendor.id)


# ── Signup and login ─────────────────────────────────────────────────────────

class CodeIn(BaseModel):
    code: str


async def _code(db, code: str) -> InvitationCode:
    row = (await db.execute(select(InvitationCode).where(
        func.upper(InvitationCode.code) == code.strip().upper()))).scalar_one_or_none()
    if not row or not row.is_usable():
        raise HTTPException(400, "That code doesn't work. Check it, or ask whoever gave it to you.")
    return row


@router.get("/options")
async def options(db: AsyncSession = Depends(get_db)):
    venues = (await db.execute(select(Venue).where(Venue.is_active.is_(True)).order_by(Venue.name))).scalars().all()
    market = (await db.execute(select(Market).limit(1))).scalar_one_or_none()
    return {
        "categories": [{"value": k, "label": v} for k, v in CATEGORIES.items()],
        "venues": [{"id": str(v.id), "name": v.name, "slug": v.slug, "neighborhood": v.neighborhood} for v in venues],
        "neighborhoods": sorted((market.neighborhoods or {}).keys()) if market else [],
    }


@router.post("/validate-code")
async def validate_code(body: CodeIn, db: AsyncSession = Depends(get_db)):
    row = await _code(db, body.code)
    return {"ok": True, "neighborhood": row.neighborhood, "label": row.label}


class SignupIn(BaseModel):
    code: str
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    categories: list[str] = Field(default_factory=list)
    venue_id: str | None = None
    neighborhood: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    schedule_note: str | None = Field(default=None, max_length=200)
    instagram: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=200)


async def _unique_scan_code(db) -> str:
    for _ in range(20):
        c = scan_code()
        if not (await db.execute(select(Vendor.id).where(Vendor.scan_code == c))).first():
            return c
    raise HTTPException(500, "Please try again.")


@router.post("/signup")
async def signup(body: SignupIn, db: AsyncSession = Depends(get_db)):
    code = await _code(db, body.code)
    if (await db.execute(select(Vendor.id).where(func.lower(Vendor.email) == body.email.lower()))).first():
        raise HTTPException(400, "That email already has a vendor account. Use 'Send me a login link' instead.")
    cats = [c for c in body.categories if c in CATEGORIES][:4]
    if not cats:
        raise HTTPException(400, "Pick at least one thing you sell.")
    venue = await db.get(Venue, as_uuid(body.venue_id)) if as_uuid(body.venue_id) else None
    market = await db.get(Market, code.market_id)
    hood = body.neighborhood or (venue.neighborhood if venue else None) or code.neighborhood
    vendor = Vendor(
        market_id=code.market_id, invitation_code_id=code.id, name=body.name.strip(),
        slug=slugify(body.name), email=body.email.lower(), scan_code=await _unique_scan_code(db),
        neighborhood=hood, city=market.city_of(hood) if market and hood else None,
        categories=cats, complementary_categories=sorted({c for cat in cats for c in CATEGORY_PAIRS.get(cat, [])}),
        description=body.description, schedule_note=body.schedule_note,
        instagram=(body.instagram or "").lstrip("@") or None, website=body.website,
        venue_id=venue.id if venue else None,
    )
    db.add(vendor)
    code.use_count += 1
    await db.flush()
    token = await new_vendor_magic_link(db, vendor)
    await db.commit()
    session = await redeem_magic_link(db, token)
    await send_login_email(db, vendor, market, login_url(token), intro="Welcome. Save this email: it's your way back into the vendor app on any phone.")
    await db.commit()
    return {"session_token": session}


class EmailIn(BaseModel):
    email: EmailStr


@router.post("/login")
async def login(body: EmailIn, db: AsyncSession = Depends(get_db)):
    vendor = (await db.execute(select(Vendor).where(func.lower(Vendor.email) == body.email.lower()))).scalar_one_or_none()
    if vendor and vendor.status != "removed":
        token = await new_vendor_magic_link(db, vendor)
        market = await db.get(Market, vendor.market_id)
        await db.commit()
        await send_login_email(db, vendor, market, login_url(token))
        await db.commit()
    return {"ok": True}


class TokenIn(BaseModel):
    token: str


@router.post("/auth")
async def auth(body: TokenIn, db: AsyncSession = Depends(get_db)):
    session = await redeem_magic_link(db, body.token)
    if not session:
        raise HTTPException(400, "This link has expired. Ask for a new one below.")
    return {"session_token": session}


# ── Profile ──────────────────────────────────────────────────────────────────

@router.get("/me")
async def me(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    venue = await db.get(Venue, vendor.venue_id) if vendor.venue_id else None
    market = await db.get(Market, vendor.market_id)
    await db.commit()
    return {
        **vendor_card(vendor, venue), "email": vendor.email,
        "publication": market.publication_name if market else "Brown Bag",
        "page_url": f"{FRONTEND_URL}/v/{vendor.scan_code}",
        "qr_url": f"{FRONTEND_URL}/v/{vendor.scan_code}?qr=1",
        "venue_qr_url": f"{FRONTEND_URL}/m/{venue.slug}?qr=1" if venue else None,
    }


class ProfileIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    schedule_note: str | None = Field(default=None, max_length=200)
    instagram: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=200)
    photo_url: str | None = None
    categories: list[str] | None = None


@router.patch("/me")
async def update_me(body: ProfileIn, vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    for field in ("name", "description", "schedule_note", "website"):
        val = getattr(body, field)
        if val is not None:
            val = val.strip()
            if field == "name":
                if val:
                    vendor.name = val
            else:
                setattr(vendor, field, val or None)
    if body.instagram is not None:
        vendor.instagram = body.instagram.strip().lstrip("@") or None
    if body.photo_url is not None and (body.photo_url == "" or body.photo_url.startswith("/media/")):
        vendor.photo_url = body.photo_url or None
    if body.categories is not None:
        cats = [c for c in body.categories if c in CATEGORIES][:4]
        if cats:
            vendor.categories = cats
            vendor.complementary_categories = sorted({c for cat in cats for c in CATEGORY_PAIRS.get(cat, [])})
    await db.commit()
    return {"ok": True}


@router.post("/photo")
async def photo(file: UploadFile = File(...), vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(400, "Please upload a photo (JPEG, PNG or WebP).")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "That photo is too large.")
    m = Media(content_type=file.content_type, data=data, size_bytes=len(data), uploaded_by=f"vendor:{vendor.id}")
    db.add(m)
    await db.commit()
    return {"url": f"/media/{m.id}"}


# ── Voice memos ──────────────────────────────────────────────────────────────

VOICE_DAILY_LIMIT = 40
_voice_counts: dict[tuple[str, str], int] = {}


@router.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...), vendor: Vendor = Depends(current_vendor)):
    """A short recording in, the words out. Nothing is stored; the vendor checks the text before sending it."""
    if not speech.available():
        raise HTTPException(503, "Voice isn't switched on yet. Please type for now.")
    ctype = (file.content_type or "").split(";")[0].lower()
    if not (ctype.startswith("audio/") or ctype in ("video/webm", "video/mp4")):
        raise HTTPException(400, "That doesn't look like a recording. Please try again.")
    data = await file.read(speech.MAX_AUDIO_BYTES + 1)
    if len(data) > speech.MAX_AUDIO_BYTES:
        raise HTTPException(400, "That recording is too long. Try a few minutes at a time.")
    if len(data) < speech.MIN_AUDIO_BYTES:
        raise HTTPException(400, "That was too short to hear anything. Hold the button and talk for a few seconds.")
    day = utcnow().strftime("%Y-%m-%d")
    key = (str(vendor.id), day)
    for k in [k for k in _voice_counts if k[1] != day]:
        _voice_counts.pop(k, None)
    if _voice_counts.get(key, 0) >= VOICE_DAILY_LIMIT:
        raise HTTPException(429, "That's a lot of recordings for one day. Please type the rest, or come back tomorrow.")
    _voice_counts[key] = _voice_counts.get(key, 0) + 1
    try:
        text = await speech.transcribe(data, ctype)
    except speech.SpeechError as e:
        raise HTTPException(e.status, str(e))
    return {"text": text}


# ── The conversation ─────────────────────────────────────────────────────────

def conv_out(conv, drafting: bool = False) -> dict:
    m = conv.story_map or {}
    is_open = conv.status == ConversationStatus.OPEN
    choosing = is_open and not conv.messages
    last_agent = max((i for i, x in enumerate(conv.messages) if x.role == "agent"), default=-1)
    last_is_agent = bool(conv.messages) and conv.messages[-1].role == "agent"

    def quick(i, x):
        return (x.meta or {}).get("quick", []) if is_open and last_is_agent and i == last_agent and not conv.resume_at else []

    return {
        "id": str(conv.id), "status": conv.status, "opening_question": conv.opening_question,
        "choosing": choosing,
        "hooks": [{"id": h["id"], "title": h["title"], "bait": h["bait"]} for h in (conv.hooks or [])] if choosing else [],
        "menu": [{"id": x["id"], "title": x["title"]} for x in scout.MENU] if choosing else [],
        "messages": [{"role": x.role, "content": x.content, "at": iso(x.created_at),
                      "images": x.image_urls or [], "quick": quick(i, x)} for i, x in enumerate(conv.messages)],
        "finished": not is_open, "escalated": bool(conv.escalated_at),
        "drafting": drafting, "voice": speech.available(),
        "paused": bool(conv.resume_at), "resume_at": iso(conv.resume_at),
        "progress": storymap.stage_of(m) if "scene" in m else "scene",
        "hook": ((m.get("hook") or {}).get("title") if isinstance(m.get("hook"), dict) else None),
    }


@router.get("/conversation")
async def get_conversation(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    conv = await open_conversation(db, vendor)
    drafting = False
    if conv.status == ConversationStatus.SUBMITTED:
        sub = (await db.execute(select(Submission).where(Submission.conversation_id == conv.id))).scalar_one_or_none()
        drafting = bool(sub and sub.status == "new" and not sub.sensitive)
    return conv_out(conv, drafting)


class StartIn(BaseModel):
    pick: str = Field(min_length=1, max_length=40)
    text: str | None = Field(default=None, max_length=4000)
    photo_url: str | None = None
    caption: str | None = Field(default=None, max_length=1000)
    voice: bool = False


@router.post("/conversation/start")
async def start(body: StartIn, bg: BackgroundTasks, vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    """The vendor tapped a story on the menu."""
    conv = await open_conversation(db, vendor)
    if conv.status != ConversationStatus.OPEN:
        conv = await open_conversation(db, vendor, force_new=True)
    if conv.messages:
        return conv_out(conv)
    try:
        conv = await start_conversation(db, vendor, conv, body.pick, text=body.text, photo_url=body.photo_url, caption=body.caption)
        if body.text and body.text.strip() and body.pick != "photo":
            result = await vendor_says(db, vendor, conv, body.text, voice=body.voice)
            if result["submission_id"]:
                bg.add_task(draft_submission, result["submission_id"])
    except ValueError as e:
        await db.rollback()
        raise HTTPException(400, str(e))
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Vendor] could not start conversation: {e}")
        await db.rollback()
        raise HTTPException(503, "The interviewer is having trouble right now. Please try again in a minute.")
    return conv_out(conv)


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    voice: bool = False      # the words came from a voice memo (the vendor checked the transcript)


@router.post("/conversation/message")
async def post_message(body: MessageIn, bg: BackgroundTasks, vendor: Vendor = Depends(current_vendor),
                       db: AsyncSession = Depends(get_db)):
    conv = await open_conversation(db, vendor)
    if conv.status != ConversationStatus.OPEN:
        conv = await open_conversation(db, vendor, force_new=True)
    try:
        result = await vendor_says(db, vendor, conv, body.text, voice=body.voice)
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Vendor] interviewer failed: {e}")
        await db.rollback()
        raise HTTPException(503, "The interviewer is having trouble right now. Your message wasn't lost: try sending it again in a minute.")
    if result["submission_id"]:
        bg.add_task(draft_submission, result["submission_id"])
    return conv_out(conv, drafting=bool(result["submission_id"]))


@router.post("/conversation/pause")
async def pause(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    """'Yes, send me one quick question tomorrow.'"""
    conv = await open_conversation(db, vendor)
    if conv.status != ConversationStatus.OPEN or not conv.messages:
        raise HTTPException(400, "There's nothing to pause right now.")
    try:
        conv = await pause_conversation(db, vendor, conv)
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Vendor] pause failed: {e}")
        await db.rollback()
        raise HTTPException(503, "Couldn't set that up just now. Please try again.")
    return conv_out(conv)


@router.post("/conversation/new")
async def new_conversation(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    conv = await open_conversation(db, vendor, force_new=True)
    return conv_out(conv)


# ── Quick updates (no interview) ────────────────────────────────────────────

class UpdateIn(BaseModel):
    text: str = Field(min_length=5, max_length=1500)


@router.post("/updates")
async def quick_update(body: UpdateIn, bg: BackgroundTasks, vendor: Vendor = Depends(current_vendor),
                       db: AsyncSession = Depends(get_db)):
    sub = Submission(vendor_id=vendor.id, raw_text=body.text.strip(), perishable=True,
                     material_notes={"move": "finish_update", "source": "quick_update"})
    db.add(sub)
    await db.commit()
    bg.add_task(draft_submission, str(sub.id), "update")
    return {"ok": True}


# ── Drafts and published stories ────────────────────────────────────────────

STATUS_LABEL = {
    BlockStatus.VENDOR_PREVIEW: "Waiting for you",
    BlockStatus.PENDING_REVIEW: "With the editor",
    BlockStatus.APPROVED: "Approved",
    BlockStatus.REJECTED: "Not running",
    BlockStatus.EXPIRED: "Expired",
}


@router.get("/stories")
async def my_stories(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    blocks = (await db.execute(select(Block).where(Block.vendor_id == vendor.id).order_by(Block.created_at.desc()))).scalars().all()
    corr = (await db.execute(select(BlockCorrection).where(BlockCorrection.vendor_id == vendor.id))).scalars().all()
    pending_drafts = (await db.execute(select(func.count()).select_from(Submission).where(
        Submission.vendor_id == vendor.id, Submission.status == "new", Submission.sensitive.is_(False)))).scalar()
    await db.commit()
    out = []
    for b in blocks:
        item = block_out(b)
        item.update({
            "status": b.status, "status_label": STATUS_LABEL.get(b.status, b.status),
            "is_public": b.is_public, "reject_reason": b.reject_reason,
            "public_url": f"{FRONTEND_URL}/s/{b.slug}" if b.status == BlockStatus.APPROVED and b.is_public else None,
            "corrections": [{"note": c.note, "status": c.status, "at": iso(c.created_at)} for c in corr if c.block_id == b.id],
            "claims": [{"id": c["id"], "text": c["text"], "kind": c["kind"], "unsupported": c["status"] == "unsupported",
                        "inferred": c["status"] == "inferred"}
                       for c in (b.claims or [])] if b.status == BlockStatus.VENDOR_PREVIEW else [],
            "editor_note": b.editor_note,
            "revisions": len(b.history or []),
            "instagram_caption": _caption(b, vendor) if b.status == BlockStatus.APPROVED else None,
        })
        out.append(item)
    return {"stories": out, "drafts_in_progress": pending_drafts}


def _caption(b: Block, vendor: Vendor) -> str:
    first = (b.body or "").split("\n")[0].strip()
    if len(first) > 220:
        first = first[:217].rsplit(" ", 1)[0] + "…"
    link = f"{FRONTEND_URL.replace('https://', '')}/s/{b.slug}"
    return (f"{b.headline}\n\n{first}\n\nThis week we're in Brown Bag, Seattle's weekly email about local makers "
            f"and market vendors. Read the whole thing and follow us there: {link}")


async def _own_block(db, vendor, block_id) -> Block:
    b = await db.get(Block, as_uuid(block_id)) if as_uuid(block_id) else None
    if not b or b.vendor_id != vendor.id:
        raise HTTPException(404, "Not found.")
    return b


@router.post("/stories/{block_id}/approve")
async def approve_draft(block_id: str, vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    b = await _own_block(db, vendor, block_id)
    if b.status == BlockStatus.VENDOR_PREVIEW:
        b.status = BlockStatus.PENDING_REVIEW
        b.vendor_viewed_at = utcnow()
    await db.commit()
    return {"status": b.status}


class ClaimDecision(BaseModel):
    id: str
    action: Literal["ok", "fix", "remove"]
    note: str | None = Field(default=None, max_length=500)


class CheckIn(BaseModel):
    decisions: list[ClaimDecision] = Field(default_factory=list, max_length=40)
    seconds: int | None = Field(default=None, ge=0, le=86400)     # how long the vendor spent on the checklist
    read_full: bool = False                                        # they opened the whole story first


MAX_REVISIONS = 2


@router.post("/stories/{block_id}/check")
async def check_draft(block_id: str, body: CheckIn, vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    """
    The vendor went through the claims. Everything confirmed -> to the editor.
    Fixes and removals are applied to the draft (their decisions are binding)
    and they check the revised version.
    """
    b = await _own_block(db, vendor, block_id)
    if b.status != BlockStatus.VENDOR_PREVIEW:
        raise HTTPException(400, "This draft isn't waiting for you any more.")
    claims = {c["id"]: c for c in (b.claims or [])}
    changes = []
    for d in body.decisions:
        if d.id not in claims or d.action == "ok":
            continue
        if d.action == "fix" and not (d.note or "").strip():
            raise HTTPException(400, "Tell us what it should say instead, or choose 'Remove'.")
        changes.append({"claim": claims[d.id]["text"], "action": d.action, "note": (d.note or "").strip()})

    check = {"seconds": body.seconds, "read_full": body.read_full, "claims": len(claims), "changes": len(changes)}

    if not changes:
        b.status = BlockStatus.PENDING_REVIEW
        b.vendor_viewed_at = utcnow()
        b.guard_notes = {**(b.guard_notes or {}), "vendor_confirmed": len(claims), "vendor_check": check}
        await db.commit()
        return {"status": b.status, "revised": False}

    def hand_to_editor(reason: str):
        note = "; ".join(f'{c["action"].upper()}: {c["claim"]}' + (f' -> {c["note"]}' if c["note"] else "") for c in changes)
        db.add(BlockCorrection(block_id=b.id, vendor_id=vendor.id, note=f"{reason} {note}"[:1000]))
        b.status = BlockStatus.PENDING_REVIEW
        b.vendor_viewed_at = utcnow()

    if len(b.history or []) >= MAX_REVISIONS:
        hand_to_editor("Vendor still has changes after two rounds.")
        await db.commit()
        return {"status": b.status, "revised": False, "handed_to_editor": True}

    sub = await db.get(Submission, b.submission_id) if b.submission_id else None
    try:
        transcript, _ = await transcript_for_submission(db, sub) if sub else ([], None)
        if not transcript:
            raise ValueError("no transcript")
        profile = await vendor_profile(db, vendor)
        title, text, notes = await writer.revise(profile, transcript, b.headline or "", b.body or "", changes)
        text = writer.snap_quotes(text, writer.vendor_texts(transcript))
        new_claims = await writer.check(title, text, transcript)
    except Exception as e:  # noqa: BLE001 - never lose the vendor's corrections
        logger.error(f"[Vendor] revision failed for {b.id}: {e}")
        await db.rollback()
        b = await _own_block(db, vendor, block_id)
        hand_to_editor("Automatic update failed; please apply.")
        await db.commit()
        return {"status": b.status, "revised": False, "handed_to_editor": True}

    b.history = (b.history or []) + [{"at": iso(utcnow()), "headline": b.headline, "body": b.body, "decisions": changes}]
    b.headline, b.body = title[:120], text
    b.word_count = len(text.split())
    b.claims = new_claims
    brief = (b.guard_notes or {}).get("brief")
    b.guard_notes = {**writer.make_guard(text, new_claims, brief), "revised_by_vendor": True, "revision_notes": notes,
                     "vendor_check": check}
    await db.commit()
    return {"status": b.status, "revised": True}


class CorrectionIn(BaseModel):
    note: str = Field(min_length=2, max_length=1000)


@router.post("/stories/{block_id}/correction")
async def correction(block_id: str, body: CorrectionIn, vendor: Vendor = Depends(current_vendor),
                     db: AsyncSession = Depends(get_db)):
    b = await _own_block(db, vendor, block_id)
    db.add(BlockCorrection(block_id=b.id, vendor_id=vendor.id, note=body.note.strip()))
    if b.status == BlockStatus.VENDOR_PREVIEW:
        b.status = BlockStatus.PENDING_REVIEW
        b.vendor_viewed_at = utcnow()
    await db.commit()
    return {"ok": True}


class VisibilityIn(BaseModel):
    is_public: bool


@router.post("/stories/{block_id}/visibility")
async def visibility(block_id: str, body: VisibilityIn, vendor: Vendor = Depends(current_vendor),
                     db: AsyncSession = Depends(get_db)):
    b = await _own_block(db, vendor, block_id)
    b.is_public = body.is_public
    await db.commit()
    return {"is_public": b.is_public}


# ── Reach ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    now = utcnow()

    async def count(stmt):
        return (await db.execute(stmt)).scalar() or 0

    out = {
        "followers": await count(select(func.count()).select_from(VendorFollow).where(
            VendorFollow.vendor_id == vendor.id, VendorFollow.is_muted.is_(False))),
        "new_followers_7": await count(select(func.count()).select_from(VendorFollow).where(
            VendorFollow.vendor_id == vendor.id, VendorFollow.first_scanned_at > now - timedelta(days=7))),
        "clicks_30": await count(select(func.count()).select_from(LinkClick).where(
            LinkClick.vendor_id == vendor.id, LinkClick.clicked_at > now - timedelta(days=30))),
        "scans_30": await count(select(func.count()).select_from(ScanEvent).where(
            ScanEvent.vendor_id == vendor.id, ScanEvent.scanned_at > now - timedelta(days=30))),
        "stories": await count(select(func.count()).select_from(Block).where(
            Block.vendor_id == vendor.id, Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.STORY)),
        "times_sent": await count(select(func.coalesce(func.sum(Block.times_used), 0)).where(Block.vendor_id == vendor.id)),
    }
    shares = (await db.execute(select(ReaderShare).where(ReaderShare.vendor_id == vendor.id)
                               .order_by(ReaderShare.created_at.desc()).limit(20))).scalars().all()
    out["reader_shares"] = [dict(share_out(s), status=s.status) for s in shares]
    await db.commit()
    return out


@router.get("/library")
async def library(vendor: Vendor = Depends(current_vendor), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Block).where(Block.market_id == vendor.market_id, Block.vendor_id != vendor.id,
                            Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.STORY)
        .order_by(Block.reviewed_at.desc().nullslast()).limit(30)
    )).scalars().all()
    vendors = {v.id: v for v in (await db.execute(select(Vendor).where(Vendor.market_id == vendor.market_id))).scalars().all()}
    await db.commit()
    return [block_out(b, vendors.get(b.vendor_id)) for b in rows]
