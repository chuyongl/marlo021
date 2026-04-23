async def process_onboarding_reply(business_id: str, reply_text: str, db):
    """
    Called when user replies to onboarding email 4 with their business description.
    Extracts info, updates business record, generates first content, then sends email 5.
    """
    from agent.brain import brain
    from sqlalchemy import select, update
    from database.models import Business, User
    import json

    # Step 1: Use Claude to extract structured info from their reply
    result = await brain.think(
        user_message=f"""Extract the following from this business description reply and return as JSON:
{{
  "description": "what the business sells or does (1-2 sentences)",
  "target_audience": "who their typical customers are",
  "tone_of_voice": "brand personality in 3-5 words",
  "upcoming_promotions": "any events or promotions mentioned, or empty string if none"
}}

Reply text: {reply_text}""",
        context={}, business_id=business_id, db=None,
        model="claude-haiku-4-5-20251001"
    )

    try:
        extracted = json.loads(result.get("reasoning", "{}"))
    except Exception:
        extracted = {"description": reply_text[:500]}

    # Step 2: Update business record with extracted info
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

    # Step 4: Generate first week of Instagram posts
    posts_for_email = []
    campaigns_for_email = []

    try:
        from agent.content_pipeline import content_pipeline
        theme = extracted.get("upcoming_promotions") or None
        posts = await content_pipeline.generate_week_of_content(
            business_id=business_id,
            db=db,
            platforms=["instagram"],
            theme=theme
        )

        # Format posts for email 5 display
        from agent.executor import executor
        import os
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        for post in posts[:3]:
            # Create approval action for each post
            action = {
                "type": "create_post",
                "platform": post.get("platform", "instagram"),
                "parameters": {
                    "caption": post.get("caption", ""),
                    "image_url": post.get("image_url"),
                    "scheduled_day": post.get("scheduled_day"),
                },
                "reasoning": f"First week of content for {biz.name}",
                "risk_level": "medium",
                "requires_approval": True
            }
            enriched = await executor.create_pending_action_with_tokens(
                action, business_id, db
            )
            posts_for_email.append({
                "day": post.get("scheduled_day") or post.get("title") or "This week",
                "caption_preview": post.get("caption", "")[:120],
                "image_url": post.get("image_url"),
                "approve_url": f"{base_url}/actions/approve?token={enriched['approval_token']}",
                "decline_url": f"{base_url}/actions/decline?token={enriched['decline_token']}",
            })

    except Exception as e:
        print(f"Content generation error (non-fatal): {e}")
        # Don't block email 5 if content generation fails — send with empty posts
        posts_for_email = []

    # Step 5: Generate a placeholder Google Ads campaign suggestion
    try:
        import os
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

        # Use brain to suggest a first campaign
        campaign_result = await brain.think(
            user_message=f"""Suggest a first Google Ads search campaign for this business.
Business: {biz.name} — {biz.description}
Target audience: {biz.target_audience}
Monthly ad budget: ${biz.monthly_ad_budget or 300}

Return JSON with:
{{
  "name": "campaign name",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "daily_budget": 8,
  "est_clicks": "30-50"
}}""",
            context={}, business_id=business_id, db=None,
            model="claude-haiku-4-5-20251001"
        )

        try:
            campaign_data = json.loads(campaign_result.get("reasoning", "{}"))
        except Exception:
            campaign_data = {
                "name": f"{biz.name} — Search Campaign",
                "keywords": [biz.industry or "local business"],
                "daily_budget": 8,
                "est_clicks": "30-50"
            }

        # Create approval action for campaign
        from agent.executor import executor
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

    # Step 6: Send email 5 with real content
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