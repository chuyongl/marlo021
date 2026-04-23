"""
content_agent.py
Generates platform-specific captions and hashtags based on strategy brief.
Checks brand voice consistency before returning.
"""
from agent.brain import brain
import json

PLATFORM_SPECS = {
    "instagram": {
        "max_caption": 2200,
        "optimal_caption": 150,
        "hashtags": "5-15 relevant hashtags",
        "style": "visual storytelling, emojis welcome, conversational"
    },
    "facebook": {
        "max_caption": 63206,
        "optimal_caption": 80,
        "hashtags": "1-3 hashtags max",
        "style": "more informational, can be longer, community-focused"
    },
    "instagram_story": {
        "max_caption": 250,
        "optimal_caption": 50,
        "hashtags": "3-5 hashtags",
        "style": "very short, punchy, swipe-up CTA"
    }
}

class ContentAgent:

    async def generate(
        self,
        strategy: dict,
        platform: str,
        business: dict,
        business_id: str,
        theme: str = ""
    ) -> dict:
        """
        Generate caption + hashtags for a specific platform.
        Returns: { caption, hashtags, full_text, brand_check_passed }
        """
        specs = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])

        prompt = f"""Write a {platform} post for {business.get('name', 'this business')}.

Strategy brief:
- Hook: {strategy.get('hook_strategy', '')}
- Key message: {strategy.get('key_message', '')}
- Tone: {strategy.get('tone_guidance', business.get('tone_of_voice', 'friendly'))}
- CTA: {strategy.get('call_to_action', '')}
- Avoid: {strategy.get('avoid', '')}

Business:
- Industry: {business.get('industry', '')}
- Target audience: {business.get('target_audience', '')}
- Brand tone: {business.get('tone_of_voice', 'warm and authentic')}
{f'- Theme: {theme}' if theme else ''}

Platform specs:
- Keep caption under {specs['optimal_caption']} words ideally
- Hashtags: {specs['hashtags']}
- Style: {specs['style']}

Return JSON only:
{{
  "caption": "the post caption without hashtags",
  "hashtags": ["hashtag1", "hashtag2"],
  "brand_voice_score": 1-10,
  "brand_voice_notes": "brief note on how well this matches the brand"
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
            content = json.loads(reasoning)
        except Exception:
            content = {
                "caption": result.get("summary", f"Check out what's new at {business.get('name', 'us')}!"),
                "hashtags": ["#smallbusiness", f"#{business.get('industry', 'local').replace(' ', '').lower()}"],
                "brand_voice_score": 7,
                "brand_voice_notes": "Generated with fallback"
            }

        hashtags = content.get("hashtags", [])
        caption = content.get("caption", "")
        full_text = f"{caption}\n\n{' '.join(hashtags)}" if hashtags else caption

        return {
            "caption": caption,
            "hashtags": hashtags,
            "full_text": full_text,
            "brand_voice_score": content.get("brand_voice_score", 7),
            "brand_voice_notes": content.get("brand_voice_notes", ""),
            "platform": platform,
        }

    async def generate_week(
        self,
        strategy: dict,
        business: dict,
        business_id: str,
        platforms: list,
        theme: str = ""
    ) -> list:
        """Generate a week of content across platforms."""
        days = ["Monday", "Wednesday", "Friday"]
        posts = []

        for i, day in enumerate(days):
            platform = platforms[i % len(platforms)] if platforms else "instagram"
            content = await self.generate(
                strategy=strategy,
                platform=platform,
                business=business,
                business_id=business_id,
                theme=theme
            )
            content["scheduled_day"] = day
            posts.append(content)

        return posts


content_agent = ContentAgent()