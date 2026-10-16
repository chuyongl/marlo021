# Brown Bag — Current Status

*Last updated: October 15, 2026*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**The pilot product is deployed on marlo021.ai** (API on api.marlo021.ai, version `0.5.0`): public website, vendor app, editor app, the weekly issue, and a live report for market organizers.

**v0.5.0 replaced the story engine** (details in `docs/STORY_ENGINE.md`): the vendor picks a story from a menu, an interviewer built from small editable skills deepens one moment at a time, the draft is written by a five-step chain, and the vendor checks a short list of facts instead of proofreading. Editors can edit every skill's wording in **Editor → Skills**.

The site starts with **five sample vendors** (marked "Sample") and their stories so every page has something to show. Remove them in Editor → Settings before real readers arrive.

---

## Entry Points

| Who | Where | How they get in |
|---|---|---|
| Readers | `/` , `/stories`, `/s/{slug}` | No login |
| Shoppers at a market (shared QR) | `/m/pike-place` | Tick vendors, enter email once |
| Shoppers at a stall (vendor QR) | `/v/{scan_code}` | Enter email once |
| Vendors | `/vendor` | Join at `/vendor/join` with a code (`PIKEPILOT`, `SEATTLE26`), then magic link |
| Editors | `/editor` | First time: setup code (given to Anna in chat), then email + password |
| Market organizers | `/report/{token}` | Private link from Editor → Markets & codes |
| Pitch pages | `/for-markets`, `/for-vendors` | Contact forms land in Editor → Inbox |

---

## What Changed in v0.5.0

**Backend**
- `content/skills/` (18 skill folders) + `content/skills.py`: skills loaded from files, editor overrides in table `skill_overrides`
- `content/scout.py`: story ideas for the weekly menu; `content/storymap.py`: story map + routing policy (plain code); `content/interviewer.py`: director, one skill per turn, rule lint; `content/nudges.py` + scheduler job: "one quick question tomorrow" emails
- `content/writer.py`: planner → drafter → fact-anchor → style-editor → editor brief; vendor claims check and revisions
- `content/llm.py`, `content/fake_llm.py`: model calls and a rule-based stand-in for tests
- New columns: `conversations.story_map/hooks/resume_at/nudge_count`, `messages.meta`, `blocks.claims/story_plan/history`; new table `skill_overrides` (added automatically at startup)
- Vendor API: `/vendor/conversation/start|pause|new`, claims check `/vendor/stories/{id}/check`. Editor API: `/editor/skills` (list, edit, reset, try)

**Frontend**
- Vendor app: story menu (scout ideas + fixed list + photo + free text), progress hint, quick-reply buttons, "I'll send one question tomorrow" state, claims checklist (Right / Not quite / Leave it out)
- Editor app: **Skills** tab, richer conversation view (skills used, rule flags), "Before you read" brief and claim table on each draft

**Tested locally** (fake AI, real Postgres, real browser): 32 unit tests; interview harness with 11 simulated vendors; full click-through (menu → conversation → claims fix → editor brief → skill edit/reset → conversation view); the morning-nudge job; legacy database migration.

---

## ⚠️ Deployed, Not Yet Verified With the Real Model

- **Real question and story quality.** The sandbox had no API key, so every test used the stand-in model. The rules (one question, no "why", echo) are enforced in code, but whether the questions are *good* needs a real conversation. First step: Anna does one as a vendor and sends the transcript.
- **Email.** Sends use `FROM_EMAIL` (Railway) or the address in Editor → Settings; must be a domain verified in Resend. Every place that sends a link also shows a copyable link.
- **Weekly send is manual.** Editor → This week's issue → Send. The scheduler now has one job (morning follow-up questions).

---

## 🔴 Next

1. Anna runs one real conversation at `/vendor`, reads it in Editor → Vendors → Open → Recent conversations, and edits the skills that miss (Editor → Skills)
2. Run `python -m tools.interview_harness` with the real key (needs `ANTHROPIC_API_KEY`) and read `backend/tools/harness_runs/`
3. Decide the sending domain and verify it in Resend
4. Remove sample content before the first real issue
5. Pike Place conversation using `/for-markets` and a report link

---

## Reference

| Item | Value |
|---|---|
| API | `https://api.marlo021.ai` (`/health` → 0.5.0) |
| Site | `https://marlo021.ai` |
| Deploy | push to `main` → Railway builds backend and frontend |
| Story engine design | `docs/STORY_ENGINE.md` |
| Tests | `python -m pytest backend/tests` (no API key needed) |
| Interview test harness | `backend/tools/interview_harness.py` (real key for real quality; `BB_FAKE_LLM=1` for plumbing) |
