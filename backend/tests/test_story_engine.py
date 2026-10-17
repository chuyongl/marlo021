"""
Tests for the story engine's deterministic parts and, with the fake model, its
orchestration. Run from backend/:   python -m pytest tests -q

These cannot judge writing quality: that needs the real model
(tools/interview_harness.py).
"""
import asyncio

from content import interviewer, nudges, scout, skills, speech, storymap, writer
from content.storymap import apply_observation, choose, new_map

EXPECTED_SKILLS = {
    "base-persona", "opener", "scene-deepener", "stakes-and-turn", "meaning-asker", "low-yield", "sensitive-guard",
    "wrap-up", "director", "story-scout", "story-planner", "story-drafter", "fact-anchor", "style-editor",
    "revision-handler", "update-writer", "editor-brief", "vendor-simulator",
}


def obs(**kw):
    base = {"scene": {"when": "", "where": "", "actions": [], "sensory": [], "dialogue": []}, "people": [],
            "want": "", "obstacle": "", "turn": "", "after": "", "meaning": "", "quotes": [], "facts": [], "update": "",
            "new_details": 0, "vendor_wants_to_stop": False, "no_story_claim": False, "language": "en",
            "language_difficulty": False, "sensitive": False, "sensitive_topic": "", "crisis": False, "target": "",
            "missing": [], "note": ""}
    base.update(kw)
    return base


def feed(m, text, n, **kw):
    o = obs(**kw)
    apply_observation(m, o, text, n)
    return choose(m, o)


# ── Skills ───────────────────────────────────────────────────────────────────

def test_all_skills_load_with_metadata():
    assert set(skills.names()) == EXPECTED_SKILLS
    for sk in skills.all_skills():
        assert sk.description and sk.stage in skills.STAGES and len(sk.body) > 100


def test_text_composes_persona_and_skill_with_examples():
    t = skills.text("base-persona", "scene-deepener")
    assert "Echo, then ask" in t and "Examples" in t and "FILMABLE".lower() in t.lower()


def test_override_replaces_body_and_reset_restores():
    default = skills.get("wrap-up").body
    skills.set_override("wrap-up", "Custom wrap-up text that is long enough.", "ed@example.com", "now")
    assert skills.get("wrap-up").body.startswith("Custom") and skills.get("wrap-up").edited
    skills.clear_override("wrap-up")
    assert skills.get("wrap-up").body == default and not skills.get("wrap-up").edited


# ── Linting the interviewer's words ─────────────────────────────────────────

def test_lint_accepts_a_good_message():
    msg = "The hand dryer, every thirty seconds. What did you do once you noticed?"
    assert interviewer.lint(msg, "scene-deepener", "The hand dryer ran every 30 seconds and people did not stop") == []


def test_lint_catches_the_known_bad_patterns():
    bad = {
        "That sounds great! Why did you start?": ['uses "why"', "exclamation mark"],
        "Tell me more about it. What was it like? And how did it feel?": ["more than one question"],
        "Great! What happened next?": ["opens with praise"],
        "What was the hardest day?": ["no echo line before the question"],
    }
    for msg, expected in bad.items():
        problems = interviewer.lint(msg, "scene-deepener", "I sold two pairs by the bathrooms that day")
        for e in expected:
            assert e in problems, (msg, problems)


def test_lint_requires_echo_to_reuse_the_vendors_words():
    p = interviewer.lint("Interesting. What happened next?", "scene-deepener", "They put me by the bathrooms and I sold two pairs")
    assert "echo does not reuse the vendor's words" in p


def test_lint_rejects_long_questions_and_repeat_openers():
    long_q = "The dryer. " + "What did you do once you noticed that it was running every thirty seconds all day long while customers " + "walked by without stopping at your table at all?"
    assert any("longer than" in x for x in interviewer.lint(long_q, "scene-deepener", "the dryer ran all day"))
    assert "starts the same way as the previous message" in interviewer.lint(
        "The dryer, okay. What happened next?", "scene-deepener", "", "The dryer, okay. What did you do?")


def test_wrap_up_must_not_ask():
    assert "must not ask a question" in interviewer.lint("Got it. Anything else?", "wrap-up")


def test_repair_keeps_the_first_question_only():
    out = interviewer.repair("The dryer. What did you do? And then what happened? Tell me more.", "scene-deepener")
    assert out.count("?") == 1 and out.endswith("do?")


# ── The story map and routing ───────────────────────────────────────────────

RICH = dict(
    scene={"when": "Saturday", "where": "by the bathrooms", "actions": ["moved the mirror", "girl tried the earrings"],
           "sensory": ["hand dryer every 30 seconds"], "dialogue": ["louder than the dryer"]},
    want="make rent that weekend", turn="moved the mirror to the front", after="mirror always goes in front",
    quotes=["these are louder than the dryer", "it's about where the table is"], new_details=5,
)
RICH_TEXT = "I moved the mirror to the front and a girl said these are louder than the dryer. Later: it's about where the table is."


def test_a_rich_answer_with_a_reflection_finishes_a_story():
    m = new_map({"id": "h1", "title": "t"})
    d = feed(m, RICH_TEXT, 1, meaning="it's about where the table is", **RICH)
    assert storymap.is_ready(m) and d.move == "finish_story" and d.skill == "wrap-up"


def test_a_ready_story_without_a_reflection_asks_for_it_once_and_then_wraps_up():
    m = new_map({"id": "h1", "title": "t"})
    d = feed(m, RICH_TEXT, 1, **RICH)
    assert storymap.is_ready(m) and (d.move, d.skill) == ("ask", "meaning-asker")
    storymap.record_skill(m, "meaning-asker")
    d = feed(m, "I did not expect to learn anything from a bathroom", 2, new_details=1)
    assert d.move == "finish_story"


def test_a_sitting_is_capped_at_eight_answers():
    assert storymap.MAX_VENDOR_TURNS == 8 and storymap.MAX_PAUSES == 1


def test_quotes_must_be_exact_words_or_they_are_dropped():
    m = new_map()
    apply_observation(m, obs(quotes=["something the vendor never said at all"], new_details=1), "I sold two pairs today", 1)
    assert m["quotes"] == []
    apply_observation(m, obs(quotes=["I sold two pairs today"], new_details=1), "I sold two pairs today", 2)
    assert len(m["quotes"]) == 1


def test_thin_scene_goes_to_scene_deepener_then_stakes_then_meaning():
    m = new_map()
    d = feed(m, "They put me by the bathrooms today and it was slow", 1, scene={**obs()["scene"], "where": "by the bathrooms"}, new_details=1)
    assert (d.move, d.skill) == ("ask", "scene-deepener")
    d = feed(m, "The dryer ran every thirty seconds and people did not stop", 2,
             scene={**obs()["scene"], "actions": ["people walked past", "dryer ran"], "sensory": ["dryer noise"]}, new_details=3)
    assert storymap.scene_ok(m) and d.skill == "stakes-and-turn"
    d = feed(m, "Rent was riding on that weekend and then I moved the mirror", 3, want="rent", turn="moved the mirror", new_details=2)
    assert storymap.stakes_ok(m) and d.skill == "meaning-asker"
    storymap.record_skill(m, "meaning-asker")
    d = feed(m, "I thought it was about the jewelry. It is about where the table is.", 4, new_details=1)
    assert d.move == "finish_story"


def test_scene_deepener_is_capped():
    m = new_map()
    for i in range(1, storymap.SCENE_MAX_TURNS + 1):
        d = feed(m, f"Another small thing happened here number {i} today", i, new_details=1, scene={**obs()["scene"], "where": f"place {i}"})
        assert d.skill == "scene-deepener"
        storymap.record_skill(m, "scene-deepener")
    d = feed(m, "One more small thing happened right here today again", storymap.SCENE_MAX_TURNS + 1, new_details=1)
    assert d.skill != "scene-deepener"


def test_a_one_word_answer_gets_an_easier_question():
    m = new_map()
    d = feed(m, "ok", 1, new_details=0)
    assert d.skill == "low-yield"


def test_thin_answers_switch_to_low_yield_then_offer_a_pause_then_finish():
    m = new_map()
    d = feed(m, "fine, not much really going on", 1, new_details=0)
    d = feed(m, "nothing really happened this week to say", 2, new_details=0)
    assert m["mode"] == "low_yield" and d.skill == "low-yield"
    feed(m, "idk man nothing at all to say right now", 3, new_details=0)
    d = feed(m, "i do not have anything to say about it", 4, new_details=0)
    assert d.move == "offer_pause"
    m["pause_offered"] = True
    d = feed(m, "no thanks really nothing to tell you about", 5, new_details=0)
    assert d.move == "nothing_here"


def test_no_story_claim_and_second_language_switch_modes_at_once():
    m = new_map()
    feed(m, "I just sell sausages, there is no story here", 1, no_story_claim=True, new_details=0)
    assert m["mode"] == "low_yield"
    m2 = new_map()
    feed(m2, "I make oil. Is good.", 1, language_difficulty=True, new_details=1)
    assert m2["mode"] == "low_yield"


def test_two_rich_answers_leave_low_yield_mode():
    m = new_map()
    feed(m, "no story", 1, no_story_claim=True)
    feed(m, "The wok is my mom's and it is very old now", 2, new_details=2)
    feed(m, "Yesterday I made forty jars in it before noon", 3, new_details=3)
    assert m["mode"] == "normal"


def test_sensitive_material_is_handled_before_anything_else():
    m = new_map()
    d = feed(m, "My mother has cancer so I started selling", 1, sensitive=True, sensitive_topic="a parent's illness", new_details=1)
    assert d.skill == "sensitive-guard" and m["private"]
    storymap.record_skill(m, "sensitive-guard")
    d = feed(m, "Keep it out please. Anyway the first sale was a ring", 2, new_details=2)
    assert d.skill != "sensitive-guard"


def test_crisis_escalates():
    m = new_map()
    assert feed(m, "i want to end it all", 1, crisis=True).move == "escalate"


def test_vendor_who_stops_keeps_the_best_outcome():
    m = new_map()
    assert feed(m, "that's all", 1, vendor_wants_to_stop=True).move == "nothing_here"
    m = new_map()
    assert feed(m, "that's all. Thursday at the north arcade", 1, vendor_wants_to_stop=True, update="North arcade Thursday").move == "finish_update"
    m = new_map()
    d = feed(m, "that's all I have to tell you", 1, vendor_wants_to_stop=True, **{**RICH, "quotes": []})
    assert d.move == "finish_story"


def test_hard_cap_on_answers():
    m = new_map()
    d = None
    for i in range(1, storymap.MAX_VENDOR_TURNS + 1):
        d = feed(m, f"a small thing number {i} happened at the stall today", i, new_details=1, scene={**obs()["scene"], "where": f"spot {i}"})
    assert d.move in ("finish_story", "finish_update", "nothing_here")


def test_target_falls_back_to_the_vendors_own_words():
    m = new_map()
    apply_observation(m, obs(target="words the vendor never typed", new_details=1), "The wok is my mom's and very old", 1)
    assert m["target"] == "The wok is my mom's and"


# ── Writing helpers ──────────────────────────────────────────────────────────

def test_style_lint_flags_ai_phrasing_but_not_a_vendors_exclamation():
    assert "journey" in writer.style_lint("It was a journey of passion.")
    assert "exclamation mark" in writer.style_lint("She loves it!")
    assert "exclamation mark" not in writer.style_lint('She said, "I\'m not famous, I\'m out of chili oil!" and laughed.')


def test_quotations_are_snapped_to_the_vendors_exact_words():
    vt = ["I thought it was about the jewelry. It is about where the table is."]
    body = 'She says, "It\'s about where the table is." Later she added: "completely invented line here nobody said".'
    fixed = writer.snap_quotes(body, vt)
    assert "It is about where the table is" in fixed
    assert "completely invented line here nobody said" in fixed   # left for the fact anchor to flag


def test_claims_merge_model_claims_with_code_checked_quotes():
    transcript = [{"role": "agent", "content": "q"}, {"role": "vendor", "content": "I made forty jars and sold out by eleven."}]
    body = 'She made forty jars. She said, "I made forty jars and sold out by eleven." Then: "never said this phrase at all".'
    anchor = {"claims": [{"text": "You made forty jars.", "kind": "number", "status": "supported", "turns": [1], "evidence": "forty jars"},
                         {"text": "You sold at dawn.", "kind": "time", "status": "unsupported", "turns": [], "evidence": ""}]}
    claims = writer.build_claims(body, transcript, anchor)
    by_text = {c["text"]: c for c in claims}
    assert by_text["You sold at dawn."]["status"] == "unsupported"
    assert by_text["I made forty jars and sold out by eleven."]["status"] == "supported"
    assert by_text["never said this phrase at all"]["status"] == "unsupported"
    assert [c["id"] for c in claims] == [f"c{i}" for i in range(1, len(claims) + 1)]
    assert len(writer.unsupported_of(claims)) == 2


# ── Orchestration with the fake model ───────────────────────────────────────

PROFILE = {"name": "Test Necklaces", "category": "jewelry", "neighborhood": "Pike Place", "products": "silver necklaces"}


def run(coro):
    return asyncio.run(coro)


def test_scout_cleans_and_numbers_hooks():
    hooks = run(scout.scout(PROFILE, {"today": "Thursday"}))
    assert [h["id"] for h in hooks] == ["h1", "h2", "h3"] and all(h["bait"].endswith("?") for h in hooks)
    assert scout.hook_for("h2", hooks)["source"] == "scout" and scout.hook_for("fire", hooks)["source"] == "menu"
    assert scout.hook_for("nope", hooks) is None


def test_full_interview_with_the_fake_model_reaches_a_story_and_every_message_is_clean():
    m = new_map({"id": "h1", "title": "The Saturday you sold out"})
    transcript = [{"role": "agent", "content": "Tell me about the last Saturday you sold out. What time did the last one go?"}]
    answers = [
        "They put me by the bathrooms and I sold like two pairs. The hand dryer ran every 30 seconds.",
        "I moved my mirror to the front so people could try earrings. A girl said these are louder than the dryer.",
        "Rent was riding on that weekend. Now the mirror always goes in front.",
        "I thought it was about the jewelry. It is about where the table is.",
    ]
    last = None
    for a in answers:
        transcript.append({"role": "vendor", "content": a})
        last = run(interviewer.next_turn(PROFILE, m, transcript))
        m = last.story_map
        assert last.problems == [], last.problems
        transcript.append({"role": "agent", "content": last.message})
        if last.finished:
            break
    assert last.finished and last.move == "finish_story"
    assert m["stage"] == "done" and m["skill_counts"]["wrap-up"] == 1
    assert m["skill_counts"].get("meaning-asker") == 1      # the reflection is asked once before wrapping up


def test_writing_chain_with_the_fake_model_returns_claims_and_a_guard():
    transcript = [
        {"role": "agent", "content": "Tell me about it."},
        {"role": "vendor", "content": "I made forty jars. They were gone by eleven."},
        {"role": "agent", "content": "Gone by eleven. What did you do next?"},
        {"role": "vendor", "content": "I went home and made eighty more."},
    ]
    draft = run(writer.write_story(PROFILE, transcript, None))
    assert draft["kind"] == "story" and draft["title"] and draft["body"]
    assert draft["claims"] and all(c["id"].startswith("c") for c in draft["claims"])
    assert "pass" in draft["guard"] and draft["plan"]["shape"]
    assert all(c["status"] != "unsupported" for c in draft["claims"])


def test_unsupported_claims_are_removed_before_anyone_sees_the_draft(monkeypatch):
    transcript = [{"role": "vendor", "content": "I made forty jars. They were gone by eleven."}]

    async def drafty(profile, transcript, story_map, plan):
        return "Forty jars", "She made forty jars. Zzz an invented detail about a purple tent. They were gone by eleven."

    monkeypatch.setattr(writer, "draft_story", drafty)
    draft = run(writer.write_story(PROFILE, transcript, None))
    assert "purple tent" not in draft["body"]
    assert not writer.unsupported_of(draft["claims"])


def test_a_vivid_scene_alone_is_enough_for_a_short_story():
    m = new_map()
    d = feed(m, "A line formed before I finished setting up and a girl showed me a video of me", 1, new_details=4,
             scene={"when": "", "where": "at the stall", "actions": ["a line formed", "a girl showed me a video"], "sensory": [], "dialogue": []})
    storymap.record_skill(m, "stakes-and-turn")
    storymap.record_skill(m, "stakes-and-turn")
    m["meaning_asked"] = True
    d = feed(m, "it felt strange to see my own hands", 2, new_details=1)
    assert storymap.is_thin_ok(m) and d.move == "finish_story"


def test_private_topics_reach_the_writer():
    from content import writer
    m = new_map()
    m["private"] = ["a death in the family"]
    ctx = writer._story_context({"name": "Rosa"}, [{"role": "vendor", "content": "My husband died in March."}], m)
    assert "PRIVATE" in ctx and "a death in the family" in ctx
    assert "PRIVATE" not in writer._story_context({"name": "Rosa"}, [{"role": "vendor", "content": "Hi there friend"}], new_map())


def test_a_good_answer_after_a_pause_gets_fresh_chances():
    m = new_map()
    feed(m, "ok", 1, new_details=0)
    feed(m, "fine", 2, new_details=0)
    feed(m, "idk", 3, new_details=0)
    feed(m, "nothing really", 4, new_details=0)
    assert m["mode"] == "low_yield" and m["low_turns_in_mode"] >= 2
    m["pause_offered"] = True
    d = feed(m, "A woman with a stroller bought the last two at two o'clock", 5, new_details=2)
    assert m["low_turns_in_mode"] == 0
    assert d.move == "ask", d


def test_the_opener_is_an_invitation_not_a_one_question_message():
    invite = ("Think of the last time a regular came for their one thing. Tell me about it from the start, whatever you "
              "remember. As long as you like, or just talk into your phone.")
    assert interviewer.lint(invite, "opener") == []
    assert "no question" in interviewer.lint(invite, "scene-deepener")        # every other skill still needs one question
    assert "more than one question" in interviewer.lint("Tell me. Where? When?", "opener")
    assert any("why" in p for p in interviewer.lint("Tell me about it from the start. Why did it happen?", "opener"))
    long = " ".join(["word"] * 80)
    assert any("longer than 70" in p for p in interviewer.lint(long, "opener"))
    assert len(interviewer.repair(long + ".", "opener").split()) <= interviewer.MAX_INVITE_WORDS


def test_claims_list_what_is_least_certain_first_and_keeps_the_new_kinds():
    transcript = [{"role": "agent", "content": "q"}, {"role": "vendor", "content": "Forty jars, all gone by eleven. My daughter helped."}]
    mk = lambda text, kind, status: {"text": text, "kind": kind, "status": status, "turns": [1] if status != "unsupported" else [], "evidence": ""}
    anchor = {"claims": [mk("You made forty jars.", "number", "supported"),
                         mk("You sold out.", "event", "inferred"),
                         mk("Your daughter was proud.", "tone", "unsupported"),
                         mk("Your daughter helped.", "person", "supported"),
                         mk("It means 'good morning'.", "translation", "inferred")]}
    claims = writer.build_claims("Body with no quotes.", transcript, anchor)
    order = [c["status"] for c in claims]
    assert order == sorted(order, key=["unsupported", "inferred", "supported"].index)
    assert {c["kind"] for c in claims} >= {"tone", "translation", "person"}
    many = {"claims": [mk(f"Fact {i}.", "other", "supported") for i in range(20)]}
    assert len(writer.build_claims("x", transcript, many)) <= writer.MAX_CLAIMS_SHOWN


def test_voice_memos_come_back_as_text_with_the_fake_model():
    assert speech.available()
    assert asyncio.run(speech.transcribe(b"x" * 3000, "audio/webm;codecs=opus")) == speech.FAKE_TRANSCRIPT
    assert speech.filename_for("audio/mp4") == "memo.m4a"
    assert speech.filename_for("audio/webm;codecs=opus") == "memo.webm"
    assert speech.filename_for("") == "memo.webm"


def test_a_vendor_who_goes_quiet_gets_one_reminder_not_three():
    assert nudges.MAX_NUDGES == 1
