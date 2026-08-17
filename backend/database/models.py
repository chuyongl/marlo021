"""
database/models.py

Brown Bag — all database models.

Brown Bag is the publication. Marlo is the backend system running it.
No user-visible string in this system should contain "Marlo".

Structure:
    markets, invitation_codes, category_pairs   — configuration
    vendors, vendor_sessions, editors           — accounts
    conversations, messages, submissions        — content intake (素材)
    blocks, block_corrections, sponsors         — publishable content
    subscribers, scan_events, vendor_follows,
      seen_blocks                               — readers
    issues, issue_renders                       — delivery

Two ideas carry the model:
  1. Everything publishable is a `Block`. One table, one approval
     lifecycle. Classes differ in how they're SELECTED, not approved.
  2. "The bank" is a query, not a table:
         status == APPROVED
         AND (expires_at IS NULL OR expires_at > now)
         AND no open corrections

Conventions:
  - All datetimes are timezone-aware UTC. Never datetime.utcnow().
  - All PKs are UUID.
  - Arrays and dicts use JSONB (Postgres).
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow() -> datetime:
    """Timezone-aware UTC now. Use this everywhere — never datetime.utcnow()."""
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ─────────────────────────────────────────────────────────────────────────────
# STATUS CONSTANTS
# Kept as plain strings rather than SQL enums so adding a value doesn't
# require a migration.
# ─────────────────────────────────────────────────────────────────────────────

class VendorStatus:
    ACTIVE = "active"
    PAUSED = "paused"
    REMOVED = "removed"


class ConversationStatus:
    OPEN = "open"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"      # ended with no 素材 — a valid outcome, not a failure


class SubmissionStatus:
    NEW = "new"
    DRAFTED = "drafted"
    DISCARDED = "discarded"


class BlockStatus:
    DRAFT = "draft"
    VENDOR_PREVIEW = "vendor_preview"   # vendor sees it BEFORE the editor
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"               # in the bank
    REJECTED = "rejected"
    EXPIRED = "expired"


class BlockClass:
    STORY = "story"        # scored per reader
    AD = "ad"              # fixed slot, same for everyone
    GREETING = "greeting"  # same for everyone (MVP)
    EVENTS = "events"      # filtered to the reader's follows
    STATIC = "static"      # referral, social, footer


class SubscriberStatus:
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"


class CorrectionStatus:
    OPEN = "open"          # blocks the block from shipping
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class IssueStatus:
    ASSEMBLING = "assembling"
    SENDING = "sending"
    SENT = "sent"


# Slot budgets — the issue skeleton is fixed
SLOT_WORD_BUDGET = {2: 200, 3: 200, 5: 120}
ISSUE_WORD_CEILING = 1000
MIN_QUALITY_SCORE = 15     # below this a block never ships
MAX_QUALITY_SCORE = 40


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

class Market(Base):
    """
    A geographic area with its own newsletter. One market = one publication.
    MVP has exactly one: Seattle.
    """
    __tablename__ = "markets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)                    # "Seattle"
    slug = Column(String, nullable=False, unique=True)       # "seattle"

    # The public brand. In the DB on purpose: the name is provisional, so
    # changing it should be a config edit rather than a code change.
    publication_name = Column(String, nullable=False, default="Brown Bag")
    from_email = Column(String, nullable=False)
    from_name = Column(String, nullable=False)

    timezone = Column(String, nullable=False, default="America/Los_Angeles")
    send_day = Column(String, nullable=False, default="Thursday")
    send_hour = Column(Integer, nullable=False, default=17)   # local hour

    # Dropdown list AND proximity adjacency, in one place:
    #   {"Ballard": {"adjacent": ["Fremont","Magnolia"], "city": "Seattle"}}
    # Hand-maintained. Local knowledge beats any dataset here.
    neighborhoods = Column(JSONB, nullable=False, default=dict)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    vendors = relationship("Vendor", back_populates="market")

    def adjacent_to(self, neighborhood: str) -> list:
        return (self.neighborhoods or {}).get(neighborhood, {}).get("adjacent", [])

    def city_of(self, neighborhood: str) -> str | None:
        return (self.neighborhoods or {}).get(neighborhood, {}).get("city")


class InvitationCode(Base):
    """
    The gate on vendor signup. We generate codes and hand them out; vendors
    self-serve from there with no editor step.

    Codes carry market + neighborhood, NOT category — one code can cover a
    whole market, and we can't presume what each stall sells.

    Two shapes in practice:
      bulk:   max_uses=100, given to a market manager
      single: max_uses=1, for one vendor we're recruiting
    """
    __tablename__ = "invitation_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)

    code = Column(String, nullable=False, unique=True, index=True)  # "BALLARD26"
    neighborhood = Column(String, nullable=True)   # prefills the signup form
    label = Column(String, nullable=True)          # internal note

    max_uses = Column(Integer, nullable=True)      # NULL = unlimited
    use_count = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("editors.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    def is_usable(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at <= utcnow():
            return False
        if self.max_uses is not None and self.use_count >= self.max_uses:
            return False
        return True


class CategoryPair(Base):
    """
    Makes complementary_categories automatic.

    Bread pairs with cheese because of what bread IS, not because of who is
    selling it. Maintained once; every vendor picking `bakery` inherits the
    pairings. Zero editor work per signup — this is what makes vendor
    signup scale.
    """
    __tablename__ = "category_pairs"

    category = Column(String, primary_key=True)       # "bakery"
    complements = Column(JSONB, nullable=False, default=list)  # ["cheese","jam"]
    display_name = Column(String, nullable=True)      # for the signup dropdown
    is_active = Column(Boolean, nullable=False, default=True)


# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNTS
# ─────────────────────────────────────────────────────────────────────────────

class Editor(Base):
    """
    Hand-provisioned, real login. The only role with a password — editors can
    approve content, so the extra friction is warranted.
    """
    __tablename__ = "editors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    market_ids = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class Vendor(Base):
    """
    A local business. Self-signs up with an invitation code and is live
    immediately — no editor activation step.
    """
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    invitation_code_id = Column(
        UUID(as_uuid=True), ForeignKey("invitation_codes.id"), nullable=True
    )

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)  # identity
    status = Column(String, nullable=False, default=VendorStatus.ACTIVE)

    # Generated at signup. This is what goes on the QR code at their stall.
    scan_code = Column(String, nullable=False, unique=True, index=True)

    # Primary proximity unit. City-level is too coarse — Ballard and Rainier
    # Beach are both "Seattle" and forty minutes apart.
    neighborhood = Column(String, nullable=True)
    city = Column(String, nullable=True)   # derived from the neighborhood map

    # Fixed list, never free text. Free text produces "baked goods", "bakery",
    # "Baked Goods" and "bread + pastry" as four categories, and interest
    # matching quietly stops working.
    categories = Column(JSONB, nullable=False, default=list)
    complementary_categories = Column(JSONB, nullable=False, default=list)

    vendor_type = Column(String, nullable=True)   # maps to vendor_profiles.py
    description = Column(Text, nullable=True)
    booth_location = Column(String, nullable=True)
    schedule_note = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)     # optional at signup

    # ~200 tokens of summary, not a growing transcript (ADR-010).
    # This is what lets the interviewer ask a SPECIFIC follow-up —
    # "are these from the old orchard you mentioned?" rather than
    # "can you tell me more?" — which is the whole difference between
    # a conversation and homework.
    vendor_memory = Column(JSONB, nullable=True)

    reply_pattern = Column(JSONB, nullable=True)   # learned response cadence
    last_submitted_at = Column(DateTime(timezone=True), nullable=True)
    silent_cycles = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    market = relationship("Market", back_populates="vendors")
    blocks = relationship("Block", back_populates="vendor")

    __table_args__ = (
        Index("ix_vendors_market_status", "market_id", "status"),
        Index("ix_vendors_silent", "silent_cycles"),
    )


class VendorSession(Base):
    """
    Magic link once, then a long session.

    One click on first visit, then the site just opens. Vendors visit weekly
    at most; password resets would be the single biggest support burden for
    users at that frequency.
    """
    __tablename__ = "vendor_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)

    session_token = Column(String, nullable=False, unique=True, index=True)
    magic_token = Column(String, nullable=True, unique=True, index=True)
    magic_expires_at = Column(DateTime(timezone=True), nullable=True)
    magic_used_at = Column(DateTime(timezone=True), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)  # ~90 days
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# CONTENT INTAKE — the interviewer agent's territory
# ─────────────────────────────────────────────────────────────────────────────

class Conversation(Base):
    """
    One cycle's chat between a vendor and the interviewer agent.

    NO TURN LIMIT. An editor working with a writer doesn't get one exchange.
    What makes people quit is vagueness ("tell me more"), not length.

    Conversations PERSIST across sessions — vendors answer between customers.
    Three questions now, more after closing, finish tomorrow.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    cycle_start = Column(Date, nullable=False)

    status = Column(String, nullable=False, default=ConversationStatus.OPEN)

    # Chosen BEFORE the reminder is sent, so the question can go in the
    # subject line. The vendor knows the answer before they click.
    opening_question = Column(Text, nullable=True)
    question_type = Column(String, nullable=True)

    # What's still missing: ["person", "stake", "scene", "detail"]
    # The interviewer asks toward the gap rather than asking generically.
    gaps_remaining = Column(JSONB, nullable=False, default=list)

    turns = Column(Integer, nullable=False, default=0)          # analytics only
    stalled_turns = Column(Integer, nullable=False, default=0)  # 2 → stop

    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_reason = Column(String, nullable=True)  # silent|sensitive|thin

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=utcnow, onupdate=utcnow)

    messages = relationship("Message", back_populates="conversation",
                            order_by="Message.created_at")

    __table_args__ = (
        Index("ix_conversations_vendor_cycle", "vendor_id", "cycle_start"),
    )


class Message(Base):
    """One turn in a conversation."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"),
                             nullable=False)
    role = Column(String, nullable=False)          # "agent" | "vendor"
    content = Column(Text, nullable=False)
    image_urls = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Submission(Base):
    """
    素材 — raw material, not copy.

    raw_text is NEVER modified. It's the audit trail from published text back
    to what the vendor actually said, which is what makes "never invent a
    fact" enforceable.

    Note: a conversation can legitimately end with NO submission. A vendor
    with nothing to say this week is a normal outcome, not a failure — the
    bank carries the gap. The system must be comfortable producing nothing
    rather than producing filler.
    """
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"),
                             nullable=True)

    raw_text = Column(Text, nullable=False)        # verbatim, never edited
    image_urls = Column(JSONB, nullable=False, default=list)

    # True  = time-sensitive ("peaches this week"), short shelf life
    # False = evergreen ("why I left nursing to make cheese"), bank it
    perishable = Column(Boolean, nullable=False, default=True)

    # What the interviewer found: person, stake, scene, quotes
    material_notes = Column(JSONB, nullable=True)

    # Difficult material — illness, loss, crisis. BLOCKS auto-drafting and
    # routes to a human first. Publishing something that could hurt the
    # person telling it is worse than a thin issue.
    sensitive = Column(Boolean, nullable=False, default=False)

    status = Column(String, nullable=False, default=SubmissionStatus.NEW)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("ix_submissions_vendor_status", "vendor_id", "status"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PUBLISHABLE CONTENT
# ─────────────────────────────────────────────────────────────────────────────

class Sponsor(Base):
    """An advertiser. Ads are the same for every reader."""
    __tablename__ = "sponsors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
    link_url = Column(String, nullable=True)
    active_from = Column(Date, nullable=True)
    active_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class Block(Base):
    """
    Everything publishable. One table, one approval lifecycle.

    Classes differ in how they're SELECTED, not how they're approved:
        story    → scored per reader
        ad       → fixed slot, same for everyone
        greeting → same for everyone (MVP)
        events   → filtered to the reader's follows
        static   → always included (referral, social, footer)

    Lifecycle:
        draft → vendor_preview → pending_review → approved → expired
                             ↘ rejected

    vendor_preview comes BEFORE editor review on purpose. The vendor is the
    only one who knows whether a fact is wrong, and catching it before the
    editor spends time is cheaper for everyone.
    """
    __tablename__ = "blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    block_class = Column(String, nullable=False, default=BlockClass.STORY)

    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"),
                           nullable=True)
    sponsor_id = Column(UUID(as_uuid=True), ForeignKey("sponsors.id"), nullable=True)

    status = Column(String, nullable=False, default=BlockStatus.DRAFT)

    headline = Column(String, nullable=True)       # <= 50 chars
    body = Column(Text, nullable=True)
    quote = Column(Text, nullable=True)            # the vendor's exact words
    image_urls = Column(JSONB, nullable=False, default=list)
    image_caption = Column(String, nullable=True)
    word_count = Column(Integer, nullable=False, default=0)

    categories = Column(JSONB, nullable=False, default=list)

    # 0-40, set by the editor at approval. Reader-independent.
    # Below MIN_QUALITY_SCORE a block never ships, regardless of follows —
    # a boring story from a followed vendor is worse than a good story from
    # a stranger, because the reader concludes the newsletter is dull.
    quality_score = Column(Integer, nullable=False, default=0)

    perishable = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    vendor_viewed_at = Column(DateTime(timezone=True), nullable=True)
    editor_id = Column(UUID(as_uuid=True), ForeignKey("editors.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reject_reason = Column(Text, nullable=True)

    times_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    vendor = relationship("Vendor", back_populates="blocks")
    corrections = relationship("BlockCorrection", back_populates="block")

    __table_args__ = (
        Index("ix_blocks_bank", "market_id", "status", "block_class"),
        Index("ix_blocks_expiry", "expires_at"),
    )

    def is_in_bank(self, now: datetime | None = None) -> bool:
        """
        "The bank" is this predicate, not a separate table.
        Note: open-correction checking requires a DB query and is handled
        in the personalizer, not here.
        """
        now = now or utcnow()
        if self.status != BlockStatus.APPROVED:
            return False
        if self.expires_at and self.expires_at <= now:
            return False
        if self.quality_score < MIN_QUALITY_SCORE:
            return False
        return True


class BlockCorrection(Base):
    """
    A vendor flagging a wrong fact. Vendors don't edit directly — that would
    break the audit trail back to raw_text and make the editor gate
    meaningless. But their corrections are binding.

    An OPEN correction pulls an approved block out of the bank until
    resolved. Shipping a known-wrong fact about someone's own business is
    the one case that overrides "the issue ships every week".
    """
    __tablename__ = "block_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    block_id = Column(UUID(as_uuid=True), ForeignKey("blocks.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)

    note = Column(Text, nullable=False)   # "north field, not the old orchard"
    status = Column(String, nullable=False, default=CorrectionStatus.OPEN)

    resolved_by = Column(UUID(as_uuid=True), ForeignKey("editors.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    block = relationship("Block", back_populates="corrections")

    __table_args__ = (
        Index("ix_corrections_open", "status", "block_id"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# READERS
# ─────────────────────────────────────────────────────────────────────────────

class Subscriber(Base):
    """
    A reader. Signs up by scanning a QR at a vendor stall. No password —
    the email address is the identity, held in a signed cookie.
    """
    __tablename__ = "subscribers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)

    email = Column(String, nullable=False, index=True)
    auth_token = Column(String, nullable=False, unique=True, index=True)
    status = Column(String, nullable=False, default=SubscriberStatus.ACTIVE)

    # Legally required. Never pre-check the consent box in the UI.
    consent_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    consent_source = Column(String, nullable=False)      # "qr_scan:A7K2"

    first_vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"),
                             nullable=True)

    # Derived from scan behavior, never a form field:
    #   {"bakery": 0.9, "produce": 0.6, "updated_at": "2026-08-12"}
    interest_vector = Column(JSONB, nullable=True)

    # Most common neighborhood among followed vendors. Someone who scanned
    # three Ballard stalls is a Ballard reader. Never asked; sharpens with
    # every scan.
    inferred_neighborhood = Column(String, nullable=True)
    inferred_city = Column(String, nullable=True)

    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_opened_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("market_id", "email", name="uq_subscriber_market_email"),
        Index("ix_subscribers_active", "market_id", "status"),
    )


class ScanEvent(Base):
    """
    Every QR scan. The most important raw signal in the system — interests
    and location both derive from it, with no form to fill in.
    """
    __tablename__ = "scan_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey("subscribers.id"),
                           nullable=True)   # NULL on a first-ever scan
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)

    scanned_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    is_signup = Column(Boolean, nullable=False, default=False)
    session_token = Column(String, nullable=True)   # pre-signup identifier
    user_agent = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_scans_vendor", "vendor_id", "scanned_at"),
        Index("ix_scans_subscriber", "subscriber_id", "scanned_at"),
    )


class VendorFollow(Base):
    """
    Created automatically by scanning — the reader never presses "follow".
    Interests are walked, not declared.
    """
    __tablename__ = "vendor_follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey("subscribers.id"),
                           nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)

    scan_count = Column(Integer, nullable=False, default=1)      # strength
    first_scanned_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_scanned_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    is_muted = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("subscriber_id", "vendor_id", name="uq_follow"),
        Index("ix_follows_subscriber", "subscriber_id"),
    )


class SeenBlock(Base):
    """
    Permanent exclusion. A story shown to a reader is NEVER eligible for that
    reader again.

    This is a different rule from vendor fatigue:
        seen    → story x reader → hard exclusion, forever
        fatigue → vendor x reader → score penalty, decays

    A table rather than a scan of issue_renders.block_ids because this is
    checked for every block against every subscriber on every send. It needs
    an indexed lookup, not an array scan across issue history.

    Supply consequence: each reader burns 3 stories permanently per issue,
    so a bank of 20 gives an individual reader ~7 weeks before they've seen
    everything. 3-5 new stories per issue is a floor, not an aspiration.
    """
    __tablename__ = "seen_blocks"

    subscriber_id = Column(UUID(as_uuid=True), ForeignKey("subscribers.id"),
                           primary_key=True)
    block_id = Column(UUID(as_uuid=True), ForeignKey("blocks.id"), primary_key=True)
    seen_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("ix_seen_subscriber", "subscriber_id"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# DELIVERY
# ─────────────────────────────────────────────────────────────────────────────

class Issue(Base):
    """
    One week's content POOL — not an email.

    An issue may hold 20 blocks while each reader sees 3. The actual emails
    are IssueRenders.
    """
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)

    issue_number = Column(Integer, nullable=False)
    send_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default=IssueStatus.ASSEMBLING)

    bank_size_at_assembly = Column(Integer, nullable=False, default=0)
    sent_count = Column(Integer, nullable=False, default=0)

    assembled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    renders = relationship("IssueRender", back_populates="issue")

    __table_args__ = (
        UniqueConstraint("market_id", "issue_number", name="uq_issue_number"),
    )


class IssueRender(Base):
    """
    What one subscriber actually received.

    Without this there is no answering "why did this person unsubscribe?"
    block_ids + unsubscribed_from_this is the only data that can diagnose
    content quality.
    """
    __tablename__ = "issue_renders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey("subscribers.id"),
                           nullable=False)

    block_ids = Column(JSONB, nullable=False, default=list)   # in slot order
    block_scores = Column(JSONB, nullable=True)               # debugging

    # How many stories came from vendors this reader actually follows.
    # If most readers sit at 0, the follow model isn't earning its complexity.
    followed_story_count = Column(Integer, nullable=False, default=0)

    # How many unseen stories they had to choose from. Dropping toward 3 for
    # long-tenured readers is the early warning that the bank is stagnating
    # for exactly the people you'd notice losing last.
    eligible_pool_size = Column(Integer, nullable=False, default=0)

    total_words = Column(Integer, nullable=False, default=0)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_vendor_ids = Column(JSONB, nullable=False, default=list)

    unsubscribed_from_this = Column(Boolean, nullable=False, default=False)

    issue = relationship("Issue", back_populates="renders")

    __table_args__ = (
        UniqueConstraint("issue_id", "subscriber_id", name="uq_render"),
        Index("ix_renders_subscriber", "subscriber_id"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL LOG
# ─────────────────────────────────────────────────────────────────────────────

class EmailLog(Base):
    """
    Every email sent, to vendors or readers. Used for deduplication and
    debugging delivery.
    """
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey("subscribers.id"),
                           nullable=True)

    email_type = Column(String, nullable=False)
    # vendor_welcome | vendor_reminder | vendor_draft_ready
    # subscriber_welcome | newsletter_issue

    to_email = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    provider_id = Column(String, nullable=True)     # Resend message id
    email_metadata = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_email_logs_type", "email_type", "sent_at"),
    )