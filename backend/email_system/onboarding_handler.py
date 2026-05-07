async def process_onboarding_reply(business_id: str, reply_text: str, db):
    """
    Called when user replies to onboarding email 4 with their business description.
    1. Extract business info and update DB
    2. Send simplified email 5 (setup complete confirmation)
    3. Generate first week of content
    4. Send first kickoff email (detailed, with mechanism explanation)
    """
    from agent.brain import brain
    from sqlalchemy import select, update
    from database.models import Business, User, PlatformIntegration, AgentAction
    from agent.content_pipeline import content_pipeline
    from agent.google_ads_agent import google_ads_agent
    from agent.strategy_agent import strategy_agent
    from email_system.sender import email_sender
    import json, os, uuid as _uuid
    from datetime import datetime, timezone

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

    # ── Step 1: Extract structured info ──────────────────────────────────────
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

    # ── Step 2: Update business record ───────────────────────────────────────
    await db.execute(
        update(Business)
        .where(Business.id == business_id)
        .values(
            description=extracted.get("description", ""),
            target_audience=extracted.get("target_audience", ""),
            tone_of_voice=extracted.get("tone_of_voice", ""),
            onboarding_step=5,
            onboarding_completed=True,
        )
    )
    await db.commit()

    # ── Step 3: Fetch updated business and user ───────────────────────────────
    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    biz = biz_result.scalar_one_or_none()
    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
    usr = user_result.scalar_one_or_none()
    first_name = (usr.full_name or "").split()[0] or "there"

    business_dict = {
        "name": biz.name,
        "industry": biz.industry or "",
        "description": biz.description or "",
        "tone_of_voice": biz.tone_of_voice or "warm and authentic",
        "target_audience": biz.target_audience or "local customers",
        "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
    }

    # ── Step 4: Check connected platforms ────────────────────────────────────
    integrations_result = await db.execute(
        select(PlatformIntegration).where(
            PlatformIntegration.business_id == business_id,
            PlatformIntegration.is_active == True
        )
    )
    integrations = integrations_result.scalars().all()
    connected = [i.platform for i in integrations]
    has_google = any(p in connected for p in ["google_ads", "google"])
    has_meta   = any(p in connected for p in ["meta", "instagram", "facebook"])
    platforms  = ["instagram"] if has_meta else ["instagram"]

    # ── Step 5: Send simplified email 5 immediately ──────────────────────────
    await email_sender.send_onboarding_step(
        step=5,
        business_id=business_id,
        user_email=usr.email,
        first_name=first_name,
        business_name=biz.name,
        db=db,
    )

    # ── Step 6: Generate posting schedule ────────────────────────────────────
    from agent.scheduler import get_posting_schedule, build_scheduled_post_time
    posting_schedule = get_posting_schedule(biz)
    posts_count = len(posting_schedule)

    # ── Step 7: Generate content strategy ────────────────────────────────────
    try:
        strategy = await strategy_agent.decide("weekly_content", {"business": business_dict}, business_id)
        strategy_summary = (
            f"{strategy.get('key_message', '')} "
            f"Tone: {strategy.get('tone_guidance', '')} "
            f"CTA: {strategy.get('call_to_action', '')}"
        ).strip()
    except Exception as e:
        print(f"[OnboardingHandler] Strategy error: {e}")
        strategy = {}
        strategy_summary = f"Building authentic content that showcases {biz.name}'s unique value to {biz.target_audience or 'local customers'}."

    # ── Step 8: Generate content pipeline ────────────────────────────────────
    posts = []
    try:
        theme = extracted.get("upcoming_promotions") or None
        raw_posts = await content_pipeline.generate_week_of_content(
            business_id=business_id,
            db=db,
            platforms=platforms,
            theme=theme,
        )
        while len(raw_posts) < posts_count:
            raw_posts.append(raw_posts[-1].copy() if raw_posts else {})
        raw_posts = raw_posts[:posts_count]
        for i, post in enumerate(raw_posts):
            post["scheduled_day"] = posting_schedule[i]
        posts = raw_posts
    except Exception as e:
        print(f"[OnboardingHandler] Content generation error: {e}")

    # ── Step 9: Store posts as pending actions ────────────────────────────────
    stored_actions = []
    for post in posts:
        action = AgentAction(
            id=_uuid.uuid4(),
            business_id=biz.id,
            action_type=f"post_{post.get('platform', 'instagram')}",
            action_parameters=post,
            approval_token=str(_uuid.uuid4()),
            decline_token=str(_uuid.uuid4()),
            status="pending",
            requires_approval=True,
            scheduled_post_time=build_scheduled_post_time(biz, post["scheduled_day"]),
            scheduled_day=post["scheduled_day"],
            approval_email_sent=False,
            created_at=datetime.utcnow(),
        )
        db.add(action)
        stored_actions.append(action)

    # ── Step 10: Generate Google Ads campaign ────────────────────────────────
    google_campaign = None
    ads_action = None
    if has_google:
        try:
            ads_strategy = await strategy_agent.decide("google_ads", {"business": business_dict}, business_id)
            google_campaign = await google_ads_agent.generate_campaign(
                business=business_dict,
                strategy=ads_strategy,
                business_id=business_id,
            )
            ads_action = AgentAction(
                id=_uuid.uuid4(),
                business_id=biz.id,
                action_type="google_ads_campaign",
                action_parameters=google_campaign,
                approval_token=str(_uuid.uuid4()),
                decline_token=str(_uuid.uuid4()),
                status="pending",
                requires_approval=True,
                scheduled_post_time=datetime.now(timezone.utc),
                scheduled_day=posting_schedule[0],
                approval_email_sent=False,
                created_at=datetime.utcnow(),
            )
            db.add(ads_action)
        except Exception as e:
            print(f"[OnboardingHandler] Google Ads generation error: {e}")

    await db.commit()

    # ── Step 11: Build image guide ────────────────────────────────────────────
    visual = strategy.get("visual_direction", "") if isinstance(strategy, dict) else ""
    image_guide = []
    for post in posts:
        day = post.get("scheduled_day", "")
        image_guide.append({
            "day": day,
            "type": "Real photo recommended",
            "description": visual or f"A photo that shows {biz.name} in action — real people and real products always outperform stock imagery.",
        })

    # ── Step 12: Get first post + tokens ─────────────────────────────────────
    first_day = posting_schedule[0]
    first_action = next(
        (a for a in stored_actions if a.scheduled_day == first_day and a.action_type != "google_ads_campaign"),
        stored_actions[0] if stored_actions else None
    )

    if not first_action:
        print(f"[OnboardingHandler] No first action found — skipping kickoff email")
        return

    # Mark first post + ads approval email as sent
    first_action.approval_email_sent = True
    if ads_action:
        ads_action.approval_email_sent = True
    await db.commit()

    # ── Step 13: Send first kickoff email ────────────────────────────────────
    await email_sender.send_first_kickoff(
        business_id=business_id,
        user_email=usr.email,
        first_name=first_name,
        business_name=biz.name,
        first_post=first_action.action_parameters or {},
        first_post_day=first_day,
        first_approve_token=first_action.approval_token,
        first_decline_token=first_action.decline_token,
        google_campaign=google_campaign,
        ads_approve_token=ads_action.approval_token if ads_action else None,
        ads_decline_token=ads_action.decline_token if ads_action else None,
        posting_schedule=posting_schedule,
        strategy_summary=strategy_summary,
        image_guide=image_guide,
        db=db,
    )

    print(f"[OnboardingHandler] Kickoff email sent for {biz.name} — {posts_count} posts: {posting_schedule}")