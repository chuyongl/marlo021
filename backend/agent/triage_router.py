"""
triage_router.py
Classifies incoming content requests and routes to the right agent pipeline.
"""
from agent.brain import brain

CONTENT_TYPES = {
    "promotional": "Time-sensitive offer, sale, discount, or event promotion",
    "seasonal": "Holiday, season, or calendar-based content",
    "photo_post": "User submitted a photo to turn into a post",
    "evergreen": "General brand content, product showcase, tips, behind-the-scenes",
    "campaign": "Google Ads or Facebook Ads campaign creation/optimization",
    "report": "Performance report or analytics summary",
    "reply": "Response to a user question or instruction",
}

class TriageRouter:

    async def classify(self, request: str, context: dict) -> dict:
        """
        Classify a content request and return routing decision.
        Returns: { type, priority, platforms, reasoning }
        """
        business_name = context.get("business", {}).get("name", "this business")
        connected = context.get("connected_platforms", [])

        prompt = f"""Classify this content request for {business_name}.

Request: "{request}"
Connected platforms: {connected}

Choose the best content type from:
{chr(10).join(f'- {k}: {v}' for k, v in CONTENT_TYPES.items())}

Also determine:
- priority: "high" (time-sensitive, user explicitly asked) or "normal"
- platforms: list of relevant platforms from {connected}
- needs_image: true/false

Return JSON only:
{{
  "type": "content_type",
  "priority": "high|normal",
  "platforms": ["platform1"],
  "needs_image": true,
  "reasoning": "one sentence why"
}}"""

        result = await brain.think(
            user_message=prompt,
            context={},
            business_id=context.get("business_id", ""),
            db=None,
            model="claude-haiku-4-5-20251001"
        )

        import json
        try:
            reasoning = result.get("reasoning", "{}")
            if "```json" in reasoning:
                reasoning = reasoning.split("```json")[1].split("```")[0]
            classification = json.loads(reasoning)
        except Exception:
            classification = {
                "type": "evergreen",
                "priority": "normal",
                "platforms": connected[:2] if connected else ["instagram"],
                "needs_image": True,
                "reasoning": "Default classification"
            }

        return classification


triage_router = TriageRouter()