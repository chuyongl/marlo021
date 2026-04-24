"""
content_agent.py
Generates platform-specific captions and hashtags based on strategy brief.
Uses brain.generate_content() for direct text output — no JSON parsing needed.
"""
from agent.brain import brain
import json

PLATFORM_SPECS = {
    "instagram": {
        "optimal_words": 50,
        "hashtags": "8-12 relevant hashtags",
        "style": "conversational, visual storytelling, emojis welcome"
    },
    "facebook": {
        "optimal_words": 80,
        "hashtags": "1-3 hashtags max",
        "style": "more informational, community-focused, can include a question"
    },
    "instagram_story": {
        "optimal_words": 20,
        "hashtags": "3-5 hashtags",
        "style": "very short, punchy, direct call to action"
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
        Returns: { caption, hashtags, full_text, brand_voice_score }
        """
        specs = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])

        # Step 1: Generate caption
        caption_prompt = f"""Write a ready-to-post {platform} caption for {business.get('name', 'this business')}.

Strategy:
- Hook approach: {strategy.get('hook_strategy', 'lead with value')}
- Key message: {strategy.get('key_message', 'showcase the business')}
- Tone: {strategy.get('tone_guidance', business.get('tone_of_voice', 'warm and authentic'))}
- Call to action: {strategy.get('call_to_action', 'visit us')}
- Avoid: {strategy.get('avoid', 'generic claims')}

Business:
- Name: {business.get('name', '')}
- Industry: {business.get('industry', '')}
- Target audience: {business.get('target_audience', 'local customers')}
{f'- Theme/context: {theme}' if theme else ''}

Requirements:
- Under {specs['optimal_words']} words
- Style: {specs['style']}
- Must sound like a real person wrote it, not AI
- Do NOT include hashtags in the caption itself
- Return ONLY the caption text, nothing else"""

        caption = await brain.generate_content(
            content_type=f"{platform} post caption",
            business=business,
            context={},
            instructions=caption_prompt
        )
        caption = caption.strip().strip('"')

        # Step 2: Generate hashtags separately
        hashtag_prompt = f"""Generate {specs['hashtags']} for this {platform} post about {business.get('name', 'a local business')}.

Business industry: {business.get('industry', 'Food & Beverage')}
Post topic: {strategy.get('key_message', 'business showcase')}
{f'Theme: {theme}' if theme else ''}

Return ONLY the hashtags as a space-separated list starting with #, nothing else.
Example format: #coffeeshop #seattle #localcafe #morningcoffee"""

        hashtag_raw = await brain.generate_content(
            content_type="hashtags",
            business=business,
            context={},
            instructions=hashtag_prompt
        )

        # Parse hashtags from raw string
        hashtags = [
            tag.strip()
            for tag in hashtag_raw.replace(',', ' ').split()
            if tag.strip().startswith('#')
        ][:15]  # cap at 15

        full_text = f"{caption}\n\n{' '.join(hashtags)}" if hashtags else caption

        return {
            "caption": caption,
            "hashtags": hashtags,
            "full_text": full_text,
            "brand_voice_score": 8,  # default good score since we're using direct generation
            "brand_voice_notes": "Generated with direct content agent",
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