import resend
import os
from dotenv import load_dotenv
from database.models import EmailLog, Business
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

load_dotenv(dotenv_path="../../.env")
resend.api_key = os.getenv("RESEND_API_KEY", "")

FROM_EMAIL = os.getenv("FROM_EMAIL", "hello@marlo.ai")
FROM_NAME = os.getenv("FROM_NAME", "Marlo")

class EmailSender:
    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        email_type: str,
        business_id: str = None,
        db: AsyncSession = None,
        reply_to: str = None
    ) -> dict:
        """Send an email via Resend and log it."""
        try:
            params = {
                "from": f"{FROM_NAME} <{FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            }
            if reply_to:
                params["reply_to"] = reply_to

            result = resend.Emails.send(params)
            message_id = result.get("id", "")

            if db and business_id:
                log = EmailLog(
                    id=uuid.uuid4(),
                    business_id=business_id,
                    email_type=email_type,
                    subject=subject,
                    resend_message_id=message_id,
                    sent_at=datetime.utcnow()
                )
                db.add(log)
                await db.commit()

            return {"success": True, "message_id": message_id}

        except Exception as e:
            print(f"Email send error: {e}")
            return {"success": False, "error": str(e)}

    async def send_morning_briefing(
        self,
        business: Business,
        user_email: str,
        user_first_name: str,
        yesterday_metrics: dict,
        pending_actions: list,
        db: AsyncSession
    ):
        from email_system.templates import morning_briefing_template
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        actions_for_email = []
        for action in pending_actions:
            actions_for_email.append({
                "title": action.get("title", action.get("action_type", "Action")),
                "description": action.get("description", action.get("agent_reasoning", "")[:200]),
                "approve_token": action.get("approval_token"),
                "decline_token": action.get("decline_token"),
                "risk_level": action.get("risk_level", "medium")
            })

        html = morning_briefing_template(
            business_name=business.name,
            first_name=user_first_name,
            yesterday_metrics=yesterday_metrics,
            actions=actions_for_email,
            base_url=base_url
        )

        await self.send(
            to_email=user_email,
            subject=f"☀️ Good morning {user_first_name} — your Marlo briefing",
            html_body=html,
            email_type="morning_briefing",
            business_id=str(business.id),
            db=db,
            reply_to=f"reply+{business.id}@reply.marlo021.ai"
        )

    async def send_onboarding_step(
        self,
        step: int,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        db: AsyncSession,
        extra_data: dict = None
    ):
        from email_system import templates
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        extra = extra_data or {}

        if step == 1:
            html = templates.onboarding_email_1(business_name, first_name, business_id, base_url)
            subject = f"👋 Welcome {first_name}! Let's set up Marlo (Step 1 of 4)"
        elif step == 2:
            html = templates.onboarding_email_2(first_name, business_id, base_url, frontend_url)
            subject = "✅ Google connected! Now let's do Instagram (Step 2 of 4)"
        elif step == 3:
            html = templates.onboarding_email_3(first_name, business_id, base_url)
            subject = "✅ Instagram connected! One more step (Step 3 of 4)"
        elif step == 4:
            html = templates.onboarding_email_4(first_name, business_id, base_url)
            subject = "Almost done! Tell me about your business (Step 4 of 4)"
        elif step == 5:
            html = templates.onboarding_email_5_ready(
                first_name,
                extra.get("campaigns", []),
                extra.get("posts", []),
                f"{base_url}/onboarding/approve-all?business_id={business_id}",
                base_url
            )
            subject = f"🚀 {first_name}, your first marketing plan is ready!"
        else:
            return

        await self.send(
            to_email=user_email,
            subject=subject,
            html_body=html,
            email_type=f"onboarding_{step}",
            business_id=business_id,
            db=db,
            reply_to=f"reply+{business_id}@reply.marlo021.ai"
        )

email_sender = EmailSender()