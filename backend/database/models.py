from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    stripe_customer_id = Column(String)
    subscription_tier = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    businesses = relationship("Business", back_populates="owner")

class Business(Base):
    __tablename__ = "businesses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    industry = Column(String)
    description = Column(Text)
    tone_of_voice = Column(Text)
    target_audience = Column(Text)
    brand_colors = Column(JSON)
    logo_url = Column(String)
    website_url = Column(String)
    monthly_ad_budget = Column(Numeric(10, 2))
    briefing_time = Column(String, default="08:00")
    timezone = Column(String, default="America/New_York")
    email_notifications = Column(Boolean, default=True)
    # Posting preferences
    posts_per_week = Column(Integer, default=3)
    preferred_post_time = Column(String, default="09:00")       # "HH:MM" 24h format
    preferred_post_timezone = Column(String, default="America/New_York")
    onboarding_step = Column(Integer, default=0)
    onboarding_completed = Column(Boolean, default=False)
    subscription_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="businesses")
    integrations = relationship("PlatformIntegration", back_populates="business")
    campaigns = relationship("Campaign", back_populates="business")

class PlatformIntegration(Base):
    __tablename__ = "platform_integrations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    platform = Column(String, nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    platform_account_id = Column(String)
    is_active = Column(Boolean, default=True)
    scopes = Column(JSON)
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    business = relationship("Business", back_populates="integrations")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    platform = Column(String)
    platform_campaign_id = Column(String)
    name = Column(String)
    status = Column(String, default="draft")
    campaign_type = Column(String)
    daily_budget = Column(Numeric(10, 2))
    total_spend = Column(Numeric(10, 2), default=0)
    ai_generated = Column(Boolean, default=True)
    last_optimized_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    metrics = relationship("CampaignMetric", back_populates="campaign")
    business = relationship("Business", back_populates="campaigns")

class CampaignMetric(Base):
    __tablename__ = "campaign_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    date = Column(DateTime, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0)
    revenue = Column(Numeric(10, 2), default=0)
    roas = Column(Numeric(6, 2))
    cpc = Column(Numeric(8, 2))
    raw_data = Column(JSON)
    campaign = relationship("Campaign", back_populates="metrics")

class AgentAction(Base):
    """
    Core pending action table.
    Also imported as PendingAction throughout the codebase — see alias below.
    """
    __tablename__ = "agent_actions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    action_type = Column(String)        # "post_instagram" | "google_ads_campaign" | etc.
    status = Column(String, default="pending")  # pending | executed | rejected | expired
    input_context = Column(JSON)
    agent_reasoning = Column(Text)
    action_parameters = Column(JSON)    # full post/campaign data
    outcome = Column(JSON)
    requires_approval = Column(Boolean, default=False)
    approval_token = Column(String, unique=True, index=True)
    decline_token = Column(String, unique=True, index=True)
    token_expires_at = Column(DateTime)
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime)
    # Scheduling
    scheduled_post_time = Column(DateTime(timezone=True), nullable=True)  # when to go live
    executed_at = Column(DateTime(timezone=True), nullable=True)           # when actually posted
    # Delivery tracking — which approval email has been sent for this action
    approval_email_sent = Column(Boolean, default=False)
    scheduled_day = Column(String, nullable=True)   # "Monday" | "Wednesday" | "Friday"
    llm_cost_usd = Column(Numeric(8, 6))
    created_at = Column(DateTime, default=datetime.utcnow)

# Alias — used interchangeably throughout codebase
PendingAction = AgentAction

class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    email_type = Column(String)
    subject = Column(String)
    resend_message_id = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    replied = Column(Boolean, default=False)
    reply_content = Column(Text)

class UserPhoto(Base):
    __tablename__ = "user_photos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    original_url = Column(String)
    enhanced_url = Column(String)
    instagram_url = Column(String)
    story_url = Column(String)
    facebook_url = Column(String)
    google_display_url = Column(String)
    caption_instagram = Column(Text)
    caption_facebook = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class ContentFeedback(Base):
    """Records every user approve/decline decision for learning."""
    __tablename__ = "content_feedback"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), index=True)
    action_id = Column(UUID(as_uuid=True), ForeignKey("agent_actions.id"), nullable=True)
    decision = Column(String, nullable=False)    # "approved" | "declined"
    reason = Column(String, nullable=True)        # optional decline reason
    content_type = Column(String, nullable=True)  # "post" | "campaign" | "email"
    platform = Column(String, nullable=True)      # "instagram" | "facebook" etc
    qa_score = Column(Integer, nullable=True)     # QA score at time of generation
    created_at = Column(DateTime, default=datetime.utcnow)