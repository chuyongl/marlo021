from fastapi import APIRouter, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import AsyncSessionLocal
from database.models import Business, User, EmailLog, UserPhoto, AgentAction
from sqlalchemy import select, desc
import base64, uuid, os, asyncio
from datetime import datetime
import httpx

router = APIRouter(prefix="/email", tags=["email-inbound"])


def clean_subject(text: str, max_len: int = 60) -> str:
    return " ".join(text[:max_len * 2].split())[:max_len]


async def load_conversation_history(business_id: str, db: AsyncSession) -> list:
    try:
        result = await db.execute(
            select(EmailLog)
            .where(
                EmailLog.business_id == business_id,
                EmailLog.email_type.in_([
                    "reply_response", "post_revision",
                    "photo_lifestyle_response", "post_approval"
                ])
            )
            .order_by(desc(EmailLog.sent_at))
            .limit(6)
        )
        logs = list(reversed(result.scalars().all()))
        history = []
        for log in logs:
            if log.reply_content:
                history.append({"role": "user", "content": log.reply_content[:500]})
            if log.subject:
                history.append({"role": "assistant", "content": f"[Sent: {log.subject}]"})
        return history[-6:]
    except Exception as e:
        print(f"[Inbound] load_conversation_history error: {e}")
        return []


async def save_user_message_to_log(business_id: str, user_message: str, db: AsyncSession):
    try:
        result = await db.execute(
            select(EmailLog)
            .where(
                EmailLog.business_id == business_id,
                EmailLog.email_type.in_([
                    "reply_response", "post_revision",
                    "photo_lifestyle_response", "post_approval",
                    "weekly_kickoff", "first_kickoff"
                ])
            )
            .order_by(desc(EmailLog.sent_at))
            .limit(1)
        )
        log = result.scalar_one_or_none()
        if log:
            log.reply_content = user_message[:1000]
            await db.commit()
    except Exception as e:
        print(f"[Inbound] save_user_message error (non-fatal): {e}")


@router.post("/inbound")
async def receive_inbound_email(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    text_body = payload.get("TextBody", "")
    attachments = payload.get("Attachments", [])
    to_full = payload.get("OriginalRecipient", payload.get("To", ""))
    business_id = extract_business_id_from_to(to_full)

    if not business_id or not text_body:
        return {"status": "ignored"}

    background_tasks.add_task(
        process_inbound_email,
        business_id=business_id,
        from_email=payload.get("From", "").lower(),
        text_body=text_body.strip(),
        attachments=attachments
    )
    return {"status": "received"}


def extract_business_id_from_to(to_address: str) -> str:
    try:
        local_part = to_address.split("@")[0]
        if "+" in local_part:
            candidate = local_part.split("+")[1]
            uuid.UUID(candidate)
            return candidate
    except Exception:
        pass
    return ""


async def process_inbound_email(business_id: str, from_email: str, text_body: str, attachments: list):
    async with AsyncSessionLocal() as db:
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalar_one_or_none()
        if not business:
            return

        user_result = await db.execute(select(User).where(User.id == business.owner_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        image_attachments = [a for a in attachments if a.get("ContentType", "").startswith("image/")]

        if image_attachments:
            await handle_photo_upload(business=business, user=user, attachments=image_attachments, message_text=text_body, db=db)
        else:
            await handle_text_reply(business=business, user=user, message=text_body, db=db)


async def handle_text_reply(business, user, message: str, db: AsyncSession):
    """
    Route inbound text replies.
    Key rule: if onboarding_completed=True, ALWAYS go to conversational reply
    regardless of onboarding_step value.
    """
    # Completed onboarding — always conversational
    if business.onboarding_completed:
        if "cancel my marlo021 subscription" in message.lower():
            await handle_cancellation(business=business, user=user, db=db)
            return
        await handle_conversational_reply(business=business, user=user, message=message, db=db)
        return

    # Still in onboarding
    if business.onboarding_step == 4:
        from email_system.onboarding_handler import process_onboarding_reply
        await process_onboarding_reply(str(business.id), message, db)
        return

    await handle_onboarding_question(business=business, user=user, message=message, db=db)


async def handle_conversational_reply(business, user, message: str, db: AsyncSession):
    from agent.reply_handler import handle_reply
    from agent.user_memory import load_memory, update_memory_async, initialize_memory_from_business
    from agent.vendor_profiles import detect_vendor_type_from_industry
    from email_system.sender import email_sender
    from email_system.templates import base_template, approve_button, decline_button

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

    business_dict = {
        "name": business.name,
        "industry": business.industry or "",
        "tone_of_voice": business.tone_of_voice or "warm and authentic",
        "target_audience": business.target_audience or "local customers",
        "description": business.description or "",
    }

    memory = load_memory(business)
    if not memory.get("vendor_type"):
        memory = await initialize_memory_from_business(business)

    vendor_type = memory.get("vendor_type") or detect_vendor_type_from_industry(business.industry or "")

    await save_user_message_to_log(str(business.id), message, db)
    conversation_history = await load_conversation_history(str(business.id), db)
    print(f"[Inbound] Loaded {len(conversation_history)} history messages")

    pending_action_dict = None
    pending_action = None
    try:
        action_result = await db.execute(
            select(AgentAction)
            .where(
                AgentAction.business_id == business.id,
                AgentAction.status == "pending",
                AgentAction.action_type.in_(["post_instagram", "post_facebook"]),
            )
            .order_by(desc(AgentAction.created_at))
            .limit(1)
        )
        pending_action = action_result.scalar_one_or_none()
        if pending_action:
            pending_action_dict = {
                "scheduled_day": pending_action.scheduled_day,
                "action_parameters": pending_action.action_parameters,
                "id": str(pending_action.id),
                "approval_token": pending_action.approval_token,
                "decline_token": pending_action.decline_token,
            }
    except Exception as e:
        print(f"[Inbound] Error loading pending action: {e}")

    result = await handle_reply(
        user_message=message,
        business=business_dict,
        memory=memory,
        vendor_type=vendor_type,
        pending_action=pending_action_dict,
        conversation_history=conversation_history,
    )

    response_text = result["response_text"]
    revised_post = result.get("revised_post")
    action_type = result.get("action_type", "conversation")

    asyncio.create_task(update_memory_async(
        business_id=str(business.id),
        user_message=message,
        assistant_response=result.get("raw_ai_response", response_text),
        current_memory=memory,
    ))

    if revised_post and action_type == "post_revision" and pending_action:
        params = dict(pending_action.action_parameters or {})
        params["caption"] = revised_post["full_caption"]
        params["hashtags"] = revised_post["hashtags"]
        pending_action.action_parameters = params
        await db.commit()

        approve_url = f"{base_url}/actions/approve?token={pending_action.approval_token}"
        decline_url = f"{base_url}/actions/decline?token={pending_action.decline_token}"

        html = base_template(f"""
        <p style="font-size:15px;color:#1F2937;margin:0 0 20px 0;">Here's your revised post:</p>
        <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:20px;margin-bottom:20px;">
          <p style="font-size:12px;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 12px 0;">
            📸 {pending_action.scheduled_day or 'Instagram'} post
          </p>
          <p style="font-size:14px;color:#1F2937;line-height:1.8;margin:0 0 8px 0;white-space:pre-wrap;">{revised_post['caption']}</p>
          {f'<p style="font-size:12px;color:#9CA3AF;margin:0 0 16px 0;">{" ".join(revised_post["hashtags"][:10])}</p>' if revised_post.get("hashtags") else ""}
          {approve_button("✓ Approve post", approve_url)}
          {decline_button("✗ Skip", decline_url)}
        </div>
        <p style="font-size:12px;color:#9CA3AF;margin:0;">{revised_post.get('follow_up', 'Want any changes? Just reply.')}</p>
        """)
        subject = f"Re: Your revised {pending_action.scheduled_day or 'Instagram'} post"

    elif revised_post and action_type == "new_post":
        # Generate image automatically
        image_url = None
        try:
            from integrations.image_gen import image_gen
            from agent.vendor_profiles import get_vendor_profile
            profile = get_vendor_profile(vendor_type)
            image_result = await image_gen.generate(
                subject=f"{revised_post['caption'][:200]} — {profile.image_style.mood}",
                business=business_dict,
                platform="instagram_feed",
            )
            image_url = image_result.get("url")
            print(f"[Inbound] Generated image: {image_url[:60] if image_url else 'None'}")
        except Exception as e:
            print(f"[Inbound] Image generation error (non-fatal): {e}")

        from agent.executor import executor
        action_dict = {
            "type": "create_post",
            "platform": "instagram",
            "parameters": {
                "caption": revised_post["full_caption"],
                "hashtags": revised_post["hashtags"],
                "image_url": image_url,
                "platform": "instagram",
            },
            "reasoning": f"User requested: {message[:100]}",
            "risk_level": "medium",
            "requires_approval": True,
        }
        enriched = await executor.create_pending_action_with_tokens(action_dict, str(business.id), db)
        approve_url = f"{base_url}/actions/approve?token={enriched['approval_token']}"
        decline_url = f"{base_url}/actions/decline?token={enriched['decline_token']}"

        image_html = (
            f'<img src="{image_url}" alt="Post image" style="width:100%;border-radius:8px;margin-bottom:12px;display:block;" />'
            if image_url else ""
        )

        html = base_template(f"""
        <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:20px;margin-bottom:20px;">
          {image_html}
          <p style="font-size:14px;color:#1F2937;line-height:1.8;margin:0 0 8px 0;white-space:pre-wrap;">{revised_post['caption']}</p>
          {f'<p style="font-size:12px;color:#9CA3AF;margin:0 0 16px 0;">{" ".join(revised_post["hashtags"][:10])}</p>' if revised_post.get("hashtags") else ""}
          {approve_button("✓ Approve & Schedule", approve_url)}
          {decline_button("✗ Skip", decline_url)}
        </div>
        <p style="font-size:12px;color:#9CA3AF;margin:0;">{revised_post.get('follow_up', 'Want any changes? Just reply.')}</p>
        """)
        subject = "Re: Your new post is ready"

    else:
        html = base_template(
            f'<p style="font-size:14px;color:#1F2937;line-height:1.8;">{response_text.replace(chr(10), "<br>")}</p>'
        )
        subject = f"Re: {clean_subject(message, 40)}"

    await email_sender.send(
        to_email=user.email,
        subject=subject,
        html_body=html,
        email_type="reply_response",
        business_id=str(business.id),
        db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )


async def handle_cancellation(business, user, db: AsyncSession):
    from email_system.sender import email_sender
    from email_system.templates import base_template
    first_name = (user.full_name or "there").split()[0]
    html = base_template(f"""
    <p style="font-size:16px;font-weight:600;color:#1F2937;margin:0 0 8px 0;">Got it, {first_name}.</p>
    <p style="font-size:14px;color:#6B7280;margin:0 0 16px 0;line-height:1.7;">
      Your subscription will be cancelled. You'll keep access until the end of your billing period.
      If you change your mind, reply within 24 hours.
    </p>
    """)
    await email_sender.send(
        to_email=user.email, subject="Your Marlo subscription cancellation",
        html_body=html, email_type="cancellation",
        business_id=str(business.id), db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )


async def handle_onboarding_question(business, user, message: str, db: AsyncSession):
    from agent.brain import brain
    from email_system.sender import email_sender
    from email_system.templates import base_template
    frontend_url = os.getenv("FRONTEND_URL", "https://marlo021.ai")
    step = business.onboarding_step
    step_context = {
        1: "User just signed up. Needs to connect Google Ads.",
        2: "Connected Google. Needs to connect Instagram.",
        3: "Connected Instagram. Needs to connect Mailchimp.",
    }.get(step, "User is in the middle of setup.")

    result = await brain.think(
        user_message=message,
        context={"step": step_context},
        business_id=str(business.id),
        db=None, model="claude-haiku-4-5-20251001"
    )
    reply_text = result.get("summary", "Happy to help! Just reply with your question.")
    html = base_template(f"""
    <p style="font-size:14px;color:#374151;line-height:1.7;margin:0 0 16px 0;">{reply_text}</p>
    <p style="font-size:13px;color:#6B7280;margin:0;">
      Still stuck? <a href="{frontend_url}/help" style="color:#2563EB;">Visit our help page</a>
    </p>
    """)
    await email_sender.send(
        to_email=user.email, subject="Re: your Marlo setup question",
        html_body=html, email_type="onboarding_reply",
        business_id=str(business.id), db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )


async def handle_photo_upload(business, user, attachments: list, message_text: str, db: AsyncSession):
    import io
    from PIL import Image
    from integrations.image_gen import image_gen
    from agent.user_memory import load_memory, initialize_memory_from_business
    from agent.vendor_profiles import detect_vendor_type_from_industry, get_vendor_profile
    from agent.reply_handler import handle_reply

    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    attachment = attachments[0]
    image_data = base64.b64decode(attachment.get("Content", ""))
    temp_dir = os.environ.get("TEMP", "/tmp")
    temp_path = os.path.join(temp_dir, f"marlo_upload_{uuid.uuid4().hex}.jpg")

    try:
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        img.save(temp_path, "JPEG", quality=95)
        upload_result = await image_gen.upload_image(temp_path)
        original_url = upload_result.get("url", "")
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

    if not original_url:
        return

    memory = load_memory(business)
    if not memory.get("vendor_type"):
        memory = await initialize_memory_from_business(business)

    vendor_type = memory.get("vendor_type") or detect_vendor_type_from_industry(business.industry or "")
    business_dict = {
        "name": business.name, "industry": business.industry or "",
        "tone_of_voice": business.tone_of_voice or "warm and authentic",
        "target_audience": business.target_audience or "local customers",
        "description": business.description or "",
    }

    caption_context = message_text.strip() if len(message_text.strip()) > 5 else ""

    lifestyle_result = await image_gen.generate_lifestyle_from_product(
        product_image_url=original_url, business=business_dict,
        caption=caption_context, platform="instagram_feed", vendor_type=vendor_type,
    )
    lifestyle_url = lifestyle_result.get("url")
    if not lifestyle_url:
        lifestyle_url = await image_gen.enhance_photo(original_url)

    reply_result = await handle_reply(
        user_message=f"Write an Instagram caption for this product photo. Context: {caption_context or 'product showcase'}",
        business=business_dict, memory=memory, vendor_type=vendor_type,
    )

    import random
    profile = get_vendor_profile(vendor_type)
    hashtag_pool = [tag for cluster in profile.hashtag_clusters for tag in cluster]
    hashtags = random.sample(hashtag_pool, min(10, len(hashtag_pool)))

    revised_post = reply_result.get("revised_post")
    caption = revised_post["caption"] if revised_post else reply_result["response_text"][:300]
    full_caption = f"{caption}\n\n{' '.join(hashtags)}"

    photo = UserPhoto(
        id=uuid.uuid4(), business_id=business.id,
        original_url=original_url, enhanced_url=lifestyle_url,
        instagram_url=lifestyle_url, caption_instagram=caption,
        status="pending", created_at=datetime.utcnow()
    )
    db.add(photo)
    await db.commit()

    from agent.executor import executor
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    action_dict = {
        "type": "create_post", "platform": "instagram",
        "parameters": {
            "caption": full_caption, "image_url": lifestyle_url,
            "platform": "instagram", "hashtags": hashtags,
            "photo_id": str(photo.id), "original_url": original_url,
        },
        "reasoning": "User sent a product photo",
        "risk_level": "medium", "requires_approval": True,
    }
    enriched = await executor.create_pending_action_with_tokens(action_dict, str(business.id), db)
    approve_url = f"{base_url}/actions/approve?token={enriched['approval_token']}"
    decline_url = f"{base_url}/actions/decline?token={enriched['decline_token']}"

    from email_system.sender import email_sender
    from email_system.templates import base_template, approve_button, decline_button
    first_name = (user.full_name or "there").split()[0]

    html = base_template(f"""
    <p style="font-size:16px;font-weight:600;color:#1F2937;margin:0 0 8px 0;">
      📸 Your photo is ready, {first_name}!
    </p>
    <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:20px;margin-bottom:16px;">
      <img src="{lifestyle_url}" alt="Generated lifestyle image"
           style="width:100%;border-radius:8px;margin-bottom:16px;display:block;" />
      <p style="font-size:14px;color:#1F2937;line-height:1.7;margin:0 0 8px 0;">{caption}</p>
      <p style="font-size:12px;color:#9CA3AF;margin:0 0 16px 0;">{' '.join(hashtags[:8])}</p>
      <div style="background:#F9FAFB;border-radius:6px;padding:10px 12px;margin-bottom:16px;">
        <p style="font-size:12px;color:#6B7280;margin:0;line-height:1.6;">
          ✏️ Want a different caption? Reply with your instructions.<br>
          🔄 Want a different image? Reply: "Try different style: [your idea]"
        </p>
      </div>
      {approve_button("✓ Post to Instagram", approve_url)}
      {decline_button("✗ Skip", decline_url)}
    </div>
    <details style="margin-top:12px;">
      <summary style="font-size:12px;color:#9CA3AF;cursor:pointer;">See original photo</summary>
      <img src="{original_url}" alt="Original" style="width:100%;max-width:300px;border-radius:6px;margin-top:8px;opacity:0.7;" />
    </details>
    """)

    await email_sender.send(
        to_email=user.email,
        subject="📸 Your lifestyle photo is ready — approve to post",
        html_body=html, email_type="photo_lifestyle_response",
        business_id=str(business.id), db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )