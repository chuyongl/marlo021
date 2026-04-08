from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from dataclasses import dataclass
from datetime import timedelta
import asyncio

@dataclass
class WorkflowInput:
    business_id: str
    task_type: str
    user_message: str = ""

@activity.defn
async def fetch_context_activity(business_id: str) -> dict:
    from agent.context_builder import context_builder
    from database.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        return await context_builder.build_full_context(business_id, db)

@activity.defn
async def run_agent_activity(business_id: str, context: dict, message: str) -> dict:
    from agent.brain import brain
    from database.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        return await brain.think(message, context, business_id, db)

@activity.defn
async def execute_actions_activity(business_id: str, actions: list, monthly_budget: float) -> list:
    from agent.executor import executor
    from database.session import AsyncSessionLocal
    results = []
    async with AsyncSessionLocal() as db:
        for action in actions:
            result = await executor.execute_action(action, business_id, monthly_budget, db)
            results.append(result)
    return results

@activity.defn
async def notify_owner_activity(business_id: str, message: str, notification_type: str) -> bool:
    # TODO Day 19: plug in real push notifications (Firebase or email)
    print(f"[NOTIFY] {notification_type} for {business_id}: {message[:120]}")
    return True

@activity.defn
async def create_pending_actions_activity(business_id: str, actions: list) -> list:
    from agent.executor import executor
    from database.session import AsyncSessionLocal
    results = []
    async with AsyncSessionLocal() as db:
        for action in actions:
            enriched = await executor.create_pending_action_with_tokens(action, business_id, db)
            results.append(enriched)
    return results

@activity.defn
async def send_morning_email_activity(business_id: str, plan: dict, pending_actions: list) -> bool:
    from email_system.sender import email_sender
    from database.session import AsyncSessionLocal
    from database.models import Business, User
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalar_one_or_none()
        if not business:
            return False

        user_result = await db.execute(select(User).where(User.id == business.owner_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return False

        first_name = (user.full_name or user.email.split("@")[0]).split()[0]

        # Build yesterday metrics from plan insights
        yesterday_metrics = {
            "highlights": [
                {"label": insight.split(":")[0] if ":" in insight else "Update",
                 "value": insight.split(":")[1].strip() if ":" in insight else insight,
                 "positive": True}
                for insight in plan.get("insights", [])[:4]
            ]
        }

        await email_sender.send_morning_briefing(
            business=business,
            user_email=user.email,
            user_first_name=first_name,
            yesterday_metrics=yesterday_metrics,
            pending_actions=pending_actions,
            db=db
        )
    return True

@workflow.defn
class MorningCheckWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> dict:
        # 1. Fetch all platform data
        context = await workflow.execute_activity(
            fetch_context_activity, input.business_id,
            start_to_close_timeout=timedelta(minutes=2)
        )

        # 2. Run agent reasoning
        message = """Good morning. Please:
1. Summarize yesterday's performance — what worked, what didn't
2. Identify the 2-3 most important actions for today
3. Flag any campaigns needing attention (high spend, low performance, unusual patterns)
4. Suggest the best content to post today
5. Note anything urgent

Keep your summary conversational — this will be read in a morning email."""

        plan = await workflow.execute_activity(
            run_agent_activity,
            args=[input.business_id, context, message],
            start_to_close_timeout=timedelta(minutes=3)
        )

        # 3. Execute zero-risk actions automatically (report generation, analytics)
        # Queue everything else with approval tokens
        monthly_budget = context.get("business", {}).get("monthly_budget", 300)

        auto_execute = [a for a in plan.get("actions", []) if a.get("risk_level") == "low" and not a.get("requires_approval")]
        need_approval = [a for a in plan.get("actions", []) if a.get("risk_level") in ("medium", "high") or a.get("requires_approval")]

        if auto_execute:
            await workflow.execute_activity(
                execute_actions_activity,
                args=[input.business_id, auto_execute, monthly_budget],
                start_to_close_timeout=timedelta(minutes=3)
            )

        # 4. Create approval tokens for actions needing review
        pending_with_tokens = await workflow.execute_activity(
            create_pending_actions_activity,
            args=[input.business_id, need_approval],
            start_to_close_timeout=timedelta(minutes=1)
        )

        # 5. Send morning email
        await workflow.execute_activity(
            send_morning_email_activity,
            args=[input.business_id, plan, pending_with_tokens],
            start_to_close_timeout=timedelta(minutes=2)
        )

        return plan

@workflow.defn
class WeeklyReportWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> dict:
        context = await workflow.execute_activity(
            fetch_context_activity,
            input.business_id,
            start_to_close_timeout=timedelta(minutes=3)
        )

        message = """Generate my weekly marketing report. Include:
1. ROI summary: total spend vs attributed revenue
2. Best and worst performing campaigns with explanations
3. Top customer segments driving results
4. Content performance: best posts and emails
5. 3 specific recommendations for next week
6. Budget pacing: am I on track with my monthly budget?"""

        report = await workflow.execute_activity(
            run_agent_activity,
            args=[input.business_id, context, message],
            start_to_close_timeout=timedelta(minutes=5)
        )

        await workflow.execute_activity(
            notify_owner_activity,
            args=[input.business_id, "Your weekly report is ready in your Marlo dashboard.", "weekly_report"],
            start_to_close_timeout=timedelta(seconds=30)
        )

        return report

async def run_worker():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="marlo-marketing",
        workflows=[MorningCheckWorkflow, WeeklyReportWorkflow],
        activities=[
            fetch_context_activity,
            run_agent_activity,
            execute_actions_activity,
            notify_owner_activity,
            create_pending_actions_activity,
            send_morning_email_activity,
        ]
    )
    print("Temporal worker running. Press Ctrl+C to stop.")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(run_worker())