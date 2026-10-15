"""
Thin async wrapper around Claude, so agents stay small and tests can run
without an API key (BB_FAKE_LLM=1).
"""

import os

import anthropic

from core.config import FAKE_LLM

DEFAULT_MODEL = os.getenv("BB_MODEL", "claude-sonnet-4-6")

_client: anthropic.AsyncAnthropic | None = None


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


async def text(system: str, user: str, max_tokens: int = 1200, model: str | None = None) -> str:
    if FAKE_LLM:
        return _fake_text(system, user)
    resp = await client().messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


async def tool(system: str, user: str, tool_def: dict, max_tokens: int = 1200, model: str | None = None) -> dict:
    if FAKE_LLM:
        return _fake_tool(tool_def["name"], user)
    resp = await client().messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system,
        tools=[tool_def],
        tool_choice={"type": "tool", "name": tool_def["name"]},
        messages=[{"role": "user", "content": user}],
    )
    return next(b.input for b in resp.content if b.type == "tool_use")


# ── Fake mode (local tests) ──────────────────────────────────────────────────

def _fake_text(system: str, user: str) -> str:
    if "first message" in system:
        return "How did the chili oil go on Saturday?"
    if "vendor update" in system:
        return "Back Thursday\n\nAt the north arcade Thursday and Saturday with new moon pendants."
    return "Forty jars, gone by eleven\n\nShe made forty jars. They were gone by eleven. Her neighbor knocked to ask if something was burning."


def _fake_tool(name: str, user: str) -> dict:
    if name == "verdict":
        return {"has_person": True, "has_stake": True, "explains_meaning": False,
                "marketing_voice": False, "names_feelings": False, "invented_facts": [],
                "pass": True, "notes": "Fake guard: fine."}
    vendor_turns = user.count("\nVendor: ")
    done = vendor_turns >= 3 or "that's all" in user.lower()
    have = {"person": "Mei", "stake": "sold out", "scene": "", "detail": "40 jars",
            "quote": "", "update": "Saturday at Ballard"}
    return {
        "have": have,
        "last_answer_added_new": True,
        "vendor_wants_to_stop": False,
        "sensitive": False,
        "target_gap": "none" if done else "scene",
        "move": "finish_story" if done else "ask",
        "message": "Thanks, you'll see a draft before anything goes out." if done else "What did the line look like when you got there?",
        "reason": "fake",
    }
