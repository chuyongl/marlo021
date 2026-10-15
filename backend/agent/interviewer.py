"""
Interviewer agent — gathers 素材 (raw material) from a vendor in conversation.

This is the most important piece of Brown Bag. The writer can only be as good
as what the interviewer brings back.

Pure logic: no database. Callers pass the vendor profile and the transcript,
and get back the next move. The router stores messages and the conversation
counters (gaps_remaining, stalled_turns).

Rules (docs/PRODUCT.md, "The Vendor Conversation"):
  - Every question refers to something the vendor just said.
  - Track what a story still lacks (person, stake, scene, detail) and ask
    toward ONE gap at a time.
  - Two answers in a row that add nothing new -> stop and keep what's there.
  - The vendor can end it anytime.
  - Never fish for pain. Active crisis -> escalate to a human, never draft.
  - Producing nothing is a correct outcome.

Besides stories, the interviewer also collects short UPDATES (where the vendor
will be, what's new, a recipe). Updates have a much lower bar and are what
most weeks will actually yield.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import anthropic

MODEL = os.getenv("INTERVIEWER_MODEL", "claude-sonnet-4-6")
STALL_LIMIT = 2

_client = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SYSTEM = """You interview a small local vendor (a market stall, a maker, a small shop) for Brown Bag, a weekly local newsletter. You are not the writer. Your job is to gather raw material in conversation so that a writer can later produce either a short story or a short update.

WHAT A STORY NEEDS
- A person (a named individual doing something, not "we" or "the business")
- Something at stake for them (it can be small: forty jars that sold out, a batch that failed)
- A scene (a specific moment: where, when, who was there)
- Concrete details (numbers, objects, words someone said, sensory things)
Something must have happened or changed. "Everything's fresh, come see us" is not material.

WHAT AN UPDATE NEEDS
A plain, useful fact for a regular customer: where and when they'll be, what's new or back, a recipe or tip in their own words. One or two specifics are enough.

HOW YOU ASK
- Every question must pick up something the vendor JUST said, using their own words or details. Never generic.
- Banned: "tell me more", "can you elaborate", "anything else?", "how did that make you feel", "what's new this week" after the opening.
- One question per message. Short. Plain words, like a curious regular at the stall, not a journalist or a marketer.
- Ask toward the single most valuable missing piece. Prefer concrete questions: "How many jars did you make?" beats "What was it like?"
- Good follow-ups chase the specific: who, how many, what exactly happened next, what someone said, what it looked/smelled like.
- Do not praise or summarize their answer back to them. At most a few words of acknowledgement, then the question.
- If they wander into something more interesting than the topic you asked about, follow it.
- Match their language and energy. If their answers are short, keep yours shorter.

HARD RULES
- Never fish for pain. If they mention something hard, you may ask about what they did or what happened next, but never ask how they are coping or probe illness, grief, or family trouble. They volunteer it or it does not exist.
- If anything suggests active crisis (self-harm, danger, someone at risk), or a story that is not theirs to tell (a customer's health, a child's private life), choose "escalate".
- Never invent or assume facts. Never promise publication.

DECIDING THE MOVE
- "ask": there is a real thread worth one more question.
- "finish_story": there is enough for a story (a person, a stake, and at least one concrete detail; a scene or a quote makes it better). Or the vendor wants to stop and there is enough.
- "finish_update": there is no story, but there is a useful update.
- "nothing_here": no story and no update worth sending, and further questions are unlikely to help, or the vendor wants to stop.
- "escalate": see hard rules.
Count an answer as "added_new" only if it contributed a new concrete fact, detail, person, quote or event. Repeating, vague cheer, or "not really" does not count.

When you finish, your closing message is one short friendly line (e.g. thanks, and that they'll see a draft before anything goes out for a story). No question in it."""

OPENING_SYSTEM = """You write the first message a local vendor sees from Brown Bag's interviewer this week. One short, specific question that is easy to answer between customers, built from what we already know about them (their products, recent stories, the season, their last conversation). Never generic like "what's new this week?". Plain words. No greeting longer than two words. Return only the message."""


TURN_TOOL = {
    "name": "next_move",
    "description": "Decide the interviewer's next move.",
    "input_schema": {
        "type": "object",
        "properties": {
            "have": {
                "type": "object",
                "description": "What the material has so far. Quote or cite the vendor's words briefly as evidence; empty string if missing.",
                "properties": {
                    "person": {"type": "string"},
                    "stake": {"type": "string"},
                    "scene": {"type": "string"},
                    "detail": {"type": "string"},
                    "quote": {"type": "string"},
                    "update": {"type": "string", "description": "Useful update facts: where/when, what's new, recipe."},
                },
                "required": ["person", "stake", "scene", "detail", "quote", "update"],
            },
            "last_answer_added_new": {"type": "boolean"},
            "vendor_wants_to_stop": {"type": "boolean"},
            "sensitive": {"type": "boolean", "description": "Difficult material (illness, loss) the vendor offered. Not a crisis, but the editor must see it first."},
            "target_gap": {"type": "string", "enum": ["person", "stake", "scene", "detail", "quote", "update", "none"]},
            "move": {"type": "string", "enum": ["ask", "finish_story", "finish_update", "nothing_here", "escalate"]},
            "message": {"type": "string", "description": "What to send the vendor now: the question, or the closing line. Empty for escalate."},
            "reason": {"type": "string", "description": "One line: why this move. For the editor's eyes only."},
        },
        "required": ["have", "last_answer_added_new", "vendor_wants_to_stop", "sensitive", "target_gap", "move", "message", "reason"],
    },
}


@dataclass
class Turn:
    move: str
    message: str
    have: dict
    target_gap: str
    added_new: bool
    sensitive: bool
    reason: str
    stalled_turns: int
    gaps_remaining: list = field(default_factory=list)

    @property
    def finished(self) -> bool:
        return self.move != "ask"


def _profile_text(vendor: dict) -> str:
    lines = [f"Vendor: {vendor.get('name', '')}"]
    for key, label in [
        ("business", "Business"),
        ("category", "Category"),
        ("neighborhood", "Where"),
        ("products", "Sells"),
        ("known_facts", "What we already know"),
        ("past_stories", "Stories already published (don't repeat)"),
    ]:
        if vendor.get(key):
            value = vendor[key]
            if isinstance(value, list):
                value = "; ".join(value)
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def _transcript_text(transcript: list[dict]) -> str:
    out = []
    for m in transcript:
        who = "Interviewer" if m["role"] == "agent" else "Vendor"
        out.append(f"{who}: {m['content']}")
    return "\n".join(out)


def opening_question(vendor: dict, season_note: str = "") -> str:
    """The first question of the week. Chosen before the reminder is sent."""
    prompt = _profile_text(vendor)
    if season_note:
        prompt += f"\nThis week: {season_note}"
    resp = client().messages.create(
        model=MODEL,
        max_tokens=200,
        system=OPENING_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip().strip('"')


def next_turn(vendor: dict, transcript: list[dict], stalled_turns: int = 0) -> Turn:
    """
    Decide the next move given the conversation so far.

    transcript: [{"role": "agent"|"vendor", "content": str}, ...]
    The last message should be the vendor's.
    """
    user = (
        f"{_profile_text(vendor)}\n\n"
        f"CONVERSATION SO FAR\n{_transcript_text(transcript)}\n\n"
        f"Answers in a row that added nothing new, before this last one: {stalled_turns}. "
        f"If this last answer also adds nothing and the count reaches {STALL_LIMIT}, you must finish "
        f"(story, update, or nothing_here) instead of asking."
    )
    resp = client().messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM,
        tools=[TURN_TOOL],
        tool_choice={"type": "tool", "name": "next_move"},
        messages=[{"role": "user", "content": user}],
    )
    data = next(b.input for b in resp.content if b.type == "tool_use")

    stalled = 0 if data["last_answer_added_new"] else stalled_turns + 1
    move = data["move"]
    message = data["message"].strip()

    # Enforce the stall rule in code, not just in the prompt.
    if move == "ask" and stalled >= STALL_LIMIT:
        have = data["have"]
        if have["person"] and have["stake"] and have["detail"]:
            move = "finish_story"
        elif have["update"]:
            move = "finish_update"
        else:
            move = "nothing_here"
        message = "Thanks, that's plenty for this week."

    gaps = [g for g in ("person", "stake", "scene", "detail") if not data["have"].get(g)]

    return Turn(
        move=move,
        message=message,
        have=data["have"],
        target_gap=data["target_gap"],
        added_new=data["last_answer_added_new"],
        sensitive=data["sensitive"],
        reason=data["reason"],
        stalled_turns=stalled,
        gaps_remaining=gaps,
    )
