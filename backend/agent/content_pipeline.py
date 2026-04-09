from agent.brain import brain
from integrations.image_gen import image_gen
from database.models import Business
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

class ContentPipeline:
    async def generate_week_of_content(
        self,
        business_id: str,
        db: AsyncSession,
        platforms: list = None,
        theme: str = None
    ) -> list:
        """
        Generate a full week of social content with images.
        Returns a list of draft posts ready for review and scheduling.
        """
        if platforms is None:
            platforms = ["instagram", "facebook"]

        result = await db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return []

        business_dict = {
            "name": business.name,
            "industry": business.industry,
            "description": business.description,
            "tone_of_voice": business.tone_of_voice,
            "target_audience": business.target_audience
        }

        # Step 1: Generate content ideas
        ideas_prompt = f"""Generate 5 unique social media post ideas for this week.
Business: {business.name} — {business.description}
Target audience: {business.target_audience}
Tone: {business.tone_of_voice}
Theme hint: {theme or 'any relevant theme for the current season'}

For each idea, provide:
1. A short title (the concept in 5 words)
2. The visual concept (what the image should show)
3. The caption (ready to post, including hashtags)
4. Best posting day (Mon–Sun)
5. Best platform (instagram, facebook, or both)

Return as JSON array."""

        ideas_response = await brain.generate_content(
            "social_media_content_plan",
            business_dict,
            {},
            ideas_prompt
        )

        # Parse ideas
        try:
            if "```json" in ideas_response:
                ideas_response = ideas_response.split("```json")[1].split("```")[0]
            ideas = json.loads(ideas_response)
        except Exception:
            ideas = [{"title": "Weekly content", "visual_concept": business.description,
                      "caption": ideas_response[:500], "day": "Monday", "platform": "instagram"}]

        # Step 2: Generate images for top 3 ideas
        posts = []
        for idea in ideas[:3]:
            try:
                image_result = await image_gen.generate(
                    subject=idea.get("visual_concept", idea.get("title", "")),
                    business=business_dict,
                    platform="instagram_feed"
                )
                posts.append({
                    "title": idea.get("title"),
                    "caption": idea.get("caption"),
                    "image_url": image_result["url"],
                    "platform": idea.get("platform", "instagram"),
                    "scheduled_day": idea.get("day"),
                    "status": "draft",
                    "business_id": business_id
                })
            except Exception as e:
                posts.append({
                    "title": idea.get("title"),
                    "caption": idea.get("caption"),
                    "image_url": None,
                    "image_error": str(e),
                    "platform": idea.get("platform", "instagram"),
                    "scheduled_day": idea.get("day"),
                    "status": "draft_no_image",
                    "business_id": business_id
                })

        return posts

    async def generate_email_campaign(
        self,
        business_id: str,
        brief: str,
        db: AsyncSession
    ) -> dict:
        """Generate a full email campaign from a plain-English brief."""
        result = await db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return {}

        business_dict = {
            "name": business.name, "industry": business.industry,
            "description": business.description, "tone_of_voice": business.tone_of_voice
        }

        # Generate subject line (two variants for A/B test)
        subjects_raw = await brain.generate_content(
            "two email subject line variants (A/B test)",
            business_dict, {},
            f"Brief: {brief}\nReturn as JSON: {{\"a\": \"subject A\", \"b\": \"subject B\"}}"
        )
        try:
            if "```json" in subjects_raw:
                subjects_raw = subjects_raw.split("```json")[1].split("```")[0]
            subjects = json.loads(subjects_raw)
        except Exception:
            subjects = {"a": f"From {business.name}", "b": f"Something special from {business.name}"}

        # Generate email body
        body_html = await brain.generate_content(
            "professional HTML email body",
            business_dict, {},
            f"""Brief: {brief}
Create a full HTML email with:
- A compelling headline
- 2-3 paragraphs of body copy
- A clear call-to-action button
- Professional layout using inline CSS only (email clients don't support stylesheets)
- Tone: {business.tone_of_voice}
Return only the HTML, no explanation."""
        )

        return {
            "subject_a": subjects.get("a"),
            "subject_b": subjects.get("b"),
            "body_html": body_html,
            "from_name": business.name,
            "brief": brief,
            "status": "draft"
        }

content_pipeline = ContentPipeline()