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
FROM_NAME  = os.getenv("FROM_NAME", "Marlo")


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

    def _reply_to(self, business_id: str) -> str:
        return f"reply+{business_id}@reply.marlo021.ai"

    # ── Onboarding steps ──────────────────────────────────────────────────────

    async def send_onboarding_step(
        self,
        step: int,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        db: AsyncSession,
        extra_data: dict = None,
        skipped_platform: str = None,
    ):
        from email_system import templates
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        extra = extra_data or {}

        if step == 1:
            html = templates.onboarding_email_1(business_name, first_name, business_id, base_url)
            subject = f"👋 Welcome {first_name}! Let's set up Marlo (Step 1 of 4)"
            email_type = "onboarding_1"

        elif step == 2:
            html = templates.onboarding_email_2(
                first_name, business_id, base_url, frontend_url,
                skipped_google=(skipped_platform == "google")
            )
            subject = (
                "Skipped Google — let's connect Instagram next (Step 2 of 4)"
                if skipped_platform == "google"
                else "✅ Google connected! Now let's do Instagram (Step 2 of 4)"
            )
            email_type = "onboarding_2"

        elif step == 3:
            html = templates.onboarding_email_3(
                first_name, business_id, base_url,
                skipped_meta=(skipped_platform == "meta")
            )
            subject = (
                "Skipped Instagram — one more optional step (Step 3 of 4)"
                if skipped_platform == "meta"
                else "✅ Instagram connected! One more step (Step 3 of 4)"
            )
            email_type = "onboarding_3"

        elif step == 4:
            is_reminder = extra.get("is_reminder", False)
            html = templates.onboarding_email_4(first_name, business_id, base_url, is_reminder=is_reminder)
            subject = (
                f"⏰ {first_name}, Marlo is waiting — reply to unlock your content"
                if is_reminder
                else "Almost done! Tell me about your business (Step 4 of 4)"
            )
            email_type = "onboarding_4_reminder" if is_reminder else "onboarding_4"

        elif step == 5:
            # Simplified confirmation only — kickoff email is sent separately
            html = templates.onboarding_complete_template(first_name, business_name)
            subject = f"✅ Setup complete, {first_name}! Your kickoff email is on its way."
            email_type = "onboarding_5"

        else:
            return

        await self.send(
            to_email=user_email,
            subject=subject,
            html_body=html,
            email_type=email_type,
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )

    # ── First kickoff (sent immediately after onboarding) ────────────────────

    async def send_first_kickoff(
        self,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        first_post: dict,
        first_post_day: str,
        first_approve_token: str,
        first_decline_token: str,
        google_campaign: dict,
        ads_approve_token: str,
        ads_decline_token: str,
        posting_schedule: list,
        strategy_summary: str,
        image_guide: list,
        db: AsyncSession,
    ):
        from email_system.templates import first_kickoff_template
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        html = first_kickoff_template(
            first_name=first_name,
            business_name=business_name,
            business_id=business_id,
            first_post=first_post,
            first_post_day=first_post_day,
            first_approve_token=first_approve_token,
            first_decline_token=first_decline_token,
            google_campaign=google_campaign,
            ads_approve_token=ads_approve_token,
            ads_decline_token=ads_decline_token,
            posting_schedule=posting_schedule,
            strategy_summary=strategy_summary,
            image_guide=image_guide,
            base_url=base_url,
        )

        await self.send(
            to_email=user_email,
            subject=f"🚀 Welcome to Marlo, {first_name} — your first content plan is ready",
            html_body=html,
            email_type="first_kickoff",
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )

    # ── Weekly kickoff (recurring) ────────────────────────────────────────────

    async def send_weekly_kickoff(
        self,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        first_post: dict,
        first_post_day: str,
        first_approve_token: str,
        first_decline_token: str,
        google_campaign: dict,
        ads_approve_token: str,
        ads_decline_token: str,
        posting_schedule: list,
        strategy_summary: str,
        image_guide: list,
        last_week_stats: dict,
        db: AsyncSession,
    ):
        from email_system.templates import weekly_kickoff_template
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        html = weekly_kickoff_template(
            first_name=first_name,
            business_name=business_name,
            business_id=business_id,
            first_post=first_post,
            first_post_day=first_post_day,
            first_approve_token=first_approve_token,
            first_decline_token=first_decline_token,
            google_campaign=google_campaign,
            ads_approve_token=ads_approve_token,
            ads_decline_token=ads_decline_token,
            posting_schedule=posting_schedule,
            strategy_summary=strategy_summary,
            image_guide=image_guide,
            last_week_stats=last_week_stats,
            base_url=base_url,
        )

        await self.send(
            to_email=user_email,
            subject=f"📅 Your week ahead, {first_name} — {first_post_day}'s post is ready",
            html_body=html,
            email_type="weekly_kickoff",
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )

    # ── Post approval (day-before drip) ──────────────────────────────────────

    async def send_post_approval(
        self,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        post: dict,
        scheduled_day: str,
        approve_token: str,
        decline_token: str,
        db: AsyncSession,
    ):
        from email_system.templates import post_approval_template
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        html = post_approval_template(
            first_name=first_name,
            post=post,
            scheduled_day=scheduled_day,
            approve_token=approve_token,
            decline_token=decline_token,
            base_url=base_url,
        )

        await self.send(
            to_email=user_email,
            subject=f"📅 Tomorrow is {scheduled_day} — approve your post now",
            html_body=html,
            email_type=f"post_approval_{scheduled_day.lower()}",
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )

    # ── Weekly analytics ──────────────────────────────────────────────────────

    async def send_weekly_analytics(
        self,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        insights: dict,
        db: AsyncSession,
    ):
        from email_system.templates import weekly_analytics_template
        from datetime import datetime, timedelta, timezone

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        insights["week_start"] = week_ago.strftime("%b %d")
        insights["week_end"]   = datetime.now(timezone.utc).strftime("%b %d")

        html = weekly_analytics_template(
            first_name=first_name,
            business_name=business_name,
            insights=insights,
        )

        await self.send(
            to_email=user_email,
            subject=f"📊 {business_name}'s weekly results — {insights['week_start']} to {insights['week_end']}",
            html_body=html,
            email_type="weekly_analytics",
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )

    # ── Morning briefing ──────────────────────────────────────────────────────

    async def send_morning_briefing(
        self,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        briefing_items: list,
        db: AsyncSession,
    ):
        from email_system.templates import morning_briefing_template
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        html = morning_briefing_template(
            business_name=business_name,
            first_name=first_name,
            yesterday_metrics={"highlights": []},
            actions=briefing_items,
            base_url=base_url,
        )

        await self.send(
            to_email=user_email,
            subject=f"☀️ Good morning {first_name} — your Marlo briefing",
            html_body=html,
            email_type="morning_briefing",
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )

    # ── Weekly performance report (legacy) ───────────────────────────────────

    async def send_weekly_report(
        self,
        business_id: str,
        user_email: str,
        first_name: str,
        business_name: str,
        report_data: dict,
        db: AsyncSession,
    ):
        from email_system.templates import weekly_report_template

        html = weekly_report_template(first_name=first_name, report_data=report_data)

        await self.send(
            to_email=user_email,
            subject=f"📊 {business_name}'s weekly report",
            html_body=html,
            email_type="weekly_report",
            business_id=business_id,
            db=db,
            reply_to=self._reply_to(business_id),
        )


email_sender = EmailSender()