async def process_onboarding_reply(business_id: str, reply_text: str, db):
    """
    Called when user replies to onboarding email 4 with their business description.
    Extracts info, updates business record, triggers the setup job, then sends email 5.
    """
    from agent.brain import brain
    from sqlalchemy import select, update
    from database.models import Business, User

    # Use Claude to extract structured info from their reply
    result = await brain.think(
        user_message=f"""Extract the following from this business description reply and return as JSON:
{{
  "description": "what the business sells",
  "target_audience": "who their customers are",
  "tone_of_voice": "brand personality",
  "upcoming_promotions": "any events or promotions mentioned"
}}

Reply text: {reply_text}""",
        context={}, business_id=business_id, db=None,
        model="claude-haiku-4-5-20251001"
    )

    import json
    try:
        extracted = json.loads(result.get("reasoning", "{}"))
    except Exception:
        extracted = {"description": reply_text[:500]}

    # Update business record
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

    # TODO Day 26-27: Run the setup job (generate first campaigns and content)
    # For now just send a "setting things up" email
    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    biz = biz_result.scalar_one_or_none()
    user_result = await db.execute(select(User).where(User.id == biz.owner_id))
    usr = user_result.scalar_one_or_none()

    from email_system.sender import email_sender
    await email_sender.send_onboarding_step(
        step=5,
        business_id=business_id,
        user_email=usr.email,
        first_name=(usr.full_name or "").split()[0] or "there",
        business_name=biz.name,
        db=db,
        extra_data={"campaigns": [], "posts": []}  # filled in on Day 26
    )