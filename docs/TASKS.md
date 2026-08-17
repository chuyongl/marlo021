# Brown Bag — Task Board

*Updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\TASKS.md`*

> **Doc rule:** REPLACED each session, never appended. Finished work moves to the completed log.

---

## The Organizing Question

**What's the shortest path to one real issue landing in one real inbox?**

Everything on that path is P0. Everything else waits — including things that feel core. The QR scan flow isn't P0 (hand-add test subscribers). The interviewer agent isn't P0 (paste in 素材 by hand). Neither is needed to prove an issue can be built and sent.

---

## ✅ P0 — Prerequisite (done)

- [x] **Writer agent test** — validated the quality bar against realistic 素材 before building. See `WRITER_TEST.md`.
  - Writer works when material is there
  - Thin material still publishable at 120 words
  - **Failure is upstream** — the interviewer is the harder build, not the writer
  - Two design changes fell out: `style_guard` matters more than weighted; interviewer needs a "nothing here" exit

---

## 🔴 P0 — One issue, end to end

| # | Task | Status |
|---|---|---|
| 1 | **`database/models.py`** — all 17 tables | ⬜ written, untested |
| 2 | **Clean up broken imports** — `main.py` routers referencing dead models | ⬜ |
| 3 | **Seed data** — one market, neighborhoods, category pairs, test vendors | ⬜ |
| 4 | **Writer agent** (`content/writer.py`) — 素材 → draft | ⬜ |
| 5 | **Style guard** (`content/style_guard.py`) — the rejector | ⬜ |
| 6 | **Editor login + review queue** | ⬜ |
| 7 | **Personalizer** — exclude seen → score → select | ⬜ |
| 8 | **Renderer** — HTML template, 9 slots, 4 fonts, ≤1000 words | ⬜ |
| 9 | **Dispatcher** — send via Resend + write `seen_blocks` | ⬜ |
| 10 | **Unsubscribe** — one-click, immediate | ⬜ |

**Build 4 and 5 together.** The style guard isn't a polish step — it's what stops filler ever reaching a reader. Building the writer without it produces something that can't be trusted.

**Done means:** paste in three submissions → writer drafts them → you approve → an issue assembles and sends to three test addresses → **each address gets a different selection.**

---

## 🟡 P1 — Real vendors can participate

| # | Task |
|---|---|
| 11 | Invitation codes — generate, validate, use tracking |
| 12 | Vendor signup form — code prefill, fixed category list |
| 13 | Magic link + 90-day session |
| 14 | **Interviewer agent** (`content/interviewer.py`) |
| 15 | Gap tracking (`content/gaps.py`) + question selection |
| 16 | **"Nothing here" exit** — end a conversation with no submission |
| 17 | Sensitivity flagging (`content/sensitivity.py`) |
| 18 | Vendor reminder emails — question in the subject line |
| 19 | Photo upload + fal.ai enhancement |

**Done means:** a real vendor gets an email, talks to the agent, and their story reaches the bank without you touching it.

**The risk lives here, not in P0.** Getting a vendor to mention her daughter is harder than writing the paragraph once she has.

---

## 🟢 P2 — Readers join, vendors collaborate

| # | Task |
|---|---|
| 20 | Scan landing `/v/{scan_code}` + subscribe flow |
| 21 | Interest vector + inferred neighborhood |
| 22 | Vendor draft preview + corrections |
| 23 | Vendor library — other vendors' published stories |
| 24 | Editor roster — vendors + story history |
| 25 | Supply monitor — approved vs pending vs reader pool depth |
| 26 | Scheduler jobs (reminder cycle, escalation, expiry, send) |

---

## 🔵 P3 — Later

- Ads and sponsors (⚠️ this is the revenue — pull forward if needed)
- Events block
- Referral block
- Greeting workflow
- Escalation queue UI
- Reader preferences page
- Open / click tracking
- Multi-market

---

## ❓ Decisions Needed From Anna

| Decision | Blocks |
|---|---|
| **Brown Bag sending domain** (not marlo021.ai) | Any outbound email — P0 #9 |
| One React app with role routing, or two? | P0 #6 (editor UI) |
| Physical QR format | P2 #20 |

---

## ✅ Completed Log

### August 12, 2026 — Design settled, models written
- [x] Named the publication **Brown Bag**; Marlo is now the backend system name
- [x] **Two-agent split**: interviewer gathers 素材, writer writes the story
- [x] **Invitation-code vendor signup** — codes carry market + neighborhood, live immediately, no editor activation
- [x] `category_pairs` table — complementary categories derived, zero editor work per signup
- [x] **Seen is permanent** — `seen_blocks` table, hard exclusion, distinct from vendor fatigue
- [x] **Vendors see drafts before editors** — `vendor_preview` status + `block_corrections`
- [x] **No turn limit** on conversations; they persist across sessions
- [x] Neighborhood-tiered proximity scoring (same +20 / adjacent +12 / city +6)
- [x] Content standards rewritten to a real quality bar; difficult material allowed, never fish for pain
- [x] `sensitivity.py` — flagged material never auto-drafts
- [x] Writer agent test (`WRITER_TEST.md`)
- [x] `database/models.py` — all 17 tables written

### August 11, 2026 — Cleanup
- [x] Archived Instagram/Stripe code to `backend/archive/` via `git mv`
- [x] Rewrote `main.py` (fault-tolerant router loading) and `scheduler.py` (jobs stripped)
- [x] Consolidated docs 11 → 7

### August 4, 2026 — Pivot
- [x] Redefined the product: consumer newsletter, free both sides
- [x] "The issue ships every week; the pipeline flexes" as a governing principle
- [x] Rule 4 in `COLLABORATION_GUIDE.md` — no unsolicited startup advice

### Earlier
- [x] Instagram posting, OAuth, user memory, vendor profiles, content safety, all core email flows, privacy + terms pages *(all archived)*