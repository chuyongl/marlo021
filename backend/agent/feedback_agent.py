"""
feedback_agent.py
Records user approve/decline decisions and surfaces patterns to improve future content.
This is the learning layer — as data accumulates, strategy_agent gets smarter.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import AgentAction, ContentFeedback
from datetime import datetime, timedelta
import uuid

class FeedbackAgent:

    async def record_approve(
        self,
        action_id: str,
        business_id: str,
        db: AsyncSession
    ):
        """Record that a user approved a piece of content."""
        feedback = ContentFeedback(
            id=uuid.uuid4(),
            business_id=business_id,
            action_id=action_id,
            decision="approved",
            created_at=datetime.utcnow()
        )
        db.add(feedback)
        await db.commit()

    async def record_decline(
        self,
        action_id: str,
        business_id: str,
        reason: str = None,
        db: AsyncSession = None
    ):
        """Record that a user declined a piece of content."""
        feedback = ContentFeedback(
            id=uuid.uuid4(),
            business_id=business_id,
            action_id=action_id,
            decision="declined",
            reason=reason,
            created_at=datetime.utcnow()
        )
        db.add(feedback)
        await db.commit()

    async def get_feedback_summary(
        self,
        business_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> dict:
        """
        Summarize feedback patterns for strategy_agent to use.
        Returns approve rate, common decline reasons, best performing content types.
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)

            result = await db.execute(
                select(ContentFeedback)
                .where(ContentFeedback.business_id == business_id)
                .where(ContentFeedback.created_at >= since)
            )
            feedbacks = result.scalars().all()

            if not feedbacks:
                return {}

            total = len(feedbacks)
            approved = len([f for f in feedbacks if f.decision == "approved"])
            declined = len([f for f in feedbacks if f.decision == "declined"])

            # Most common decline reasons
            reasons = [f.reason for f in feedbacks if f.decision == "declined" and f.reason]
            top_reason = max(set(reasons), key=reasons.count) if reasons else None

            return {
                "total_decisions": total,
                "approved": approved,
                "declined": declined,
                "approve_rate": round(approved / total * 100) if total > 0 else None,
                "top_declined_reason": top_reason,
                "period_days": days
            }

        except Exception as e:
            print(f"[FeedbackAgent] Error getting summary: {e}")
            return {}

    async def ask_decline_reason(
        self,
        business_id: str,
        action_id: str,
        action_type: str,
        base_url: str
    ) -> str:
        """
        Returns HTML for a quick decline reason form.
        Embedded in the declined page — optional, one tap.
        """
        reasons = [
            ("wrong_tone", "Wrong tone"),
            ("not_relevant", "Not relevant right now"),
            ("poor_quality", "Quality not good enough"),
            ("wrong_timing", "Wrong timing"),
            ("other", "Other"),
        ]
        buttons = " ".join([
            f'<a href="{base_url}/actions/feedback?action_id={action_id}&reason={code}" '
            f'style="display:inline-block;background:#F3F4F6;color:#374151;padding:8px 16px;'
            f'border-radius:20px;text-decoration:none;font-size:13px;margin:4px;">{label}</a>'
            for code, label in reasons
        ])
        return f"""
        <div style="margin-top:24px;padding-top:24px;border-top:1px solid #E5E7EB;">
          <p style="color:#9CA3AF;font-size:13px;margin:0 0 12px 0;">
            Optional: Help Marlo learn — why did you skip this?
          </p>
          {buttons}
        </div>"""


feedback_agent = FeedbackAgent()