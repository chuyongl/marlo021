async def process_onboarding_reply(business_id: str, reply_text: str, db):
    """
    Called when user replies to onboarding email 4 with their business description.
    Extracts info, updates business record, generates first content, then sends email 5.
    """
    from agent.brain import brain
    from sqlalchemy import select, update
    from database.models import Business, User
    import json, os

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

    # Step 1: Extract structured info from their reply
    extract_prompt = f"""Extract the following from this business description and return ONLY valid JSON, no explanation:
{{
  "description": "what the business sells or does (1-2 sentences)",
  "target_audience": "who their typical customers are",
  "tone_of_voice": "brand personality in 3-5 words",
  "upcoming_promotions": "any events or promotions mentioned, or empty string if none"
}}

Business description: {reply_text}"""

    raw = await brain.generate_content(
        content_type="business info extraction JSON",
        business={},
        context={},
        instructions=extract_prompt
    )

    try:
        clean = raw.strip()
        if "```" in clean:
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        extracted = json.loads(clean.strip())
    except Exception:
        extracted = {"description": reply_text[:500]}

    # Step 2: Update business record
    await db.execute(
        update(Business)
        .where(Business.id == business_id)
        .values(
            description=extracted.get("description", ""),
            target_audience=extracted.get("target_audience", ""),
            tone_of_voice=extracted.get("tone_of_voice", ""),
            onboarding_step=5
        )
    )
    await db.commit()

    # Step 3: Fetch updated business and user
    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    biz = biz_result.scalar_one_or_none()
    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
    usr = user_result.scalar_one_or_none()
    first_name = (usr.full_name or "").split()[0] or "there"

    # Step 3b: Check which platforms are connected
    from database.models import PlatformIntegration
    from sqlalchemy import select as sa_select
    integrations_result = await db.execute(
        sa_select(PlatformIntegration)
        .where(PlatformIntegration.business_id == business_id)
        .where(PlatformIntegration.is_active == True)
    )
    integrations = integrations_result.scalars().all()
    connected_platforms = [i.platform for i in integrations]
    has_google = any(p in connected_platforms for p in ["google_ads", "google"])
    has_meta = any(p in connected_platforms for p in ["meta", "instagram", "facebook"])
    has_mailchimp = "mailchimp" in connected_platforms

    # Determine which platforms to generate content for
    content_platforms = []
    if has_meta:
        content_platforms.append("instagram")
    if not content_platforms:
        # Fallback: generate instagram content even if not connected
        # (user can connect later, content is ready)
        content_platforms = ["instagram"]

    # Step 4: Generate first week of posts for connected platforms
    posts_for_email = []

    try:
        from agent.content_pipeline import content_pipeline
        from agent.executor import executor

        theme = extracted.get("upcoming_promotions") or None
        posts = await content_pipeline.generate_week_of_content(
            business_id=business_id,
            db=db,
            platforms=content_platforms,
            theme=theme
        )

        for post in posts[:3]:
            action = {
                "type": "create_post",
                "platform": post.get("platform", "instagram"),
                "parameters": {
                    "caption": post.get("caption", ""),
                    "image_url": post.get("image_url"),
                    "scheduled_day": post.get("scheduled_day"),
                    "hashtags": post.get("hashtags", []),
                },
                "reasoning": f"First week of content for {biz.name}",
                "risk_level": "medium",
                "requires_approval": True
            }
            enriched = await executor.create_pending_action_with_tokens(
                action, business_id, db
            )
            posts_for_email.append({
                "scheduled_day": post.get("scheduled_day") or "This week",
                "day": post.get("scheduled_day") or "This week",
                "caption": post.get("caption", ""),
                "hashtags": post.get("hashtags", []),
                "image_url": post.get("image_url"),
                "platform": post.get("platform", "instagram"),
                "approve_url": f"{base_url}/actions/approve?token={enriched['approval_token']}",
                "decline_url": f"{base_url}/actions/decline?token={enriched['decline_token']}",
            })

    except Exception as e:
        print(f"Content generation error (non-fatal): {e}")
        posts_for_email = []

    # Step 5: Generate Google Ads campaign — ONLY if Google is connected
    campaigns_for_email = []

    if has_google:
        from agent.executor import executor

        campaign_prompt = f"""Suggest a first Google Ads search campaign for this business.
Business: {biz.name} — {biz.description or 'local business'}
Target audience: {biz.target_audience or 'local customers'}
Monthly ad budget: ${biz.monthly_ad_budget or 300}

Return ONLY valid JSON, no explanation:
{{
  "name": "campaign name",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "daily_budget": 8,
  "est_clicks": "30-50",
  "goal": "one sentence describing the campaign goal"
}}"""

        raw_campaign = await brain.generate_content(
            content_type="Google Ads campaign suggestion JSON",
            business={"name": biz.name, "industry": biz.industry or ""},
            context={},
            instructions=campaign_prompt
        )

        try:
            clean = raw_campaign.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            campaign_data = json.loads(clean.strip())
        except Exception:
            campaign_data = {
                "name": f"{biz.name} — Search Campaign",
                "keywords": [biz.industry or "local business", biz.name],
                "daily_budget": 8,
                "est_clicks": "30-50",
                "goal": "Drive local awareness and website visits"
            }

        campaign_action = {
            "type": "create_campaign",
            "platform": "google_ads",
            "parameters": campaign_data,
            "reasoning": f"First Google Ads campaign for {biz.name}",
            "risk_level": "medium",
            "requires_approval": True
        }
        enriched_campaign = await executor.create_pending_action_with_tokens(
            campaign_action, business_id, db
        )
        campaign_data["approve_url"] = f"{base_url}/actions/approve?token={enriched_campaign['approval_token']}"
        campaign_data["decline_url"] = f"{base_url}/actions/decline?token={enriched_campaign['decline_token']}"
        campaigns_for_email = [campaign_data]

    except Exception as e:
        print(f"Campaign suggestion error (non-fatal): {e}")
        campaigns_for_email = []

    # Step 6: Send email 5
    from email_system.sender import email_sender
    await email_sender.send_onboarding_step(
        step=5,
        business_id=business_id,
        user_email=usr.email,
        first_name=first_name,
        business_name=biz.name,
        db=db,
        extra_data={
            "campaigns": campaigns_for_email,
            "posts": posts_for_email
        }
    )