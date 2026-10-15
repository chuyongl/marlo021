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

from agent.interviewer import client, _profile_text, _transcript_text

WRITER_MODEL = os.getenv("WRITER_MODEL", "claude-sonnet-4-6")
GUARD_MODEL = os.getenv("GUARD_MODEL", "claude-sonnet-4-6")


STORY_SYSTEM = """You write short stories about local vendors for Brown Bag, a weekly local newsletter. The bar: is there a person, is something at stake for them, would a stranger want to know how it turned out? Aim for a good magazine piece: stakes, specificity, restraint. Not fancy prose.

How to write it
- Use only facts from the transcript. Every sentence must trace to something the vendor said. Never invent a detail, a feeling, a time, a name or a number.
- Lift the vendor's own images and words. "My hands look old in it" cannot be improved.
- At most one direct quote, and only if it carries something a paraphrase would lose.
- Never name the feeling ("she was overwhelmed", "a labor of love"). Show the concrete thing.
- Short sentences at the emotional moments.
- End on the last concrete detail. Never a closing line that explains the meaning, sums up, or invites the reader to visit.
- No marketing language, no urgency, no exclamation marks.
- Third person, past tense for what happened; present tense is fine for what's true now.
- Length follows the material: rich material about 180-200 words, thin material about 100-120. Never pad.
- If you delete a sentence and the reader loses nothing, delete it.
- Headline: at most 50 characters, concrete, from the story's own details. Not a pun, not a question.

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


def write(kind: str, vendor: dict, transcript: list[dict]) -> dict:
    """kind: 'story' or 'update'. Returns {kind, title, body, words}."""
    system = STORY_SYSTEM if kind == "story" else UPDATE_SYSTEM
    resp = client().messages.create(
        model=WRITER_MODEL,
        max_tokens=1200,
        system=system,
        messages=[{
            "role": "user",
            "content": f"{_profile_text(vendor)}\n\nTRANSCRIPT\n{_transcript_text(transcript)}",
        }],
    )
    title, body = _split(resp.content[0].text)
    return {"kind": kind, "title": title, "body": body, "words": len(body.split())}


def guard(draft: dict, transcript: list[dict]) -> dict:
    resp = client().messages.create(
        model=GUARD_MODEL,
        max_tokens=800,
        system=GUARD_SYSTEM,
        tools=[GUARD_TOOL],
        tool_choice={"type": "tool", "name": "verdict"},
        messages=[{
            "role": "user",
            "content": (
                f"KIND: {draft['kind']}\n\nTRANSCRIPT\n{_transcript_text(transcript)}\n\n"
                f"DRAFT\n{draft['title']}\n\n{draft['body']}"
            ),
        }],
    )
    return next(b.input for b in resp.content if b.type == "tool_use")


def write_checked(kind: str, vendor: dict, transcript: list[dict], retries: int = 1) -> dict:
    """Write, guard, and retry once with the guard's notes if it fails."""
    draft = write(kind, vendor, transcript)
    verdict = guard(draft, transcript)
    attempt = 0
    while not verdict["pass"] and attempt < retries:
        attempt += 1
        fix = verdict["notes"]
        if verdict["invented_facts"]:
            fix += " Remove these unsupported claims: " + "; ".join(verdict["invented_facts"])
        transcript_note = transcript + [{"role": "agent", "content": f"[Editor note to writer, not part of the interview: {fix}]"}]
        draft = write(kind, vendor, transcript_note)
        verdict = guard(draft, transcript)
    draft["guard"] = verdict
    return draft
