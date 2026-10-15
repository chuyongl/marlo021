"""
Interview harness — runs the interviewer against simulated vendors and writes
a readable report, so we can judge question quality before real vendors see it.

Usage (from backend/):
    python -m tools.interview_harness            # all personas
    python -m tools.interview_harness mei karen  # some personas

Needs ANTHROPIC_API_KEY. Reports go to backend/tools/harness_runs/.

The simulated vendor knows things the interviewer doesn't, and only gives
them up when asked a good question. That is the point: a lazy interviewer
gets thin answers, a good one gets the story.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

from agent import interviewer
from agent.interviewer import client
from agent.writer import write_checked

MAX_TURNS = 14

PERSONAS = {
    "mei": {
        "vendor": {
            "name": "Mei",
            "business": "Fortune Noodle",
            "category": "prepared food",
            "neighborhood": "Ballard Farmers Market",
            "products": "hand-pulled noodles, chili oil",
            "known_facts": "Makes chili oil in small batches. Did a cooking demo in July.",
        },
        "hidden": (
            "Last Saturday you sold out of chili oil by 11am; you usually go till 2. You made 40 jars because last month "
            "you made 60 and took 20 home. A line formed before you finished setting up. A girl showed you a TikTok video "
            "of you making chili oil at the July demo, filmed without you knowing, 90,000 views. You don't have TikTok. "
            "It felt a little strange; 'my hands look old in it'. Your 12-year-old daughter made you watch it four times and "
            "said 'mom you're famous'; you said 'I'm not famous, I'm out of chili oil'. This week you're making 80 jars; you "
            "were up until 1am Tuesday toasting Sichuan peppercorns, the apartment smells, your neighbor knocked to check if "
            "something was burning."
        ),
        "style": "Friendly, answers in one or two sentences, a bit dry and funny. Doesn't volunteer the TikTok thing unless asked why it sold out or what happened.",
    },
    "dan": {
        "vendor": {
            "name": "Dan",
            "business": "Hollow Ridge Farm",
            "category": "produce",
            "neighborhood": "University District Farmers Market",
            "products": "kale, chard, tomatoes, seasonal vegetables",
        },
        "hidden": (
            "Rain last week split about a third of your late tomatoes. Usually split ones go to the pigs, but there were too "
            "many, so you made sauce for the first time: thirty-something jars, labeled in marker on masking tape. Your wife "
            "Jen found the recipe on the back of an old seed catalog. You'll have the sauce at the end of the table Saturday."
        ),
        "style": "Laconic farmer. Very short answers ('Just the usual.'). Only opens up when asked about something concrete.",
    },
    "karen": {
        "vendor": {
            "name": "Karen",
            "business": "Sweet Pea Bakery",
            "category": "bakery",
            "neighborhood": "Fremont Sunday Market",
            "products": "croissants, sourdough, pastries",
        },
        "hidden": "Nothing happened this week. Same products as always. It was busy.",
        "style": (
            "Talks only in upbeat marketing phrases: 'Everything's fresh!', 'We'd love to see everyone Saturday!'. "
            "Says 'we', never names anyone. Nothing changed, nothing went wrong. After 3-4 questions, says she has to get back to work."
        ),
    },
    "lena": {
        "vendor": {
            "name": "Lena",
            "business": "Lena Ruiz Jewelry",
            "category": "handmade jewelry",
            "neighborhood": "Pike Place Market (day stall)",
            "products": "hammered silver necklaces and earrings",
            "known_facts": "Day-stall artisan; her table location changes day to day.",
        },
        "hidden": (
            "You only got a table three days last week because day stalls go by seniority and the cruise-ship season ended. "
            "On the days you don't get a table you sell almost nothing. A woman from Ohio bought a necklace in August and "
            "emailed you a photo of wearing it at her daughter's wedding; you printed it and taped it inside your toolbox lid. "
            "You hammer every piece on an old railroad spike your grandfather gave you. This week you'll be at the north arcade "
            "Thursday and Saturday, and you just finished a new set of tiny moon pendants."
        ),
        "style": "Warm but busy, answers between customers, medium-length answers. Mentions the toolbox photo only if asked about customers or a specific piece.",
    },
    "otto": {
        "vendor": {
            "name": "Otto",
            "business": "Kettle & Smoke Sausage",
            "category": "butcher",
            "neighborhood": "Columbia City Farmers Market",
            "products": "smoked sausages, bratwurst",
        },
        "hidden": (
            "New this week: a smoked apple-sage sausage. Your quick recipe customers keep asking for: slice the sausage, brown "
            "it in a dry pan, add a sliced onion and a splash of cider, cook until sticky, serve on toast. You'll be at "
            "Columbia City Wednesday 3-7pm. Nothing dramatic happened."
        ),
        "style": "Practical, happy to share cooking tips, a few sentences per answer. Not a storyteller.",
    },
}

SIM_SYSTEM = """You are role-playing a small local vendor being interviewed by text message, between customers. Stay in character.
- Only say things consistent with your private facts. Never invent big new events. Small, natural filler is fine.
- Do not volunteer your private facts all at once. Answer what you're asked. A vague question gets a vague answer; a specific question gets a specific answer.
- Real people type short messages, skip punctuation sometimes, and don't narrate their feelings unless asked well.
- If the questions get boring or repetitive, say so briefly or say you need to get back to work.
Return only your reply text."""


def simulate_vendor(persona: dict, transcript: list[dict]) -> str:
    convo = "\n".join(
        ("Interviewer: " if m["role"] == "agent" else "You: ") + m["content"] for m in transcript
    )
    resp = client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SIM_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Who you are: {persona['vendor']['name']} of {persona['vendor']['business']}.\n"
                f"Your private facts: {persona['hidden']}\n"
                f"How you talk: {persona['style']}\n\n"
                f"Conversation so far:\n{convo}\n\nYour reply:"
            ),
        }],
    )
    return resp.content[0].text.strip()


def run(key: str) -> str:
    persona = PERSONAS[key]
    vendor = persona["vendor"]
    lines = [f"## {vendor['name']} — {vendor['business']}", ""]

    opening = interviewer.opening_question(vendor)
    transcript = [{"role": "agent", "content": opening}]
    stalled = 0
    turn = None

    for _ in range(MAX_TURNS):
        transcript.append({"role": "vendor", "content": simulate_vendor(persona, transcript)})
        turn = interviewer.next_turn(vendor, transcript, stalled)
        stalled = turn.stalled_turns
        lines.append(
            f"<!-- target={turn.target_gap} added_new={turn.added_new} stalled={stalled} move={turn.move} :: {turn.reason} -->"
        )
        if turn.message:
            transcript.append({"role": "agent", "content": turn.message})
        if turn.finished:
            break

    for m in transcript:
        who = "**Interviewer:**" if m["role"] == "agent" else f"**{vendor['name']}:**"
        lines.append(f"> {who} {m['content']}")
        lines.append(">")
    lines.append("")
    lines.append(f"**Outcome:** `{turn.move}` · sensitive={turn.sensitive} · gaps left: {turn.gaps_remaining or 'none'}")
    lines.append("")

    kind = {"finish_story": "story", "finish_update": "update"}.get(turn.move)
    if kind:
        draft = write_checked(kind, vendor, transcript)
        g = draft["guard"]
        lines += [
            f"### Draft ({kind}, {draft['words']} words) — guard: {'PASS' if g['pass'] else 'FAIL'}",
            "",
            f"**{draft['title']}**",
            "",
            draft["body"],
            "",
            f"*Guard notes:* {g['notes']}" + (f" · invented: {g['invented_facts']}" if g["invented_facts"] else ""),
            "",
        ]
    else:
        lines.append("*No draft — correct if there was nothing there.*\n")
    return "\n".join(lines)


def main(keys: list[str]) -> None:
    keys = keys or list(PERSONAS)
    out_dir = pathlib.Path(__file__).parent / "harness_runs"
    out_dir.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    report = [f"# Interview harness run {stamp}", ""]
    for k in keys:
        print(f"running {k}...", flush=True)
        report.append(run(k))
    path = out_dir / f"run-{stamp}.md"
    path.write_text("\n".join(report), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main(sys.argv[1:])
