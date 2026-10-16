"""
Thin async wrapper around Claude, so the agents stay small and tests can run
without an API key (BB_FAKE_LLM=1, see content/fake_llm.py).

`tag` names the skill or step making the call. Real calls ignore it; the fake
model uses it to answer like that skill would.
"""

from __future__ import annotations

import base64
import logging
import os

import anthropic

from core.config import FAKE_LLM

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("BB_MODEL", "claude-sonnet-4-6")

_client: anthropic.AsyncAnthropic | None = None


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=90.0)
    return _client


def _user_content(user: str, images: list[tuple[str, bytes]] | None):
    if not images:
        return user
    blocks = [
        {"type": "image", "source": {"type": "base64", "media_type": mt, "data": base64.b64encode(data).decode()}}
        for mt, data in images
    ]
    blocks.append({"type": "text", "text": user})
    return blocks


async def _create(model: str | None, **kwargs):
    """Call the model; if a per-step model name is wrong, fall back to the default."""
    chosen = model or DEFAULT_MODEL
    try:
        return await client().messages.create(model=chosen, **kwargs)
    except anthropic.NotFoundError:
        if chosen == DEFAULT_MODEL:
            raise
        logger.error(f"[LLM] model {chosen!r} not found; using {DEFAULT_MODEL!r}")
        return await client().messages.create(model=DEFAULT_MODEL, **kwargs)


async def text(system: str, user: str, max_tokens: int = 1200, model: str | None = None,
               tag: str | None = None, images: list[tuple[str, bytes]] | None = None) -> str:
    if FAKE_LLM:
        from content import fake_llm
        return fake_llm.text(tag or "", system, user)
    resp = await _create(
        model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": _user_content(user, images)}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


async def tool(system: str, user: str, tool_def: dict, max_tokens: int = 1200, model: str | None = None,
               tag: str | None = None) -> dict:
    if FAKE_LLM:
        from content import fake_llm
        return fake_llm.tool(tool_def["name"], system, user)
    resp = await _create(
        model, max_tokens=max_tokens, system=system, tools=[tool_def],
        tool_choice={"type": "tool", "name": tool_def["name"]},
        messages=[{"role": "user", "content": user}],
    )
    return next(b.input for b in resp.content if b.type == "tool_use")
