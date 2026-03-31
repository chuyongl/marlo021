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
    hashed_password = Column(String, nullable=True)  # nullable: email-only users don't need a password
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
    # Email preferences
    briefing_time = Column(String, default="08:00")   # local time for morning email
    timezone = Column(String, default="America/New_York")
    email_notifications = Column(Boolean, default=True)
    onboarding_step = Column(Integer, default=0)      # 0-5, tracks where they are in setup
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="businesses")
    integrations = relationship("PlatformIntegration", back_populates="business")
    campaigns = relationship("Campaign", back_populates="business")

class PlatformIntegration(Base):
    __tablename__ = "platform_integrations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    platform = Column(String, nullable=False)
    access_token = Column(Text)        # encrypted at rest
    refresh_token = Column(Text)       # encrypted at rest
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
    __tablename__ = "agent_actions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    action_type = Column(String)
    status = Column(String, default="pending")
    input_context = Column(JSON)
    agent_reasoning = Column(Text)
    action_parameters = Column(JSON)
    outcome = Column(JSON)
    requires_approval = Column(Boolean, default=False)
    # Email approval tokens — the key new field
    approval_token = Column(String, unique=True, index=True)  # one-click approve link token
    decline_token = Column(String, unique=True, index=True)   # one-click decline link token
    token_expires_at = Column(DateTime)                        # tokens expire after 48 hours
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime)
    executed_at = Column(DateTime)
    llm_cost_usd = Column(Numeric(8, 6))
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailLog(Base):
    __tablename__ = "email_logs"
    # Track every email sent to every user — for debugging deliverability
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    email_type = Column(String)       # morning_briefing | weekly_report | approval_needed | onboarding_1 etc.
    subject = Column(String)
    resend_message_id = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    replied = Column(Boolean, default=False)
    reply_content = Column(Text)

class UserPhoto(Base):
    __tablename__ = "user_photos"
    # Photos sent by users via email attachment
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    original_url = Column(String)     # raw image from email
    enhanced_url = Column(String)     # after fal.ai enhancement
    instagram_url = Column(String)    # 1080×1080
    story_url = Column(String)        # 1080×1920
    facebook_url = Column(String)     # 1200×628
    google_display_url = Column(String)  # 1200×628 landscape
    caption_instagram = Column(Text)
    caption_facebook = Column(Text)
    status = Column(String, default="pending")  # pending | approved | posted
    created_at = Column(DateTime, default=datetime.utcnow)