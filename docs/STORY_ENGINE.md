# Brown Bag — The Story Engine

*Added October 15, 2026 (v0.5.0); revised October 17, 2026 (v0.6.0: free-recall opener, voice memos, fuller fact check, feedback to the vendor). Replaces the single-prompt interviewer and the single-step writer.*

> **Doc rule:** REPLACED when the engine changes, never appended.

## Why it changed

The first interviewer asked everything in one prompt and mostly collected basic facts (what, where, how many). Anna's verdict: "hunting for basic information, not stories. I need longer, good stories."

Research on interviewing practice (oral history, clean language, journalism, StoryCorps-style prompts) points the same way: people tell stories about **moments**, not topics; **one concrete question after an echo** beats a list; **"why" makes people defensive**; **reluctant or second-language speakers need easier questions, not more of them**; and a model writes better when each step has **one small job**. So the engine is a chain of small skills, each an editable instruction file, with the routing done in plain code.

## The flow

```
Vendor opens "This week"
  │
  ├─ Story scout (1 model call): 2-4 story ideas from profile, season, past headlines, notes, market news
  │  + fixed menu (first sale, hardest day, a regular, a mistake, fire, photo, something else)
  │
  ▼ vendor taps one
Opener skill ── an INVITATION, not a question: "Tell me about it from the start, whatever you
  │               remember. As long as you like, or just talk into your phone." (photo variant reads the image)
  │               The vendor can type, or record a voice memo (see Voice memos).
  │
  ▼ for every vendor answer:
Director (model, tool call) ── updates the STORY MAP from the newest answer
  │                           (scene details, people, want/obstacle/turn/after/meaning,
  │                            exact quotes, facts, "wants to stop", "I have no story",
  │                            language difficulty, sensitive, crisis, what to echo)
  ▼
storymap.choose() ── PLAIN CODE picks the next move. No model.
  │
  ▼
Interviewer = base-persona + ONE skill ── writes the message
  │
  ▼
Lint ── one question, <=25 words, no "why", no praise, no "!"/emoji, no banned phrases,
        echo reuses the vendor's words, no repeated opener. One retry, then a code repair.
```

## Routing policy (`backend/content/storymap.py`)

In order, first match wins:

| # | Condition | Move |
|---|---|---|
| 1 | Possible crisis | Stop, hand to a person, no draft |
| 2 | Vendor wants to stop | Finish with the best outcome (story > update > nothing) |
| 3 | 8 vendor answers | Finish (aim: a long free telling, then 4 to 6 sharp questions) |
| 4 | Sensitive topic raised and not yet handled | `sensitive-guard` (ask only: keep it out or mention generally?) |
| 5 | Story map ready (filmable scene + stakes, or a vivid scene alone) | `meaning-asker` once if the vendor has not said what it meant, then `wrap-up` |
| 6 | Low-yield mode (2 thin answers in a row, "I have no story", or language difficulty) | `low-yield` skill; after 2 more thin answers offer one question tomorrow (max 1 pause), else finish |
| 7 | One-word answer ("ok") | `low-yield` |
| 8 | Scene thin (fewer than 3 details or 2 actions) | `scene-deepener` (max 4) |
| 9 | No want/obstacle or no turn/after | `stakes-and-turn` (max 2) |
| 10 | Fewer than 2 quotes and meaning never asked | `meaning-asker` (once, last). The question is expectation versus reality: what the vendor thought it would be, and what it turned out to be |
| 11 | Otherwise | Finish. A vivid scene alone is enough for a short story |

Low-yield mode ends after two rich answers in a row. One rich answer resets the "thin" count, so someone who finally opens up after a pause is not cut off.

## Skills

Each is a folder `backend/content/skills/<name>/SKILL.md` (name, description, stage, instructions) plus optional example files read with it. Editors change the instructions in **Editor → Skills**; the next conversation uses them (cached at most 30 seconds). "Back to the original" restores the file version. Examples ship with the code and are read-only.

| Stage | Skills |
|---|---|
| Finding a story | `story-scout` |
| Interviewing | `base-persona` (rules every message follows), `opener`, `scene-deepener`, `stakes-and-turn`, `meaning-asker`, `low-yield`, `sensitive-guard`, `wrap-up` |
| Reading the answers | `director` |
| Writing and checking | `story-planner`, `story-drafter`, `fact-anchor`, `style-editor`, `revision-handler`, `update-writer`, `editor-brief` |
| Testing only | `vendor-simulator` |

## Micro-sessions

If a vendor is giving thin answers, the interviewer offers "one quick question tomorrow". If they accept, the question is written immediately (an extra-easy one) and a job running every 30 minutes (`content/nudges.py`) adds it to the conversation the next morning (market time) and emails a sign-in link. At most 1 reminder per conversation: one follow-up is a courtesy, three is a chase.

## The writing chain (`backend/content/writer.py`)

1. **story-planner**: picks a shape (scene-first, bait-first, object-centered), outlines beats that each cite the vendor turns they come from, proposes headlines, chooses quotes only from the verified list (exact vendor words found in the transcript).
2. **story-drafter**: writes from the outline. Plain, the vendor's voice, no marketing language.
3. **fact-anchor**: lists every claim in the draft and marks it supported / inferred / unsupported with the turn and evidence. Quotations are checked again in code; near-matches are snapped to the exact words.
4. Unsupported claims are removed (up to 2 passes via `revision-handler`).
5. **style-editor**: light polish; discarded if it changes more than 10% and introduces unsupported claims.
6. **editor-brief**: scores the draft 1-4 on scene, person, stakes, turn, voice, place, truthfulness, plainness, pull; verdict run / edit / hold; whether it could lead the issue.

Quick updates ("North arcade Thursday") use one `update-writer` call and a simple check.

## Vendor claims check

The vendor sees the first paragraph, can open the whole story or **listen to it** read aloud (the phone's own voice), and gets a short list of claims to mark **Right**, **Not quite** (with a note), or **Leave it out**. The list is ordered by how likely it is to be wrong, up to 14 claims plus quotes:

1. things we could not trace to their words (pre-selected "Leave it out"),
2. things we only worked out from what they said ("You didn't say this directly. Is it true?"),
3. the rest, by how embarrassing a wrong detail would be: numbers, names, places, times, people, events.

Claim kinds also include **tone** (a feeling or manner attributed to someone), **translation** (our English for something said in another language) and **person** ("This is about someone else. Is it okay to include?"). Their decisions are binding: `revision-handler` rewrites around them, claims are re-extracted, and they check the new version. After 2 revisions, or if the automatic rewrite fails, their note goes to the editor as a correction.

When everything is confirmed it goes to the editor, who sees the claim table, the rubric, the number the vendor confirmed, how long the vendor spent and whether they opened or listened to the whole story. A "confirmed everything in under 20 seconds without opening the story" chip tells the editor to look harder. Stored in `blocks.guard_notes.vendor_check`.

## Voice memos

The vendor can record up to five minutes instead of typing (button "Record instead of typing", shown only when `OPENAI_API_KEY` is set). The browser records, `POST /vendor/voice/transcribe` sends the audio to OpenAI's transcription model (`gpt-4o-transcribe` by default, set with `BB_STT_MODEL`), and the words come back **into the text box for the vendor to check and fix before sending**. The recording is not stored. Messages sent this way carry `meta.voice = true`; the editor sees a "spoken" chip. Limits: 12 MB per recording, 40 recordings per vendor per day.

Cost: about $0.006 per audio minute, $0.36 per hour. A pilot of 30 vendors doing 10 minutes a week is about $1.80 a week.

Speech to text can slip, especially with noise and less common languages. That is why the vendor always sees the text first. Not verified: accuracy for Amharic and other languages the model does not list; test with a real recording before promising it.

Words in another language: the writer quotes only the original words and gives the English meaning in parentheses without quotation marks; the translation is a claim the vendor checks.

## After publication

When an editor approves a story for the first time, the vendor gets an email ("Approved: {headline}") with the public link and, if the editor typed one, **a line from the editor** (Editor → Review → "A line for the vendor"). The line also shows on the story in the vendor app. Sample vendors get nothing, and approving again does not email again. Failure to send never blocks the approval.

## Privacy

Anything the vendor marked private reaches the writer as a PRIVATE block (leave it out unless the vendor clearly allowed it). In practice sensitive conversations are not drafted at all: they go to Editor → Review → "Needs a person first".

## Editor tools

- **Skills tab**: edit, reset, and "Try it" (runs one skill with the saved wording on an answer you type, and shows if it breaks the rules).
- **Vendors → Open → Recent conversations**: each message shows which skill wrote it and any rule problem; above it the skills used, the vendor's own lines, what they wanted and the turn.
- **Review**: "Before you read" box with verdict, rubric, claims traced, vendor-confirmed count and revisions; "Claim by claim" table.

## Testing

- `backend/tests/` (38 tests): routing policy, linting, claims check and ordering, privacy, voice stand-in, reminder cap. Run `python -m pytest backend/tests` with no API key.
- `python -m tools.interview_harness`: 11 simulated vendors (terse, rambler, second-language, "I have no story", marketing talk, sensitive, in a hurry, plus the five original ones). With a real key it measures how many planted details the interviewer gets out, rubric scores, and hard rule checks. With `BB_FAKE_LLM=1` it only proves the plumbing. Reports go to `backend/tools/harness_runs/`.
- `BB_FAKE_LLM=1` runs the whole app without a key (rule-based stand-in in `content/fake_llm.py`).

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `BB_MODEL` | `claude-sonnet-4-6` | Default model for everything |
| `INTERVIEWER_MODEL`, `WRITER_MODEL`, `GUARD_MODEL`, `JUDGE_MODEL`, `SCOUT_MODEL` | `BB_MODEL` | Per-step overrides |
| `BB_DIRECTOR_MODEL` | `BB_MODEL` | The director runs on every vendor answer. Set it to a smaller, cheaper model once quality is confirmed |
| `OPENAI_API_KEY` | unset | Turns on voice memos (the record button appears). Set it in the Railway backend service only; never in chat or in the repo |
| `BB_STT_MODEL` | `gpt-4o-transcribe` | Speech-to-text model (`gpt-4o-mini-transcribe` is half the price) |
| `BB_FAKE_LLM` | off | Use the stand-in model (voice returns a fixed sentence) |

## How to find out whether the new flow is better

Do not trust the design on paper. For 5 to 10 real vendors, run both ways and let Anna choose blind:

- **A (simple):** one open question ("Tell me about the last time something surprised you at the stall"), the vendor answers by voice or typing, straight into the writing chain.
- **B (full):** the whole flow above.

Anna reads both drafts without knowing which is which and picks the one she would run. If A wins or ties, collapse the routing to A plus one follow-up. Also record: minutes the vendor spent, words they gave, how many claims they changed, and how many of the vendors come back the next week.

## Not built yet

- A cheaper director model (a setting exists; needs a real-transcript comparison first).
- Reading the vendor's Instagram for the scout.
- Checking Amharic and other less common languages in speech to text.
- Real-model quality is untested at the time of writing: the sandbox had no API key. Run the harness and one real conversation first, then tune the skills in the editor.
