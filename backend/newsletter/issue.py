"""
Assemble, personalize, render and send the weekly issue.

Each reader's issue:
  1. Greeting from the named editor (same for everyone)
  2. The story of the week (personalized), plus a second shorter story if the bank allows
  3. From your vendors: short updates, followed vendors first
  4. Readers made this: one or two reader photos/notes
  5. Share yours / nominate a shop / forward
  6. Footer: why you get this, unsubscribe

Selection rules (docs/PRODUCT.md): a story a reader has seen is excluded
forever; score = quality + relevance + discovery + proximity - fatigue.
"""

import asyncio
import html
import logging
from datetime import timedelta

from sqlalchemy import and_, exists, func, not_, or_, select

from core.auth import sign
from core.config import API_URL, FRONTEND_URL
from core.mail import send_email
from database.models import (
    Block, BlockClass, BlockCorrection, BlockStatus, CorrectionStatus, Issue, IssueRender,
    IssueStatus, Market, MIN_QUALITY_SCORE, ReaderShare, SeenBlock, Subscriber, SubscriberStatus,
    Vendor, VendorFollow, utcnow,
)
from database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

SEND_DELAY_SECONDS = 0.6   # stay under the provider's per-second limit


# ── Selection ────────────────────────────────────────────────────────────────

def _bank(now, cls):
    open_corr = exists().where(and_(BlockCorrection.block_id == Block.id,
                                    BlockCorrection.status == CorrectionStatus.OPEN))
    return and_(
        Block.status == BlockStatus.APPROVED,
        Block.block_class == cls,
        Block.quality_score >= MIN_QUALITY_SCORE,
        or_(Block.expires_at.is_(None), Block.expires_at > now),
        not_(open_corr),
    )


async def select_for(db, market: Market, subscriber: Subscriber | None) -> dict:
    now = utcnow()
    followed: set = set()
    seen: set = set()
    recent_vendors: set = set()
    if subscriber:
        followed = set((await db.execute(
            select(VendorFollow.vendor_id).where(VendorFollow.subscriber_id == subscriber.id,
                                                 VendorFollow.is_muted.is_(False))
        )).scalars().all())
        seen = set((await db.execute(
            select(SeenBlock.block_id).where(SeenBlock.subscriber_id == subscriber.id)
        )).scalars().all())
        last = (await db.execute(
            select(IssueRender.block_ids).where(IssueRender.subscriber_id == subscriber.id)
            .order_by(IssueRender.sent_at.desc().nullslast()).limit(1)
        )).scalar_one_or_none() or []
        if last:
            recent_vendors = set((await db.execute(
                select(Block.vendor_id).where(Block.id.in_(last))
            )).scalars().all())

    vendors = {v.id: v for v in (await db.execute(
        select(Vendor).where(Vendor.market_id == market.id, Vendor.status == "active")
    )).scalars().all()}
    followed_cats = {c for vid in followed if vid in vendors for c in (vendors[vid].categories or [])}
    complements = {c for vid in followed if vid in vendors for c in (vendors[vid].complementary_categories or [])}
    home = subscriber.inferred_neighborhood if subscriber else None

    def score(b: Block) -> float:
        v = vendors.get(b.vendor_id)
        s = b.quality_score or 0
        if b.vendor_id in followed:
            s += 60
        cats = set(b.categories or [])
        if cats & complements:
            s += 25
        elif cats & followed_cats:
            s += 10
        if v and home and v.neighborhood:
            if v.neighborhood == home:
                s += 20
            elif v.neighborhood in market.adjacent_to(home):
                s += 12
        if b.vendor_id in recent_vendors:
            s -= 40
        # newer first among ties
        s += min(10, max(0, 10 - (now - b.created_at).days / 3))
        return s

    def eligible(cls):
        return select(Block).where(Block.market_id == market.id, _bank(now, cls))

    stories = [b for b in (await db.execute(eligible(BlockClass.STORY))).scalars().all()
               if b.id not in seen and b.vendor_id in vendors]
    stories.sort(key=score, reverse=True)
    picked_stories, used_vendors = [], set()
    for b in stories:
        if b.vendor_id in used_vendors:
            continue
        picked_stories.append(b)
        used_vendors.add(b.vendor_id)
        if len(picked_stories) == 2:
            break

    updates = [b for b in (await db.execute(eligible(BlockClass.UPDATE))).scalars().all()
               if b.id not in seen and b.vendor_id in vendors]
    updates.sort(key=lambda b: (b.vendor_id in followed, score(b)), reverse=True)
    picked_updates, seen_upd_vendor = [], set()
    for b in updates:
        if b.vendor_id in seen_upd_vendor:
            continue
        picked_updates.append(b)
        seen_upd_vendor.add(b.vendor_id)
        if len(picked_updates) == 4:
            break

    shares = (await db.execute(
        select(ReaderShare).where(ReaderShare.status == "approved")
        .order_by(ReaderShare.featured_count.asc(), ReaderShare.created_at.desc()).limit(2)
    )).scalars().all()

    return {
        "stories": picked_stories,
        "updates": picked_updates,
        "shares": list(shares),
        "vendors": vendors,
        "followed": followed,
        "pool_size": len(stories),
    }


# ── Rendering ────────────────────────────────────────────────────────────────

INK = "#2b2118"
MUTED = "#7a6a58"
KRAFT = "#b07a45"
PAPER = "#f6f1e9"


def _e(s) -> str:
    return html.escape(s or "")


def _paras(text: str, size: int = 17) -> str:
    out = []
    for p in (text or "").split("\n"):
        p = p.strip()
        if p:
            out.append(f'<p style="margin:0 0 14px;font-size:{size}px;line-height:1.6;color:{INK}">{_e(p)}</p>')
    return "".join(out)


def track(subscriber, issue, path: str, kind: str, block=None, vendor_id=None) -> str:
    if not subscriber:
        return FRONTEND_URL + path
    token = sign({
        "s": str(subscriber.id), "i": str(issue.id) if issue else None,
        "b": str(block.id) if block else None,
        "v": str(vendor_id or (block.vendor_id if block else "")) or None,
        "k": kind, "p": path,
    }, 400 * 24 * 3600)
    return f"{API_URL}/r/{token}"


def render(market: Market, issue: Issue | None, sel: dict, subscriber: Subscriber | None) -> tuple[str, str, int]:
    """Returns (subject, html, word_count)."""
    pub = _e(market.publication_name or "Brown Bag")
    vendors = sel["vendors"]
    words = 0
    parts = []

    greeting = (issue.greeting if issue else None) or ""
    if greeting:
        words += len(greeting.split())
        sig = _e(issue.editor_name) if issue and issue.editor_name else ""
        parts.append(_paras(greeting, 16) + (
            f'<p style="margin:0 0 8px;font-size:15px;color:{MUTED}">— {sig}, editor</p>' if sig else ""))

    for i, b in enumerate(sel["stories"]):
        v = vendors.get(b.vendor_id)
        words += b.word_count or 0
        link = track(subscriber, issue, f"/s/{b.slug}", "story", b)
        vlink = track(subscriber, issue, f"/v/{v.scan_code}", "vendor", vendor_id=v.id) if v else "#"
        label = "This week's story" if i == 0 else "One more"
        if i == 0:
            body_html = _paras(b.body)
        else:
            body_html = _paras(_lead(b.body)) + (
                f'<p style="margin:0 0 14px;font-size:15px"><a href="{link}" style="color:{KRAFT}">Read the rest of the story</a></p>')
        parts.append(f'''
<tr><td style="padding:28px 0 8px;border-top:1px solid #e3d8c8">
<p style="margin:0 0 6px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:{KRAFT}">{label}</p>
<h2 style="margin:0 0 6px;font-family:Georgia,serif;font-size:{26 if i == 0 else 21}px;line-height:1.25;color:{INK}">
<a href="{link}" style="color:{INK};text-decoration:none">{_e(b.headline)}</a></h2>
<p style="margin:0 0 16px;font-size:14px;color:{MUTED}"><a href="{vlink}" style="color:{MUTED}">{_e(v.name if v else "")}</a>{(" · " + _e(v.neighborhood)) if v and v.neighborhood else ""}</p>
{body_html}
</td></tr>''')

    if sel["updates"]:
        rows = []
        for b in sel["updates"]:
            v = vendors.get(b.vendor_id)
            words += b.word_count or 0
            vlink = track(subscriber, issue, f"/v/{v.scan_code}", "vendor", b) if v else "#"
            mark = " ★" if b.vendor_id in sel["followed"] else ""
            rows.append(f'''<p style="margin:0 0 4px;font-size:15px;font-weight:bold;color:{INK}"><a href="{vlink}" style="color:{INK};text-decoration:none">{_e(v.name if v else "")}</a>{mark} — {_e(b.headline)}</p>
<p style="margin:0 0 16px;font-size:15px;line-height:1.55;color:{INK}">{_e(b.body)}</p>''')
        heading = "From your vendors" if sel["followed"] else "Around the markets"
        parts.append(f'''<tr><td style="padding:24px 0 8px;border-top:1px solid #e3d8c8">
<p style="margin:0 0 14px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:{KRAFT}">{heading}</p>{"".join(rows)}</td></tr>''')

    if sel["shares"]:
        rows = []
        for s in sel["shares"]:
            v = vendors.get(s.vendor_id) if s.vendor_id else None
            img = (f'<img src="{_e(_abs(s.image_url))}" width="520" style="width:100%;max-width:520px;border-radius:6px;margin:0 0 8px" alt="">'
                   if s.image_url else "")
            credit = _e(s.reader_name or "A reader")
            about = f" · from {_e(v.name)}" if v else ""
            rows.append(f'''{img}<p style="margin:0 0 4px;font-size:15px;line-height:1.55;color:{INK}">“{_e(s.text)}”</p>
<p style="margin:0 0 18px;font-size:13px;color:{MUTED}">— {credit}{about}</p>''')
        share_link = track(subscriber, issue, f"/share?t={subscriber.auth_token}" if subscriber else "/share", "share")
        parts.append(f'''<tr><td style="padding:24px 0 8px;border-top:1px solid #e3d8c8">
<p style="margin:0 0 14px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:{KRAFT}">Readers made this</p>{"".join(rows)}
<p style="margin:0 0 8px;font-size:15px;color:{INK}">Made something with what you bought? <a href="{share_link}" style="color:{KRAFT}">Send us a photo</a> and it might run here.</p></td></tr>''')

    nominate = track(subscriber, issue, "/nominate", "nominate")
    footer_follow = ""
    if subscriber and sel["followed"]:
        names = ", ".join(_e(vendors[v].name) for v in sel["followed"] if v in vendors)
        footer_follow = f"You follow {names}. "
    unsub = f"{FRONTEND_URL}/unsubscribe?t={subscriber.auth_token}" if subscriber else "#"
    web = f"{FRONTEND_URL}/stories"
    parts.append(f'''<tr><td style="padding:24px 0 0;border-top:1px solid #e3d8c8">
<p style="margin:0 0 10px;font-size:15px;color:{INK}">Know a shop or a stall we should write about? <a href="{nominate}" style="color:{KRAFT}">Nominate them</a>. If you liked a story, forward this to a neighbor.</p>
<p style="margin:16px 0 0;font-size:12px;line-height:1.6;color:{MUTED}">{footer_follow}You get {pub} because you followed a local vendor. Every story is checked by the vendor and approved by a person before it goes out.
<a href="{web}" style="color:{MUTED}">Read past stories</a> · <a href="{unsub}" style="color:{MUTED}">Unsubscribe</a></p></td></tr>''')

    lead = sel["stories"][0].headline if sel["stories"] else (sel["updates"][0].headline if sel["updates"] else "This week")
    subject = (issue.subject if issue and issue.subject else None) or lead
    number = f"No. {issue.issue_number} · " if issue else ""
    doc = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(subject)}</title></head>
<body style="margin:0;background:{PAPER};font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fffdf9;border:1px solid #e3d8c8;border-radius:10px">
<tr><td style="padding:28px 28px 8px">
<table role="presentation" width="100%"><tr><td style="font-family:Georgia,serif;font-size:28px;font-weight:bold;color:{INK}">{pub}</td>
<td align="right" style="font-size:12px;color:{MUTED}">{number}{_e(market.name)}</td></tr></table></td></tr>
<tr><td style="padding:8px 28px 28px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:12px 0 8px"></td></tr>{"".join(p if p.lstrip().startswith("<tr") else f"<tr><td style='padding:8px 0'>{p}</td></tr>" for p in parts)}
</table></td></tr></table></td></tr></table></body></html>'''
    return subject, doc, words


def _lead(text: str, paras: int = 2) -> str:
    return "\n".join([p for p in (text or "").split("\n") if p.strip()][:paras])


def _abs(url: str) -> str:
    if url and url.startswith("/"):
        return API_URL + url
    return url


# ── Issues and sending ───────────────────────────────────────────────────────

async def draft_issue(db, market: Market) -> Issue:
    issue = (await db.execute(
        select(Issue).where(Issue.market_id == market.id, Issue.status == IssueStatus.ASSEMBLING)
        .order_by(Issue.issue_number.desc()).limit(1)
    )).scalar_one_or_none()
    if issue:
        return issue
    last = (await db.execute(select(func.max(Issue.issue_number)).where(Issue.market_id == market.id))).scalar() or 0
    issue = Issue(market_id=market.id, issue_number=last + 1, send_date=utcnow().date(),
                  status=IssueStatus.ASSEMBLING)
    db.add(issue)
    await db.commit()
    return issue


async def send_issue(issue_id) -> None:
    """Background job: one personalized email per active subscriber."""
    async with AsyncSessionLocal() as db:
        issue = await db.get(Issue, issue_id)
        market = await db.get(Market, issue.market_id)
        subs = (await db.execute(
            select(Subscriber).where(Subscriber.status == SubscriberStatus.ACTIVE)
        )).scalars().all()
        sent = 0
        last_error = None
        for sub in subs:
            try:
                sel = await select_for(db, market, sub)
                if not sel["stories"] and not sel["updates"]:
                    continue
                subject, doc, words = render(market, issue, sel, sub)
                ok, info = await send_email(
                    db, sub.email, subject, doc, "newsletter_issue", market, subscriber_id=sub.id,
                    headers={"List-Unsubscribe": f"<{FRONTEND_URL}/unsubscribe?t={sub.auth_token}>"},
                )
                if not ok:
                    logger.warning(f"[Issue] {sub.email}: {info}")
                    last_error = info
                    continue
                blocks = sel["stories"] + sel["updates"]
                db.add(IssueRender(
                    issue_id=issue.id, subscriber_id=sub.id, block_ids=[str(b.id) for b in blocks],
                    followed_story_count=sum(1 for b in sel["stories"] if b.vendor_id in sel["followed"]),
                    eligible_pool_size=sel["pool_size"], total_words=words, sent_at=utcnow(),
                ))
                for b in blocks:
                    db.add(SeenBlock(subscriber_id=sub.id, block_id=b.id))
                    b.times_used = (b.times_used or 0) + 1
                for s in sel["shares"]:
                    s.featured_count = (s.featured_count or 0) + 1
                sub.last_sent_at = utcnow()
                await db.commit()
                sent += 1
                await asyncio.sleep(SEND_DELAY_SECONDS)
            except Exception as e:  # noqa: BLE001
                await db.rollback()
                logger.error(f"[Issue] send to {sub.email} failed: {e}")
        issue = await db.get(Issue, issue_id)
        if sent == 0 and last_error:
            # Nothing went out: put the issue back so the editor can fix and retry.
            issue.status = IssueStatus.ASSEMBLING
            issue.last_error = last_error[:500]
        else:
            issue.status = IssueStatus.SENT
            issue.sent_count = sent
            issue.sent_at = utcnow()
            issue.last_error = None
        await db.commit()
        logger.info(f"[Issue] #{issue.issue_number} sent to {sent}")
