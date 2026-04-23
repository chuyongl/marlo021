"""
qa_agent.py
Quality checks generated content before it reaches the user.
Catches brand mismatches, platform spec violations, and low quality output.
"""
from agent.brain import brain
import json

class QAAgent:

    async def check(
        self,
        content: dict,
        strategy: dict,
        business: dict,
        business_id: str
    ) -> dict:
        """
        Check content quality. Returns { passed, score, issues, suggestions }
        score 1-10: 7+ passes, below 7 triggers regeneration.
        """
        platform = content.get("platform", "instagram")
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])
        brand_voice_score = content.get("brand_voice_score", 7)

        # Fast checks first (no LLM needed)
        issues = []

        # Caption length check
        if len(caption) < 10:
            issues.append("Caption too short")
        if platform == "instagram" and len(caption.split()) > 300:
            issues.append("Caption too long for Instagram")

        # Hashtag count
        if platform == "instagram" and len(hashtags) > 30:
            issues.append("Too many hashtags for Instagram (max 30)")
        if platform == "facebook" and len(hashtags) > 5:
            issues.append("Too many hashtags for Facebook (keep to 1-3)")

        # Brand voice score from content agent
        if brand_voice_score < 6:
            issues.append(f"Low brand voice score ({brand_voice_score}/10)")

        # If fast checks already found issues, skip LLM check
        if len(issues) >= 2:
            return {
                "passed": False,
                "score": 4,
                "issues": issues,
                "suggestions": ["Regenerate with stricter brand guidelines"]
            }

        # LLM quality check for borderline cases
        if brand_voice_score < 8 or issues:
            prompt = f"""Quality check this {platform} caption for {business.get('name', 'this business')}.

Caption: "{caption}"
Hashtags: {hashtags}

Brand:
- Tone: {business.get('tone_of_voice', 'friendly')}
- Audience: {business.get('target_audience', 'general')}

Strategy alignment:
- Key message should be: {strategy.get('key_message', '')}
- Should avoid: {strategy.get('avoid', '')}

Rate quality 1-10 and identify any issues. Return JSON only:
{{
  "score": 7,
  "passes": true,
  "issues": ["issue1"],
  "suggestions": ["suggestion1"]
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
                qa_result = json.loads(reasoning)
                return {
                    "passed": qa_result.get("passes", True) and qa_result.get("score", 7) >= 7,
                    "score": qa_result.get("score", 7),
                    "issues": issues + qa_result.get("issues", []),
                    "suggestions": qa_result.get("suggestions", [])
                }
            except Exception:
                pass

        return {
            "passed": len(issues) == 0,
            "score": brand_voice_score,
            "issues": issues,
            "suggestions": []
        }


qa_agent = QAAgent()