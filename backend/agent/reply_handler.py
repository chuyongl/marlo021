"""
reply_handler.py

Handles all user email replies with:
- User memory (compact knowledge base — not raw history)
- Vendor-aware content generation
- User-first execution (do first, ask later — never ask more than one question)
- Content safety filtering
"""

import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


REPLY_SYSTEM_PROMPT = """You are Marlo, a helpful marketing assistant for small businesses.

YOUR JOB:
The user has replied to a marketing email. Read what they want and DO IT immediately.

CORE RULES:
1. EXECUTE FIRST. If you have enough to act, act now.
2. NEVER ask more than one question. Ever.
3. Talk TO the user directly. Never use third person ("Anna wants...").
4. Match their energy. Casual = casual. Detailed = detailed.
5. Keep responses SHORT unless delivering a post.
6. Their raw notes, story, or content = USE IT DIRECTLY. Don't ask permission.

═══════════════════════════════════════
CRITICAL: WHEN TO USE THE POST FORMAT
═══════════════════════════════════════
Use the POST format whenever:
- User asks to rewrite, modify, or change a post
- User asks you to "make it" something (less salesy, funnier, more personal, etc.)
- User gives you their own content and says "use this" or "make this a post"
- User provides a story or update and you need to turn it into a post
- You are creating any new Instagram/social media content

The POST format is MANDATORY for any post content. Never put post content in plain text.

POST FORMAT — use EXACTLY this structure with no deviations:
POST:
[caption only, no hashtags here]

HASHTAGS:
[hashtags on one line]

FOLLOW_UP:
[one short sentence max — "Want any changes? Just reply." unless you have a specific question]

═══════════════════════════════════════
FOR EVERYTHING ELSE (questions, info):
═══════════════════════════════════════
Answer naturally in 2-4 sentences. No special format needed.
"""


async def handle_reply(
    user_message: str,
    business: dict,
    memory: dict,
    vendor_type: str = None,
    pending_action: dict = None,
) -> dict:
    """
    Handle a user's email reply.

    Returns:
        {
            "response_text": str,
            "revised_post": dict or None,
            "action_type": "post_revision" | "new_post" | "conversation" | "safety_block",
            "raw_ai_response": str,
        }
    """
    from agent.content_safety import check_content_safety, get_safe_redirect_message
    from agent.vendor_profiles import get_vendor_profile, detect_vendor_type_from_industry
    from agent.user_memory import format_for_prompt

    # Safety check
    safety = await check_content_safety(user_message)
    if safety.get("blocked"):
        return {
            "response_text": get_safe_redirect_message(),
            "revised_post": None,
            "action_type": "safety_block",
            "raw_ai_response": "",
        }

    # Vendor profile
    if not vendor_type:
        vendor_type = memory.get("vendor_type") or detect_vendor_type_from_industry(
            business.get("industry", "")
        )
    profile = get_vendor_profile(vendor_type)

    # Compact context block (~200 tokens)
    memory_context = format_for_prompt(memory)

    context_block = f"""BUSINESS:
Name: {business.get('name', '')}
Industry: {business.get('industry', '')}
Tone: {business.get('tone_of_voice', 'warm and authentic')}
Audience: {business.get('target_audience', '')}
Vendor type: {profile.display_name}
Caption style: {profile.caption_tone}

USER MEMORY:
{memory_context}"""

    if pending_action:
        params = pending_action.get("action_parameters") or pending_action.get("parameters", {})
        caption = params.get("caption", "")
        caption_clean = caption.split("\n\n#")[0] if "\n\n#" in caption else caption
        context_block += f"""

CURRENT PENDING POST:
Day: {pending_action.get('scheduled_day', '')}
Caption: {caption_clean[:300]}"""

    messages = [{
        "role": "user",
        "content": f"{context_block}\n\nUser message: {user_message}"
    }]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=REPLY_SYSTEM_PROMPT,
        messages=messages,
    )

    raw_response = response.content[0].text.strip()

    # Parse post if present
    revised_post = None
    action_type = "conversation"

    if "POST:" in raw_response:
        action_type = "post_revision" if pending_action else "new_post"
        try:
            post_section = raw_response.split("POST:")[1]
            caption = ""
            hashtags_text = ""
            follow_up = "Want any changes? Just reply."

            if "HASHTAGS:" in post_section:
                caption = post_section.split("HASHTAGS:")[0].strip()
                rest = post_section.split("HASHTAGS:")[1]
                if "FOLLOW_UP:" in rest:
                    hashtags_text = rest.split("FOLLOW_UP:")[0].strip()
                    follow_up = rest.split("FOLLOW_UP:")[1].strip()
                else:
                    hashtags_text = rest.strip()
            else:
                caption = post_section.strip()

            hashtags = [
                t.strip() for t in hashtags_text.replace(",", " ").split()
                if t.strip().startswith("#")
            ]

            revised_post = {
                "caption": caption,
                "hashtags": hashtags,
                "full_caption": f"{caption}\n\n{' '.join(hashtags)}" if hashtags else caption,
                "follow_up": follow_up,
            }

            # Clean email response
            email_lines = ["Here's your revised post:\n", caption]
            if hashtags:
                email_lines.append(f"\n{' '.join(hashtags[:10])}")
            email_lines.append(f"\n\n{follow_up}")
            raw_response = "\n".join(email_lines)

        except Exception as e:
            print(f"[ReplyHandler] Post parse error: {e}")
            action_type = "conversation"

    return {
        "response_text": raw_response,
        "revised_post": revised_post,
        "action_type": action_type,
        "raw_ai_response": response.content[0].text,
    }