"""
Writer agent and style guard.

The writer turns 素材 (the interview transcript) into a story or a short
update. The style guard checks every draft against the bar before an editor
ever sees it. A rejection is cheap and normal.

Prompt notes come from docs/WRITER_TEST: lift the vendor's own images, one
quote at most, end on the last concrete thing, never name the feeling, never
invent a fact, length follows the material.
"""

from __future__ import annotations

import os

from content import llm
from content.interviewer import _profile_text, _transcript_text

WRITER_MODEL = os.getenv("WRITER_MODEL", llm.DEFAULT_MODEL)
GUARD_MODEL = os.getenv("GUARD_MODEL", llm.DEFAULT_MODEL)


STORY_SYSTEM = """You write feature stories about local vendors and makers for Brown Bag, a weekly local newsletter. Readers open it to meet the people behind the stalls. The bar: is there a person, is something at stake for them, would a stranger want to know how it turned out? Aim for a good magazine feature: stakes, specificity, a sense of the person, and restraint.

How to write it
- Use only facts from the transcript. Every sentence must trace to something the vendor said. Never invent a detail, a feeling, a time, a name, a number or a place. You may arrange, connect and order what they said.
- Build it as a story, not a profile: open inside a moment or with the most striking detail, then go back to where it started (the origin), then the turn (what was hard, surprising or decided), and land on a concrete image from the present.
- Use the vendor's own words. Quote them two or three times where their phrasing carries something a paraphrase would lose. Their voice is the point.
- Never name the feeling ("she was overwhelmed", "a labor of love", "passion"). Show the concrete thing.
- Vary sentence length. Short sentences at the emotional moments.
- End on the last concrete detail. Never a closing line that explains the meaning, sums up, or invites the reader to visit or buy.
- No marketing language, no urgency, no exclamation marks, no product listings.
- Third person, past tense for what happened; present tense for what is true now.
- Length follows the material. With a full conversation, write 450 to 700 words in short paragraphs. With thinner material, write what it honestly supports (at least 150 words) and never pad.
- Headline: at most 60 characters, concrete, from the story's own details. Not a pun, not a question.

Return the headline on the first line, a blank line, then the story."""

UPDATE_SYSTEM = """You write a short vendor update for Brown Bag, a weekly local newsletter. It is a note a regular customer would find useful: where and when the vendor will be, what's new or back, or a recipe or tip in their own words.
- 25 to 70 words. Plain and warm, like a note pinned at the stall.
- Only facts from the transcript. Never invent times, places, prices or products.
- Keep the vendor's own phrasing where it's good. A recipe stays in their words and steps.
- No marketing language, no urgency, no exclamation marks.
Return a title (at most 40 characters) on the first line, a blank line, then the update."""

GUARD_TOOL = {
    "name": "verdict",
    "description": "Judge a draft against Brown Bag's bar.",
    "input_schema": {
        "type": "object",
        "properties": {
            "has_person": {"type": "boolean"},
            "has_stake": {"type": "boolean"},
            "explains_meaning": {"type": "boolean", "description": "Ends on or contains a line that explains what it all means, sums up, or moralizes."},
            "marketing_voice": {"type": "boolean"},
            "names_feelings": {"type": "boolean"},
            "invented_facts": {"type": "array", "items": {"type": "string"}, "description": "Any claim in the draft not supported by the transcript. Empty if none."},
            "pass": {"type": "boolean"},
            "notes": {"type": "string", "description": "One or two lines for the editor."},
        },
        "required": ["has_person", "has_stake", "explains_meaning", "marketing_voice", "names_feelings", "invented_facts", "pass", "notes"],
    },
}

GUARD_SYSTEM = """You are Brown Bag's style guard. You check a draft against the transcript it came from. Be strict about facts: anything in the draft the vendor did not say is an invented fact (reasonable restatement is fine; new specifics are not).
A STORY passes only if: it has a person and a stake, it does not explain its own meaning, it has no marketing voice, it does not name feelings, and it has no invented facts.
An UPDATE passes if it is useful, has no marketing voice and no invented facts (person and stake are not required)."""


def _split(text: str) -> tuple[str, str]:
    text = text.strip()
    head, _, body = text.partition("\n")
    return head.strip().strip("#*\" ").strip(), body.strip()


async def write(kind: str, vendor: dict, transcript: list[dict]) -> dict:
    """kind: 'story' or 'update'. Returns {kind, title, body, words}."""
    system = STORY_SYSTEM if kind == "story" else UPDATE_SYSTEM
    out = await llm.text(
        system,
        f"{_profile_text(vendor)}\n\nTRANSCRIPT\n{_transcript_text(transcript)}",
        max_tokens=2500,
        model=WRITER_MODEL,
    )
    title, body = _split(out)
    return {"kind": kind, "title": title, "body": body, "words": len(body.split())}


async def guard(draft: dict, transcript: list[dict]) -> dict:
    return await llm.tool(
        GUARD_SYSTEM,
        (
            f"KIND: {draft['kind']}\n\nTRANSCRIPT\n{_transcript_text(transcript)}\n\n"
            f"DRAFT\n{draft['title']}\n\n{draft['body']}"
        ),
        GUARD_TOOL,
        max_tokens=800,
        model=GUARD_MODEL,
    )


async def write_checked(kind: str, vendor: dict, transcript: list[dict], retries: int = 1) -> dict:
    """Write, guard, and retry once with the guard's notes if it fails."""
    draft = await write(kind, vendor, transcript)
    verdict = await guard(draft, transcript)
    attempt = 0
    while not verdict["pass"] and attempt < retries:
        attempt += 1
        fix = verdict["notes"]
        if verdict["invented_facts"]:
            fix += " Remove these unsupported claims: " + "; ".join(verdict["invented_facts"])
        transcript_note = transcript + [{"role": "agent", "content": f"[Editor note to writer, not part of the interview: {fix}]"}]
        draft = await write(kind, vendor, transcript_note)
        verdict = await guard(draft, transcript)
    draft["guard"] = verdict
    return draft
