"""
strategy_agent.py
Analyzes business metrics and context to decide the best content strategy.
As more data accumulates, this agent's recommendations improve automatically.
"""
from agent.brain import brain
import json

class StrategyAgent:

    async def decide(self, content_type: str, context: dict, business_id: str) -> dict:
        """
        Decide content strategy based on metrics, history, and business context.
        Returns a strategy brief for the content agent.
        """
        business = context.get("business", {})
        metrics = context.get("recent_metrics", {})
        recent_actions = context.get("recent_actions", [])
        feedback_summary = context.get("feedback_summary", {})

        # Build strategy context from available data
        metrics_insight = ""
        if metrics:
            ctr = metrics.get("avg_ctr", 0)
            spend = metrics.get("total_spend", 0)
            clicks = metrics.get("total_clicks", 0)
            if ctr > 3:
                metrics_insight = f"Ads are performing well (CTR {ctr}%) — reinforce what's working."
            elif ctr > 0:
                metrics_insight = f"CTR is {ctr}% — try a stronger hook or more specific offer."
            else:
                metrics_insight = "No recent ad data yet — focus on brand awareness content."

        # What content has been approved vs declined recently
        approved_types = [a["type"] for a in recent_actions if a.get("status") == "executed"]
        declined_types = [a["type"] for a in recent_actions if a.get("status") == "rejected"]

        # Feedback patterns
        approve_rate = feedback_summary.get("approve_rate", None)
        top_declined_reason = feedback_summary.get("top_declined_reason", None)

        prompt = f"""You are a marketing strategist for {business.get('name', 'a small business')}.

Business context:
- Industry: {business.get('industry', 'unknown')}
- Target audience: {business.get('target_audience', 'general')}
- Brand tone: {business.get('tone_of_voice', 'friendly')}
- Monthly ad budget: ${business.get('monthly_ad_budget', 300)}

Performance data:
- {metrics_insight}
- Recently approved content types: {approved_types[:5] if approved_types else 'none yet'}
- Recently declined content types: {declined_types[:3] if declined_types else 'none yet'}
{f'- Owner approval rate: {approve_rate}%' if approve_rate else ''}
{f'- Common decline reason: {top_declined_reason}' if top_declined_reason else ''}

Content request type: {content_type}

Create a strategy brief for this content. Return JSON only:
{{
  "hook_strategy": "how to open the content to grab attention",
  "key_message": "the one thing this content should communicate",
  "tone_guidance": "specific tone notes for this piece",
  "call_to_action": "what action should the audience take",
  "avoid": "what to avoid based on past declines or brand",
  "visual_direction": "what the image/visual should convey"
}}"""

        result = await brain.think(
            user_message=prompt,
            context={},
            business_id=business_id,
            db=None,
            model="claude-haiku-4-5-20251001"
        )

        try:
            reasoning = result.get("reasoning", "{}")
            if "```json" in reasoning:
                reasoning = reasoning.split("```json")[1].split("```")[0]
            strategy = json.loads(reasoning)
        except Exception:
            strategy = {
                "hook_strategy": "Lead with your unique value",
                "key_message": f"What makes {business.get('name', 'us')} special",
                "tone_guidance": business.get("tone_of_voice", "warm and authentic"),
                "call_to_action": "Visit us or learn more",
                "avoid": "Generic claims without specifics",
                "visual_direction": "Show the product or experience clearly"
            }

        return strategy


strategy_agent = StrategyAgent()