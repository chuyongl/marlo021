"""
The story map: the interview's small, explicit working state, and the rules
that read it.

Instead of one big prompt guessing what to do next, every vendor answer is
turned into updates to this map (by the director, content/interviewer.py), and
the NEXT SKILL is chosen here, in plain code, from the map:

    scene still thin?          -> scene-deepener   (up to 5 turns)
    no want/obstacle or turn?  -> stakes-and-turn  (up to 2 turns)
    quotes missing?            -> meaning-asker    (once, last)
    enough for a story?        -> wrap-up

Plus modes that override the path: low-yield (one-liners, "I have no story",
second-language answers), sensitive material, a vendor who wants to stop.

Nothing here calls a model. It can be tested in milliseconds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MAX_VENDOR_TURNS = 10        # hard cap on a single sitting
SCENE_MAX_TURNS = 5          # scene-deepener uses, in total
STAKES_MAX_TURNS = 2
LOW_YIELD_STREAK = 2         # consecutive thin answers that switch to low-yield mode
PAUSE_AFTER_LOW_TURNS = 2    # thin answers inside low-yield mode before offering a micro-session
MAX_PAUSES = 2               # micro-sessions per conversation

MISSING_ORDER = ("sequence", "position", "sensory", "dialogue", "hands")


def new_map(hook: dict | None = None) -> dict:
    return {
        "stage": "talking",             # choose | talking | done
        "hook": hook,
        "scene": {"when": "", "where": "", "actions": [], "sensory": [], "dialogue": []},
        "people": [],                   # [{who, role, consent}]
        "want": "", "obstacle": "", "turn": "", "after": "", "meaning": "",
        "quotes": [],                   # [{text, turn, translated}]
        "facts": [],                    # [{claim, turn}]
        "update": "",
        "private": [],                  # topics the vendor raised that need care
        "language": "en",
        "mode": "normal",               # normal | low_yield
        "yield_history": [],
        "low_streak": 0, "rich_streak": 0, "low_turns_in_mode": 0, "last_words": 0,
        "pending_sensitive": "", "sensitive_handled": False,
        "meaning_asked": False, "pause_offered": False, "pauses": 0,
        "skill_counts": {}, "recent_skills": [],
        "vendor_turns": 0,
        "target": "", "missing": list(MISSING_ORDER[:2]),
        "micro": None,                  # {question, sent}
        "notes": [],
    }


# ── Text helpers ─────────────────────────────────────────────────────────────

def norm(s: str) -> str:
    return re.sub(r"[\W_]+", " ", (s or "").lower()).strip()


def contains_text(haystack: str, needle: str) -> bool:
    n = norm(needle)
    return bool(n) and n in norm(haystack)


def _add_unique(items: list, new: list, limit: int = 12) -> None:
    seen = {norm(x) for x in items}
    for x in new or []:
        x = (x or "").strip()
        if x and norm(x) not in seen:
            items.append(x)
            seen.add(norm(x))
    del items[limit:]


# ── Reading the map ──────────────────────────────────────────────────────────

def scene_details(m: dict) -> int:
    s = m["scene"]
    return (1 if s["when"] else 0) + (1 if s["where"] else 0) + len(s["actions"]) + len(s["sensory"]) + len(s["dialogue"])


def scene_ok(m: dict) -> bool:
    return scene_details(m) >= 3 and len(m["scene"]["actions"]) >= 2


def stakes_ok(m: dict) -> bool:
    return bool(m["want"] or m["obstacle"]) and bool(m["turn"] or m["after"])


def is_ready(m: dict) -> bool:
    """Enough for a full story: a filmable scene, stakes, a turn, two real quotes."""
    return scene_ok(m) and stakes_ok(m) and len(m["quotes"]) >= 2


def is_thin_ok(m: dict) -> bool:
    """Enough to write a short honest story (the writer will not pad).

    Either a little scene plus a hint of stakes, or a real scene on its own: a vivid
    moment is a fine short piece even when the vendor never says what was at stake.
    """
    if scene_ok(m):
        return True
    return scene_details(m) >= 2 and bool(m["want"] or m["obstacle"] or m["turn"] or m["after"])


def count(m: dict, skill: str) -> int:
    return int(m["skill_counts"].get(skill, 0))


def stage_of(m: dict) -> str:
    """For the progress hint in the app: scene -> stakes -> wrap."""
    if m.get("stage") == "done":
        return "done"
    if not scene_ok(m):
        return "scene"
    if not stakes_ok(m):
        return "stakes"
    return "wrap"


def prompt_view(m: dict) -> dict:
    """The part of the map the interviewer and director read (no bookkeeping)."""
    keep = ("hook", "scene", "people", "want", "obstacle", "turn", "after", "meaning", "quotes", "update", "private", "language", "mode")
    out = {k: m.get(k) for k in keep}
    out["hook"] = (m.get("hook") or {}).get("title") if isinstance(m.get("hook"), dict) else m.get("hook")
    return out


def memory_notes(m: dict) -> list[str]:
    """Short facts to remember about this vendor for next time."""
    notes = []
    hook = (m.get("hook") or {}).get("title") if isinstance(m.get("hook"), dict) else None
    if hook:
        notes.append(f"told a story about: {hook}")
    notes += [f["claim"] for f in m.get("facts", [])[:5]]
    notes += [f"{p['who']} ({p['role']})" if p.get("role") else p["who"] for p in m.get("people", [])[:3]]
    return notes


# ── Updating the map from the director's observation ─────────────────────────

def apply_observation(m: dict, obs: dict, vendor_text: str, turn: int) -> None:
    """Merge what the director saw in the newest vendor message. Mutates m."""
    m["vendor_turns"] = turn
    sc = obs.get("scene") or {}
    for key in ("when", "where"):
        val = (sc.get(key) or "").strip()
        if val:
            m["scene"][key] = val
    for key in ("actions", "sensory", "dialogue"):
        _add_unique(m["scene"][key], sc.get(key) or [], 10)

    for p in obs.get("people") or []:
        who = (p.get("who") or "").strip()
        if who and norm(who) not in {norm(x["who"]) for x in m["people"]}:
            m["people"].append({"who": who, "role": (p.get("role") or "").strip(), "consent": p.get("consent") or "ask"})
    del m["people"][8:]

    for key in ("want", "obstacle", "turn", "after", "meaning"):
        val = (obs.get(key) or "").strip()
        if val:
            m[key] = val

    # Quotes must be the vendor's exact words, or they are dropped.
    for q in obs.get("quotes") or []:
        q = (q or "").strip().strip('"“”')
        if len(q.split()) >= 3 and contains_text(vendor_text, q) and norm(q) not in {norm(x["text"]) for x in m["quotes"]}:
            m["quotes"].append({"text": q, "turn": turn, "translated": (obs.get("language") or "en") not in ("en", "")})
    del m["quotes"][8:]

    for f in obs.get("facts") or []:
        f = (f or "").strip()
        if f and norm(f) not in {norm(x["claim"]) for x in m["facts"]}:
            m["facts"].append({"claim": f, "turn": turn})
    del m["facts"][14:]

    upd = (obs.get("update") or "").strip()
    if upd:
        m["update"] = upd

    m["language"] = (obs.get("language") or m.get("language") or "en")[:8]

    # Yield: did this answer add concrete things?
    words = len(vendor_text.split())
    new_details = max(0, min(6, int(obs.get("new_details") or 0)))
    stopping = bool(obs.get("vendor_wants_to_stop"))
    low = (new_details == 0 or (words < 5 and new_details < 2)) and not stopping
    m["last_words"] = words
    m["yield_history"] = (m["yield_history"] + [new_details])[-12:]
    m["low_streak"] = m["low_streak"] + 1 if low else 0
    m["rich_streak"] = m["rich_streak"] + 1 if new_details >= 2 else 0

    if m["mode"] == "normal" and (m["low_streak"] >= LOW_YIELD_STREAK or obs.get("no_story_claim") or obs.get("language_difficulty")):
        m["mode"] = "low_yield"
        m["low_turns_in_mode"] = 0
    elif m["mode"] == "low_yield":
        if m["rich_streak"] >= 2:
            m["mode"] = "normal"
            m["low_turns_in_mode"] = 0
        elif new_details >= 2:
            m["low_turns_in_mode"] = 0      # a good answer (say, after a micro-session) earns fresh chances
        elif low:
            m["low_turns_in_mode"] += 1

    if obs.get("sensitive") and not m["sensitive_handled"]:
        topic = (obs.get("sensitive_topic") or "something personal").strip()
        m["pending_sensitive"] = topic
        _add_unique(m["private"], [topic], 6)

    m["target"] = (obs.get("target") or "").strip()
    if not contains_text(vendor_text, m["target"]):
        m["target"] = " ".join(vendor_text.split()[:6])
    missing = [x for x in (obs.get("missing") or []) if x in MISSING_ORDER]
    m["missing"] = missing or list(MISSING_ORDER[:2])
    if obs.get("note"):
        m["notes"] = (m["notes"] + [obs["note"]])[-12:]


def record_skill(m: dict, skill: str) -> None:
    m["skill_counts"][skill] = count(m, skill) + 1
    m["recent_skills"] = (m["recent_skills"] + [skill])[-8:]
    if skill == "meaning-asker":
        m["meaning_asked"] = True
    if skill == "sensitive-guard":
        m["sensitive_handled"] = True
        m["pending_sensitive"] = ""


# ── Choosing the next skill ──────────────────────────────────────────────────

@dataclass
class Decision:
    move: str                 # ask | offer_pause | finish_story | finish_update | nothing_here | escalate
    skill: str | None
    reason: str


def _finish(m: dict, why: str) -> Decision:
    if is_ready(m) or is_thin_ok(m):
        return Decision("finish_story", "wrap-up", why)
    if m.get("update"):
        return Decision("finish_update", None, why)
    return Decision("nothing_here", None, why)


def choose(m: dict, obs: dict[str, Any]) -> Decision:
    """The whole routing policy, in order. Called after apply_observation()."""
    if obs.get("crisis"):
        return Decision("escalate", None, "possible crisis")
    if obs.get("vendor_wants_to_stop"):
        return _finish(m, "vendor wants to stop")
    if m["vendor_turns"] >= MAX_VENDOR_TURNS:
        return _finish(m, f"reached {MAX_VENDOR_TURNS} answers")
    if m.get("pending_sensitive"):
        return Decision("ask", "sensitive-guard", f"sensitive: {m['pending_sensitive']}")
    if is_ready(m):
        return Decision("finish_story", "wrap-up", "story map is ready")

    if m["mode"] == "low_yield":
        if m["low_turns_in_mode"] >= PAUSE_AFTER_LOW_TURNS:
            if not m["pause_offered"] and m["pauses"] < MAX_PAUSES:
                return Decision("offer_pause", None, "still thin after making it easier")
            return _finish(m, "still thin; keeping what we have")
        return Decision("ask", "low-yield", "thin answers: make it easier")

    if m["low_streak"] >= 1 and m.get("last_words", 99) < 5:
        # A one-word answer ("ok") gives the scene-deepener nothing to follow. Make the next answer easier.
        return Decision("ask", "low-yield", "one-word answer")
    if not scene_ok(m) and count(m, "scene-deepener") < SCENE_MAX_TURNS:
        return Decision("ask", "scene-deepener", f"scene has {scene_details(m)} details, {len(m['scene']['actions'])} actions")
    if not stakes_ok(m) and count(m, "stakes-and-turn") < STAKES_MAX_TURNS and scene_details(m) >= 1:
        return Decision("ask", "stakes-and-turn", "no clear want/obstacle or turn yet")
    if not m["meaning_asked"] and len(m["quotes"]) < 2 and scene_details(m) >= 2:
        return Decision("ask", "meaning-asker", "need the vendor's own line")
    return _finish(m, "asked what is useful to ask")
