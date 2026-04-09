from agent.brain import brain
from agent.context_builder import context_builder
from agent.executor import executor
from integrations.competitive_intel import competitive_intel
from database.session import AsyncSessionLocal
import json

class OptimizationLoop:
    """
    Weekly optimization cycle. Runs automatically every Monday via Temporal.
    Reviews performance, checks competitors, recommends changes.
    """

    async def run_weekly_optimization(self, business_id: str) -> dict:
        async with AsyncSessionLocal() as db:
            # 1. Get full performance context
            context = await context_builder.build_full_context(business_id, db)

            # 2. Get competitor ads (using business keywords)
            industry = context.get("business", {}).get("industry", "")
            competitor_ads = await competitive_intel.get_meta_competitor_ads(
                [industry, context.get("business", {}).get("name", "")]
            )
            context["competitor_intelligence"] = competitor_ads[:5]

            # 3. Ask the agent for optimization recommendations
            optimization_message = """Run the weekly optimization analysis. Review:
1. Which campaigns are performing above target ROAS? (increase budget)
2. Which are below target? (reduce budget or pause)
3. What competitor ads are running? Are there creative angles we should try?
4. What content worked best? Recommend more of it.
5. Any keywords or audiences to add or remove?

Provide specific, numbered recommendations with estimated impact.
For each budget change, specify exact new daily budget amount."""

            recommendations = await brain.think(
                user_message=optimization_message,
                context=context,
                business_id=business_id,
                db=db
            )

            # 4. Auto-execute low-risk optimizations, queue medium/high risk
            monthly_budget = context.get("business", {}).get("monthly_budget", 300)
            results = []
            for action in recommendations.get("actions", []):
                result = await executor.execute_action(
                    action, business_id, monthly_budget, db
                )
                results.append(result)

            return {
                "recommendations": recommendations,
                "execution_results": results,
                "business_id": business_id
            }

optimization_loop = OptimizationLoop()