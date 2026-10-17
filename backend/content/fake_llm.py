"""
A stand-in model for local tests (BB_FAKE_LLM=1). It is NOT clever: it follows
simple rules so the whole pipeline (scout, director, skills, linting, writing
chain, claims check) can be exercised without an API key. Real quality can only
be judged with the real model (see tools/interview_harness.py).
"""

from __future__ import annotations

import json
import re

_STOP_WORDS = ("that's all", "thats all", "i have to go", "gotta go", "done for this week", "nothing more")
_NO_STORY = ("no story", "nothing special", "nothing happened", "nothing really", "just sell")
_SENSITIVE = ("cancer", "chemo", "passed away", "died", "funeral", "divorce", "deport", "lawsuit", "eviction", "diagnos")
_CRISIS = ("kill myself", "suicide", "hurt myself", "end it all")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" ,;:.!?\"'“”")


def _clauses(text: str) -> list[str]:
    parts = re.split(r"[.!?;\n]|,\s", text)
    return [_clean(p) for p in parts if len(p.split()) >= 3]


# ── Tools ────────────────────────────────────────────────────────────────────

def tool(name: str, system: str, user: str) -> dict:
    return globals()["_tool_" + name](system, user)


def _tool_observe(system: str, user: str) -> dict:
    m = re.search(r"NEWEST VENDOR MESSAGE \(V(\d+)\):\n(.*)\nEND", user, re.S)
    text = (m.group(2) if m else "").strip()
    low = text.lower()
    words = text.split()
    mp = re.search(r"<map>(.*?)</map>", user, re.S)
    cur = json.loads(mp.group(1)) if mp else {}
    scene = cur.get("scene") or {}
    clauses = _clauses(text)
    digits = re.findall(r"\d+", text)
    nd = 0 if len(words) < 3 else min(6, len(clauses) + len(digits))
    people = [{"who": w, "role": w, "consent": "ask"} for w in re.findall(r"\b(daughter|mom|mother|wife|husband|neighbor|customer|woman|man|girl|lady)\b", low)][:2]

    def first(*keys):
        for c in clauses:
            if any(k in c.lower() for k in keys):
                return c
        return ""

    quotes = [c for c in clauses if len(c.split()) >= 4][:2]
    where = ""
    wm = re.search(r"\b(?:at|by|near|in) the ([a-z ]{3,24})", low)
    if wm:
        where = _clean(wm.group(0))
    target = max(clauses, key=len) if clauses else text
    target = " ".join(target.split()[:6])
    actions = clauses[:3]
    need_actions = len(scene.get("actions", [])) < 2
    missing = []
    if need_actions:
        missing.append("sequence")
    if not scene.get("where") and not where:
        missing.append("position")
    if not scene.get("sensory"):
        missing.append("sensory")
    if not scene.get("dialogue"):
        missing.append("dialogue")
    return {
        "scene": {"when": "", "where": where, "actions": actions if nd else [], "sensory": [c for c in clauses if re.search(r"smell|sound|loud|hear|saw|look", c.lower())][:1],
                  "dialogue": [c for c in clauses if " said" in c.lower() or "told me" in c.lower()][:1]},
        "people": people,
        "want": first("hoping", "wanted", "counting on", "need", "rent", "trying to"),
        "obstacle": first(" but ", "until", "wrong", "didn't", "split", "broke", "rain", "nobody"),
        "turn": first("then ", "instead", "flipped", "changed", "so i"),
        "after": first("now ", "since ", "next ", "every week", "from then"),
        "meaning": first("stays with", "what i think", "i learned") if "stays with" in low else "",
        "quotes": quotes if nd else [],
        "facts": [c for c in clauses if re.search(r"\d", c)][:3],
        "update": first("saturday", "sunday", "thursday", "friday", "wednesday", "tuesday", "monday") if re.search(r"\b(be at|will be|new this)\b", low) else "",
        "new_details": nd,
        "vendor_wants_to_stop": any(p in low for p in _STOP_WORDS),
        "no_story_claim": any(p in low for p in _NO_STORY),
        "language": "zh" if re.search(r"[一-鿿]", text) else "en",
        "language_difficulty": False,
        "sensitive": any(p in low for p in _SENSITIVE),
        "sensitive_topic": next((p for p in _SENSITIVE if p in low), ""),
        "crisis": any(p in low for p in _CRISIS),
        "target": target,
        "missing": missing[:3],
        "note": f"fake director: {nd} new details",
    }


def _tool_propose_hooks(system: str, user: str) -> dict:
    return {"hooks": [
        {"title": "The Saturday you sold out", "bait": "Was last Saturday as busy as it looked? What time did the last one go?",
         "hint": "Ask about the last time they sold out: what time the last one went.", "why": "fake scout"},
        {"title": "The regular who always asks for one thing", "bait": "Is there a regular who always asks for the same one?",
         "hint": "Ask what the regular bought the first time.", "why": "fake scout"},
        {"title": "What changes when the rain starts", "bait": "What do you do differently on a rainy Saturday?",
         "hint": "Ask about the last rainy market day.", "why": "fake scout"},
    ]}


def _tool_plan_story(system: str, user: str) -> dict:
    vs = re.findall(r"\[V(\d+)\] Vendor: (.*)", user)
    head = " ".join(vs[0][1].split()[:6]) if vs else "A week at the stall"
    return {"focus": "This is a story about one moment at the stall.", "shape": "scene_first",
            "outline": [{"beat": "The moment", "turns": [1], "note": ""}, {"beat": "What changed", "turns": [len(vs) or 1], "note": ""}],
            "headline_options": [head[:58], "A morning at the stall", "What happened Saturday"], "quotes": [], "ending": "", "thin": len(vs) < 3}


def _draft_part(user: str) -> str:
    return user.split("DRAFT\n", 1)[1] if "DRAFT\n" in user else user


def _tool_check_claims(system: str, user: str) -> dict:
    part = _draft_part(user)
    _, _, body = part.partition("\n\n")
    claims, bad = [], []
    for s in re.split(r"(?<=[.!?])\s+", body):
        s = s.strip()
        if not s:
            continue
        if "zzz" in s.lower():
            claims.append({"text": f"You said: {s}", "kind": "other", "status": "unsupported", "turns": [], "evidence": ""})
            bad.append(s)
        elif re.search(r"\d", s):
            claims.append({"text": _clean(re.sub(r"[“”\"]", "", s)), "kind": "number", "status": "supported", "turns": [1], "evidence": _clean(s)})
    return {"claims": claims, "unsupported_sentences": bad}


def _tool_revised_draft(system: str, user: str) -> dict:
    part = user.split("CURRENT DRAFT\n", 1)[1].split("\n\nVENDOR DECISIONS", 1)[0]
    title, _, body = part.partition("\n\n")
    removes = re.findall(r'- REMOVE: "(.*)"', user)
    fixes = re.findall(r'- FIX: "(.*)" -> the vendor says: "(.*)"', user)

    def toks(s):
        return {w for w in re.findall(r"[a-z]{4,}", s.lower())}

    out = []
    for s in re.split(r"(?<=[.!?])\s+", body):
        t = toks(s)
        if any(len(t & toks(r)) >= 2 or "zzz" in s.lower() and "zzz" in r.lower() for r in removes):
            continue
        for claim, note in fixes:
            if len(t & toks(claim)) >= 2:
                s = note.strip()
        out.append(s)
    return {"headline": title.strip(), "body": " ".join(out).strip(), "notes": "fake revision"}


def _tool_editor_brief(system: str, user: str) -> dict:
    return {"scores": {k: 3 for k in ("scene", "person", "stakes", "turn", "voice", "place", "truthfulness", "plainness", "pull")},
            "strongest_quotes": [], "whats_missing": "One more concrete detail about the people there.", "verdict": "edit", "lead_worthy": False}


def _tool_verdict(system: str, user: str) -> dict:
    return {"marketing_voice": False, "invented_facts": [], "pass": True, "notes": "Fake guard: fine."}


# ── Text ─────────────────────────────────────────────────────────────────────

def _target(user: str) -> str:
    m = re.search(r'TARGET \(.*?\): "(.*?)"', user)
    return _clean(m.group(1)) if m else "that"


def text(tag: str, system: str, user: str) -> str:
    n = user.count("Interviewer:")
    t = _target(user)
    lead = [f"{t[:1].upper()}{t[1:]}.", f"Got it, {t}.", f"{t[:1].upper()}{t[1:]}, okay.", f"So, {t}."][n % 4]
    if tag == "opener":
        return "Think of the last time something surprised you at the stall. Tell me about it from the start, whatever you remember. As long as you like, or just talk into your phone."
    if tag == "scene-deepener":
        qs = ["What happened right after that?", "Where were you standing when that happened?", "What did they actually say?",
              "What could you hear around you?", "What were your hands doing?"]
        return f"{lead} {qs[n % len(qs)]}"
    if tag == "stakes-and-turn":
        qs = ["What were you hoping would happen that day?", "Was there a moment it flipped?", "What did you do next?"]
        return f"{lead} {qs[n % len(qs)]}"
    if tag == "meaning-asker":
        return f"{lead} When you think about that day now, what stays with you?"
    if tag == "low-yield":
        qs = ["Was that morning or afternoon?", "Was it a regular or someone new?", "Was it sunny or rainy?"]
        return f"Got it. {qs[n % len(qs)]}"
    if tag == "sensitive-guard":
        return "Thank you for telling me that. Would you like it kept out of the story, or mentioned only in a general way?"
    if tag == "wrap-up":
        return "I'll write that up now. You'll see the draft first and can fix anything that's off."
    if tag == "story-drafter":
        name = (re.search(r"^Vendor: (.*)$", user, re.M) or [None, "The vendor"])[1]
        vs = re.findall(r"\[V\d+\] Vendor: (.*)", user)
        quotes = re.findall(r"^- (.*)$", user.split("VERIFIED QUOTES", 1)[1], re.M) if "VERIFIED QUOTES" in user else []
        title = _clean(" ".join((vs[0] if vs else "A week at the stall").split()[:6]))[:58]
        paras = [f"{name} remembers it plainly."]
        for i, v in enumerate(vs):
            sents = [s for s in re.split(r"(?<=[.!?])\s+", v.strip()) if s]
            if sents:
                q = quotes[i] if i < len(quotes) else sents[0]
                paras.append(f"{name} says: “{_clean(q)}.” " + " ".join(sents[1:3]))
        return title + "\n\n" + "\n\n".join(paras)
    if tag == "style-editor":
        part = _draft_part(user)
        return part
    if tag == "update-writer":
        vs = re.findall(r"\[V\d+\] Vendor: (.*)", user) or re.findall(r"Vendor: (.*)", user)
        body = " ".join(vs)[:300]
        return "Update from the stall\n\n" + body
    if tag == "vendor-simulator":
        facts = re.search(r"Your private facts: (.*?)\nHow you talk", user, re.S)
        sents = re.split(r"(?<=[.!?])\s+", facts.group(1).strip()) if facts else ["Not much."]
        k = user.count("Interviewer:")
        chunk = sents[(k - 1) * 2:(k - 1) * 2 + 2] if k else sents[:1]
        return " ".join(chunk) or "I need to get back to work."
    return "ok"
