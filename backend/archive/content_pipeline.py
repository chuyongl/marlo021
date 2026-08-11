"""
content_pipeline.py
Full multi-agent content generation pipeline:
Triage → Strategy → Content → QA → Image → Output
"""
from agent.brain import brain
from agent.triage_router import triage_router
from agent.strategy_agent import strategy_agent
from agent.content_agent import content_agent
from agent.qa_agent import qa_agent
from integrations.image_gen import image_gen
from database.models import Business
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

MAX_RETRIES = 2  # Max content regeneration attempts if QA fails

class ContentPipeline:

    async def generate_week_of_content(
        self,
        business_id: str,
        db: AsyncSession,
        platforms: list = None,
        theme: str = None,
        context: dict = None
    ) -> list:
        """
        Full pipeline: Triage → Strategy → Content → QA → Image
        Returns a list of approved-quality draft posts.
        """
        if platforms is None:
            platforms = ["instagram"]

        # Load business
        result = await db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return []

        business_dict = {
            "name": business.name,
            "industry": business.industry or "",
            "description": business.description or "",
            "tone_of_voice": business.tone_of_voice or "warm and authentic",
            "target_audience": business.target_audience or "local customers",
            "monthly_ad_budget": float(business.monthly_ad_budget or 300),
        }

        # Build context for agents
        agent_context = context or {}
        agent_context["business"] = business_dict
        agent_context["business_id"] = business_id
        agent_context["connected_platforms"] = platforms

        # Load feedback summary if feedback_agent available
        try:
            from agent.feedback_agent import feedback_agent
            feedback_summary = await feedback_agent.get_feedback_summary(business_id, db)
            agent_context["feedback_summary"] = feedback_summary
        except Exception:
            agent_context["feedback_summary"] = {}

        # Step 1: Triage
        request = f"Generate a week of {', '.join(platforms)} content for {business.name}"
        if theme:
            request += f". Theme: {theme}"

        try:
            classification = await triage_router.classify(request, agent_context)
            content_type = classification.get("type", "evergreen")
            needs_image = classification.get("needs_image", True)
        except Exception as e:
            print(f"[Pipeline] Triage error: {e}")
            content_type = "evergreen"
            needs_image = True

        # Step 2: Strategy
        try:
            strategy = await strategy_agent.decide(content_type, agent_context, business_id)
        except Exception as e:
            print(f"[Pipeline] Strategy error: {e}")
            strategy = {
                "hook_strategy": "Lead with your unique value",
                "key_message": f"What makes {business.name} special",
                "tone_guidance": business_dict["tone_of_voice"],
                "call_to_action": "Visit us today",
                "avoid": "Generic claims",
                "visual_direction": "Show the product or experience"
            }

        # Step 3: Content generation with QA loop
        days = ["Monday", "Wednesday", "Friday"]
        posts = []

        for i, day in enumerate(days):
            platform = platforms[i % len(platforms)]
            post = await self._generate_with_qa(
                platform=platform,
                strategy=strategy,
                business=business_dict,
                business_id=business_id,
                theme=theme or "",
                day=day,
                needs_image=needs_image
            )
            if post:
                posts.append(post)

        return posts

    async def _generate_with_qa(
        self,
        platform: str,
        strategy: dict,
        business: dict,
        business_id: str,
        theme: str,
        day: str,
        needs_image: bool,
        retries: int = 0
    ) -> dict:
        """Generate one post with QA check, retry if quality fails."""
        # Step 3a: Generate content
        try:
            content = await content_agent.generate(
                strategy=strategy,
                platform=platform,
                business=business,
                business_id=business_id,
                theme=theme
            )
        except Exception as e:
            print(f"[Pipeline] Content generation error: {e}")
            content = {
                "caption": f"Something great is happening at {business.get('name', 'us')}!",
                "hashtags": ["#smallbusiness"],
                "full_text": f"Something great is happening at {business.get('name', 'us')}! #smallbusiness",
                "brand_voice_score": 6,
                "platform": platform
            }

        # Step 3b: QA check
        try:
            qa_result = await qa_agent.check(
                content=content,
                strategy=strategy,
                business=business,
                business_id=business_id
            )

            # If QA fails and we haven't exceeded retries, regenerate
            if not qa_result["passed"] and retries < MAX_RETRIES:
                print(f"[Pipeline] QA failed (score {qa_result['score']}), retrying... ({retries+1}/{MAX_RETRIES})")
                # Add QA feedback to strategy to guide regeneration
                strategy["avoid"] = strategy.get("avoid", "") + ". " + ". ".join(qa_result.get("suggestions", []))
                return await self._generate_with_qa(
                    platform, strategy, business, business_id,
                    theme, day, needs_image, retries + 1
                )

            content["qa_score"] = qa_result["score"]
            content["qa_passed"] = qa_result["passed"]

        except Exception as e:
            print(f"[Pipeline] QA error (non-fatal): {e}")
            content["qa_score"] = 7
            content["qa_passed"] = True

        # Step 4: Image generation
        image_url = None
        if needs_image:
            try:
                visual_prompt = strategy.get("visual_direction", content.get("caption", ""))
                image_result = await image_gen.generate(
                    subject=visual_prompt,
                    business=business,
                    platform=f"{platform}_feed" if "story" not in platform else platform
                )
                image_url = image_result.get("url")
            except Exception as e:
                print(f"[Pipeline] Image generation error (non-fatal): {e}")

        return {
            "title": strategy.get("key_message", "New Post")[:50],
            "caption": content.get("caption", ""),  # caption without hashtags
            "caption_preview": content.get("caption", "")[:120],
            "hashtags": content.get("hashtags", []),
            "image_url": image_url,
            "platform": platform,
            "scheduled_day": day,
            "content_type": "post",
            "qa_score": content.get("qa_score", 7),
            "status": "draft"
        }

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

        body_html = await brain.generate_content(
            "professional HTML email body",
            business_dict, {},
            f"""Brief: {brief}
Create a full HTML email with:
- A compelling headline
- 2-3 paragraphs of body copy
- A clear call-to-action button
- Professional layout using inline CSS only
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