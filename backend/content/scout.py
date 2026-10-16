"""
The story scout: before the vendor sees anything, work out which stories are
worth asking about, and offer a short menu of easy ones.

An editor never opens with "tell me about your business". They arrive with a
guess ("the Saturday you sold out"), and the vendor says yes, or no, or "no,
but...". The scout makes those guesses from what we already know, phrased as
questions, never as facts. The vendor sees them as tappable cards next to a
fixed menu of universal market stories (the first sale, a regular, a mistake
that turned out well, the thing you would save from a fire, a photo).
"""

from __future__ import annotations

import logging
import os

from content import llm, skills

logger = logging.getLogger(__name__)

MODEL = os.getenv("SCOUT_MODEL", llm.DEFAULT_MODEL)

# The fixed menu. `hint` goes to the opener (the vendor never sees it).
MENU = [
    {"id": "first_sale", "title": "The first thing you ever sold",
     "hint": "Take me to the very first sale: where were they standing, what did the person buy?"},
    {"id": "hardest_day", "title": "Your hardest market day",
     "hint": "The last time a market day went badly: what did they find when they got there?"},
    {"id": "regular", "title": "A regular you'd recognize anywhere",
     "hint": "A regular customer: what did they buy the very first time?"},
    {"id": "mistake", "title": "A mistake that turned out well",
     "hint": "The last time something went wrong and they did something different because of it."},
    {"id": "fire", "title": "The one thing at your stall you'd grab in a fire",
     "hint": "The object: when did they last use it, where did it come from?"},
    {"id": "photo", "title": "Send a photo and tell me what's happening in it",
     "hint": "They will send a photo from their phone."},
    {"id": "free", "title": "Something else is on my mind",
     "hint": "No topic: ask about the most recent thing at the stall they'd tell a friend."},
]
MENU_BY_ID = {m["id"]: m for m in MENU}

SCOUT_TOOL = {
    "name": "propose_hooks",
    "description": "Propose 2 to 4 story hooks for this vendor.",
    "input_schema": {
        "type": "object",
        "properties": {
            "hooks": {
                "type": "array", "minItems": 1, "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"}, "bait": {"type": "string"},
                        "hint": {"type": "string"}, "why": {"type": "string"},
                    },
                    "required": ["title", "bait", "hint", "why"],
                },
            }
        },
        "required": ["hooks"],
    },
}


def context_text(profile: dict, ctx: dict) -> str:
    lines = [f"Today: {ctx.get('today', '')}. City: Seattle."]
    lines.append(f"Vendor: {profile.get('name', '')}")
    for key, label in [("category", "Sells"), ("neighborhood", "Where"), ("products", "In their words")]:
        if profile.get(key):
            lines.append(f"{label}: {profile[key]}")
    for key, label in [
        ("schedule", "Schedule note"), ("venue", "Usual market"), ("memory", "Notes from earlier conversations"),
        ("past_headlines", "Past stories about them (do not repeat)"), ("recent_updates", "Recent short updates they sent"),
        ("reader_notes", "What readers sent about them"), ("market_headlines", "What other vendors' recent stories covered"),
    ]:
        v = ctx.get(key)
        if v:
            lines.append(f"{label}: " + ("; ".join(v) if isinstance(v, list) else str(v)))
    return "\n".join(lines)


def _clean(hooks: list[dict]) -> list[dict]:
    out, seen = [], set()
    for h in hooks or []:
        title = (h.get("title") or "").strip().strip('"')[:70]
        bait = (h.get("bait") or "").strip()[:180]
        if not title or not bait or title.lower() in seen:
            continue
        seen.add(title.lower())
        out.append({"id": f"h{len(out) + 1}", "title": title, "bait": bait,
                    "hint": (h.get("hint") or "").strip()[:240], "why": (h.get("why") or "").strip()[:200],
                    "source": "scout"})
        if len(out) == 4:
            break
    return out


async def scout(profile: dict, ctx: dict) -> list[dict]:
    """2 to 4 hooks for this vendor, or [] if the scout has nothing useful (the menu still works)."""
    data = await llm.tool(skills.text("story-scout"), context_text(profile, ctx), SCOUT_TOOL,
                          max_tokens=900, model=MODEL, tag="story-scout")
    return _clean(data.get("hooks", []))


def hook_for(pick: str, hooks: list[dict]) -> dict | None:
    """Resolve what the vendor tapped (a scout hook id like 'h2', or a menu id) to a hook dict."""
    for h in hooks or []:
        if h["id"] == pick:
            return {**h, "source": "scout"}
    if pick in MENU_BY_ID:
        return {**MENU_BY_ID[pick], "source": "menu"}
    return None
