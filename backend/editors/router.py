"""
Editor app API: sign-in, the review queue, vendors, codes, venues, the
weekly issue, readers, inquiries and settings.
"""

import hashlib
import logging
import re
import secrets
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from content import interviewer, scout, skills, storymap
from content.pipeline import draft_submission, open_conversation, scout_context, vendor_profile
from core.auth import check_password, current_editor, editor_token, hash_password, new_vendor_magic_link
from core.config import FRONTEND_URL, SETUP_CODE_SHA256
from core.mail import send_email
from core.util import CATEGORIES, CATEGORY_PAIRS, as_uuid, iso, short_id, slugify
from database.models import (
    Block, BlockClass, BlockCorrection, BlockStatus, Conversation, ConversationStatus, CorrectionStatus,
    Editor, InvitationCode, Issue, IssueRender, IssueStatus, Lead, LinkClick, Market, MAX_QUALITY_SCORE,
    Message, Nomination, ReaderShare, ScanEvent, SeenBlock, SkillOverride, Submission, Subscriber, SubscriberStatus,
    Vendor, VendorFollow, VendorSession, Venue, utcnow,
)
from database.session import AsyncSessionLocal, get_db
from newsletter.issue import draft_issue, render, select_for, send_issue
from public.router import block_out, share_out, vendor_card
from vendors.router import _unique_scan_code, login_url, send_login_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/editor")


async def _market(db) -> Market:
    m = (await db.execute(select(Market).order_by(Market.created_at).limit(1))).scalar_one_or_none()
    if not m:
        raise HTTPException(503, "Not set up yet.")
    return m


# ── Sign-in ──────────────────────────────────────────────────────────────────

@router.get("/setup-status")
async def setup_status(db: AsyncSession = Depends(get_db)):
    n = (await db.execute(select(func.count()).select_from(Editor))).scalar()
    return {"needs_setup": n == 0}


class SetupIn(BaseModel):
    code: str
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


@router.post("/setup")
async def setup(body: SetupIn, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(func.count()).select_from(Editor))).scalar():
        raise HTTPException(400, "Setup is already done. Sign in instead.")
    if hashlib.sha256(body.code.strip().encode()).hexdigest() != SETUP_CODE_SHA256:
        raise HTTPException(400, "That setup code isn't right.")
    market = await _market(db)
    ed = Editor(email=body.email.lower(), name=body.name.strip(), hashed_password=hash_password(body.password),
                market_ids=[str(market.id)])
    db.add(ed)
    await db.commit()
    return {"token": editor_token(ed), "name": ed.name}


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    ed = (await db.execute(select(Editor).where(func.lower(Editor.email) == body.email.lower()))).scalar_one_or_none()
    if not ed or not ed.is_active or not check_password(body.password, ed.hashed_password):
        raise HTTPException(400, "Email or password is wrong.")
    return {"token": editor_token(ed), "name": ed.name}


@router.get("/me")
async def me(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    return {"name": ed.name, "email": ed.email, "publication": market.publication_name, "market": market.name}


class NewEditorIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


@router.post("/editors")
async def add_editor(body: NewEditorIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(Editor.id).where(func.lower(Editor.email) == body.email.lower()))).first():
        raise HTTPException(400, "That email already has an editor account.")
    db.add(Editor(email=body.email.lower(), name=body.name, hashed_password=hash_password(body.password),
                  market_ids=ed.market_ids))
    await db.commit()
    return {"ok": True}


# ── Overview ─────────────────────────────────────────────────────────────────

@router.get("/overview")
async def overview(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    now = utcnow()

    async def count(stmt):
        return (await db.execute(stmt)).scalar() or 0

    approved_stories = await count(select(func.count()).select_from(Block).where(
        Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.STORY))
    new_this_week = await count(select(func.count()).select_from(Block).where(
        Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.STORY,
        Block.reviewed_at > now - timedelta(days=7)))
    pending = await count(select(func.count()).select_from(Block).where(Block.status == BlockStatus.PENDING_REVIEW))
    with_vendor = await count(select(func.count()).select_from(Block).where(Block.status == BlockStatus.VENDOR_PREVIEW))
    if pending > 3 and new_this_week < 3:
        diagnosis = "Editors are the bottleneck: drafts are waiting for review."
    elif new_this_week < 3:
        diagnosis = "Vendors are the bottleneck: fewer than 3 new stories this week. Send this week's questions."
    else:
        diagnosis = "Supply is healthy."
    return {
        "readers": await count(select(func.count()).select_from(Subscriber).where(Subscriber.status == SubscriberStatus.ACTIVE)),
        "new_readers_7": await count(select(func.count()).select_from(Subscriber).where(Subscriber.created_at > now - timedelta(days=7))),
        "vendors": await count(select(func.count()).select_from(Vendor).where(Vendor.status == "active")),
        "sample_vendors": await count(select(func.count()).select_from(Vendor).where(Vendor.is_sample.is_(True))),
        "approved_stories": approved_stories, "new_stories_7": new_this_week,
        "pending_review": pending, "waiting_on_vendor": with_vendor,
        "open_corrections": await count(select(func.count()).select_from(BlockCorrection).where(BlockCorrection.status == CorrectionStatus.OPEN)),
        "pending_shares": await count(select(func.count()).select_from(ReaderShare).where(ReaderShare.status == "pending")),
        "new_leads": await count(select(func.count()).select_from(Lead).where(Lead.status == "new")),
        "new_nominations": await count(select(func.count()).select_from(Nomination).where(Nomination.status == "new")),
        "clicks_7": await count(select(func.count()).select_from(LinkClick).where(LinkClick.clicked_at > now - timedelta(days=7))),
        "issues_sent": await count(select(func.count()).select_from(Issue).where(Issue.status == IssueStatus.SENT)),
        "diagnosis": diagnosis,
    }


# ── Queue ────────────────────────────────────────────────────────────────────

@router.get("/queue")
async def queue(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    vendors = {v.id: v for v in (await db.execute(select(Vendor))).scalars().all()}
    blocks = (await db.execute(select(Block).where(
        Block.status.in_([BlockStatus.PENDING_REVIEW, BlockStatus.VENDOR_PREVIEW])).order_by(Block.created_at))).scalars().all()
    subs = {s.id: s for s in (await db.execute(select(Submission).where(
        Submission.id.in_([b.submission_id for b in blocks if b.submission_id] or [None])))).scalars().all()}
    corrections = (await db.execute(select(BlockCorrection).where(BlockCorrection.status == CorrectionStatus.OPEN)
                                    .order_by(BlockCorrection.created_at))).scalars().all()
    corr_blocks = {b.id: b for b in (await db.execute(select(Block).where(
        Block.id.in_([c.block_id for c in corrections] or [None])))).scalars().all()}
    escalated = (await db.execute(select(Submission).where(
        Submission.sensitive.is_(True), Submission.status == "new").order_by(Submission.created_at))).scalars().all()
    shares = (await db.execute(select(ReaderShare).where(ReaderShare.status == "pending").order_by(ReaderShare.created_at))).scalars().all()

    def draft(b: Block) -> dict:
        d = block_out(b, vendors.get(b.vendor_id))
        d.update({"status": b.status, "quality_score": b.quality_score, "guard": b.guard_notes,
                  "claims": [{"text": c["text"], "kind": c["kind"], "status": c["status"], "evidence": c.get("evidence", "")}
                             for c in (b.claims or [])],
                  "revisions": len(b.history or []),
                  "is_public": b.is_public,
                  "raw_text": subs[b.submission_id].raw_text if b.submission_id in subs else None,
                  "corrections": [{"id": str(c.id), "note": c.note} for c in corrections if c.block_id == b.id]})
        return d

    return {
        "drafts": [draft(b) for b in blocks if b.status == BlockStatus.PENDING_REVIEW],
        "with_vendor": [draft(b) for b in blocks if b.status == BlockStatus.VENDOR_PREVIEW],
        "corrections": [{"id": str(c.id), "note": c.note, "created_at": iso(c.created_at),
                         "block": draft(corr_blocks[c.block_id]) if c.block_id in corr_blocks else None}
                        for c in corrections if corr_blocks.get(c.block_id) and corr_blocks[c.block_id].status == BlockStatus.APPROVED],
        "escalations": [{"id": str(s.id), "raw_text": s.raw_text, "created_at": iso(s.created_at),
                         "vendor": vendor_card(vendors[s.vendor_id]) if s.vendor_id in vendors else None}
                        for s in escalated],
        "shares": [dict(share_out(s, vendors.get(s.vendor_id)), email=s.email) for s in shares],
    }


class BlockEdit(BaseModel):
    headline: str | None = Field(default=None, max_length=140)
    body: str | None = None
    quality_score: int | None = Field(default=None, ge=0, le=MAX_QUALITY_SCORE)
    is_public: bool | None = None
    action: str = "save"   # save | approve | reject
    reject_reason: str | None = None


@router.patch("/blocks/{block_id}")
async def edit_block(block_id: str, body: BlockEdit, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    b = await db.get(Block, as_uuid(block_id)) if as_uuid(block_id) else None
    if not b:
        raise HTTPException(404, "Not found.")
    if body.headline is not None:
        b.headline = body.headline.strip()
    if body.body is not None:
        b.body = body.body.strip()
        b.word_count = len(b.body.split())
    if body.quality_score is not None:
        b.quality_score = body.quality_score
    if body.is_public is not None:
        b.is_public = body.is_public
    if body.action == "approve":
        if not b.quality_score:
            b.quality_score = 25
        b.status = BlockStatus.APPROVED
        b.editor_id = ed.id
        b.reviewed_at = utcnow()
        if not b.slug:
            b.slug = f"{slugify(b.headline)}-{short_id()}"
        await db.execute(update(BlockCorrection).where(
            BlockCorrection.block_id == b.id, BlockCorrection.status == CorrectionStatus.OPEN
        ).values(status=CorrectionStatus.RESOLVED, resolved_by=ed.id, resolved_at=utcnow()))
    elif body.action == "reject":
        b.status = BlockStatus.REJECTED
        b.reject_reason = body.reject_reason
        b.editor_id = ed.id
        b.reviewed_at = utcnow()
    await db.commit()
    return {"status": b.status}


class BlockNew(BaseModel):
    vendor_id: str
    kind: str = "story"
    headline: str = Field(min_length=2, max_length=140)
    body: str = Field(min_length=5)
    submission_id: str | None = None


@router.post("/blocks")
async def new_block(body: BlockNew, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    v = await db.get(Vendor, as_uuid(body.vendor_id)) if as_uuid(body.vendor_id) else None
    if not v:
        raise HTTPException(400, "Pick a vendor.")
    kind = BlockClass.UPDATE if body.kind == "update" else BlockClass.STORY
    b = Block(market_id=v.market_id, vendor_id=v.id, block_class=kind, status=BlockStatus.VENDOR_PREVIEW,
              headline=body.headline.strip(), body=body.body.strip(), word_count=len(body.body.split()),
              categories=v.categories or [], perishable=kind == BlockClass.UPDATE,
              expires_at=(utcnow() + timedelta(days=14)) if kind == BlockClass.UPDATE else None,
              slug=f"{slugify(body.headline)}-{short_id()}", submission_id=as_uuid(body.submission_id))
    db.add(b)
    if body.submission_id:
        sub = await db.get(Submission, as_uuid(body.submission_id))
        if sub:
            sub.status = "drafted"
    await db.commit()
    return {"id": str(b.id)}


class SubmissionAction(BaseModel):
    action: str   # draft | discard
    kind: str | None = None


@router.post("/submissions/{sub_id}")
async def submission_action(sub_id: str, body: SubmissionAction, bg: BackgroundTasks,
                            ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    sub = await db.get(Submission, as_uuid(sub_id)) if as_uuid(sub_id) else None
    if not sub:
        raise HTTPException(404, "Not found.")
    if body.action == "discard":
        sub.status = "discarded"
        await db.commit()
    else:
        sub.sensitive = False
        await db.commit()
        bg.add_task(draft_submission, str(sub.id), body.kind)
    return {"ok": True}


class SimpleAction(BaseModel):
    action: str


@router.post("/corrections/{cid}")
async def correction_action(cid: str, body: SimpleAction, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    c = await db.get(BlockCorrection, as_uuid(cid)) if as_uuid(cid) else None
    if not c:
        raise HTTPException(404, "Not found.")
    c.status = CorrectionStatus.DISMISSED if body.action == "dismiss" else CorrectionStatus.RESOLVED
    c.resolved_by = ed.id
    c.resolved_at = utcnow()
    await db.commit()
    return {"ok": True}


@router.post("/shares/{sid}")
async def share_action(sid: str, body: SimpleAction, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    s = await db.get(ReaderShare, as_uuid(sid)) if as_uuid(sid) else None
    if not s:
        raise HTTPException(404, "Not found.")
    s.status = "approved" if body.action == "approve" else "rejected"
    s.reviewed_at = utcnow()
    await db.commit()
    return {"ok": True}


# ── Vendors ──────────────────────────────────────────────────────────────────

@router.get("/vendors")
async def vendors(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Vendor).where(Vendor.status != "removed").order_by(Vendor.created_at.desc()))).scalars().all()
    venues = {v.id: v for v in (await db.execute(select(Venue))).scalars().all()}
    follows = dict((await db.execute(select(VendorFollow.vendor_id, func.count()).where(
        VendorFollow.is_muted.is_(False)).group_by(VendorFollow.vendor_id))).all())
    approved = dict((await db.execute(select(Block.vendor_id, func.count()).where(
        Block.status == BlockStatus.APPROVED).group_by(Block.vendor_id))).all())
    waiting = dict((await db.execute(select(Block.vendor_id, func.count()).where(
        Block.status.in_([BlockStatus.PENDING_REVIEW, BlockStatus.VENDOR_PREVIEW])).group_by(Block.vendor_id))).all())
    last_seen = dict((await db.execute(select(VendorSession.vendor_id, func.max(VendorSession.last_seen_at))
                                       .group_by(VendorSession.vendor_id))).all())
    out = []
    for v in rows:
        out.append({**vendor_card(v, venues.get(v.venue_id)), "email": v.email, "status": v.status,
                    "followers": follows.get(v.id, 0), "approved": approved.get(v.id, 0),
                    "waiting": waiting.get(v.id, 0), "last_submitted_at": iso(v.last_submitted_at),
                    "last_seen_at": iso(last_seen.get(v.id)), "silent_cycles": v.silent_cycles,
                    "created_at": iso(v.created_at)})
    return out


class VendorIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    venue_id: str | None = None
    neighborhood: str | None = None
    categories: list[str] = Field(default_factory=list)
    description: str | None = None
    schedule_note: str | None = None
    instagram: str | None = None
    send_link: bool = True


@router.post("/vendors")
async def add_vendor(body: VendorIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    if (await db.execute(select(Vendor.id).where(func.lower(Vendor.email) == body.email.lower()))).first():
        raise HTTPException(400, "That email already has a vendor account.")
    venue = await db.get(Venue, as_uuid(body.venue_id)) if as_uuid(body.venue_id) else None
    cats = [c for c in body.categories if c in CATEGORIES][:4] or ["crafts"]
    hood = body.neighborhood or (venue.neighborhood if venue else None)
    v = Vendor(market_id=market.id, name=body.name.strip(), slug=slugify(body.name), email=body.email.lower(),
               scan_code=await _unique_scan_code(db), neighborhood=hood, city=market.city_of(hood) if hood else None,
               categories=cats, complementary_categories=sorted({c for cat in cats for c in CATEGORY_PAIRS.get(cat, [])}),
               description=body.description, schedule_note=body.schedule_note,
               instagram=(body.instagram or "").lstrip("@") or None, venue_id=venue.id if venue else None)
    db.add(v)
    await db.flush()
    token = await new_vendor_magic_link(db, v)
    await db.commit()
    url = login_url(token)
    sent, info = (False, "")
    if body.send_link:
        sent, info = await send_login_email(db, v, market, url, subject=f"You're in {market.publication_name}",
                                            intro=f"{ed.name or 'Your editor'} set up a {market.publication_name} page for {v.name}. Tap below to open your vendor app: it asks you a question or two each week and turns your answers into a short story for local readers.")
        await db.commit()
    return {"id": str(v.id), "login_url": url, "email_sent": sent, "email_error": None if sent else info}


class VendorPatch(BaseModel):
    status: str | None = None
    venue_id: str | None = None
    name: str | None = None
    description: str | None = None
    schedule_note: str | None = None


@router.patch("/vendors/{vid}")
async def patch_vendor(vid: str, body: VendorPatch, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    v = await db.get(Vendor, as_uuid(vid)) if as_uuid(vid) else None
    if not v:
        raise HTTPException(404, "Not found.")
    if body.status in ("active", "paused", "removed"):
        v.status = body.status
    if body.venue_id is not None:
        venue = await db.get(Venue, as_uuid(body.venue_id)) if as_uuid(body.venue_id) else None
        v.venue_id = venue.id if venue else None
    for f in ("name", "description", "schedule_note"):
        val = getattr(body, f)
        if val is not None:
            setattr(v, f, val.strip() or (v.name if f == "name" else None))
    await db.commit()
    return {"ok": True}


class LinkIn(BaseModel):
    send: bool = False


@router.post("/vendors/{vid}/login-link")
async def vendor_link(vid: str, body: LinkIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    v = await db.get(Vendor, as_uuid(vid)) if as_uuid(vid) else None
    if not v:
        raise HTTPException(404, "Not found.")
    token = await new_vendor_magic_link(db, v)
    await db.commit()
    url = login_url(token)
    sent, info = False, None
    if body.send:
        market = await db.get(Market, v.market_id)
        sent, info = await send_login_email(db, v, market, url)
        await db.commit()
    return {"login_url": url, "email_sent": sent, "email_error": None if sent else info}


@router.get("/vendors/{vid}/conversations")
async def vendor_conversations(vid: str, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    convs = (await db.execute(select(Conversation).where(Conversation.vendor_id == as_uuid(vid))
                              .order_by(Conversation.created_at.desc()).limit(10))).scalars().all()
    out = []
    for c in convs:
        await db.refresh(c, ["messages"])
        m = c.story_map or {}
        out.append({"id": str(c.id), "status": c.status, "week": c.cycle_start.isoformat(),
                    "escalated": bool(c.escalated_at), "turns": c.turns,
                    "hooks": [h.get("title") for h in (c.hooks or [])],
                    "hook": (m.get("hook") or {}).get("title") if isinstance(m.get("hook"), dict) else None,
                    "map": {"mode": m.get("mode"), "yield": m.get("yield_history"), "skills": m.get("skill_counts"),
                            "ready": storymap.is_ready(m) if "scene" in m else False,
                            "details": storymap.scene_details(m) if "scene" in m else 0,
                            "want": m.get("want"), "turn": m.get("turn"), "quotes": [q["text"] for q in m.get("quotes", [])]},
                    "messages": [{"role": x.role, "content": x.content, "skill": (x.meta or {}).get("skill"),
                                  "target": (x.meta or {}).get("target"), "problems": (x.meta or {}).get("problems") or [],
                                  "images": x.image_urls or []} for x in c.messages]})
    return out


class RemindIn(BaseModel):
    vendor_ids: list[str] | None = None


@router.post("/vendors/remind")
async def remind(body: RemindIn, bg: BackgroundTasks, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    q = select(Vendor.id).where(Vendor.status == "active", Vendor.is_sample.is_(False))
    if body.vendor_ids:
        q = q.where(Vendor.id.in_([as_uuid(x) for x in body.vendor_ids if as_uuid(x)]))
    ids = [str(x) for x in (await db.execute(q)).scalars().all()]
    bg.add_task(_send_reminders, ids)
    return {"queued": len(ids)}


async def _send_reminders(vendor_ids: list[str]) -> None:
    for vid in vendor_ids:
        async with AsyncSessionLocal() as db:
            try:
                v = await db.get(Vendor, as_uuid(vid))
                market = await db.get(Market, v.market_id)
                conv = await open_conversation(db, v)
                if conv.status != ConversationStatus.OPEN:
                    continue
                token = await new_vendor_magic_link(db, v)
                await db.commit()
                q = conv.opening_question or "Which story is easiest to tell this week?"
                await send_login_email(db, v, market, login_url(token), subject=f"{v.name}: {q}"[:140],
                                       intro=f"A quick one for this week: <b>{q}</b><br><br>Tap the story that's easiest to tell and answer in a line or two, whenever you have a minute. Nothing gets written until you've seen it.")
                if v.last_submitted_at is None or v.last_submitted_at < utcnow() - timedelta(days=7):
                    v.silent_cycles = (v.silent_cycles or 0) + 1
                await db.commit()
            except Exception as e:  # noqa: BLE001
                logger.error(f"[Remind] {vid}: {e}")


# ── Skills (the instructions behind the interviewer and the writer) ──────────

def _skill_out(sk) -> dict:
    return {"name": sk.name, "description": sk.description, "stage": sk.stage, "body": sk.body,
            "default_body": sk.default_body, "edited": sk.edited, "edited_by": sk.edited_by, "edited_at": sk.edited_at,
            "extras": [{"name": k, "text": v} for k, v in sorted(sk.extras.items())]}


@router.get("/skills")
async def list_skills(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    await skills.refresh(db, force=True)
    order = {s: i for i, s in enumerate(skills.STAGES)}
    return [_skill_out(sk) for sk in sorted(skills.all_skills(), key=lambda x: (order.get(x.stage, 9), x.name))]


class SkillIn(BaseModel):
    body: str = Field(min_length=20, max_length=20000)


@router.put("/skills/{name}")
async def save_skill(name: str, body: SkillIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    if name not in skills.names():
        raise HTTPException(404, "No such skill.")
    row = await db.get(SkillOverride, name)
    text_ = body.body.strip()
    if row:
        row.body, row.updated_by = text_, ed.email
    else:
        row = SkillOverride(name=name, body=text_, updated_by=ed.email)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    skills.set_override(name, row.body, row.updated_by, iso(row.updated_at))
    return _skill_out(skills.get(name))


@router.delete("/skills/{name}")
async def reset_skill(name: str, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    if name not in skills.names():
        raise HTTPException(404, "No such skill.")
    await db.execute(delete(SkillOverride).where(SkillOverride.name == name))
    await db.commit()
    skills.clear_override(name)
    return _skill_out(skills.get(name))


class TryIn(BaseModel):
    vendor_id: str | None = None
    question: str = Field(default="Tell me about the last Saturday you sold out. What time did the last jar go?", max_length=500)
    answer: str = Field(default="", max_length=3000)


def _pick_target(answer: str) -> str:
    parts = [p.strip() for p in re.split(r"[.!?;\n]", answer) if len(p.split()) >= 3]
    return " ".join((max(parts, key=len) if parts else answer).split()[:6])


INTERVIEW_TRY = {"scene-deepener", "stakes-and-turn", "meaning-asker", "low-yield", "sensitive-guard", "wrap-up"}


@router.post("/skills/{name}/try")
async def try_skill(name: str, body: TryIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    """Run one skill on a sample answer, with the live instructions, so you can see what it would say."""
    if name not in skills.names():
        raise HTTPException(404, "No such skill.")
    await skills.refresh(db)
    vendor = await db.get(Vendor, as_uuid(body.vendor_id)) if body.vendor_id and as_uuid(body.vendor_id) else None
    if vendor is None:
        vendor = (await db.execute(select(Vendor).where(Vendor.is_sample.is_(True)).limit(1))).scalar_one_or_none() \
            or (await db.execute(select(Vendor).limit(1))).scalar_one_or_none()
    if vendor is None:
        raise HTTPException(400, "Add a vendor first so there is a profile to use.")
    profile = await vendor_profile(db, vendor)
    answer = body.answer.strip()
    transcript = [{"role": "agent", "content": body.question}] + ([{"role": "vendor", "content": answer}] if answer else [])
    try:
        if name == "story-scout":
            hooks = await scout.scout(profile, await scout_context(db, vendor))
            return {"output": "\n".join(f"{h['title']}  /  {h['bait']}  ({h['why']})" for h in hooks) or "(no hooks)", "problems": []}
        if name == "opener":
            msg, problems = await interviewer.opening(profile, {"id": "try", "title": answer or "The last time you sold out", "hint": ""})
            return {"output": msg, "problems": problems}
        if name == "director":
            if not answer:
                raise HTTPException(400, "Type what a vendor said.")
            m = storymap.new_map({"id": "try", "title": "try"})
            obs = await interviewer.observe(profile, m, transcript, answer, 1)
            storymap.apply_observation(m, obs, answer, 1)
            d = storymap.choose(m, obs)
            import json
            return {"output": json.dumps({"observation": obs, "next": {"move": d.move, "skill": d.skill, "why": d.reason}}, indent=2, ensure_ascii=False), "problems": []}
        if name in INTERVIEW_TRY:
            m = storymap.new_map({"id": "try", "title": "try"})
            target = _pick_target(answer)
            extra = "SENSITIVE_TOPIC: something personal" if name == "sensitive-guard" else ""
            msg, problems = await interviewer.speak(name, profile, m, transcript, target=target, missing=["sequence", "position"], extra=extra)
            return {"output": msg, "problems": problems}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Editor] try skill {name}: {e}")
        raise HTTPException(503, f"The model call failed: {e}")
    raise HTTPException(400, "This one runs inside the writing chain. Use it from a real conversation, then read the draft in Review.")


# ── Codes and venues ─────────────────────────────────────────────────────────

@router.get("/codes")
async def codes(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(InvitationCode).order_by(InvitationCode.created_at.desc()))).scalars().all()
    return [{"id": str(c.id), "code": c.code, "label": c.label, "neighborhood": c.neighborhood,
             "max_uses": c.max_uses, "use_count": c.use_count, "is_active": c.is_active,
             "signup_url": f"{FRONTEND_URL}/vendor/join?code={c.code}"} for c in rows]


class CodeNew(BaseModel):
    code: str | None = None
    label: str | None = None
    neighborhood: str | None = None
    max_uses: int | None = 50


@router.post("/codes")
async def new_code(body: CodeNew, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    code = (body.code or secrets.token_hex(3)).strip().upper().replace(" ", "")
    if (await db.execute(select(InvitationCode.id).where(func.upper(InvitationCode.code) == code))).first():
        raise HTTPException(400, "That code already exists.")
    db.add(InvitationCode(market_id=market.id, code=code, label=body.label, neighborhood=body.neighborhood,
                          max_uses=body.max_uses, created_by=ed.id))
    await db.commit()
    return {"code": code}


@router.post("/codes/{cid}/toggle")
async def toggle_code(cid: str, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    c = await db.get(InvitationCode, as_uuid(cid))
    if not c:
        raise HTTPException(404, "Not found.")
    c.is_active = not c.is_active
    await db.commit()
    return {"is_active": c.is_active}


@router.get("/venues")
async def venues(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Venue).order_by(Venue.created_at))).scalars().all()
    counts = dict((await db.execute(select(Vendor.venue_id, func.count()).where(Vendor.status == "active")
                                    .group_by(Vendor.venue_id))).all())
    return [{"id": str(v.id), "name": v.name, "slug": v.slug, "neighborhood": v.neighborhood,
             "description": v.description, "schedule_note": v.schedule_note, "vendors": counts.get(v.id, 0),
             "qr_url": f"{FRONTEND_URL}/m/{v.slug}?qr=1", "page_url": f"{FRONTEND_URL}/m/{v.slug}",
             "report_url": f"{FRONTEND_URL}/report/{v.report_token}"} for v in rows]


class VenueIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    neighborhood: str | None = None
    description: str | None = None
    schedule_note: str | None = None


@router.post("/venues")
async def new_venue(body: VenueIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    slug = slugify(body.name, 40)
    if (await db.execute(select(Venue.id).where(Venue.slug == slug))).first():
        slug = f"{slug}-{short_id(3)}"
    db.add(Venue(market_id=market.id, name=body.name.strip(), slug=slug, neighborhood=body.neighborhood,
                 description=body.description, schedule_note=body.schedule_note,
                 report_token=secrets.token_urlsafe(16)))
    await db.commit()
    return {"slug": slug}


@router.post("/venues/{vid}/new-report-link")
async def new_report_link(vid: str, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    v = await db.get(Venue, as_uuid(vid))
    if not v:
        raise HTTPException(404, "Not found.")
    v.report_token = secrets.token_urlsafe(16)
    await db.commit()
    return {"report_url": f"{FRONTEND_URL}/report/{v.report_token}"}


# ── The weekly issue ─────────────────────────────────────────────────────────

@router.get("/issue")
async def issue(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    iss = await draft_issue(db, market)
    sel = await select_for(db, market, None)
    readers = (await db.execute(select(func.count()).select_from(Subscriber).where(Subscriber.status == SubscriberStatus.ACTIVE))).scalar()
    history = (await db.execute(select(Issue).where(Issue.status != IssueStatus.ASSEMBLING)
                                .order_by(Issue.issue_number.desc()).limit(12))).scalars().all()
    clicks = dict((await db.execute(select(LinkClick.issue_id, func.count()).group_by(LinkClick.issue_id))).all())
    return {
        "id": str(iss.id), "issue_number": iss.issue_number, "subject": iss.subject, "greeting": iss.greeting,
        "editor_name": iss.editor_name or ed.name, "status": iss.status, "readers": readers,
        "last_error": iss.last_error,
        "stories_available": sel["pool_size"],
        "preview_stories": [b.headline for b in sel["stories"]],
        "preview_updates": [b.headline for b in sel["updates"]],
        "history": [{"issue_number": h.issue_number, "subject": h.subject, "status": h.status,
                     "sent_count": h.sent_count, "sent_at": iso(h.sent_at), "clicks": clicks.get(h.id, 0)} for h in history],
    }


class IssuePatch(BaseModel):
    subject: str | None = Field(default=None, max_length=140)
    greeting: str | None = Field(default=None, max_length=1500)
    editor_name: str | None = Field(default=None, max_length=80)


@router.patch("/issue")
async def patch_issue(body: IssuePatch, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    iss = await draft_issue(db, market)
    if body.subject is not None:
        iss.subject = body.subject.strip() or None
    if body.greeting is not None:
        iss.greeting = body.greeting.strip() or None
    if body.editor_name is not None:
        iss.editor_name = body.editor_name.strip() or None
    await db.commit()
    return {"ok": True}


@router.get("/issue/preview", response_class=HTMLResponse)
async def preview(email: str | None = None, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    iss = await draft_issue(db, market)
    sub = None
    if email:
        sub = (await db.execute(select(Subscriber).where(func.lower(Subscriber.email) == email.lower()))).scalar_one_or_none()
    sel = await select_for(db, market, sub)
    if not iss.editor_name:
        iss.editor_name = ed.name
    _, doc, _ = render(market, iss, sel, sub)
    return HTMLResponse(doc)


class TestIn(BaseModel):
    email: EmailStr


@router.post("/issue/test")
async def test_send(body: TestIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    iss = await draft_issue(db, market)
    if not iss.editor_name:
        iss.editor_name = ed.name
    sub = (await db.execute(select(Subscriber).where(func.lower(Subscriber.email) == body.email.lower()))).scalar_one_or_none()
    sel = await select_for(db, market, sub)
    subject, doc, _ = render(market, iss, sel, None)
    ok, info = await send_email(db, body.email, f"[Test] {subject}", doc, "issue_test", market)
    await db.commit()
    if not ok:
        raise HTTPException(400, f"The test didn't send: {info}")
    return {"ok": True}


@router.post("/issue/send")
async def send(bg: BackgroundTasks, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    iss = await draft_issue(db, market)
    if iss.status != IssueStatus.ASSEMBLING:
        raise HTTPException(400, "This issue is already sending.")
    if not iss.editor_name:
        iss.editor_name = ed.name
    iss.status = IssueStatus.SENDING
    iss.assembled_at = utcnow()
    if not iss.subject:
        sel = await select_for(db, market, None)
        iss.subject = sel["stories"][0].headline if sel["stories"] else f"{market.publication_name} No. {iss.issue_number}"
    await db.commit()
    bg.add_task(send_issue, iss.id)
    return {"ok": True, "issue_number": iss.issue_number}


# ── Readers and inquiries ────────────────────────────────────────────────────

@router.get("/readers")
async def readers(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    subs = (await db.execute(select(Subscriber).order_by(Subscriber.created_at.desc()).limit(500))).scalars().all()
    follows = dict((await db.execute(select(VendorFollow.subscriber_id, func.count()).where(
        VendorFollow.is_muted.is_(False)).group_by(VendorFollow.subscriber_id))).all())
    sources = dict((await db.execute(select(Subscriber.signup_source, func.count()).group_by(Subscriber.signup_source))).all())
    return {
        "readers": [{"email": s.email, "status": s.status, "source": s.signup_source, "follows": follows.get(s.id, 0),
                     "neighborhood": s.inferred_neighborhood, "created_at": iso(s.created_at)} for s in subs],
        "by_source": {k or "unknown": v for k, v in sources.items()},
    }


@router.get("/inbox")
async def inbox(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    leads = (await db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(100))).scalars().all()
    noms = (await db.execute(select(Nomination).order_by(Nomination.created_at.desc()).limit(100))).scalars().all()
    return {
        "leads": [{"id": str(l.id), "kind": l.kind, "name": l.name, "organization": l.organization, "email": l.email,
                   "message": l.message, "status": l.status, "created_at": iso(l.created_at)} for l in leads],
        "nominations": [{"id": str(n.id), "shop_name": n.shop_name, "where": n.where, "why": n.why,
                         "email": n.nominator_email, "status": n.status, "created_at": iso(n.created_at)} for n in noms],
    }


class StatusIn(BaseModel):
    status: str


@router.post("/inbox/{kind}/{item_id}")
async def inbox_status(kind: str, item_id: str, body: StatusIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    model = Lead if kind == "lead" else Nomination
    row = await db.get(model, as_uuid(item_id))
    if not row:
        raise HTTPException(404, "Not found.")
    row.status = body.status[:20]
    await db.commit()
    return {"ok": True}


# ── Settings and sample data ─────────────────────────────────────────────────

@router.get("/settings")
async def settings(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    m = await _market(db)
    eds = (await db.execute(select(Editor).order_by(Editor.created_at))).scalars().all()
    return {"publication_name": m.publication_name, "from_email": m.from_email, "from_name": m.from_name,
            "market": m.name, "editors": [{"name": e.name, "email": e.email} for e in eds]}


class SettingsIn(BaseModel):
    publication_name: str | None = None
    from_email: EmailStr | None = None
    from_name: str | None = None


@router.patch("/settings")
async def patch_settings(body: SettingsIn, ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    m = await _market(db)
    if body.publication_name:
        m.publication_name = body.publication_name.strip()
    if body.from_email:
        m.from_email = body.from_email
    if body.from_name:
        m.from_name = body.from_name.strip()
    await db.commit()
    return {"ok": True}


@router.delete("/samples")
async def remove_samples(ed: Editor = Depends(current_editor), db: AsyncSession = Depends(get_db)):
    vids = (await db.execute(select(Vendor.id).where(Vendor.is_sample.is_(True)))).scalars().all()
    if vids:
        bids = (await db.execute(select(Block.id).where(Block.vendor_id.in_(vids)))).scalars().all()
        cids = (await db.execute(select(Conversation.id).where(Conversation.vendor_id.in_(vids)))).scalars().all()
        await db.execute(delete(ReaderShare).where(ReaderShare.vendor_id.in_(vids)))
        await db.execute(delete(LinkClick).where(or_(LinkClick.vendor_id.in_(vids), LinkClick.block_id.in_(bids or [None]))))
        if bids:
            await db.execute(delete(SeenBlock).where(SeenBlock.block_id.in_(bids)))
            await db.execute(delete(BlockCorrection).where(BlockCorrection.block_id.in_(bids)))
            await db.execute(delete(Block).where(Block.id.in_(bids)))
        await db.execute(delete(Submission).where(Submission.vendor_id.in_(vids)))
        if cids:
            await db.execute(delete(Message).where(Message.conversation_id.in_(cids)))
            await db.execute(delete(Conversation).where(Conversation.id.in_(cids)))
        await db.execute(delete(VendorFollow).where(VendorFollow.vendor_id.in_(vids)))
        await db.execute(delete(ScanEvent).where(ScanEvent.vendor_id.in_(vids)))
        await db.execute(delete(VendorSession).where(VendorSession.vendor_id.in_(vids)))
        await db.execute(update(Subscriber).where(Subscriber.first_vendor_id.in_(vids)).values(first_vendor_id=None))
        await db.execute(delete(Vendor).where(Vendor.id.in_(vids)))
    await db.execute(delete(ReaderShare).where(ReaderShare.vendor_id.is_(None), ReaderShare.reader_name.like("%(sample)%")))
    await db.commit()
    return {"removed_vendors": len(vids)}
