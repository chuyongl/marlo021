"""
Interview harness: runs the real story engine (scout hook -> opener -> director
-> story map -> one skill per turn -> writing chain) against simulated vendors,
and writes a report you can read in five minutes.

Usage (from backend/):
    python -m tools.interview_harness                  # every persona
    python -m tools.interview_harness mei terse esl    # some personas
    python -m tools.interview_harness --no-draft       # interview only (cheaper)
    python -m tools.interview_harness --list

With ANTHROPIC_API_KEY set it uses the real model and tells you how good the
interviewing is. With BB_FAKE_LLM=1 it uses the rule-based stand-in: that only
proves the plumbing and the routing rules, not the quality of the questions.

Reports go to backend/tools/harness_runs/ (a .md to read, a .json to compare runs).
The process exits with status 1 if any hard check fails, so it can sit in CI.

What it checks
  Hard checks (a failure is a bug or a bad skill):
    - every interviewer message passes the rules (one question, no "why", no praise, short)
    - never more than 10 vendor answers
    - each persona's expected behavior (e.g. a terse vendor gets the "low-yield" skill,
      a vendor who mentions a death gets the "sensitive-guard" skill first)
    - the draft has no claim the vendor did not make, and every quote is the vendor's own words
    - sensitive details the vendor asked to keep out stay out
  Soft scores (read them, they are not pass/fail):
    - planted-detail recall: of the details the simulated vendor knows, how many did the
      interviewer get out of them, and how many made it into the draft
    - the editor-brief rubric (scene, person, stakes, turn, voice, place, ...), 1-4 each
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import pathlib
import sys

from content import interviewer, llm, scout, skills, storymap
from content.writer import quotes_in, write_checked

MAX_SIM_TURNS = 14

PAUSE_REPLY = "Yes, send me one tomorrow"


def hook(id_: str, title: str, hint: str = "") -> dict:
    return {"id": id_, "title": title, "hint": hint, "source": "scout"}


PERSONAS: dict[str, dict] = {
    # ── Rich vendors (the interviewer should get the story out) ──────────────
    "mei": {
        "vendor": {"name": "Mei", "business": "Fortune Noodle", "category": "prepared food",
                   "neighborhood": "Ballard Farmers Market", "products": "hand-pulled noodles, chili oil",
                   "known_facts": "Makes chili oil in small batches. Did a cooking demo in July."},
        "pick": hook("h1", "The Saturday you sold out", "Ask about last Saturday: what time did the last jar go?"),
        "hidden": (
            "Last Saturday you sold out of chili oil by 11am; you usually go till 2. You made 40 jars because last month "
            "you made 60 and took 20 home. A line formed before you finished setting up. A girl showed you a TikTok video "
            "of you making chili oil at the July demo, filmed without you knowing, 90,000 views. You don't have TikTok. "
            "It felt a little strange; 'my hands look old in it'. Your 12-year-old daughter made you watch it four times and "
            "said 'mom you're famous'; you said 'I'm not famous, I'm out of chili oil'. This week you're making 80 jars; you "
            "were up until 1am Tuesday toasting Sichuan peppercorns, the apartment smells, your neighbor knocked to check if "
            "something was burning."),
        "style": "Friendly, answers in one or two sentences, a bit dry and funny. Doesn't volunteer the TikTok thing unless asked what happened or who was in line.",
        "planted": [["tiktok"], ["90,000", "90000"], ["80 jars", "80 jar"], ["sichuan"], ["neighbor"], ["famous"], ["hands look old", "old hands"]],
        "expect": {"moves": {"finish_story"}},
    },
    "dan": {
        "vendor": {"name": "Dan", "business": "Hollow Ridge Farm", "category": "produce",
                   "neighborhood": "University District Farmers Market", "products": "kale, chard, tomatoes, seasonal vegetables"},
        "pick": "hardest_day",
        "hidden": (
            "Rain last week split about a third of your late tomatoes. Usually split ones go to the pigs, but there were too "
            "many, so you made sauce for the first time: thirty-something jars, labeled in marker on masking tape. Your wife "
            "Jen found the recipe on the back of an old seed catalog. You'll have the sauce at the end of the table Saturday."),
        "style": "Laconic farmer. Very short answers ('Just the usual.'). Only opens up when asked about something concrete.",
        "planted": [["split"], ["pigs"], ["sauce"], ["jen"], ["seed catalog"], ["masking tape"]],
        "expect": {"moves": {"finish_story", "finish_update"}},
    },
    "lena": {
        "vendor": {"name": "Lena", "business": "Lena Ruiz Jewelry", "category": "handmade jewelry",
                   "neighborhood": "Pike Place Market (day stall)", "products": "hammered silver necklaces and earrings",
                   "known_facts": "Day-stall artisan; her table location changes day to day."},
        "pick": "regular",
        "hidden": (
            "You only got a table three days last week because day stalls go by seniority and the cruise-ship season ended. "
            "On the days you don't get a table you sell almost nothing. A woman from Ohio bought a necklace in August and "
            "emailed you a photo of wearing it at her daughter's wedding; you printed it and taped it inside your toolbox lid. "
            "You hammer every piece on an old railroad spike your grandfather gave you. This week you'll be at the north arcade "
            "Thursday and Saturday, and you just finished a new set of tiny moon pendants."),
        "style": "Warm but busy, answers between customers, medium-length answers. Mentions the toolbox photo only if asked about customers or a specific piece.",
        "planted": [["railroad spike"], ["ohio"], ["toolbox"], ["wedding"], ["moon pendant"], ["north arcade"]],
        "expect": {"moves": {"finish_story", "finish_update"}},
    },
    "otto": {
        "vendor": {"name": "Otto", "business": "Kettle & Smoke Sausage", "category": "butcher",
                   "neighborhood": "Columbia City Farmers Market", "products": "smoked sausages, bratwurst"},
        "pick": "first_sale",
        "hidden": (
            "New this week: a smoked apple-sage sausage. Your quick recipe customers keep asking for: slice the sausage, brown "
            "it in a dry pan, add a sliced onion and a splash of cider, cook until sticky, serve on toast. You'll be at "
            "Columbia City Wednesday 3-7pm. Nothing dramatic happened."),
        "style": "Practical, happy to share cooking tips, a few sentences per answer. Not a storyteller.",
        "planted": [["apple-sage", "apple sage"], ["cider"], ["wednesday"], ["onion"]],
        "expect": {"moves": {"finish_story", "finish_update"}},
    },
    # ── Hard cases (the reason the new engine exists) ────────────────────────
    "terse": {
        "vendor": {"name": "Ruth", "business": "Stem & Root Plants", "category": "plants",
                   "neighborhood": "Fremont Sunday Market", "products": "houseplants, succulents, cuttings"},
        "pick": "regular",
        "hidden": (
            "A retired bus driver named Walt buys one succulent every Saturday, always the smallest one. You asked him once "
            "and he said he lines them up along the dashboard of his old Buick. It is his 41st one. Since March you've saved "
            "the smallest cutting of the week in a yogurt tub under the table for him. He pays in quarters."),
        "style": ("Answers in one to three words: 'ok', 'yes', 'sure', 'idk', 'nothing really'. Gives a full sentence only when "
                  "the question is very specific and easy, like a choice between two things or a number."),
        "planted": [["walt"], ["buick"], ["dashboard"], ["41"], ["yogurt"], ["quarters"], ["smallest"]],
        "expect": {"skills": ["low-yield"], "moves": {"finish_story", "finish_update", "nothing_here", "offer_pause"}},
    },
    "rambler": {
        "vendor": {"name": "Gus", "business": "Wheel & Wedge Cheese", "category": "cheese",
                   "neighborhood": "West Seattle Farmers Market", "products": "aged cheddar, washed-rind wheels"},
        "pick": "mistake",
        "hidden": (
            "In July the cheese cave in your garage lost power for two nights and 30 wheels of washed-rind went soft and "
            "orange. You almost threw them out. A neighbor kid named Dev said they smelled like his grandmother's kitchen "
            "in Pune, so you sold them as 'Dev's wheel' for half price. All 30 were gone in two Saturdays. You also like to "
            "complain about the market fees, your bad knee, and the Seahawks, and you drift to those constantly."),
        "style": ("Long rambling answers of 70-120 words that wander into weather, market fees, his knee and football, "
                  "burying one real detail in each answer."),
        "planted": [["power"], ["30 wheels", "thirty wheels", "30 wheel"], ["dev"], ["pune"], ["half price"], ["garage"]],
        "expect": {"moves": {"finish_story"}},
    },
    "esl": {
        "vendor": {"name": "Thanh", "business": "Saigon Corner", "category": "prepared food",
                   "neighborhood": "Columbia City Farmers Market", "products": "banh mi, pickled carrots"},
        "pick": "first_sale",
        "hidden": (
            "Your first day at the market in 2019 you sold only six sandwiches. One man bought four and came back the next "
            "Saturday with five coworkers. The pickled carrots are your mother's recipe from Da Nang; she sent the recipe in "
            "a voice message and you wrote it on a napkin. You still keep the napkin in the cash box."),
        "style": ("Vietnamese is your first language. Short simple English sentences, sometimes missing articles or tense "
                  "('Sell only six sandwich.'). You do not understand idioms and need simple questions."),
        "planted": [["six"], ["four"], ["coworker"], ["da nang"], ["napkin"], ["mother"], ["voice message"]],
        "expect": {"moves": {"finish_story", "finish_update", "offer_pause"}},
    },
    "skeptic": {
        "vendor": {"name": "Pat", "business": "Little Goat Soap", "category": "bath & body",
                   "neighborhood": "Phinney Market", "products": "goat milk soap"},
        "pick": "free",
        "hidden": (
            "You say you have no story, you just sell soap. But: you named the first three goats after your aunts. Last "
            "month a woman smelled the lavender bar and started crying because it smelled like her grandmother's linen closet; "
            "she bought six bars and you gave her a seventh. You pour the soap into molds at 5am on Fridays."),
        "style": "Flat and a bit defensive. Opens with 'I don't really have a story, I just sell soap.' Gives details only when asked about one specific moment.",
        "planted": [["aunt"], ["lavender"], ["crying", "cried"], ["linen closet"], ["seventh"], ["5am", "5 am"]],
        "expect": {"skills": ["low-yield"], "moves": {"finish_story", "finish_update", "nothing_here", "offer_pause"}},
    },
    "karen": {
        "vendor": {"name": "Karen", "business": "Sweet Pea Bakery", "category": "bakery",
                   "neighborhood": "Fremont Sunday Market", "products": "croissants, sourdough, pastries"},
        "pick": "free",
        "hidden": "Nothing happened this week. Same products as always. It was busy.",
        "style": ("Talks only in upbeat marketing phrases: 'Everything's fresh!', 'We'd love to see everyone Saturday!'. "
                  "Says 'we', never names anyone. Nothing changed, nothing went wrong. After 3-4 questions, says she has to get back to work."),
        "planted": [],
        "expect": {"moves": {"nothing_here", "finish_update", "finish_story", "offer_pause"}, "no_invention": True},
    },
    "sensitive": {
        "vendor": {"name": "Rosa", "business": "Rosa's Empanadas", "category": "prepared food",
                   "neighborhood": "Ballard Farmers Market", "products": "beef and spinach empanadas"},
        "pick": "hardest_day",
        "hidden": (
            "Your husband Luis died in March. The stall was his idea and this is your first season alone. You almost did not "
            "come back. A regular named Tom has brought you a coffee every Saturday since April. You still use Luis's folding "
            "table, which has a scorch mark from the first week. If you are asked whether the death should be in the story, "
            "you answer: please keep it out, just say the stall was his idea."),
        "style": "Warm, quiet. Mentions that your husband died in your second answer, briefly, without being asked.",
        "planted": [["tom"], ["coffee"], ["scorch"], ["folding table"]],
        "expect": {"skills": ["sensitive-guard"], "moves": {"finish_story", "finish_update", "escalate"},
                   "routed_to_person": True, "keep_out": ["died", "death", "passed away", "funeral", "widow"]},
    },
    "busy": {
        "vendor": {"name": "Marcus", "business": "Marcus Metalworks", "category": "handmade goods",
                   "neighborhood": "Pike Place Market (day stall)", "products": "hand-forged knives and bottle openers"},
        "pick": "regular",
        "hidden": (
            "A chef from a Capitol Hill restaurant orders three paring knives every month and you deliver them yourself on "
            "the bus, wrapped in newspaper. Last week the bus driver asked if you were carrying fish."),
        "style": "Always rushed, answers in a line. By your third answer say 'gotta go, customers' and stop answering.",
        "planted": [["chef"], ["bus"], ["newspaper"], ["fish"], ["paring knives"]],
        "expect": {"max_vendor_turns": 5, "moves": {"finish_story", "finish_update", "nothing_here", "offer_pause"}},
    },
}


# ── Running one persona ──────────────────────────────────────────────────────

async def simulate_vendor(persona: dict, transcript: list[dict]) -> str:
    convo = "\n".join(("Interviewer: " if m["role"] == "agent" else "You: ") + m["content"] for m in transcript)
    v = persona["vendor"]
    return (await llm.text(
        skills.text("vendor-simulator"),
        (f"Who you are: {v['name']} of {v['business']}.\n"
         f"Your private facts: {persona['hidden']}\n"
         f"How you talk: {persona['style']}\n\n"
         f"Conversation so far:\n{convo}\n\nYour reply:"),
        max_tokens=400, tag="vendor-simulator",
    )).strip()


def resolve_hook(pick) -> dict:
    if isinstance(pick, dict):
        return pick
    h = scout.hook_for(pick, [])
    if not h:
        raise ValueError(f"Unknown story pick: {pick}")
    return h


def found(patterns: list[str], text: str) -> bool:
    t = storymap.norm(text)
    return any(storymap.norm(p) in t for p in patterns)


def recall(planted: list[list[str]], text: str) -> list[bool]:
    return [found(p, text) for p in planted]


async def run_persona(key: str, with_draft: bool) -> dict:
    persona = PERSONAS[key]
    vendor = persona["vendor"]
    expect = persona.get("expect", {})
    profile = {**vendor, "memory": {}}
    h = resolve_hook(persona["pick"])
    m = storymap.new_map(h)
    log: list[dict] = []          # annotated transcript lines for the report
    hard: list[str] = []          # hard check failures
    lint_problems = 0

    if h.get("id") == "free":
        # The vendor starts talking on their own: no opener, their first message is the story.
        transcript: list[dict] = []
        first = await simulate_vendor(persona, [{"role": "agent", "content": "What's on your mind this week?"}])
        transcript.append({"role": "vendor", "content": first})
        log.append({"role": "agent", "text": "(free choice: the vendor starts)", "skill": "opener"})
        log.append({"role": "vendor", "text": first})
        opening_done = True
    else:
        msg, problems = await interviewer.opening(profile, h)
        lint_problems += len(problems)
        transcript = [{"role": "agent", "content": msg}]
        log.append({"role": "agent", "text": msg, "skill": "opener", "problems": problems})
        opening_done = True
        transcript.append({"role": "vendor", "content": await simulate_vendor(persona, transcript)})
        log.append({"role": "vendor", "text": transcript[-1]["content"]})
    assert opening_done

    last_turn = None
    for _ in range(MAX_SIM_TURNS):
        turn = await interviewer.next_turn(profile, m, transcript)
        last_turn, m = turn, turn.story_map
        if turn.message:
            transcript.append({"role": "agent", "content": turn.message})
            log.append({"role": "agent", "text": turn.message, "skill": turn.skill or turn.move, "problems": turn.problems,
                        "target": turn.target, "reason": turn.reason})
            lint_problems += len(turn.problems)
        if turn.move == "offer_pause":
            log.append({"role": "vendor", "text": f"[taps] {PAUSE_REPLY}"})
            q, problems = await interviewer.micro_question(profile, m, transcript)
            m["pauses"] = int(m.get("pauses", 0)) + 1
            m["micro"] = {"question": q, "sent": True}
            lint_problems += len(problems)
            transcript.append({"role": "agent", "content": q})
            log.append({"role": "agent", "text": f"[next morning] {q}", "skill": "micro-session", "problems": problems})
        elif turn.finished:
            break
        reply = await simulate_vendor(persona, transcript)
        transcript.append({"role": "vendor", "content": reply})
        log.append({"role": "vendor", "text": reply})

    move = last_turn.move if last_turn else "none"
    vendor_texts = [x["content"] for x in transcript if x["role"] == "vendor"]
    all_vendor = "\n".join(vendor_texts)
    agent_msgs = [x["content"] for x in transcript if x["role"] == "agent"]

    # ── Hard checks on the interview ─────────────────────────────────────────
    if lint_problems:
        bad = [f'"{e["text"][:70]}": {"; ".join(e["problems"])}' for e in log if e.get("problems")]
        hard.append(f"{lint_problems} interviewer message(s) broke the rules: " + " | ".join(bad[:3]))
    for a in agent_msgs:
        if " why " in f" {a.lower()} " or a.lower().startswith("why"):
            hard.append(f'a message asked "why": {a[:70]}')
            break
    if m["vendor_turns"] > storymap.MAX_VENDOR_TURNS:
        hard.append(f"{m['vendor_turns']} vendor answers (cap is {storymap.MAX_VENDOR_TURNS})")
    if expect.get("moves") and move not in expect["moves"]:
        hard.append(f"ended with '{move}', expected one of {sorted(expect['moves'])}")
    for sk in expect.get("skills", []):
        if not m["skill_counts"].get(sk) and move != "escalate":
            hard.append(f"expected the '{sk}' skill to be used, it was not")
    if expect.get("max_vendor_turns") and m["vendor_turns"] > expect["max_vendor_turns"]:
        hard.append(f"took {m['vendor_turns']} answers, expected at most {expect['max_vendor_turns']}")
    if "sensitive-guard" in expect.get("skills", []):
        # The guard must come before the wrap-up, not after.
        order = [e.get("skill") for e in log if e["role"] == "agent"]
        if "sensitive-guard" in order and "wrap-up" in order and order.index("sensitive-guard") > order.index("wrap-up"):
            hard.append("the sensitive-guard question came after the wrap-up")

    # ── Draft ────────────────────────────────────────────────────────────────
    draft = None
    kind = {"finish_story": "story", "finish_update": "update"}.get(move)
    # Same rule as production (content/pipeline._finish): anything sensitive goes to a person, not to the writer.
    routed_to_person = bool(last_turn and (last_turn.sensitive or move == "escalate"))
    if expect.get("routed_to_person") and not routed_to_person:
        hard.append("sensitive material was not routed to an editor")
    if kind and with_draft and not routed_to_person:
        try:
            draft = await write_checked(kind, profile, transcript, m if kind == "story" else None)
        except Exception as e:  # noqa: BLE001
            hard.append(f"the writing chain failed: {e}")
    if draft:
        g = draft["guard"]
        if g.get("invented_facts"):
            hard.append(f"draft has claims the vendor never made: {g['invented_facts'][:3]}")
        vn = [storymap.norm(t) for t in vendor_texts]
        for q in quotes_in(draft["body"]):
            if len(q.split()) >= 3 and not any(storymap.norm(q) in t for t in vn):
                hard.append(f'quote is not the vendor\'s words: "{q[:70]}"')
                break
        for word in expect.get("keep_out", []):
            if word in draft["body"].lower():
                hard.append(f'draft mentions "{word}" which the vendor asked to keep out')
                break

    planted = persona.get("planted", [])
    got = recall(planted, all_vendor)
    used = recall(planted, draft["body"]) if draft else [False] * len(planted)
    brief = (draft or {}).get("guard", {}).get("brief") or {}
    scores = brief.get("scores") or {}
    return {
        "key": key, "name": vendor["name"], "business": vendor["business"], "pick": h.get("title", h.get("id")),
        "move": move, "vendor_turns": m["vendor_turns"], "skills": m["skill_counts"], "mode": m["mode"],
        "yield": m["yield_history"], "pauses": m.get("pauses", 0), "lint_problems": lint_problems,
        "log": log, "hard": hard,
        "planted": [p[0] for p in planted], "elicited": got, "used": used,
        "draft": None if not draft else {"title": draft["title"], "body": draft["body"], "words": draft["words"],
                                          "kind": kind, "guard": draft["guard"]},
        "rubric": scores, "rubric_avg": round(sum(scores.values()) / len(scores), 2) if scores else None,
        "verdict": brief.get("verdict"), "missing": brief.get("whats_missing"),
        "story_map": storymap.prompt_view(m), "routed_to_person": routed_to_person,
    }


# ── Report ───────────────────────────────────────────────────────────────────

def frac(flags: list[bool]) -> str:
    return f"{sum(flags)}/{len(flags)}" if flags else "–"


def render(results: list[dict], stamp: str, fake: bool) -> str:
    out = [f"# Interview harness run {stamp}", ""]
    out.append("Model: " + ("**FAKE (rule-based stand-in). This run checks plumbing and routing only. Question quality is NOT measured.**" if fake
                            else f"{llm.DEFAULT_MODEL}"))
    out += ["", "| Vendor | Ended | Answers | Skills used | Rule breaks | Details got / used | Rubric avg | Hard fails |",
            "|---|---|---|---|---|---|---|---|"]
    for r in results:
        sk = ", ".join(f"{k}×{v}" for k, v in r["skills"].items()) or "–"
        out.append(f"| {r['name']} ({r['key']}) | {r['move']} | {r['vendor_turns']} | {sk} | {r['lint_problems']} | "
                   f"{frac(r['elicited'])} / {frac(r['used'])} | {r['rubric_avg'] if r['rubric_avg'] is not None else '–'} | "
                   f"{'**' + str(len(r['hard'])) + '**' if r['hard'] else '0'} |")
    out.append("")
    for r in results:
        out += [f"## {r['name']} — {r['business']}  (`{r['key']}`)", "", f"Story picked: *{r['pick']}* · mode at end: {r['mode']} · "
                f"yield per answer: {r['yield']} · micro-sessions: {r['pauses']}", ""]
        for e in r["log"]:
            if e["role"] == "agent":
                tag = f"`{e.get('skill')}`" + (f" ⚠ {'; '.join(e['problems'])}" if e.get("problems") else "")
                out.append(f"> **Interviewer** {tag}: {e['text']}")
            else:
                out.append(f"> **{r['name']}:** {e['text']}")
            out.append(">")
        out += ["", f"**Outcome:** `{r['move']}`", ""]
        if r["planted"]:
            out.append("**Details the vendor knew** (got it out of them / used in the draft): " +
                       ", ".join(f"{p} {'✓' if g else '✗'}/{'✓' if u else '✗'}" for p, g, u in zip(r["planted"], r["elicited"], r["used"])))
            out.append("")
        d = r["draft"]
        if r.get("routed_to_person"):
            out += ["*Sensitive material: nothing is drafted automatically. This goes to an editor under “Needs a person first”.*", ""]
        elif d:
            g = d["guard"]
            out += [f"### Draft ({d['kind']}, {d['words']} words) — style check {'PASS' if g['pass'] else 'FLAGGED'}", "",
                    f"**{d['title']}**", "", d["body"], "",
                    f"*Check:* {g['notes']} · claims {g.get('claims_supported', '?')}/{g.get('claims_total', '?')} traced to the vendor", ""]
            if r["rubric"]:
                out.append("*Rubric (1-4):* " + ", ".join(f"{k} {v}" for k, v in r["rubric"].items()) +
                           f" · verdict **{r['verdict']}**" + (f" · missing: {r['missing']}" if r["missing"] else ""))
                out.append("")
        else:
            out += ["*No draft was written for this run.*", ""]
        if r["hard"]:
            out += ["**HARD FAILS**", ""] + [f"- {x}" for x in r["hard"]] + [""]
    n_fail = sum(1 for r in results if r["hard"])
    out += ["---", f"{len(results)} vendor(s), {n_fail} with hard failures."]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("personas", nargs="*", help="which personas to run (default: all)")
    ap.add_argument("--no-draft", action="store_true", help="interview only; skip the writing chain")
    ap.add_argument("--list", action="store_true", help="list personas and exit")
    args = ap.parse_args(argv)

    if args.list:
        for k, p in PERSONAS.items():
            print(f"{k:10} {p['vendor']['name']:8} {p['style'][:80]}")
        return 0
    unknown = [k for k in args.personas if k not in PERSONAS]
    if unknown:
        print(f"Unknown persona(s): {', '.join(unknown)}. Try --list.")
        return 2
    keys = args.personas or list(PERSONAS)

    async def go() -> list[dict]:
        res = []
        for k in keys:
            print(f"running {k}...", flush=True)
            res.append(await run_persona(k, not args.no_draft))
        return res

    results = asyncio.run(go())
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    out_dir = pathlib.Path(__file__).parent / "harness_runs"
    out_dir.mkdir(exist_ok=True)
    fake = bool(llm.FAKE_LLM)
    (out_dir / f"run-{stamp}.md").write_text(render(results, stamp, fake), encoding="utf-8")
    (out_dir / f"run-{stamp}.json").write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(out_dir / f"run-{stamp}.md")
    failed = [r["key"] for r in results if r["hard"]]
    if failed:
        print("HARD FAILS:", ", ".join(failed))
        for r in results:
            for x in r["hard"]:
                print(f"  {r['key']}: {x}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
