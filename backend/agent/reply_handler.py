"""
reply_handler.py

Two-step approach:
1. classify_intent() — Haiku, fast, cheap. Determines what user wants.
2. handle_reply() — Sonnet, generates the right response for that intent.

Intent types:
- post_request: user gave content to turn into a post, or asked to write one
- post_revision: user wants to change an existing pending post
- conversation: question, feedback, or chat — no post needed
"""

import anthropic
import os
import json

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ─── Step 1: Intent Classification ────────────────────────────────────────────

CLASSIFY_PROMPT = """You classify what a user wants in one word.

INTENT OPTIONS:
- post_request: user provided content/story/notes to turn into a post, OR asked to write/create a post about something
- post_revision: user wants to change an existing post (make it X, change Y, edit Z, rewrite it)
- conversation: question, feedback, general chat, anything else

EXAMPLES:
"use my message as the post" → post_request
"This week we hit a milestone..." (long text) → post_request
"Make it less salesy" → post_revision
"Change the tone to be more personal" → post_revision
"Rewrite this using my content: [content]" → post_request
"What time does my post go live?" → conversation
"Can you help me with Mailchimp?" → conversation
"Make the caption shorter" → post_revision
"I want to post about our new product launch" → post_request

Respond with ONLY one of: post_request, post_revision, conversation"""


async def classify_intent(user_message: str, has_pending_action: bool) -> str:
    """Classify user intent using Haiku. Fast and cheap."""
    try:
        context = f"User has a pending post waiting for approval: {has_pending_action}\n\nUser message: {user_message[:500]}"
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content": f"{CLASSIFY_PROMPT}\n\n{context}"}]
        )
        intent = response.content[0].text.strip().lower()
        if intent not in ("post_request", "post_revision", "conversation"):
            intent = "post_request" if len(user_message) > 100 else "conversation"
        print(f"[ReplyHandler] Intent: {intent}")
        return intent
    except Exception as e:
        print(f"[ReplyHandler] classify_intent error: {e}")
        # Fallback: long messages are probably post requests
        return "post_request" if len(user_message) > 100 else "conversation"


# ─── Step 2: Generate Response ─────────────────────────────────────────────────

POST_GENERATION_PROMPT = """You are Marlo, a marketing assistant. Generate an Instagram post.

RULES:
- Use the user's content, voice, and story directly
- Keep their authentic message — clean up spelling/grammar only
- Match the vendor's caption style
- ALWAYS use this exact format, no exceptions:

POST:
[caption only — no hashtags]

HASHTAGS:
[hashtags on one line]

FOLLOW_UP:
[one sentence: "Want any changes? Just reply." or a specific question if needed]"""

POST_REVISION_PROMPT = """You are Marlo, a marketing assistant. Revise the existing post based on user instructions.

RULES:
- Apply the user's instruction to the existing post
- Keep the core message, just change what they asked
- ALWAYS use this exact format, no exceptions:

POST:
[revised caption — no hashtags]

HASHTAGS:
[hashtags on one line]

FOLLOW_UP:
[one sentence: "Want any changes? Just reply."]"""

CONVERSATION_PROMPT = """You are Marlo, a helpful marketing assistant.
Answer naturally in 2-4 sentences. Be direct and helpful.
Do NOT generate a post. Just answer the question or respond to the message."""


async def handle_reply(
    user_message: str,
    business: dict,
    memory: dict,
    vendor_type: str = None,
    pending_action: dict = None,
) -> dict:
    """
    Main entry point. Classifies intent then generates appropriate response.

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

    # Safety check first
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
    memory_context = format_for_prompt(memory)

    # Classify intent
    intent = await classify_intent(user_message, has_pending_action=pending_action is not None)

    # Build context block
    context_block = f"""BUSINESS:
Name: {business.get('name', '')}
Industry: {business.get('industry', '')}
Tone: {business.get('tone_of_voice', 'warm and authentic')}
Audience: {business.get('target_audience', '')}
Vendor type: {profile.display_name}
Caption style: {profile.caption_tone}

USER MEMORY:
{memory_context}"""

    if pending_action and intent == "post_revision":
        params = pending_action.get("action_parameters") or pending_action.get("parameters", {})
        caption = params.get("caption", "")
        caption_clean = caption.split("\n\n#")[0] if "\n\n#" in caption else caption
        context_block += f"""

EXISTING POST TO REVISE:
Day: {pending_action.get('scheduled_day', '')}
Current caption: {caption_clean[:400]}"""

    # Select system prompt based on intent
    if intent == "post_request":
        system_prompt = POST_GENERATION_PROMPT
        action_type_if_post = "new_post"
    elif intent == "post_revision":
        system_prompt = POST_REVISION_PROMPT
        action_type_if_post = "post_revision"
    else:
        system_prompt = CONVERSATION_PROMPT
        action_type_if_post = "conversation"

    messages = [{
        "role": "user",
        "content": f"{context_block}\n\nUser message: {user_message}"
    }]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
        messages=messages,
    )

    raw_response = response.content[0].text.strip()
    print(f"[ReplyHandler] Raw response preview: {raw_response[:100]}")

    # Parse post if intent was post-related
    revised_post = None
    action_type = "conversation"

    if intent in ("post_request", "post_revision") and "POST:" in raw_response:
        action_type = action_type_if_post
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

            # Clean email response text
            email_lines = ["Here's your post:\n", caption]
            if hashtags:
                email_lines.append(f"\n{' '.join(hashtags[:10])}")
            email_lines.append(f"\n\n{follow_up}")
            raw_response = "\n".join(email_lines)

        except Exception as e:
            print(f"[ReplyHandler] Post parse error: {e}")
            action_type = "conversation"

    elif intent in ("post_request", "post_revision") and "POST:" not in raw_response:
        # AI didn't follow format — log it and treat as conversation
        print(f"[ReplyHandler] WARNING: intent was {intent} but AI didn't use POST: format")
        action_type = "conversation"

    return {
        "response_text": raw_response,
        "revised_post": revised_post,
        "action_type": action_type,
        "raw_ai_response": response.content[0].text,
    }