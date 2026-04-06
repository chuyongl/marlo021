from agent.guardrails import guardrails
from database.models import AgentAction, PlatformIntegration
from database.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

class AgentExecutor:
    """
    Takes a proposed action from the brain, checks guardrails, and executes.
    This is the bridge between what the AI wants to do and what actually happens.
    """

    async def execute_action(
        self,
        action: dict,
        business_id: str,
        monthly_budget: float,
        db: AsyncSession
    ) -> dict:
        action_type = action.get("type")
        platform = action.get("platform", "")
        params = action.get("parameters", {})

        # ---- Step 1: Guardrail check ----
        if action_type == "bid_change":
            check = await guardrails.check_bid_change(
                current_bid=params.get("current_bid", 0),
                proposed_bid=params.get("new_bid", 0)
            )
        elif action_type in ("spend_action", "create_campaign"):
            check = await guardrails.check_spend_action(
                business_id=business_id,
                platform=platform,
                proposed_spend=params.get("amount", 0),
                monthly_budget=monthly_budget
            )
        elif action_type == "send_email":
            check = await guardrails.check_email_send(
                recipient_count=params.get("recipient_count", 0),
                business_id=business_id
            )
        else:
            check = {"allowed": True, "requires_approval": False, "risk": "low", "reason": "Standard action"}

        # ---- Step 2: Blocked ----
        if not check.get("allowed"):
            await self._log(db, business_id, action, "blocked", check["reason"])
            return {"status": "blocked", "reason": check["reason"]}

        # ---- Step 3: Needs approval ----
        if check.get("requires_approval") or action.get("requires_approval"):
            action_id = await self._log(db, business_id, action, "pending_approval", check["reason"])
            return {
                "status": "pending_approval",
                "action_id": str(action_id),
                "reason": check["reason"],
                "message": "This action needs your approval in your Marlo dashboard."
            }

        # ---- Step 4: Execute ----
        result = await self._execute(action, business_id, db)
        await self._log(db, business_id, action, "executed", outcome=result)
        return {"status": "executed", "result": result}

    async def _execute(self, action: dict, business_id: str, db: AsyncSession) -> dict:
        action_type = action.get("type")
        platform = action.get("platform", "")
        params = action.get("parameters", {})

        int_result = await db.execute(
            select(PlatformIntegration)
            .where(PlatformIntegration.business_id == business_id)
            .where(PlatformIntegration.platform == platform)
            .where(PlatformIntegration.is_active == True)
        )
        integration = int_result.scalar_one_or_none()

        if action_type == "bid_change" and platform == "google_ads" and integration:
            from integrations.google_ads import GoogleAdsIntegration
            gads = GoogleAdsIntegration(
                access_token=integration.access_token,
                refresh_token=integration.refresh_token,
                customer_id=integration.platform_account_id
            )
            success = gads.update_campaign_budget(
                campaign_id=params["campaign_id"],
                new_daily_budget_usd=params["new_daily_budget"]
            )
            return {"success": success, "new_budget": params["new_daily_budget"]}

        elif action_type == "create_post" and platform == "instagram" and integration:
            from integrations.meta import MetaIntegration
            meta = MetaIntegration(
                access_token=integration.access_token,
                ad_account_id=integration.platform_account_id
            )
            result = await meta.post_to_instagram(
                ig_account_id=params["ig_account_id"],
                image_url=params["image_url"],
                caption=params["caption"]
            )
            return result

        elif action_type == "send_email":
            email_result = await db.execute(
                select(PlatformIntegration)
                .where(PlatformIntegration.business_id == business_id)
                .where(PlatformIntegration.platform == "mailchimp")
                .where(PlatformIntegration.is_active == True)
            )
            mc_integration = email_result.scalar_one_or_none()
            if mc_integration:
                from integrations.email_marketing import MailchimpIntegration
                mc = MailchimpIntegration(
                    api_key=mc_integration.access_token,
                    list_id=mc_integration.platform_account_id
                )
                return await mc.create_and_send_campaign(
                    subject=params["subject"],
                    preview_text=params.get("preview_text", ""),
                    body_html=params["body_html"],
                    from_name=params["from_name"],
                    from_email=params["from_email"],
                    segment_id=params.get("segment_id")
                )

        elif action_type == "generate_report":
            from agent.context_builder import context_builder
            from agent.brain import brain
            context = await context_builder.build_full_context(business_id, db)
            return await brain.think(
                user_message="Generate a comprehensive weekly performance report with ROI analysis and next week's recommendations.",
                context=context,
                business_id=business_id,
                db=db
            )

        return {"status": "no_handler", "action_type": action_type}

    async def _log(self, db: AsyncSession, business_id: str, action: dict, status: str,
                   reason: str = "", outcome: dict = None):
        log = AgentAction(
            id=uuid.uuid4(),
            business_id=business_id,
            action_type=action.get("type"),
            status=status,
            input_context=action,
            agent_reasoning=action.get("reasoning", reason),
            action_parameters=action.get("parameters", {}),
            outcome=outcome or {},
            requires_approval=(status == "pending_approval"),
            created_at=datetime.utcnow()
        )
        db.add(log)
        await db.commit()
        return log.id

executor = AgentExecutor()