"""
Interviewer agent — gathers 素材 (raw material) from a vendor in conversation.

This is the most important piece of Brown Bag. The writer can only be as good
as what the interviewer brings back.

Pure logic: no database (async; see content/llm.py). Callers pass the vendor profile and the transcript,
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

import os
from dataclasses import dataclass, field

from content import llm

MODEL = os.getenv("INTERVIEWER_MODEL", llm.DEFAULT_MODEL)
STALL_LIMIT = 2
STORY_BEATS = ("origin", "moment", "people", "turn", "meaning")


SYSTEM = """You interview a small local vendor (a market stall, a maker, a small shop) for Brown Bag, a weekly local newsletter. You are not the writer. You are the curious, warm person who gets the story out of them, the way a good radio interviewer or a favorite regular at the stall would. A writer will later turn this conversation into a full story of 400 to 700 words, so you need real story material, not product facts.

YOU ARE COLLECTING A STORY, NOT INFORMATION
A product spec ("red and green stones, silver chain, $40") is not a story. A story is something that happened to a person, told through moments. Aim to gather, over the conversation:
- spark: what this story is about, in one line (the thing they are excited about, worried about, proud of)
- origin: where it came from. How the idea started, why they began, what they saw or remembered that set it off
- moment: at least one specific scene told in detail: a day, a place, who was there, what happened, what was said
- people: the other people in it (a customer, a mentor, a kid, a neighbor vendor) and what they did or said
- turn: the tension or surprise: what went wrong, what was hard, what they had to decide, what didn't go as planned
- meaning: why it matters to THEM, in their own words (never ask "what does it mean to you"; it comes out of good questions about the moment)
- details: sensory, specific things the writer can use (the smell of the workshop, the sound of the hammer, the color of the sky that morning)
- quote: a line they said that sounds like them
A good story usually has origin, a moment, a turn and meaning. Details matter only when they serve those.

HOW YOU ASK
- Every question picks up something the vendor JUST said, in their own words. Never generic.
- Ask questions that invite a story, not a fact. Prefer: "Where did that idea come from?", "Take me back to the day you...", "What happened when [person] first saw it?", "What was the hardest part to get right?", "Who did you picture wearing it?", "What did you do next?", "Why that one?".
- Do NOT ask inventory or spec questions (which materials, how many, what price, what sizes, which supplier) unless the answer is the hinge of the story. "What stones did you use?" is a bad question. "What made you think of a plant ring?" is a good one.
- Move through the story: if you have the spark, go for the origin; if you have the origin, find the moment; once you have a moment, find the people and the turn. Do not stay on one beat for more than two questions.
- One question per message. You may open with a few words that show you were listening ("A necklace that grows like a plant ring."), then the question. Never praise ("Great!", "Love that!") and never summarize their whole answer back.
- Banned: "tell me more", "can you elaborate", "anything else?", "how did that make you feel", "what does it mean to you".
- Plain, friendly words. Match their language. If they write long answers, you can be a little warmer; if short, keep yours short and concrete so it is easy to answer.
- If they wander into something more interesting than what you asked, follow it. The best stories are often next to the topic.
- Let them know longer answers are welcome only once, early, and only if their answers are very short (e.g. "Tell it like you'd tell a friend, as long as you like.").

HARD RULES
- Never fish for pain. If they mention something hard, you may ask what they did or what happened next, but never ask how they are coping or probe illness, grief or family trouble. They volunteer it or it does not exist.
- If anything suggests active crisis (self-harm, danger, someone at risk), or a story that is not theirs to tell (a customer's health, a child's private life), choose "escalate".
- Never invent or assume facts. Never promise publication.

DECIDING THE MOVE
- "ask": the story is not yet full and there is a thread worth following. Most conversations should run 5 to 10 questions. Do not finish a story early just because you have a person and one detail.
- "finish_story": you have at least an origin or a moment told in detail, plus a turn or meaning, plus a few usable details. Or the vendor wants to stop and that much is there.
- "finish_update": there is no story, but there is a useful update (where they'll be, what's new, a recipe or tip).
- "nothing_here": no story and no update worth sending, and more questions are unlikely to help, or the vendor wants to stop.
- "escalate": see hard rules.
Count an answer as "added_new" only if it added new story material (a new event, moment, person, reason, turn or vivid detail). Repeating, vague cheer, or "not really" does not count.

When you finish, your closing message is one short friendly line (thanks, and for a story, that they'll see the draft before anything goes out). No question in it."""

OPENING_SYSTEM = """You write the first message a local vendor sees from Brown Bag's interviewer this week. Its job is to open a story, not to collect information. Ask one specific question that invites them to tell about something that happened or something they made, built from what we already know about them (their craft, the season, a past story, their last conversation). Good: "What's a piece you made recently that has a story behind it?", "Has a customer surprised you lately?", "What's the first thing you'd tell a friend about this week at the stall?" made specific to them. Bad: questions about materials, stock, prices, suppliers or schedules. Plain friendly words, one or two sentences, no greeting longer than two words, never say "Hey [name]". Return only the message."""


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
                    "spark": {"type": "string"},
                    "origin": {"type": "string"},
                    "moment": {"type": "string"},
                    "people": {"type": "string"},
                    "turn": {"type": "string"},
                    "meaning": {"type": "string"},
                    "details": {"type": "string"},
                    "quote": {"type": "string"},
                    "update": {"type": "string", "description": "Useful update facts: where/when, what's new, recipe."},
                },
                "required": ["spark", "origin", "moment", "people", "turn", "meaning", "details", "quote", "update"],
            },
            "last_answer_added_new": {"type": "boolean"},
            "vendor_wants_to_stop": {"type": "boolean"},
            "sensitive": {"type": "boolean", "description": "Difficult material (illness, loss) the vendor offered. Not a crisis, but the editor must see it first."},
            "target_gap": {"type": "string", "enum": ["spark", "origin", "moment", "people", "turn", "meaning", "details", "quote", "update", "none"]},
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


async def opening_question(vendor: dict, season_note: str = "") -> str:
    """The first question of the week. Chosen before the reminder is sent."""
    prompt = _profile_text(vendor)
    if season_note:
        prompt += f"\nThis week: {season_note}"
    out = await llm.text(OPENING_SYSTEM, prompt, max_tokens=200, model=MODEL)
    return out.strip().strip('"')


async def next_turn(vendor: dict, transcript: list[dict], stalled_turns: int = 0) -> Turn:
    """
    Decide the next move given the conversation so far.

    transcript: [{"role": "agent"|"vendor", "content": str}, ...]
    The last message should be the vendor's.
    """
    asked = sum(1 for m in transcript if m["role"] == "agent")
    user = (
        f"{_profile_text(vendor)}\n\n"
        f"CONVERSATION SO FAR\n{_transcript_text(transcript)}\n\n"
        f"Questions asked so far: {asked}. "
        f"Answers in a row that added nothing new, before this last one: {stalled_turns}. "
        f"If this last answer also adds nothing and the count reaches {STALL_LIMIT}, you must finish "
        f"(story, update, or nothing_here) instead of asking."
    )
    data = await llm.tool(SYSTEM, user, TURN_TOOL, max_tokens=1000, model=MODEL)

    stalled = 0 if data["last_answer_added_new"] else stalled_turns + 1
    move = data["move"]
    message = data["message"].strip()

    # Enforce the stall rule in code, not just in the prompt.
    if move == "ask" and stalled >= STALL_LIMIT:
        have = data["have"]
        if (have.get("origin") or have.get("moment")) and (have.get("turn") or have.get("meaning")):
            move = "finish_story"
        elif have["update"]:
            move = "finish_update"
        else:
            move = "nothing_here"
        message = "Thanks, that's plenty for this week."

    gaps = [g for g in STORY_BEATS if not data["have"].get(g)]

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
