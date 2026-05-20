"""
content_safety.py

Content safety layer for Marlo.
Principles:
- Silent filtering: don't lecture users, just redirect
- Normal users never feel restricted
- Bad actors can't generate harmful content
"""

import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SAFETY_PROMPT = """You are a content safety classifier for a small business marketing tool.

Classify if the following user request should be BLOCKED.

BLOCK if the request asks to generate:
- Hate speech, discrimination based on race, gender, religion, sexuality
- Sexual or explicit content
- Content targeting or harming minors
- Violent or threatening content
- Illegal activities or products
- Spam or deceptive marketing (fake reviews, misleading claims)
- Content impersonating other businesses or public figures

ALLOW everything else, including:
- Promotional posts and marketing copy
- Product descriptions and captions
- Business updates and milestone announcements
- Opinion pieces and thought leadership
- Edgy, humorous, or unconventional content
- Any normal small business marketing need

Respond with ONLY a JSON object:
{"blocked": true/false, "reason": "brief reason if blocked, empty string if allowed"}
"""


async def check_content_safety(user_input: str) -> dict:
    """
    Check if user input should be blocked.
    Returns: {"blocked": bool, "reason": str}
    Uses Haiku for cost efficiency.
    """
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"{SAFETY_PROMPT}\n\nUser request: {user_input[:500]}"
            }]
        )
        text = response.content[0].text.strip()
        import json
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Safety] Check failed (allowing): {e}")
        return {"blocked": False, "reason": ""}


def get_safe_redirect_message() -> str:
    """Non-preachy redirect when content is blocked."""
    return (
        "I can't help with that particular request. "
        "Want me to write something different for this post instead? "
        "Just let me know what direction you'd like to take it."
    )