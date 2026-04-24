"""
strategy_agent.py
Analyzes business metrics and context to decide the best content strategy.
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

        # Build metrics insight
        metrics_insight = "No recent ad data yet — focus on brand awareness."
        if metrics:
            ctr = metrics.get("avg_ctr", 0)
            if ctr > 3:
                metrics_insight = f"Ads performing well (CTR {ctr}%) — reinforce what's working."
            elif ctr > 0:
                metrics_insight = f"CTR is {ctr}% — try a stronger hook or more specific offer."

        approved_types = [a["type"] for a in recent_actions if a.get("status") == "executed"]
        declined_types = [a["type"] for a in recent_actions if a.get("status") == "rejected"]
        approve_rate = feedback_summary.get("approve_rate")
        top_declined_reason = feedback_summary.get("top_declined_reason")

        prompt = f"""You are a marketing strategist for {business.get('name', 'a small business')}.

Business:
- Industry: {business.get('industry', 'unknown')}
- Target audience: {business.get('target_audience', 'general')}
- Brand tone: {business.get('tone_of_voice', 'friendly and authentic')}
- Monthly ad budget: ${business.get('monthly_ad_budget', 300)}

Performance:
- {metrics_insight}
- Recently approved content types: {approved_types[:5] if approved_types else 'none yet'}
- Recently declined: {declined_types[:3] if declined_types else 'none yet'}
{f'- Approval rate: {approve_rate}%' if approve_rate else ''}
{f'- Common decline reason: {top_declined_reason}' if top_declined_reason else ''}

Content type needed: {content_type}

Create a strategy brief. Return ONLY valid JSON, no explanation:
{{
  "hook_strategy": "how to open the content to grab attention",
  "key_message": "the one thing this content should communicate",
  "tone_guidance": "specific tone notes for this piece",
  "call_to_action": "what action should the audience take",
  "avoid": "what to avoid based on past declines or brand",
  "visual_direction": "what the image should convey"
}}"""

        raw = await brain.generate_content(
            content_type="marketing strategy brief JSON",
            business=business,
            context={},
            instructions=prompt
        )

        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            strategy = json.loads(clean.strip())
        except Exception:
            strategy = {
                "hook_strategy": "Lead with something specific and real about the business",
                "key_message": f"What makes {business.get('name', 'us')} worth visiting",
                "tone_guidance": business.get("tone_of_voice", "warm and authentic"),
                "call_to_action": "Come visit us or order online",
                "avoid": "Generic claims, corporate language, vague statements",
                "visual_direction": "Show the actual product or experience, not stock photos"
            }

        return strategy


strategy_agent = StrategyAgent()