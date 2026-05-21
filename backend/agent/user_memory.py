"""
user_memory.py

Per-user knowledge base. Replaces raw conversation history.
Stored as JSONB in businesses.user_memory column.
~200 tokens per call vs ~2000 for raw history.
"""

import anthropic
import os
import json
from datetime import datetime

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DEFAULT_MEMORY = {
    "vendor_type": None,
    "content_preferences": {
        "likes": [],
        "dislikes": [],
        "style_notes": ""
    },
    "recent_context": "",
    "pending_topics": [],
    "updated_at": ""
}

UPDATE_PROMPT = """You maintain a compact user memory for a marketing assistant.

CURRENT MEMORY:
{current_memory}

NEW CONVERSATION:
User said: {user_message}
Assistant responded: {assistant_response}

Update the memory by:
1. Adding any NEW content preferences mentioned (likes/dislikes/style notes)
2. Updating recent_context to reflect what the user is working on NOW (1 sentence max)
3. Adding any topics they want to cover in future posts to pending_topics
4. Removing pending_topics that were already addressed
5. Keeping the memory CONCISE — max 3 items per list, merge similar items

Return ONLY valid JSON matching this exact structure:
{
  "vendor_type": "string or null",
  "content_preferences": {
    "likes": ["max 3 items"],
    "dislikes": ["max 3 items"],
    "style_notes": "one sentence max"
  },
  "recent_context": "one sentence about what they're working on right now",
  "pending_topics": ["max 3 items"],
  "updated_at": "YYYY-MM-DD"
}"""


def load_memory(business) -> dict:
    """Load user memory from business record. Returns default if empty."""
    try:
        raw = getattr(business, "user_memory", None)
        if raw and isinstance(raw, dict):
            return {**DEFAULT_MEMORY, **raw}
        if raw and isinstance(raw, str):
            parsed = json.loads(raw)
            return {**DEFAULT_MEMORY, **parsed}
    except Exception:
        pass
    return dict(DEFAULT_MEMORY)


def format_for_prompt(memory: dict) -> str:
    """Format memory as compact context string. ~200 tokens."""
    parts = []

    if memory.get("vendor_type"):
        parts.append(f"Vendor type: {memory['vendor_type']}")

    prefs = memory.get("content_preferences", {})
    if prefs.get("likes"):
        parts.append(f"Content they like: {', '.join(prefs['likes'])}")
    if prefs.get("dislikes"):
        parts.append(f"Content they dislike: {', '.join(prefs['dislikes'])}")
    if prefs.get("style_notes"):
        parts.append(f"Style: {prefs['style_notes']}")

    if memory.get("recent_context"):
        parts.append(f"Current context: {memory['recent_context']}")

    if memory.get("pending_topics"):
        parts.append(f"Topics they want to cover: {', '.join(memory['pending_topics'])}")

    return "\n".join(parts) if parts else "No previous context."


async def update_memory_async(
    business_id: str,
    user_message: str,
    assistant_response: str,
    current_memory: dict,
):
    """
    Update user memory after a conversation turn.
    Runs asynchronously — doesn't block the response to the user.
    Uses Haiku for cost efficiency.
    """
    from database.session import AsyncSessionLocal
    from database.models import Business
    from sqlalchemy import select

    try:
        prompt = UPDATE_PROMPT.format(
            current_memory=json.dumps(current_memory, indent=2),
            user_message=user_message[:500],
            assistant_response=assistant_response[:500],
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()

        updated_memory = json.loads(text)
        updated_memory["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Business).where(Business.id == business_id)
            )
            biz = result.scalar_one_or_none()
            if biz:
                biz.user_memory = updated_memory
                await db.commit()
                print(f"[UserMemory] Updated for {business_id}")

    except Exception as e:
        print(f"[UserMemory] Update failed (non-fatal): {e}")


async def initialize_memory_from_business(business) -> dict:
    """Build initial memory from existing business profile."""
    from agent.vendor_profiles import detect_vendor_type_from_industry

    vendor_type = detect_vendor_type_from_industry(business.industry or "")

    memory = {
        "vendor_type": vendor_type,
        "content_preferences": {
            "likes": [],
            "dislikes": [],
            "style_notes": business.tone_of_voice or ""
        },
        "recent_context": f"{business.name} — {business.description or business.industry or 'small business'}",
        "pending_topics": [],
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d")
    }
    return memory