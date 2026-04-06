from temporalio.client import Client
from temporalio.common import Schedule, ScheduleActionStartWorkflow, ScheduleSpec
from agent.workflows import MorningCheckWorkflow, WeeklyReportWorkflow, WorkflowInput
import asyncio

async def register_schedules_for_business(business_id: str):
    client = await Client.connect("localhost:7233")

    await client.create_schedule(
        f"morning-check-{business_id}",
        Schedule(
            action=ScheduleActionStartWorkflow(
                MorningCheckWorkflow.run,
                WorkflowInput(business_id=business_id, task_type="morning_check"),
                id=f"morning-{business_id}",
                task_queue="marlo-marketing"
            ),
            spec=ScheduleSpec(cron_expressions=["0 8 * * *"])  # 8am daily
        )
    )

    await client.create_schedule(
        f"weekly-report-{business_id}",
        Schedule(
            action=ScheduleActionStartWorkflow(
                WeeklyReportWorkflow.run,
                WorkflowInput(business_id=business_id, task_type="weekly_report"),
                id=f"weekly-{business_id}",
                task_queue="marlo-marketing"
            ),
            spec=ScheduleSpec(cron_expressions=["0 7 * * 1"])  # 7am every Monday
        )
    )
    print(f"Schedules registered for {business_id}")

if __name__ == "__main__":
    import sys
    business_id = sys.argv[1] if len(sys.argv) > 1 else "test-business-id"
    asyncio.run(register_schedules_for_business(business_id))