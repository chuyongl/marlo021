"""
The interviewer: a director plus a small set of interview skills.

Every vendor answer goes through two short model calls:

  1. DIRECTOR (skill: director). Reads the answer and reports what it added
     to the story map: concrete details, quotes, who else was there, what the
     vendor wanted, what changed, and flags (wants to stop, sensitive, crisis,
     second language). It never talks to the vendor.
  2. INTERVIEWER (base-persona + ONE chosen skill). The skill is chosen in
     code from the map (content/storymap.py). It writes one message: an echo
     of the vendor's own words, then one question.

Every message is linted before it is sent (one question, no "why", no praise,
an echo that reuses the vendor's words). One retry with the problems named,
then a minimal repair. Pure logic: no database. Callers pass the profile, the
map and the transcript, and store what comes back.
"""

from __future__ import annotations

import json
import logging
import os
import re
from copy import deepcopy
from dataclasses import dataclass, field

from content import llm, skills, storymap

logger = logging.getLogger(__name__)

MODEL = os.getenv("INTERVIEWER_MODEL", llm.DEFAULT_MODEL)
DIRECTOR_MODEL = os.getenv("BB_DIRECTOR_MODEL", llm.DEFAULT_MODEL)

# ── Director tool ────────────────────────────────────────────────────────────

_STR_LIST = {"type": "array", "items": {"type": "string"}}

OBSERVE_TOOL = {
    "name": "observe",
    "description": "Report what the newest vendor message added to the story map.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scene": {
                "type": "object",
                "properties": {
                    "when": {"type": "string"}, "where": {"type": "string"},
                    "actions": _STR_LIST, "sensory": _STR_LIST, "dialogue": _STR_LIST,
                },
                "required": ["when", "where", "actions", "sensory", "dialogue"],
            },
            "people": {
                "type": "array",
                "items": {"type": "object", "properties": {
                    "who": {"type": "string"}, "role": {"type": "string"}, "consent": {"type": "string", "enum": ["ask", "named", "anonymous"]},
                }, "required": ["who", "role", "consent"]},
            },
            "want": {"type": "string"}, "obstacle": {"type": "string"}, "turn": {"type": "string"},
            "after": {"type": "string"}, "meaning": {"type": "string"},
            "quotes": _STR_LIST, "facts": _STR_LIST, "update": {"type": "string"},
            "new_details": {"type": "integer", "minimum": 0, "maximum": 6},
            "vendor_wants_to_stop": {"type": "boolean"}, "no_story_claim": {"type": "boolean"},
            "language": {"type": "string"}, "language_difficulty": {"type": "boolean"},
            "sensitive": {"type": "boolean"}, "sensitive_topic": {"type": "string"}, "crisis": {"type": "boolean"},
            "target": {"type": "string"},
            "missing": {"type": "array", "items": {"type": "string", "enum": list(storymap.MISSING_ORDER)}},
            "note": {"type": "string"},
        },
        "required": ["scene", "people", "want", "obstacle", "turn", "after", "meaning", "quotes", "facts", "update",
                     "new_details", "vendor_wants_to_stop", "no_story_claim", "language", "language_difficulty",
                     "sensitive", "sensitive_topic", "crisis", "target", "missing", "note"],
    },
}


# ── Text helpers ─────────────────────────────────────────────────────────────

def profile_text(vendor: dict) -> str:
    lines = [f"Vendor: {vendor.get('name', '')}"]
    for key, label in [
        ("category", "Sells"), ("neighborhood", "Where"), ("products", "In their words"),
        ("known_facts", "What we already know"), ("past_stories", "Stories already published (don't repeat)"),
    ]:
        if vendor.get(key):
            value = vendor[key]
            if isinstance(value, list):
                value = "; ".join(value)
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def transcript_text(transcript: list[dict]) -> str:
    """Readable transcript with numbered vendor messages (V1, V2, ...)."""
    out, n = [], 0
    for m in transcript:
        if m["role"] == "agent":
            out.append(f"Interviewer: {m['content']}")
        else:
            n += 1
            out.append(f"[V{n}] Vendor: {m['content']}")
    return "\n".join(out)


def _last(transcript: list[dict], role: str) -> str:
    for m in reversed(transcript):
        if m["role"] == role:
            return m["content"]
    return ""


# ── Linting what the interviewer says ────────────────────────────────────────

_STOP = set("""the and that this with have from they them were was what when where which would could about your just like then
than into over some very been being also only more most much many even each such there their here said say says""".split())

BANNED = ("tell me more", "can you elaborate", "how did that make you feel", "what does it mean to you",
          "what challenges", "anything else?", "journey", "passion")
PRAISE = re.compile(r"^\s*(great|awesome|amazing|wow|love that|that'?s (so |really )?(great|awesome|amazing|wonderful|fantastic)|fantastic|wonderful)\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")

ECHO_SKILLS = {"scene-deepener", "stakes-and-turn", "meaning-asker"}
NO_QUESTION_SKILLS = {"wrap-up"}
MAX_QUESTION_WORDS = 25
MAX_WORDS = 60


def _sentences(t: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s]


def lint(msg: str, skill: str, last_vendor: str = "", prev_agent: str = "") -> list[str]:
    """Problems with an interviewer message. Empty list means it is fine."""
    t = (msg or "").strip()
    if not t:
        return ["empty message"]
    problems: list[str] = []
    low = t.lower()
    qn = t.count("?")
    sents = _sentences(t)
    if skill in NO_QUESTION_SKILLS:
        if qn:
            problems.append("must not ask a question")
    else:
        if qn > 1:
            problems.append("more than one question")
        if qn == 0 and skill != "sensitive-guard":
            problems.append("no question")
        for s in sents:
            if "?" in s and len(s.split()) > MAX_QUESTION_WORDS:
                problems.append(f"question longer than {MAX_QUESTION_WORDS} words")
                break
    if re.search(r"\bwhy\b", low):
        problems.append('uses "why"')
    for phrase in BANNED:
        if phrase in low:
            problems.append(f'banned phrase "{phrase}"')
    if PRAISE.search(t):
        problems.append("opens with praise")
    if "!" in t:
        problems.append("exclamation mark")
    if EMOJI.search(t):
        problems.append("emoji")
    if len(t.split()) > MAX_WORDS:
        problems.append(f"longer than {MAX_WORDS} words")
    if skill in ECHO_SKILLS:
        before_q = [s for s in sents if "?" not in s]
        if not before_q or sents[0].endswith("?"):
            problems.append("no echo line before the question")
        elif last_vendor and len(last_vendor.split()) >= 6:
            theirs = set(re.findall(r"[a-z']{4,}", last_vendor.lower())) - _STOP
            echoed = set(re.findall(r"[a-z']{4,}", " ".join(before_q).lower()))
            if theirs and not (theirs & echoed):
                problems.append("echo does not reuse the vendor's words")
    if prev_agent and len(t.split()) >= 3:
        if t.lower().split()[:3] == prev_agent.lower().split()[:3]:
            problems.append("starts the same way as the previous message")
    return problems


def sanitize(msg: str) -> str:
    t = (msg or "").strip().strip('"“”').strip()
    t = EMOJI.sub("", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.replace("!", ".").strip()


def repair(msg: str, skill: str) -> str:
    """Last resort when the model keeps breaking the rules: keep the first question only."""
    t = sanitize(msg)
    if skill in NO_QUESTION_SKILLS:
        return t.replace("?", ".")
    sents = _sentences(t)
    out = []
    for s in sents:
        out.append(s)
        if "?" in s:
            break
    t = " ".join(out)
    words = t.split()
    if len(words) > MAX_WORDS:
        t = " ".join(words[-MAX_WORDS:])
    return t


# ── Speaking: persona + one skill ────────────────────────────────────────────

def _turn_prompt(profile: dict, m: dict, transcript: list[dict], *, target: str = "", missing=(), extra: str = "") -> str:
    prev = [x["content"] for x in transcript if x["role"] == "agent"][-3:]
    parts = [
        profile_text(profile),
        "WHAT WE KNOW SO FAR (the story map)\n" + json.dumps(storymap.prompt_view(m), ensure_ascii=False),
        "TRANSCRIPT\n" + transcript_text(transcript),
    ]
    if target:
        parts.append(f'TARGET (the vendor\'s exact words to follow up on): "{target}"')
    if missing:
        parts.append("STILL MISSING: " + ", ".join(missing))
    if prev:
        parts.append("Your last messages began: " + " | ".join(f'"{" ".join(p.split()[:4])}..."' for p in prev)
                     + ". Do not start this one the same way.")
    if extra:
        parts.append(extra)
    parts.append("Write the next message.")
    return "\n\n".join(parts)


async def speak(skill: str, profile: dict, m: dict, transcript: list[dict], *, target: str = "", missing=(),
                extra: str = "", images: list | None = None) -> tuple[str, list[str]]:
    """One message from the interviewer using one skill. Returns (message, remaining lint problems)."""
    system = skills.text("base-persona", skill)
    user = _turn_prompt(profile, m, transcript, target=target, missing=missing, extra=extra)
    last_vendor, prev_agent = _last(transcript, "vendor"), _last(transcript, "agent")

    msg = sanitize(await llm.text(system, user, max_tokens=300, model=MODEL, tag=skill, images=images))
    problems = lint(msg, skill, last_vendor, prev_agent)
    if problems:
        retry = user + f"\n\nYour draft was:\n{msg}\n\nIt has these problems: {'; '.join(problems)}. Write it again and fix all of them."
        msg2 = sanitize(await llm.text(system, retry, max_tokens=300, model=MODEL, tag=skill, images=images))
        p2 = lint(msg2, skill, last_vendor, prev_agent)
        if len(p2) <= len(problems):
            msg, problems = msg2, p2
    if problems:
        fixed = repair(msg, skill)
        after = lint(fixed, skill, last_vendor, prev_agent)
        if len(after) <= len(problems):
            msg, problems = fixed, after
        logger.warning(f"[Interviewer] {skill}: shipped with problems {problems}")
    return msg, problems


async def opening(profile: dict, hook: dict, photo: tuple[str, bytes] | None = None, caption: str = "") -> tuple[str, list[str]]:
    """The first question, built from the story the vendor picked."""
    system = skills.text("base-persona", "opener")
    lines = [profile_text(profile), f"THE STORY THEY PICKED: {hook.get('title', '')}"]
    if hook.get("hint"):
        lines.append(f"Hint from our scout (a question to check, not a fact): {hook['hint']}")
    if hook.get("id") == "free":
        lines.append("They picked 'free': no topic. Ask about the most recent thing at the stall they would tell a friend about.")
    if photo:
        lines.append("They sent the attached photo." + (f' Their caption: "{caption}"' if caption else ""))
    lines.append("Write the first message.")
    user = "\n\n".join(lines)
    msg = sanitize(await llm.text(system, user, max_tokens=250, model=MODEL, tag="opener", images=[photo] if photo else None))
    problems = lint(msg, "opener")
    if problems:
        msg2 = sanitize(await llm.text(system, user + f"\n\nYour draft was:\n{msg}\n\nProblems: {'; '.join(problems)}. Write it again.",
                                       max_tokens=250, model=MODEL, tag="opener", images=[photo] if photo else None))
        p2 = lint(msg2, "opener")
        if len(p2) <= len(problems):
            msg, problems = msg2, p2
    if problems:
        fixed = repair(msg, "opener")
        msg, problems = fixed, lint(fixed, "opener")
    return msg, problems


# ── The director ─────────────────────────────────────────────────────────────

async def observe(profile: dict, m: dict, transcript: list[dict], vendor_text: str, turn: int) -> dict:
    user = (
        f"{profile_text(profile)}\n\n"
        f"CURRENT STORY MAP\n<map>{json.dumps(storymap.prompt_view(m), ensure_ascii=False)}</map>\n\n"
        f"TRANSCRIPT\n{transcript_text(transcript)}\n\n"
        f"NEWEST VENDOR MESSAGE (V{turn}):\n{vendor_text}\nEND"
    )
    return await llm.tool(skills.text("director"), user, OBSERVE_TOOL, max_tokens=1100, model=DIRECTOR_MODEL, tag="observe")


# ── One full turn ────────────────────────────────────────────────────────────

@dataclass
class Turn:
    move: str                       # ask | offer_pause | finish_story | finish_update | nothing_here | escalate
    message: str
    story_map: dict
    skill: str | None
    target: str = ""
    reason: str = ""
    note: str = ""
    sensitive: bool = False
    quick: list = field(default_factory=list)
    problems: list = field(default_factory=list)

    @property
    def finished(self) -> bool:
        return self.move not in ("ask", "offer_pause")

    @property
    def missing(self) -> list:
        return self.story_map.get("missing", [])

    def meta(self) -> dict:
        return {"skill": self.skill, "target": self.target, "reason": self.reason, "problems": self.problems,
                "quick": self.quick}


PAUSE_MESSAGE = ("Totally fine to keep this short. Want me to send you one quick question tomorrow instead? "
                 "You can answer it in a few words.")
PAUSE_QUICK = [{"label": "Yes, send me one tomorrow", "action": "pause"}, {"label": "No, that's all for this week", "action": "stop"}]
UPDATE_CLOSE = "Thanks, that's useful. I'll tidy it into a short note. You'll see it before it goes anywhere."
NOTHING_CLOSE = "Thanks for taking a minute. No story this week, and that's completely fine."
ESCALATE_CLOSE = "Thank you for telling me. A person from Brown Bag will read this personally."


async def next_turn(profile: dict, story_map: dict, transcript: list[dict]) -> Turn:
    """
    Decide and write the interviewer's next move.

    transcript: [{"role": "agent"|"vendor", "content": str}, ...], last message is the vendor's.
    story_map: the conversation's current map (not modified; a new one is returned in the Turn).
    """
    m = deepcopy(story_map) if story_map else storymap.new_map({"id": "free", "title": "", "source": "free"})
    vendor_text = _last(transcript, "vendor")
    turn_no = m["vendor_turns"] + 1

    obs = await observe(profile, m, transcript, vendor_text, turn_no)
    storymap.apply_observation(m, obs, vendor_text, turn_no)
    d = storymap.choose(m, obs)
    note = obs.get("note", "")
    sensitive = bool(obs.get("sensitive") or m["private"])

    base = dict(story_map=m, target=m["target"], reason=d.reason, note=note, sensitive=sensitive)

    if d.move == "escalate":
        m["stage"] = "done"
        return Turn(move="escalate", message=ESCALATE_CLOSE, skill=None, **base)
    if d.move == "offer_pause":
        m["pause_offered"] = True
        return Turn(move="offer_pause", message=PAUSE_MESSAGE, skill="pause-offer", quick=PAUSE_QUICK, **base)
    if d.move == "finish_update":
        m["stage"] = "done"
        return Turn(move=d.move, message=UPDATE_CLOSE, skill=None, **base)
    if d.move == "nothing_here":
        m["stage"] = "done"
        return Turn(move=d.move, message=NOTHING_CLOSE, skill=None, **base)
    if d.move == "finish_story":
        msg, problems = await speak("wrap-up", profile, m, transcript)
        m["stage"] = "done"
        storymap.record_skill(m, "wrap-up")
        return Turn(move="finish_story", message=msg, skill="wrap-up", problems=problems, **base)

    skill = d.skill or "scene-deepener"
    extra = ""
    if skill == "sensitive-guard":
        extra = f"SENSITIVE_TOPIC: {m['private'][-1] if m['private'] else 'something personal'}"
    elif skill == "low-yield":
        extra = f"The vendor's language: {m['language']}. Thin answers in a row: {m['low_streak']}."
    elif skill == "stakes-and-turn":
        gone = [k for k, v in (("want", m["want"] or m["obstacle"]), ("turn", m["turn"] or m["after"])) if not v]
        extra = "STILL MISSING (stakes): " + (", ".join(gone) or "nothing; ask what changed afterward")
    msg, problems = await speak(skill, profile, m, transcript, target=m["target"], missing=m["missing"], extra=extra)
    storymap.record_skill(m, skill)
    return Turn(move="ask", message=msg, skill=skill, problems=problems, **base)


async def micro_question(profile: dict, story_map: dict, transcript: list[dict]) -> tuple[str, list[str]]:
    """One extra-easy question to send by email tomorrow (a micro-session)."""
    m = deepcopy(story_map)
    if m.get("mode") == "low_yield":
        skill = "low-yield"           # they struggled to answer open questions: send a choice or a tiny concrete one
    else:
        skill = "scene-deepener" if not storymap.scene_ok(m) else "stakes-and-turn"
    extra = ("This question will arrive by email tomorrow as a one-minute follow-up. Make it extra easy to answer: "
             "a choice between two concrete things, or one small concrete detail. Start with a short echo of the vendor's words.")
    return await speak(skill, profile, m, transcript, target=m.get("target", ""), missing=m.get("missing", []), extra=extra)
