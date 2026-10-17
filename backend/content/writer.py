"""
The writing chain: transcript -> plan -> draft -> fact anchor -> style edit ->
editor brief, and the revision step that applies a vendor's fixes.

Each step is its own skill and its own model call, so each does one job:

  story-planner   picks the shape and an outline; every beat cites the vendor
                  message (V1, V2 ...) it comes from. No prose.
  story-drafter   writes the feature from the outline, quoting only lines the
                  vendor really said.
  fact-anchor     lists every checkable claim in the draft and where the
                  vendor said it. Anything unsupported is removed before
                  anyone reads it. Quotations are checked in code.
  style-editor    a line edit that can cut and swap words but never add a fact.
                  If it introduces an unsupported claim, its edit is discarded.
  editor-brief    scores the draft on the rubric for the human editor.

The claims that survive are what the vendor confirms (instead of proofreading
600 words on a phone). Updates stay a single short call plus a guard.
"""

from __future__ import annotations

import difflib
import logging
import os
import re

from content import llm, skills
from content.interviewer import profile_text, transcript_text
from content.storymap import contains_text, norm

logger = logging.getLogger(__name__)

WRITER_MODEL = os.getenv("WRITER_MODEL", llm.DEFAULT_MODEL)
ANCHOR_MODEL = os.getenv("GUARD_MODEL", llm.DEFAULT_MODEL)
JUDGE_MODEL = os.getenv("JUDGE_MODEL", llm.DEFAULT_MODEL)
MAX_CLAIMS_SHOWN = 14
MAX_QUOTES_SHOWN = 4
MAX_FIX_PASSES = 2

# ── Tools ────────────────────────────────────────────────────────────────────

PLAN_TOOL = {
    "name": "plan_story",
    "description": "Plan the story: focus, shape, outline with sources, headline options, quotes to use.",
    "input_schema": {
        "type": "object",
        "properties": {
            "focus": {"type": "string"},
            "shape": {"type": "string", "enum": ["scene_first", "bait_first", "object_centered"]},
            "outline": {"type": "array", "items": {"type": "object", "properties": {
                "beat": {"type": "string"}, "turns": {"type": "array", "items": {"type": "integer"}}, "note": {"type": "string"},
            }, "required": ["beat", "turns", "note"]}},
            "headline_options": {"type": "array", "items": {"type": "string"}},
            "quotes": {"type": "array", "items": {"type": "string"}},
            "ending": {"type": "string"},
            "thin": {"type": "boolean"},
        },
        "required": ["focus", "shape", "outline", "headline_options", "quotes", "ending", "thin"],
    },
}

ANCHOR_TOOL = {
    "name": "check_claims",
    "description": "List the checkable claims in the draft and where the vendor said each.",
    "input_schema": {
        "type": "object",
        "properties": {
            "claims": {"type": "array", "items": {"type": "object", "properties": {
                "text": {"type": "string"},
                "kind": {"type": "string", "enum": ["number", "name", "place", "time", "person", "event", "tone", "translation", "other"]},
                "status": {"type": "string", "enum": ["supported", "inferred", "unsupported"]},
                "turns": {"type": "array", "items": {"type": "integer"}},
                "evidence": {"type": "string"},
            }, "required": ["text", "kind", "status", "turns", "evidence"]}},
            "unsupported_sentences": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["claims", "unsupported_sentences"],
    },
}

REVISE_TOOL = {
    "name": "revised_draft",
    "description": "The draft after applying the vendor's decisions.",
    "input_schema": {
        "type": "object",
        "properties": {"headline": {"type": "string"}, "body": {"type": "string"}, "notes": {"type": "string"}},
        "required": ["headline", "body", "notes"],
    },
}

_SCORE = {"type": "integer", "minimum": 1, "maximum": 4}
BRIEF_TOOL = {
    "name": "editor_brief",
    "description": "Rubric scores and a brief for the editor.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scores": {"type": "object", "properties": {k: _SCORE for k in (
                "scene", "person", "stakes", "turn", "voice", "place", "truthfulness", "plainness", "pull")},
                "required": ["scene", "person", "stakes", "turn", "voice", "place", "truthfulness", "plainness", "pull"]},
            "strongest_quotes": {"type": "array", "items": {"type": "string"}},
            "whats_missing": {"type": "string"},
            "verdict": {"type": "string", "enum": ["run", "edit", "hold"]},
            "lead_worthy": {"type": "boolean"},
        },
        "required": ["scores", "strongest_quotes", "whats_missing", "verdict", "lead_worthy"],
    },
}

# Updates keep a simple guard.
GUARD_TOOL = {
    "name": "verdict",
    "description": "Judge a short update against Brown Bag's bar.",
    "input_schema": {
        "type": "object",
        "properties": {
            "marketing_voice": {"type": "boolean"},
            "invented_facts": {"type": "array", "items": {"type": "string"}},
            "pass": {"type": "boolean"},
            "notes": {"type": "string"},
        },
        "required": ["marketing_voice", "invented_facts", "pass", "notes"],
    },
}
GUARD_SYSTEM = ("You check a short vendor update against the transcript it came from. Anything in the update the vendor did "
                "not say is an invented fact (restating is fine; new specifics are not). It passes if it is useful, has no "
                "marketing voice and no invented facts.")


# ── Deterministic helpers ────────────────────────────────────────────────────

STYLE_PATTERNS = [
    (r"\bnestled\b", "nestled"), (r"\bbustling\b", "bustling"), (r"\bvibrant\b", "vibrant"),
    (r"\bhidden gem\b", "hidden gem"), (r"\btapestry\b", "tapestry"), (r"\bjourney\b", "journey"),
    (r"\bpassion(ate)?\b", "passion"), (r"\blabou?r of love\b", "labor of love"), (r"\btestament to\b", "testament to"),
    (r"\bmore than just\b", "more than just"), (r"\bin a world where\b", "in a world where"),
    (r"\bwhether you'?re\b", "whether you're"), (r"\blook no further\b", "look no further"),
    (r"\bat the end of the day\b", "at the end of the day"), (r"\bdelve\b", "delve"),
    (r"!", "exclamation mark"),
]
QUOTE_RE = re.compile(r"[“\"]([^“”\"\n]{6,}?)[”\"]")


def style_lint(text: str) -> list[str]:
    found = []
    for pattern, label in STYLE_PATTERNS:
        if re.search(pattern, text, re.I) and label not in found:
            found.append(label)
    # Exclamation marks inside a vendor's direct quote are theirs; only flag narration.
    if "exclamation mark" in found and "!" not in QUOTE_RE.sub("", text):
        found.remove("exclamation mark")
    for para in re.split(r"\n\s*\n", text):
        if para.count("—") >= 2 and "em dashes" not in found:
            found.append("em dashes")
    return found


def split_title(text: str) -> tuple[str, str]:
    text = text.strip()
    head, _, body = text.partition("\n")
    return head.strip().strip("#*\" ").strip(), body.strip()


def vendor_texts(transcript: list[dict]) -> list[str]:
    return [m["content"] for m in transcript if m["role"] == "vendor"]


def quotes_in(body: str) -> list[str]:
    return [q.strip() for q in QUOTE_RE.findall(body)]


def snap_quotes(body: str, vtexts: list[str]) -> str:
    """
    A quotation must be the vendor's exact words. If the model changed one
    slightly ("um" removed, a word moved), snap it back to the closest exact
    wording from the transcript. If nothing is close, leave it for the fact
    anchor to flag.
    """
    corpus = " ".join(vtexts)
    words = corpus.split()
    for q in quotes_in(body):
        if contains_text(corpus, q):
            continue
        qn, n = norm(q), len(q.split())
        best, best_r = None, 0.0
        for size in range(max(2, n - 2), n + 3):
            for i in range(0, max(0, len(words) - size) + 1):
                cand = " ".join(words[i:i + size])
                r = difflib.SequenceMatcher(None, qn, norm(cand)).ratio()
                if r > best_r:
                    best, best_r = cand, r
        if best and best_r >= 0.85:
            best = best.strip(" ,;:").rstrip(".!?")
            body = body.replace(q, best)
    return body


def change_ratio(a: str, b: str) -> float:
    return 1.0 - difflib.SequenceMatcher(None, a.split(), b.split()).ratio()


def verified_quotes(story_map: dict | None, vtexts: list[str]) -> list[str]:
    """Lines we know are the vendor's own words: the director's picks, then other long exact sentences."""
    corpus = " ".join(vtexts)
    out: list[str] = []
    for q in (story_map or {}).get("quotes", []):
        if contains_text(corpus, q["text"]) and q["text"] not in out:
            out.append(q["text"])
    for t in vtexts:
        for s in re.split(r"(?<=[.!?])\s+", t.strip()):
            s = s.strip()
            if len(s.split()) >= 6 and s not in out and len(out) < 12:
                out.append(s)
    return out


_KIND_ORDER = ("translation", "number", "name", "place", "time", "person", "tone", "event", "other")


def _priority(kind: str) -> int:
    return _KIND_ORDER.index(kind) if kind in _KIND_ORDER else len(_KIND_ORDER)


def build_claims(body: str, transcript: list[dict], anchor: dict) -> list[dict]:
    """Merge the model's claim list with code-checked quotations and assign ids."""
    vts = vendor_texts(transcript)
    corpus = " ".join(vts)
    facts = []
    for c in (anchor.get("claims") or [])[:20]:
        text = (c.get("text") or "").strip()
        if not text:
            continue
        facts.append({"text": text, "kind": c.get("kind", "other"), "status": c.get("status", "unsupported"),
                      "turns": c.get("turns") or [], "evidence": (c.get("evidence") or "").strip()})
    # What the vendor must see first: things we could not trace, then things we only worked out ("inferred"),
    # then the rest by how embarrassing a wrong detail would be.
    unsupported = [f for f in facts if f["status"] == "unsupported"]
    inferred = sorted((f for f in facts if f["status"] == "inferred"), key=lambda f: _priority(f["kind"]))
    supported = sorted((f for f in facts if f["status"] == "supported"), key=lambda f: _priority(f["kind"]))
    facts = (unsupported + inferred + supported)[:MAX_CLAIMS_SHOWN]

    quotes = []
    for q in quotes_in(body):
        ok = contains_text(corpus, q)
        turns = [i + 1 for i, t in enumerate(vts) if contains_text(t, q)] if ok else []
        quotes.append({"text": q, "kind": "quote", "status": "supported" if ok else "unsupported",
                       "turns": turns[:2], "evidence": q if ok else ""})
    quotes = sorted(quotes, key=lambda x: x["status"] == "supported")[:MAX_QUOTES_SHOWN]

    out = []
    for i, c in enumerate(facts + quotes, start=1):
        out.append({"id": f"c{i}", **c})
    return out


def unsupported_of(claims: list[dict]) -> list[dict]:
    return [c for c in claims if c["status"] == "unsupported"]


# ── Steps ────────────────────────────────────────────────────────────────────

def _story_context(profile: dict, transcript: list[dict], story_map: dict | None) -> str:
    vts = vendor_texts(transcript)
    quotes = verified_quotes(story_map, vts)
    qlist = "\n".join(f"- {q}" for q in quotes) or "- (none)"
    private = [t for t in (story_map or {}).get("private", []) if t]
    private_block = ("\n\nPRIVATE (the vendor touched on these. Leave them out of the story unless the vendor clearly said "
                     "they may be included; if they asked for a general mention, keep it to a few plain words)\n"
                     + "\n".join(f"- {t}" for t in private)) if private else ""
    lang = ((story_map or {}).get("language") or "en").lower()
    lang_block = ""
    if lang not in ("en", "en-us", ""):
        lang_block = (f"\n\nLANGUAGE: the vendor spoke '{lang}', not English. The quotes above are in their own words. "
                      "Put a short direct quote in quotation marks only in its ORIGINAL words, then give the English meaning "
                      "right after it in parentheses WITHOUT quotation marks. Never put your own English translation inside "
                      "quotation marks as if it were spoken.")
    return (f"{profile_text(profile)}\n\nTRANSCRIPT\n{transcript_text(transcript)}\n\n"
            f"VERIFIED QUOTES (the vendor's exact words; copy exactly, never alter)\n{qlist}{private_block}{lang_block}")


async def plan_story(profile, transcript, story_map) -> dict:
    return await llm.tool(skills.text("story-planner"), _story_context(profile, transcript, story_map), PLAN_TOOL,
                          max_tokens=1600, model=WRITER_MODEL, tag="story-planner")


async def draft_story(profile, transcript, story_map, plan: dict) -> tuple[str, str]:
    import json
    user = _story_context(profile, transcript, story_map) + "\n\nOUTLINE FROM THE PLANNER\n" + json.dumps(plan, ensure_ascii=False)
    out = await llm.text(skills.text("story-drafter"), user, max_tokens=2600, model=WRITER_MODEL, tag="story-drafter")
    return split_title(out)


async def anchor(title: str, body: str, transcript: list[dict]) -> dict:
    user = f"TRANSCRIPT\n{transcript_text(transcript)}\n\nDRAFT\n{title}\n\n{body}"
    return await llm.tool(skills.text("fact-anchor"), user, ANCHOR_TOOL, max_tokens=2500, model=ANCHOR_MODEL, tag="fact-anchor")


async def check(title: str, body: str, transcript: list[dict]) -> list[dict]:
    return build_claims(body, transcript, await anchor(title, body, transcript))


async def revise(profile: dict, transcript: list[dict], title: str, body: str, decisions: list[dict]) -> tuple[str, str, str]:
    """
    Apply decisions: [{"claim": "You made forty jars.", "action": "remove"|"fix", "note": "It was fifty."}].
    Returns (title, body, notes).
    """
    lines = []
    for d in decisions:
        if d["action"] == "fix":
            lines.append(f'- FIX: "{d["claim"]}" -> the vendor says: "{d.get("note", "").strip()}"')
        else:
            lines.append(f'- REMOVE: "{d["claim"]}"')
    user = (f"{profile_text(profile)}\n\nTRANSCRIPT\n{transcript_text(transcript)}\n\nCURRENT DRAFT\n{title}\n\n{body}\n\n"
            "VENDOR DECISIONS (binding)\n" + "\n".join(lines))
    data = await llm.tool(skills.text("revision-handler"), user, REVISE_TOOL, max_tokens=2600, model=WRITER_MODEL, tag="revision-handler")
    return (data.get("headline") or title).strip(), (data.get("body") or body).strip(), data.get("notes", "")


async def style_edit(title: str, body: str, flags: list[str]) -> tuple[str, str]:
    user = f"FLAGGED PHRASES: {', '.join(flags) if flags else 'none'}\n\nDRAFT\n{title}\n\n{body}"
    out = await llm.text(skills.text("style-editor"), user, max_tokens=2600, model=WRITER_MODEL, tag="style-editor")
    return split_title(out)


async def editor_brief(title: str, body: str, transcript: list[dict], claims: list[dict]) -> dict | None:
    user = (f"TRANSCRIPT\n{transcript_text(transcript)}\n\nDRAFT\n{title}\n\n{body}\n\n"
            f"FACT CHECK: {len(claims)} claims, {len(unsupported_of(claims))} unsupported.")
    try:
        return await llm.tool(skills.text("editor-brief"), user, BRIEF_TOOL, max_tokens=900, model=JUDGE_MODEL, tag="editor-brief")
    except Exception as e:  # noqa: BLE001 - the brief is a convenience
        logger.warning(f"[Writer] editor brief failed: {e}")
        return None


def make_guard(body: str, claims: list[dict], brief: dict | None) -> dict:
    bad = unsupported_of(claims)
    flags = style_lint(body)
    words = len(body.split())
    notes = []
    if bad:
        notes.append(f"{len(bad)} claim(s) the vendor did not say.")
    if flags:
        notes.append("Style flags: " + ", ".join(flags) + ".")
    if words < 120:
        notes.append("Short: the material was thin.")
    if brief and brief.get("verdict") == "hold":
        notes.append("Brief says hold: " + (brief.get("whats_missing") or ""))
    passed = not bad and not flags and words >= 120 and not (brief and brief.get("verdict") == "hold")
    return {
        "pass": passed,
        "notes": " ".join(notes) or "Every claim traces to something the vendor said.",
        "invented_facts": [c["text"] for c in bad],
        "style_flags": flags,
        "claims_total": len(claims),
        "claims_supported": sum(1 for c in claims if c["status"] != "unsupported"),
        "brief": brief,
    }


# ── Entry points ─────────────────────────────────────────────────────────────

async def write_story(profile: dict, transcript: list[dict], story_map: dict | None = None) -> dict:
    vts = vendor_texts(transcript)
    plan = await plan_story(profile, transcript, story_map)
    title, body = await draft_story(profile, transcript, story_map, plan)
    body = snap_quotes(body, vts)
    claims = await check(title, body, transcript)

    passes = 0
    while unsupported_of(claims) and passes < MAX_FIX_PASSES:
        passes += 1
        decisions = [{"claim": c["text"], "action": "remove"} for c in unsupported_of(claims)]
        title, body, _ = await revise(profile, transcript, title, body, decisions)
        body = snap_quotes(body, vts)
        claims = await check(title, body, transcript)

    # Line edit. If it adds anything the vendor didn't say, throw the edit away.
    t2, b2 = await style_edit(title, body, style_lint(body))
    b2 = snap_quotes(b2, vts)
    if b2 and b2 != body and len(b2.split()) >= 0.6 * len(body.split()):
        if change_ratio(body, b2) > 0.10:
            c2 = await check(t2, b2, transcript)
            if not unsupported_of(c2):
                title, body, claims = t2, b2, c2
        else:
            title, body = t2 or title, b2
            claims = build_claims(body, transcript, {"claims": [c for c in claims if c["kind"] != "quote"]})

    brief = await editor_brief(title, body, transcript, claims)
    return {"kind": "story", "title": title[:120], "body": body, "words": len(body.split()),
            "guard": make_guard(body, claims, brief), "claims": claims, "plan": plan}


async def write_update(profile: dict, transcript: list[dict]) -> dict:
    out = await llm.text(skills.text("update-writer"), f"{profile_text(profile)}\n\nTRANSCRIPT\n{transcript_text(transcript)}",
                         max_tokens=500, model=WRITER_MODEL, tag="update-writer")
    title, body = split_title(out)
    verdict = await llm.tool(GUARD_SYSTEM, f"TRANSCRIPT\n{transcript_text(transcript)}\n\nUPDATE\n{title}\n\n{body}",
                             GUARD_TOOL, max_tokens=500, model=ANCHOR_MODEL, tag="update-guard")
    flags = style_lint(body)
    verdict["style_flags"] = flags
    if flags:
        verdict["pass"] = False
        verdict["notes"] = (verdict.get("notes", "") + " Style flags: " + ", ".join(flags) + ".").strip()
    return {"kind": "update", "title": title[:120], "body": body, "words": len(body.split()), "guard": verdict,
            "claims": None, "plan": None}


async def write_checked(kind: str, profile: dict, transcript: list[dict], story_map: dict | None = None) -> dict:
    if kind == "update":
        return await write_update(profile, transcript)
    return await write_story(profile, transcript, story_map)
