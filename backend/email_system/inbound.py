from fastapi import APIRouter, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import AsyncSessionLocal
from database.models import Business, User, EmailLog, UserPhoto
from sqlalchemy import select
import json, base64, uuid, os
from datetime import datetime
import httpx

router = APIRouter(prefix="/email", tags=["email-inbound"])

@router.post("/inbound")
async def receive_inbound_email(request: Request, background_tasks: BackgroundTasks):
    """
    Postmark sends a JSON payload here whenever someone replies to a Marlo email.
    We parse it and hand off to the agent in the background.
    """
    payload = await request.json()

    from_email = payload.get("From", "").lower()
    subject = payload.get("Subject", "")
    text_body = payload.get("TextBody", "")
    html_body = payload.get("HtmlBody", "")
    attachments = payload.get("Attachments", [])

    to_full = payload.get("OriginalRecipient", payload.get("To", ""))
    business_id = extract_business_id_from_to(to_full)

    if not business_id or not text_body:
        return {"status": "ignored"}

    background_tasks.add_task(
        process_inbound_email,
        business_id=business_id,
        from_email=from_email,
        text_body=text_body.strip(),
        attachments=attachments
    )
    return {"status": "received"}

def extract_business_id_from_to(to_address: str) -> str:
    """Extract business ID from reply+BUSINESS_ID@domain format.
    Returns empty string if not found or not a valid UUID.
    """
    try:
        local_part = to_address.split("@")[0]
        if "+" in local_part:
            candidate = local_part.split("+")[1]
            uuid.UUID(candidate)  # raises ValueError if not a valid UUID
            return candidate
    except Exception:
        pass
    return ""

async def process_inbound_email(
    business_id: str,
    from_email: str,
    text_body: str,
    attachments: list
):
    async with AsyncSessionLocal() as db:
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalar_one_or_none()
        if not business:
            return

        user_result = await db.execute(select(User).where(User.id == business.owner_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        image_attachments = [
            a for a in attachments
            if a.get("ContentType", "").startswith("image/")
        ]

        if image_attachments:
            await handle_photo_upload(
                business=business,
                user=user,
                attachments=image_attachments,
                message_text=text_body,
                db=db
            )
        else:
            await handle_text_reply(
                business=business,
                user=user,
                message=text_body,
                db=db
            )

async def handle_text_reply(business, user, message: str, db: AsyncSession):
    """Process a plain-text reply — route to onboarding handler or main agent."""
    from email_system.sender import email_sender

    first_name = (user.full_name or "there").split()[0]

    # Step 4: collect business info
    if business.onboarding_step == 4:
        from email_system.onboarding_handler import process_onboarding_reply
        await process_onboarding_reply(str(business.id), message, db)
        return

    # Steps 1-3: still in onboarding — answer setup questions with lightweight AI
    if business.onboarding_step < 4:
        await handle_onboarding_question(
            business=business,
            user=user,
            first_name=first_name,
            message=message,
            db=db
        )
        return

    # Step 5+: fully onboarded — use the full agent brain
    # Check if this is a post revision instruction first
    lower_msg = message.lower()
    revision_days = ["monday", "wednesday", "friday", "tuesday", "thursday", "saturday", "sunday"]
    is_revision = any(
        f"change {day}" in lower_msg or f"edit {day}" in lower_msg or f"rewrite {day}" in lower_msg
        for day in revision_days
    )

    if is_revision:
        await handle_post_revision(
            business=business,
            user=user,
            message=message,
            db=db
        )
        return
    from agent.brain import brain
    from agent.executor import executor

    # Try to build full context, fall back to basic context if module missing
    try:
        from agent.context_builder import context_builder
        context = await context_builder.build_full_context(str(business.id), db)
    except (ImportError, Exception):
        context = {
            "business_name": business.name,
            "industry": business.industry,
            "description": business.description or "",
            "target_audience": business.target_audience or "",
            "tone_of_voice": business.tone_of_voice or "",
            "monthly_ad_budget": str(business.monthly_ad_budget or 300),
        }

    result = await brain.think(
        user_message=message,
        context=context,
        business_id=str(business.id),
        db=db
    )

    monthly_budget = float(business.monthly_ad_budget or 300)
    pending_actions = []

    for action in result.get("actions", []):
        if action.get("requires_approval") or action.get("risk_level") in ("medium", "high"):
            enriched = await executor.create_pending_action_with_tokens(
                action, str(business.id), db
            )
            pending_actions.append(enriched)
        else:
            await executor.execute_action(action, str(business.id), monthly_budget, db)

    summary = result.get("summary", "Done!")

    if pending_actions:
        from email_system.templates import base_template, approve_button, decline_button
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        actions_html = f'<p style="font-size:15px;color:#1F2937;margin:0 0 20px 0;">{summary}</p>'
        for a in pending_actions:
            approve_url = f"{base_url}/actions/approve?token={a['approval_token']}"
            decline_url = f"{base_url}/actions/decline?token={a['decline_token']}"
            actions_html += f"""
            <div style="margin-bottom:20px;">
              <p style="font-size:14px;font-weight:600;color:#1F2937;margin:0 0 6px 0;">{a['title']}</p>
              <p style="font-size:13px;color:#6B7280;margin:0 0 12px 0;">{a['description']}</p>
              {approve_button("✓ Approve", approve_url)}
              {decline_button("✗ Decline", decline_url)}
            </div>"""
        html = base_template(actions_html)
        subject = f"Re: {summary[:60]}"
    else:
        from email_system.templates import base_template
        html = base_template(f'<p style="font-size:15px;color:#1F2937;">{summary}</p>')
        subject = f"Re: {summary[:50]}"

    await email_sender.send(
        to_email=user.email,
        subject=subject,
        html_body=html,
        email_type="reply_response",
        business_id=str(business.id),
        db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )


async def handle_onboarding_question(business, user, first_name: str, message: str, db: AsyncSession):
    """Handle replies during onboarding steps 1-3 with lightweight AI."""
    from agent.brain import brain
    from email_system.sender import email_sender
    from email_system.templates import base_template

    frontend_url = os.getenv("FRONTEND_URL", "https://marlo021.ai")
    step = business.onboarding_step

    step_context = {
        1: "The user is setting up Marlo and has just signed up. They need to connect Google Ads next.",
        2: "The user has connected Google. They now need to connect Facebook & Instagram.",
        3: "The user has connected Google and Instagram. They now need to connect Mailchimp.",
    }.get(step, "The user is in the middle of setting up Marlo.")

    system_prompt = f"""You are Marlo, a friendly AI marketing assistant helping a small business owner set up their account.

{step_context}

The user has replied to a setup email with a question or message. Answer helpfully and concisely.
Keep your reply short (2-4 sentences max). Be warm and encouraging.
If they're asking about why they need a Facebook Page, explain: Meta requires Instagram Business accounts to be linked to a Facebook Page before any third-party tool can post. The Page just needs to exist — it doesn't need posts or followers.
If they're asking why they need a Business Instagram account: Instagram only allows third-party tools to post to Business or Creator accounts, not personal ones. Switching is free and keeps all their posts and followers.
If they seem stuck or frustrated, reassure them and point them to: {frontend_url}/help
Always end with a clear next action for them to take."""

    result = await brain.think(
        user_message=message,
        context={"system_override": system_prompt},
        business_id=str(business.id),
        db=None,
        model="claude-haiku-4-5-20251001"
    )

    reply_text = result.get("summary", "Happy to help! If you're stuck, just reply with your question and I'll walk you through it.")

    html = base_template(f"""
    <p style="font-size:15px;color:#1F2937;margin:0 0 16px 0;">Hi {first_name}!</p>
    <p style="font-size:14px;color:#374151;line-height:1.7;margin:0 0 16px 0;">{reply_text}</p>
    <p style="font-size:13px;color:#6B7280;margin:0;">
      Still stuck? Visit <a href="{frontend_url}/help" style="color:#2563EB;">{frontend_url}/help</a>
      or just reply again and I'll help.
    </p>
    """)

    await email_sender.send(
        to_email=user.email,
        subject="Re: your Marlo setup question",
        html_body=html,
        email_type="onboarding_reply",
        business_id=str(business.id),
        db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )


async def handle_post_revision(business, user, message: str, db: AsyncSession):
    """Handle 'Change Monday post: make it funnier' style revision requests."""
    from agent.brain import brain
    from email_system.sender import email_sender
    from email_system.templates import base_template, approve_button, decline_button
    import os

    frontend_url = os.getenv("FRONTEND_URL", "https://marlo021.ai")
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    first_name = (user.full_name or "there").split()[0]

    business_dict = {
        "name": business.name,
        "industry": business.industry or "",
        "tone_of_voice": business.tone_of_voice or "warm and authentic",
        "target_audience": business.target_audience or "local customers",
        "description": business.description or "",
    }

    # Generate revised post
    revision_prompt = f"""A business owner wants to revise an Instagram post.

Business: {business.name}
Industry: {business_dict['industry']}
Brand tone: {business_dict['tone_of_voice']}
Target audience: {business_dict['target_audience']}

Their revision request: "{message}"

Write a revised ready-to-post Instagram caption that addresses their feedback.
Then write 8-10 relevant hashtags separately.

Return ONLY this format:
CAPTION:
[the caption here]

HASHTAGS:
[hashtags here]"""

    raw = await brain.generate_content(
        content_type="revised Instagram post",
        business=business_dict,
        context={},
        instructions=revision_prompt
    )

    # Parse caption and hashtags
    caption = raw.strip()
    hashtags_text = ""
    if "HASHTAGS:" in raw.upper():
        parts = raw.upper().split("HASHTAGS:")
        caption_part = raw[:raw.upper().find("HASHTAGS:")].strip()
        if "CAPTION:" in caption_part.upper():
            caption = caption_part[caption_part.upper().find("CAPTION:") + 8:].strip()
        else:
            caption = caption_part.strip()
        hashtags_text = raw[raw.upper().find("HASHTAGS:") + 9:].strip()
    elif "CAPTION:" in raw.upper():
        caption = raw[raw.upper().find("CAPTION:") + 8:].strip()

    # Create a pending action for the revised post
    from agent.executor import executor
    action = {
        "type": "create_post",
        "platform": "instagram",
        "parameters": {
            "caption": f"{caption}\n\n{hashtags_text}" if hashtags_text else caption,
            "platform": "instagram",
        },
        "reasoning": f"Revised post per owner request: {message[:100]}",
        "risk_level": "medium",
        "requires_approval": True
    }
    enriched = await executor.create_pending_action_with_tokens(
        action, str(business.id), db
    )
    approve_url = f"{base_url}/actions/approve?token={enriched['approval_token']}"
    decline_url = f"{base_url}/actions/decline?token={enriched['decline_token']}"

    html = base_template(f"""
    <p style="font-size:16px;font-weight:600;color:#1F2937;margin:0 0 8px 0;">
      ✏️ Here's your revised post, {first_name}!
    </p>
    <p style="font-size:13px;color:#6B7280;margin:0 0 20px 0;">
      Based on: <em>"{message[:80]}{'...' if len(message) > 80 else ''}"</em>
    </p>

    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:20px;margin-bottom:20px;">
      <p style="font-size:13px;font-weight:600;color:#374151;margin:0 0 10px 0;">📸 Revised Instagram post</p>
      <p style="font-size:14px;color:#1F2937;line-height:1.8;margin:0 0 8px 0;white-space:pre-wrap;">{caption}</p>
      {f'<p style="font-size:12px;color:#9CA3AF;margin:0;">{hashtags_text}</p>' if hashtags_text else ''}
    </div>

    <div style="background:#EFF6FF;border-radius:6px;padding:12px 14px;margin-bottom:20px;">
      <p style="font-size:12px;color:#1D4ED8;margin:0;line-height:1.6;">
        Still not right? Reply again with more instructions and I'll revise further.
      </p>
    </div>

    {approve_button("✓ Approve & Schedule", approve_url)}
    {decline_button("✗ Skip", decline_url)}
    """)

    await email_sender.send(
        to_email=user.email,
        subject=f"Re: Your revised post is ready",
        html_body=html,
        email_type="post_revision",
        business_id=str(business.id),
        db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )


async def handle_photo_upload(business, user, attachments: list, message_text: str, db: AsyncSession):
    """Process a photo sent via email attachment."""
    import io
    from PIL import Image
    import pillow_heif

    pillow_heif.register_heif_opener()

    attachment = attachments[0]
    image_data = base64.b64decode(attachment.get("Content", ""))

    from integrations.image_gen import image_gen

    temp_dir = os.environ.get("TEMP", "/tmp")
    temp_path = os.path.join(temp_dir, f"marlo_upload_{uuid.uuid4().hex}.jpg")

    img = Image.open(io.BytesIO(image_data))
    img = img.convert("RGB")
    img.save(temp_path, "JPEG", quality=95)

    upload_result = await image_gen.upload_image(temp_path)
    original_url = upload_result.get("url", "")
    enhanced_url = await image_gen.enhance_photo(original_url)

    business_dict = {
        "name": business.name, "industry": business.industry,
        "description": business.description, "tone_of_voice": business.tone_of_voice,
        "target_audience": business.target_audience
    }

    caption_hint = message_text if len(message_text) > 5 else ""
    platform_results = await image_gen.prepare_photo_for_platforms(
        enhanced_url, business_dict, caption_hint=caption_hint
    )

    photo = UserPhoto(
        id=uuid.uuid4(),
        business_id=business.id,
        original_url=original_url,
        enhanced_url=enhanced_url,
        instagram_url=platform_results.get("instagram_feed", {}).get("url"),
        story_url=platform_results.get("instagram_story", {}).get("url"),
        facebook_url=platform_results.get("facebook_feed", {}).get("url"),
        google_display_url=platform_results.get("google_display", {}).get("url"),
        caption_instagram=platform_results.get("instagram_feed", {}).get("caption"),
        caption_facebook=platform_results.get("facebook_feed", {}).get("caption"),
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(photo)
    await db.commit()

    from agent.executor import executor
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    platform_previews = []

    for platform_key, platform_data in platform_results.items():
        if platform_data.get("url"):
            action = {
                "type": "create_post",
                "platform": platform_key.split("_")[0],
                "parameters": {
                    "image_url": platform_data["url"],
                    "caption": platform_data.get("caption", ""),
                    "platform_key": platform_key,
                    "photo_id": str(photo.id)
                },
                "reasoning": f"User sent a photo — posting to {platform_key.replace('_', ' ')}",
                "risk_level": "medium",
                "requires_approval": True
            }
            enriched = await executor.create_pending_action_with_tokens(
                action, str(business.id), db
            )
            platform_previews.append({
                "platform_label": platform_key.replace("_", " ").title(),
                "caption": platform_data.get("caption", ""),
                "image_url": platform_data["url"],
                "approve_url": f"{base_url}/actions/approve?token={enriched['approval_token']}"
            })

    from email_system.sender import email_sender
    from email_system.templates import photo_response_template

    first_name = (user.full_name or "there").split()[0]
    html = photo_response_template(first_name, "", platform_previews, base_url)

    await email_sender.send(
        to_email=user.email,
        subject="📸 Your photo is ready — approve to post",
        html_body=html,
        email_type="photo_response",
        business_id=str(business.id),
        db=db
    )

    try:
        os.remove(temp_path)
    except Exception:
        pass