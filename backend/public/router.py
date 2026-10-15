"""
Public endpoints: the website, QR landings, following, sharing, nominating,
unsubscribing, click tracking, media and the market report.

No login anywhere here. A reader's identity is the auth_token in their links
(and remembered by their browser after they follow once).
"""

import secrets
import uuid
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import verify
from core.config import FRONTEND_URL
from core.mail import send_email
from core.util import as_uuid, iso
from database.models import (
    Block, BlockClass, BlockStatus, Issue, IssueStatus, Lead, LinkClick, Market, Media, Nomination,
    ReaderShare, ScanEvent, Subscriber, SubscriberStatus, Vendor, VendorFollow, Venue, utcnow,
)
from database.session import AsyncSessionLocal, get_db

router = APIRouter()

MAX_UPLOAD = 4 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


# ── Serializers ──────────────────────────────────────────────────────────────

def vendor_card(v: Vendor, venue: Venue | None = None) -> dict:
    return {
        "id": str(v.id), "name": v.name, "slug": v.slug, "scan_code": v.scan_code,
        "neighborhood": v.neighborhood, "categories": v.categories or [],
        "description": v.description, "schedule_note": v.schedule_note,
        "photo_url": v.photo_url, "instagram": v.instagram, "website": v.website,
        "venue": {"name": venue.name, "slug": venue.slug} if venue else None,
        "is_sample": v.is_sample,
    }


def block_out(b: Block, vendor: Vendor | None = None) -> dict:
    return {
        "id": str(b.id), "kind": b.block_class, "headline": b.headline, "body": b.body,
        "slug": b.slug, "image_urls": b.image_urls or [], "word_count": b.word_count,
        "created_at": iso(b.created_at), "reviewed_at": iso(b.reviewed_at),
        "is_sample": b.is_sample,
        "vendor": vendor_card(vendor) if vendor else None,
    }


def share_out(s: ReaderShare, vendor: Vendor | None = None) -> dict:
    return {"id": str(s.id), "text": s.text, "image_url": s.image_url, "reader_name": s.reader_name,
            "vendor": {"name": vendor.name, "scan_code": vendor.scan_code} if vendor else None,
            "created_at": iso(s.created_at)}


async def _market(db) -> Market:
    m = (await db.execute(select(Market).order_by(Market.created_at).limit(1))).scalar_one_or_none()
    if not m:
        raise HTTPException(503, "Not set up yet.")
    return m


def _public_blocks():
    now = utcnow()
    return select(Block).where(
        Block.status == BlockStatus.APPROVED, Block.is_public.is_(True),
        Block.block_class.in_([BlockClass.STORY, BlockClass.UPDATE]),
        (Block.expires_at.is_(None)) | (Block.expires_at > now - timedelta(days=60)),
    )


# ── Website content ──────────────────────────────────────────────────────────

@router.get("/public/home")
async def home(db: AsyncSession = Depends(get_db)):
    market = await _market(db)
    stories = (await db.execute(
        _public_blocks().where(Block.block_class == BlockClass.STORY)
        .order_by(Block.reviewed_at.desc().nullslast()).limit(6)
    )).scalars().all()
    vendors = {v.id: v for v in (await db.execute(select(Vendor).where(Vendor.status == "active"))).scalars().all()}
    venues = (await db.execute(select(Venue).where(Venue.is_active.is_(True)).order_by(Venue.created_at))).scalars().all()
    counts = {
        "vendors": len(vendors),
        "stories": (await db.execute(select(func.count()).select_from(Block).where(
            Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.STORY))).scalar(),
        "readers": (await db.execute(select(func.count()).select_from(Subscriber).where(
            Subscriber.status == SubscriberStatus.ACTIVE))).scalar(),
    }
    return {
        "publication": market.publication_name, "market": market.name,
        "stories": [block_out(b, vendors.get(b.vendor_id)) for b in stories],
        "venues": [{"name": v.name, "slug": v.slug, "neighborhood": v.neighborhood,
                    "vendor_count": sum(1 for x in vendors.values() if x.venue_id == v.id)} for v in venues],
        "counts": counts,
    }


@router.get("/public/stories")
async def stories(limit: int = 40, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        _public_blocks().where(Block.block_class == BlockClass.STORY)
        .order_by(Block.reviewed_at.desc().nullslast()).limit(min(limit, 100))
    )).scalars().all()
    vendors = {v.id: v for v in (await db.execute(select(Vendor))).scalars().all()}
    return [block_out(b, vendors.get(b.vendor_id)) for b in rows]


@router.get("/public/story/{slug}")
async def story(slug: str, db: AsyncSession = Depends(get_db)):
    b = (await db.execute(_public_blocks().where(Block.slug == slug))).scalar_one_or_none()
    if not b:
        raise HTTPException(404, "This story isn't available.")
    v = await db.get(Vendor, b.vendor_id) if b.vendor_id else None
    venue = await db.get(Venue, v.venue_id) if v and v.venue_id else None
    more = (await db.execute(
        _public_blocks().where(Block.vendor_id == b.vendor_id, Block.id != b.id)
        .order_by(Block.created_at.desc()).limit(4)
    )).scalars().all()
    out = block_out(b, v)
    out["vendor"] = vendor_card(v, venue) if v else None
    out["more"] = [block_out(m) for m in more]
    return out


@router.get("/public/vendors")
async def vendor_list(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Vendor).where(Vendor.status == "active").order_by(Vendor.name))).scalars().all()
    return [{"id": str(v.id), "name": v.name, "scan_code": v.scan_code} for v in rows]


@router.get("/public/venue/{slug}")
async def venue(slug: str, db: AsyncSession = Depends(get_db)):
    ven = (await db.execute(select(Venue).where(Venue.slug == slug))).scalar_one_or_none()
    if not ven:
        raise HTTPException(404, "We don't know this market yet.")
    vendors = (await db.execute(
        select(Vendor).where(Vendor.venue_id == ven.id, Vendor.status == "active").order_by(Vendor.name)
    )).scalars().all()
    latest = {}
    for b in (await db.execute(
        _public_blocks().where(Block.vendor_id.in_([v.id for v in vendors])).order_by(Block.created_at.desc())
    )).scalars().all():
        latest.setdefault(b.vendor_id, b)
    return {
        "name": ven.name, "slug": ven.slug, "neighborhood": ven.neighborhood,
        "description": ven.description, "schedule_note": ven.schedule_note,
        "vendors": [dict(vendor_card(v), latest=block_out(latest[v.id]) if v.id in latest else None) for v in vendors],
    }


@router.get("/public/vendor/{scan_code}")
async def vendor_page(scan_code: str, qr: int = 0, request: Request = None, db: AsyncSession = Depends(get_db)):
    v = (await db.execute(select(Vendor).where(func.upper(Vendor.scan_code) == scan_code.upper()))).scalar_one_or_none()
    if not v or v.status == "removed":
        raise HTTPException(404, "We couldn't find this vendor.")
    ven = await db.get(Venue, v.venue_id) if v.venue_id else None
    if qr:
        db.add(ScanEvent(vendor_id=v.id, user_agent=(request.headers.get("user-agent") or "")[:300] if request else None))
        await db.commit()
    blocks = (await db.execute(
        _public_blocks().where(Block.vendor_id == v.id).order_by(Block.created_at.desc()).limit(12)
    )).scalars().all()
    shares = (await db.execute(
        select(ReaderShare).where(ReaderShare.vendor_id == v.id, ReaderShare.status == "approved")
        .order_by(ReaderShare.created_at.desc()).limit(6)
    )).scalars().all()
    followers = (await db.execute(select(func.count()).select_from(VendorFollow).where(VendorFollow.vendor_id == v.id))).scalar()
    return {
        **vendor_card(v, ven),
        "stories": [block_out(b) for b in blocks if b.block_class == BlockClass.STORY],
        "updates": [block_out(b) for b in blocks if b.block_class == BlockClass.UPDATE][:3],
        "shares": [share_out(s) for s in shares],
        "followers": followers,
    }


# ── Following ────────────────────────────────────────────────────────────────

class FollowIn(BaseModel):
    email: EmailStr | None = None
    token: str | None = None
    vendor_ids: list[str] = Field(default_factory=list)
    consent: bool = False
    source: str = "website"          # qr_vendor | qr_venue | story_page | website | invite ...
    source_ref: str | None = None    # scan code, venue slug or story slug
    ref: str | None = None           # referring subscriber token (forwarded story)


async def _subscriber_by_token(db, token: str | None) -> Subscriber | None:
    if not token:
        return None
    return (await db.execute(select(Subscriber).where(Subscriber.auth_token == token))).scalar_one_or_none()


async def _follow(db, sub: Subscriber, vendor: Vendor) -> bool:
    f = (await db.execute(select(VendorFollow).where(
        VendorFollow.subscriber_id == sub.id, VendorFollow.vendor_id == vendor.id))).scalar_one_or_none()
    if f:
        f.scan_count += 1
        f.last_scanned_at = utcnow()
        f.is_muted = False
        return False
    db.add(VendorFollow(subscriber_id=sub.id, vendor_id=vendor.id))
    return True


async def _recompute_neighborhood(db, sub: Subscriber) -> None:
    rows = (await db.execute(
        select(Vendor.neighborhood, func.count()).join(VendorFollow, VendorFollow.vendor_id == Vendor.id)
        .where(VendorFollow.subscriber_id == sub.id, Vendor.neighborhood.is_not(None))
        .group_by(Vendor.neighborhood).order_by(func.count().desc())
    )).all()
    if rows:
        sub.inferred_neighborhood = rows[0][0]


@router.post("/public/follow")
async def follow(body: FollowIn, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    sub = await _subscriber_by_token(db, body.token)
    created = False
    if not sub:
        if not body.email:
            raise HTTPException(400, "Please enter your email.")
        sub = (await db.execute(select(Subscriber).where(func.lower(Subscriber.email) == body.email.lower()))).scalar_one_or_none()
        if not sub:
            if not body.consent:
                raise HTTPException(400, "Please tick the box to agree to receive the weekly email.")
            market = await _market(db)
            referrer = await _subscriber_by_token(db, body.ref)
            sub = Subscriber(
                email=body.email.lower(), auth_token=secrets.token_urlsafe(24), home_market_id=market.id,
                consent_source=f"{body.source}:{body.source_ref or ''}"[:120], signup_source=body.source,
                referred_by_id=referrer.id if referrer else None,
            )
            db.add(sub)
            await db.flush()
            created = True
        elif sub.status != SubscriberStatus.ACTIVE:
            sub.status = SubscriberStatus.ACTIVE
            sub.unsubscribed_at = None

    vendors = []
    for vid in body.vendor_ids[:30]:
        v = await db.get(Vendor, as_uuid(vid)) if as_uuid(vid) else None
        if v and v.status == "active":
            vendors.append(v)
    new_names = []
    for v in vendors:
        if await _follow(db, sub, v):
            new_names.append(v.name)
        db.add(ScanEvent(subscriber_id=sub.id, vendor_id=v.id, is_signup=created,
                         session_token=body.source))
        if created and not sub.first_vendor_id:
            sub.first_vendor_id = v.id
    await db.flush()
    await _recompute_neighborhood(db, sub)
    await db.commit()

    if created:
        bg.add_task(_welcome, str(sub.id), [v.name for v in vendors])
    follows = await _follows_of(db, sub)
    return {"token": sub.auth_token, "email": sub.email, "created": created,
            "newly_followed": new_names, "follows": follows}


async def _follows_of(db, sub: Subscriber) -> list[dict]:
    rows = (await db.execute(
        select(Vendor).join(VendorFollow, VendorFollow.vendor_id == Vendor.id)
        .where(VendorFollow.subscriber_id == sub.id, VendorFollow.is_muted.is_(False))
    )).scalars().all()
    return [{"id": str(v.id), "name": v.name, "scan_code": v.scan_code} for v in rows]


async def _welcome(subscriber_id: str, vendor_names: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        sub = await db.get(Subscriber, uuid.UUID(subscriber_id))
        market = await _market(db)
        pub = market.publication_name or "Brown Bag"
        who = ", ".join(vendor_names) if vendor_names else "local vendors"
        html_body = f"""<div style="font-family:Georgia,serif;max-width:520px;margin:auto;padding:24px;color:#2b2118">
<h1 style="font-size:26px;margin:0 0 12px">{pub}</h1>
<p style="font-size:17px;line-height:1.6">You're following {who}.</p>
<p style="font-size:17px;line-height:1.6">Once a week you'll get one short email: a real story from a local vendor, where your vendors will be, what's new, and what other readers made with what they bought. That's all.</p>
<p style="font-size:15px;line-height:1.6">Follow more vendors any time at <a href="{FRONTEND_URL}" style="color:#b07a45">{FRONTEND_URL.replace('https://', '')}</a>.</p>
<p style="font-size:12px;color:#7a6a58">Didn't mean to sign up? <a href="{FRONTEND_URL}/unsubscribe?t={sub.auth_token}" style="color:#7a6a58">Unsubscribe</a>.</p></div>"""
        await send_email(db, sub.email, f"You're on the {pub} list", html_body, "subscriber_welcome", market,
                         subscriber_id=sub.id)
        await db.commit()


@router.get("/public/me")
async def me(t: str, db: AsyncSession = Depends(get_db)):
    sub = await _subscriber_by_token(db, t)
    if not sub:
        raise HTTPException(404, "Not found.")
    return {"email": sub.email, "status": sub.status, "follows": await _follows_of(db, sub)}


class TokenVendor(BaseModel):
    t: str
    vendor_id: str | None = None


@router.post("/public/unfollow")
async def unfollow(body: TokenVendor, db: AsyncSession = Depends(get_db)):
    sub = await _subscriber_by_token(db, body.t)
    if not sub:
        raise HTTPException(404, "Not found.")
    f = (await db.execute(select(VendorFollow).where(
        VendorFollow.subscriber_id == sub.id, VendorFollow.vendor_id == as_uuid(body.vendor_id)))).scalar_one_or_none()
    if f:
        f.is_muted = True
        await db.commit()
    return {"follows": await _follows_of(db, sub)}


@router.post("/public/unsubscribe")
async def unsubscribe(body: TokenVendor, db: AsyncSession = Depends(get_db)):
    sub = await _subscriber_by_token(db, body.t)
    if not sub:
        raise HTTPException(404, "This link isn't valid anymore.")
    sub.status = SubscriberStatus.UNSUBSCRIBED
    sub.unsubscribed_at = utcnow()
    await db.commit()
    return {"email": sub.email, "status": sub.status}


# ── Reader shares, nominations, leads ────────────────────────────────────────

class ShareIn(BaseModel):
    t: str | None = None
    email: EmailStr | None = None
    reader_name: str | None = Field(default=None, max_length=80)
    vendor_id: str | None = None
    text: str = Field(min_length=3, max_length=1200)
    image_url: str | None = None


@router.post("/public/share")
async def share(body: ShareIn, db: AsyncSession = Depends(get_db)):
    sub = await _subscriber_by_token(db, body.t)
    v = await db.get(Vendor, as_uuid(body.vendor_id)) if as_uuid(body.vendor_id) else None
    image = body.image_url if body.image_url and body.image_url.startswith("/media/") else None
    db.add(ReaderShare(subscriber_id=sub.id if sub else None, vendor_id=v.id if v else None,
                       reader_name=body.reader_name, email=(sub.email if sub else body.email),
                       text=body.text.strip(), image_url=image))
    await db.commit()
    return {"ok": True}


class NominateIn(BaseModel):
    shop_name: str = Field(min_length=2, max_length=120)
    where: str | None = Field(default=None, max_length=160)
    why: str | None = Field(default=None, max_length=1200)
    email: EmailStr | None = None
    t: str | None = None


@router.post("/public/nominate")
async def nominate(body: NominateIn, db: AsyncSession = Depends(get_db)):
    sub = await _subscriber_by_token(db, body.t)
    db.add(Nomination(shop_name=body.shop_name, where=body.where, why=body.why,
                      nominator_email=(sub.email if sub else body.email), subscriber_id=sub.id if sub else None))
    await db.commit()
    return {"ok": True}


class LeadIn(BaseModel):
    kind: str = "market"
    name: str = Field(min_length=1, max_length=120)
    organization: str | None = Field(default=None, max_length=160)
    email: EmailStr
    message: str | None = Field(default=None, max_length=3000)


@router.post("/public/lead")
async def lead(body: LeadIn, db: AsyncSession = Depends(get_db)):
    db.add(Lead(kind=body.kind if body.kind in ("market", "vendor") else "market", name=body.name,
                organization=body.organization, email=body.email, message=body.message))
    await db.commit()
    return {"ok": True}


# ── Media ────────────────────────────────────────────────────────────────────

@router.post("/public/media")
async def upload(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(400, "Please upload a photo (JPEG, PNG or WebP).")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "That photo is too large. Please use one under 4 MB.")
    m = Media(content_type=file.content_type, data=data, size_bytes=len(data), uploaded_by="public")
    db.add(m)
    await db.commit()
    return {"url": f"/media/{m.id}"}


@router.get("/media/{media_id}")
async def media(media_id: str, db: AsyncSession = Depends(get_db)):
    m = await db.get(Media, as_uuid(media_id)) if as_uuid(media_id) else None
    if not m:
        raise HTTPException(404)
    return Response(m.data, media_type=m.content_type,
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})


# ── Click tracking ───────────────────────────────────────────────────────────

@router.get("/r/{token}")
async def click(token: str, db: AsyncSession = Depends(get_db)):
    body = verify(token)
    if not body:
        return RedirectResponse(FRONTEND_URL)
    path = body.get("p") or "/"
    if not path.startswith("/"):
        path = "/"
    try:
        db.add(LinkClick(subscriber_id=as_uuid(body.get("s")), issue_id=as_uuid(body.get("i")),
                         block_id=as_uuid(body.get("b")), vendor_id=as_uuid(body.get("v")),
                         kind=body.get("k") or "story"))
        await db.commit()
    except Exception:  # noqa: BLE001
        await db.rollback()
    sep = "&" if "?" in path else "?"
    return RedirectResponse(f"{FRONTEND_URL}{path}{sep}src=email", status_code=302)


# ── Market report (read-only, for the venue's organization) ─────────────────

@router.get("/public/report/{token}")
async def report(token: str, db: AsyncSession = Depends(get_db)):
    ven = (await db.execute(select(Venue).where(Venue.report_token == token))).scalar_one_or_none()
    if not ven:
        raise HTTPException(404, "This report link isn't valid.")
    market = await db.get(Market, ven.market_id)
    now = utcnow()
    vendors = (await db.execute(select(Vendor).where(Vendor.venue_id == ven.id, Vendor.status == "active")
                                .order_by(Vendor.name))).scalars().all()
    vids = [v.id for v in vendors]
    if not vids:
        vids = [uuid.uuid4()]

    async def count(stmt):
        return (await db.execute(stmt)).scalar() or 0

    follower_ids = select(VendorFollow.subscriber_id).where(VendorFollow.vendor_id.in_(vids), VendorFollow.is_muted.is_(False))
    readers = await count(select(func.count(func.distinct(Subscriber.id))).where(
        Subscriber.id.in_(follower_ids), Subscriber.status == SubscriberStatus.ACTIVE))
    new_7 = await count(select(func.count()).select_from(VendorFollow).where(
        VendorFollow.vendor_id.in_(vids), VendorFollow.first_scanned_at > now - timedelta(days=7)))
    new_30 = await count(select(func.count()).select_from(VendorFollow).where(
        VendorFollow.vendor_id.in_(vids), VendorFollow.first_scanned_at > now - timedelta(days=30)))
    clicks_30 = await count(select(func.count()).select_from(LinkClick).where(
        LinkClick.vendor_id.in_(vids), LinkClick.clicked_at > now - timedelta(days=30)))
    scans_30 = await count(select(func.count()).select_from(ScanEvent).where(
        ScanEvent.vendor_id.in_(vids), ScanEvent.scanned_at > now - timedelta(days=30)))
    shares = await count(select(func.count()).select_from(ReaderShare).where(ReaderShare.vendor_id.in_(vids)))
    issues_sent = await count(select(func.count()).select_from(Issue).where(
        Issue.market_id == ven.market_id, Issue.status == IssueStatus.SENT))

    per_vendor = []
    for v in vendors:
        per_vendor.append({
            "name": v.name, "scan_code": v.scan_code, "is_sample": v.is_sample,
            "categories": v.categories or [],
            "followers": await count(select(func.count()).select_from(VendorFollow).where(
                VendorFollow.vendor_id == v.id, VendorFollow.is_muted.is_(False))),
            "stories": await count(select(func.count()).select_from(Block).where(
                Block.vendor_id == v.id, Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.STORY)),
            "updates": await count(select(func.count()).select_from(Block).where(
                Block.vendor_id == v.id, Block.status == BlockStatus.APPROVED, Block.block_class == BlockClass.UPDATE)),
            "clicks_30": await count(select(func.count()).select_from(LinkClick).where(
                LinkClick.vendor_id == v.id, LinkClick.clicked_at > now - timedelta(days=30))),
            "reader_shares": await count(select(func.count()).select_from(ReaderShare).where(ReaderShare.vendor_id == v.id)),
        })

    weeks = []
    for i in range(7, -1, -1):
        start, end = now - timedelta(days=7 * (i + 1)), now - timedelta(days=7 * i)
        weeks.append({"week_ending": end.date().isoformat(), "new_follows": await count(
            select(func.count()).select_from(VendorFollow).where(
                VendorFollow.vendor_id.in_(vids), VendorFollow.first_scanned_at > start,
                VendorFollow.first_scanned_at <= end))})

    recent = (await db.execute(
        select(Block).where(Block.vendor_id.in_(vids), Block.status == BlockStatus.APPROVED,
                            Block.block_class == BlockClass.STORY).order_by(Block.reviewed_at.desc().nullslast()).limit(5)
    )).scalars().all()
    vmap = {v.id: v for v in vendors}
    return {
        "venue": {"name": ven.name, "slug": ven.slug, "neighborhood": ven.neighborhood},
        "publication": market.publication_name if market else "Brown Bag",
        "generated_at": iso(now),
        "totals": {"vendors": len(vendors), "sample_vendors": sum(1 for v in vendors if v.is_sample),
                   "readers": readers, "new_follows_7": new_7, "new_follows_30": new_30,
                   "clicks_30": clicks_30, "scans_30": scans_30, "reader_shares": shares,
                   "issues_sent": issues_sent},
        "weeks": weeks,
        "vendors": per_vendor,
        "recent_stories": [block_out(b, vmap.get(b.vendor_id)) for b in recent],
        "qr_url": f"{FRONTEND_URL}/m/{ven.slug}",
    }
