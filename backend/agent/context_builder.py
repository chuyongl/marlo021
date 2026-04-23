"""
context_builder.py
Assembles a complete business context dict for the AI brain.
Pulls from: business profile, platform integrations, recent agent actions,
campaign metrics, and email logs.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database.models import (
    Business, PlatformIntegration, AgentAction,
    CampaignMetrics, Campaign, EmailLog
)
from datetime import datetime, timedelta
import os

class ContextBuilder:

    async def build_full_context(self, business_id: str, db: AsyncSession) -> dict:
        """
        Build the full context dict passed to brain.think().
        Gracefully handles missing data at every step.
        """
        context = {}

        # 1. Business profile
        try:
            biz_result = await db.execute(
                select(Business).where(Business.id == business_id)
            )
            biz = biz_result.scalar_one_or_none()
            if biz:
                context["business"] = {
                    "name": biz.name,
                    "industry": biz.industry or "",
                    "description": biz.description or "",
                    "tone_of_voice": biz.tone_of_voice or "",
                    "target_audience": biz.target_audience or "",
                    "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
                    "onboarding_step": biz.onboarding_step,
                    "website_url": biz.website_url or "",
                }
        except Exception as e:
            print(f"[ContextBuilder] Error loading business: {e}")

        # 2. Connected platforms
        try:
            integrations_result = await db.execute(
                select(PlatformIntegration)
                .where(PlatformIntegration.business_id == business_id)
                .where(PlatformIntegration.is_active == True)
            )
            integrations = integrations_result.scalars().all()
            context["connected_platforms"] = [i.platform for i in integrations]
        except Exception as e:
            print(f"[ContextBuilder] Error loading integrations: {e}")
            context["connected_platforms"] = []

        # 3. Recent campaign metrics (last 7 days)
        try:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            metrics_result = await db.execute(
                select(CampaignMetrics)
                .join(Campaign, CampaignMetrics.campaign_id == Campaign.id)
                .where(Campaign.business_id == business_id)
                .where(CampaignMetrics.date >= seven_days_ago)
                .order_by(desc(CampaignMetrics.date))
                .limit(20)
            )
            metrics = metrics_result.scalars().all()
            if metrics:
                total_spend = sum(float(m.spend or 0) for m in metrics)
                total_clicks = sum(int(m.clicks or 0) for m in metrics)
                total_impressions = sum(int(m.impressions or 0) for m in metrics)
                context["recent_metrics"] = {
                    "period": "last 7 days",
                    "total_spend": round(total_spend, 2),
                    "total_clicks": total_clicks,
                    "total_impressions": total_impressions,
                    "avg_ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
                    "avg_cpc": round(total_spend / total_clicks, 2) if total_clicks > 0 else 0,
                }
        except Exception as e:
            print(f"[ContextBuilder] Error loading metrics: {e}")

        # 4. Recent agent actions (last 10)
        try:
            actions_result = await db.execute(
                select(AgentAction)
                .where(AgentAction.business_id == business_id)
                .order_by(desc(AgentAction.executed_at))
                .limit(10)
            )
            actions = actions_result.scalars().all()
            context["recent_actions"] = [
                {
                    "type": a.action_type,
                    "status": a.status,
                    "reasoning": (a.agent_reasoning or "")[:200],
                    "date": a.executed_at.isoformat() if a.executed_at else "",
                }
                for a in actions
            ]
        except Exception as e:
            print(f"[ContextBuilder] Error loading actions: {e}")
            context["recent_actions"] = []

        # 5. Recent email logs (last 5)
        try:
            emails_result = await db.execute(
                select(EmailLog)
                .where(EmailLog.business_id == business_id)
                .order_by(desc(EmailLog.sent_at))
                .limit(5)
            )
            emails = emails_result.scalars().all()
            context["recent_emails"] = [
                {
                    "type": e.email_type,
                    "subject": e.subject,
                    "sent_at": e.sent_at.isoformat() if e.sent_at else "",
                }
                for e in emails
            ]
        except Exception as e:
            print(f"[ContextBuilder] Error loading email logs: {e}")
            context["recent_emails"] = []

        # 6. Today's date for temporal awareness
        context["current_date"] = datetime.utcnow().strftime("%Y-%m-%d")
        context["base_url"] = os.getenv("APP_BASE_URL", "http://localhost:8000")

        return context


context_builder = ContextBuilder()