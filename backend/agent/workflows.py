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

@workflow.defn
class MorningCheckWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> dict:
        context = await workflow.execute_activity(
            fetch_context_activity,
            input.business_id,
            start_to_close_timeout=timedelta(minutes=2)
        )

        message = """Good morning. Please:
1. Review overnight performance across all platforms
2. Identify the 1-2 most important things to do today
3. Flag any campaigns with unusual spend or low performance
4. Suggest the best content to post today based on recent engagement data
5. Note anything urgent"""

        plan = await workflow.execute_activity(
            run_agent_activity,
            args=[input.business_id, context, message],
            start_to_close_timeout=timedelta(minutes=3)
        )

        monthly_budget = context.get("business", {}).get("monthly_budget", 300)
        safe_actions = [a for a in plan.get("actions", []) if a.get("risk_level") == "low"]

        if safe_actions:
            await workflow.execute_activity(
                execute_actions_activity,
                args=[input.business_id, safe_actions, monthly_budget],
                start_to_close_timeout=timedelta(minutes=5)
            )

        await workflow.execute_activity(
            notify_owner_activity,
            args=[input.business_id, plan.get("summary", "Morning check complete."), "morning_briefing"],
            start_to_close_timeout=timedelta(seconds=30)
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
            notify_owner_activity
        ]
    )
    print("Temporal worker running. Press Ctrl+C to stop.")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(run_worker())