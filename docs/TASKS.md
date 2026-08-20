# Brown Bag — Task Board

*Updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\TASKS.md`*

> **Doc rule:** REPLACED each session, never appended. Finished work moves to the completed log.

---

## The Organizing Question

**What's the shortest path to one real issue landing in one real inbox?**

Everything on that path is P0. Everything else waits — including things that feel core. The QR scan flow isn't P0 (hand-add test subscribers). The interviewer agent isn't P0 (paste in 素材 by hand).

---

## 🔴 P0 — One issue, end to end

| # | Task | Status |
|---|---|---|
| 1 | `database/models.py` — 19 tables | ✅ deployed |
| 2 | Archive v1 routers, clean `main.py` | ✅ deployed |
| 3 | **Seed data** — market, neighbourhoods, category pairs, test vendors | ⬜ next |
| 4 | **Writer agent** (`content/writer.py`) | ⬜ |
| 5 | **Style guard** (`content/style_guard.py`) | ⬜ |
| 6 | **Editor login + review queue** | ⬜ |
| 7 | **Personalizer** — exclude seen → score → select | ⬜ |
| 8 | **Renderer** — HTML, 9 slots, ≤1000 words | ⬜ |
| 9 | **Dispatcher** — Resend + write `seen_blocks` | ⬜ |
| 10 | **Unsubscribe** — one-click, immediate | ⬜ |

**Build 4 and 5 together.** The style guard isn't polish — it's what stops filler ever reaching a reader.

**Done means:** paste in three submissions → writer drafts → approve → issue assembles and sends to three test addresses → **each gets a different selection.**

⚠️ Prompt quality deliberately deferred to after P1. See `STATUS.md`.

---

## 🟡 P1 — Real vendors can participate

| # | Task |
|---|---|
| 11 | Invitation codes — generate, validate, use tracking |
| 12 | Vendor signup form — code prefill, fixed category list |
| 13 | Magic link + 90-day session |
| 14 | **Interviewer agent** (`content/interviewer.py`) |
| 15 | Gap tracking + question selection |
| 16 | **"Nothing here" exit** — end a conversation with no submission |
| 17 | Sensitivity flagging |
| 18 | Vendor reminder emails — question in the subject line |
| 19 | Photo upload + fal.ai enhancement |

**The risk lives here, not in P0.** Getting a maker to mention her daughter is harder than writing the paragraph once she has.

---

## 🟢 P2 — Readers join, vendors collaborate

| # | Task |
|---|---|
| 20 | Scan landing `/v/{scan_code}` + subscribe flow |
| 21 | Interest vector + inferred neighbourhood |
| 22 | Vendor draft preview + corrections |
| 23 | Vendor library |
| 24 | Editor roster |
| 25 | Supply monitor |
| 26 | Scheduler jobs |

---

## 🔵 P3 — Later

- Ads and sponsors (⚠️ this is the revenue — pull forward if needed)
- Events block · referral block · greeting workflow
- Escalation queue UI · reader preferences · open/click tracking
- **Prompt craft pass** — tune writer and interviewer against real material
- Multi-market

---

## 🧹 Cleanup Debt

- [ ] **⚠️ Rewrite `Privacy.tsx` and `Terms.tsx`** — both describe the Instagram product and Stripe billing. They're legal documents currently making false statements. **Must be done before any real reader subscribes.**
- [ ] Remove or rebuild `/blog`, `/help`, `/signup`, `/setup` — all stale, now unlinked
- [ ] Brown Bag reader-facing site (separate from the Marlo page) — Morning Brew style, subscription options, featured story

---

## ❓ Decisions Needed From Anna

| Decision | Blocks |
|---|---|
| **Brown Bag sending domain** (not marlo021.ai) | P0 #9 |
| One React app with role routing, or two? | P0 #6 |
| Physical QR format | P2 #20 |

---

## ✅ Completed Log

### August 12, 2026 — Design settled, foundation deployed, landing page rebuilt
- [x] Named the publication **Brown Bag**; Marlo is the backend system name
- [x] **Two-agent split**: interviewer gathers 素材, writer writes the story
- [x] **Invitation-code vendor signup** — codes carry market + neighbourhood, live immediately
- [x] `category_pairs` — complementary categories derived, zero editor work per signup
- [x] **Seen is permanent** — `seen_blocks` table, distinct from vendor fatigue
- [x] **Vendors see drafts before editors** — `vendor_preview` + `block_corrections`
- [x] **No turn limit** on conversations; they persist across sessions
- [x] Neighbourhood-tiered proximity (same +20 / adjacent +12 / city +6)
- [x] Content standards rewritten; difficult material allowed, never fish for pain
- [x] Writer agent test (`WRITER_TEST.md`) — bar reachable, failure is upstream
- [x] `TABLES_EXAMPLE.md` — all 19 tables with worked example data
- [x] **`database/models.py` — 19 tables, deployed**
- [x] **All v1 routers archived; `main.py` v0.3.0 deployed clean**
- [x] **Marlo landing page rebuilt** — light editorial, six figures, live inbox-dealing and interview animations
- [x] `LANDING_PAGE_REFERENCE.md` — NewForm design notes

### August 11, 2026 — Cleanup
- [x] Archived Instagram/Stripe code via `git mv`
- [x] Rewrote `main.py` and `scheduler.py`
- [x] Consolidated docs 11 → 8

### August 4, 2026 — Pivot
- [x] Redefined the product: consumer newsletter, free both sides
- [x] "The issue ships every week; the pipeline flexes"
- [x] Rule 4 in `COLLABORATION_GUIDE.md` — no unsolicited startup advice

### Earlier
- [x] Instagram posting, OAuth, user memory, vendor profiles, content safety, email flows *(all archived)*