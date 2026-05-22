"""
reply_handler.py

Two-step approach:
1. classify_intent() — Haiku, fast, cheap
2. handle_reply() — Sonnet, generates response with conversation history

conversation_history format:
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."},
]
Max 3 exchanges (6 messages) to keep tokens manageable.
"""

import anthropic
import os

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
"use what I told you" → post_request
"that content I shared earlier" → post_request

Respond with ONLY one of: post_request, post_revision, conversation"""


async def classify_intent(
    user_message: str,
    has_pending_action: bool,
    conversation_history: list = None
) -> str:
    """Classify user intent using Haiku. Includes recent history for context."""
    try:
        history_context = ""
        if conversation_history:
            recent = conversation_history[-4:]  # last 2 exchanges
            lines = []
            for msg in recent:
                role = "User" if msg["role"] == "user" else "Marlo"
                lines.append(f"{role}: {msg['content'][:150]}")
            history_context = "\n\nRECENT CONVERSATION:\n" + "\n".join(lines)

        context = (
            f"User has a pending post waiting for approval: {has_pending_action}"
            f"{history_context}"
            f"\n\nNew user message: {user_message[:500]}"
        )
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
        return "post_request" if len(user_message) > 100 else "conversation"


# ─── Step 2: Generate Response ─────────────────────────────────────────────────

POST_GENERATION_PROMPT = """You are Marlo, a marketing assistant. Generate an Instagram post.

RULES:
- Use the user's content, voice, and story directly
- If user says "use what I said" or "use my content" — look at the conversation history for their content
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
    conversation_history: list = None,
) -> dict:
    """
    Main entry point. Classifies intent then generates appropriate response.

    Args:
        conversation_history: list of {"role": "user"/"assistant", "content": str}
                              last 3 exchanges max, loaded from EmailLog

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

    conversation_history = conversation_history or []

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
    memory_context = format_for_prompt(memory)

    # Classify intent (with history for context)
    intent = await classify_intent(
        user_message,
        has_pending_action=pending_action is not None,
        conversation_history=conversation_history
    )

    # Build system context block
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

    # Select system prompt
    if intent == "post_request":
        system_prompt = POST_GENERATION_PROMPT
        action_type_if_post = "new_post"
    elif intent == "post_revision":
        system_prompt = POST_REVISION_PROMPT
        action_type_if_post = "post_revision"
    else:
        system_prompt = CONVERSATION_PROMPT
        action_type_if_post = "conversation"

    # Build messages with conversation history
    messages = []

    # Add context as first user message (system context)
    messages.append({
        "role": "user",
        "content": f"[CONTEXT]\n{context_block}\n[/CONTEXT]\n\nReady."
    })
    messages.append({
        "role": "assistant",
        "content": "Got it. What do you need?"
    })

    # Add conversation history (last 3 exchanges = 6 messages)
    for msg in conversation_history[-6:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"][:500]  # truncate long messages
        })

    # Add current message
    messages.append({
        "role": "user",
        "content": user_message
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
        messages=messages,
    )

    raw_response = response.content[0].text.strip()
    print(f"[ReplyHandler] Intent={intent} | Response preview: {raw_response[:80]}")

    # Parse post
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

            email_lines = ["Here's your post:\n", caption]
            if hashtags:
                email_lines.append(f"\n{' '.join(hashtags[:10])}")
            email_lines.append(f"\n\n{follow_up}")
            raw_response = "\n".join(email_lines)

        except Exception as e:
            print(f"[ReplyHandler] Post parse error: {e}")
            action_type = "conversation"

    elif intent in ("post_request", "post_revision") and "POST:" not in raw_response:
        print(f"[ReplyHandler] WARNING: intent={intent} but no POST: format in response")
        action_type = "conversation"

    return {
        "response_text": raw_response,
        "revised_post": revised_post,
        "action_type": action_type,
        "raw_ai_response": response.content[0].text,
    }