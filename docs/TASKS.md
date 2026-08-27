# Brown Bag — Task Board

*Updated: August 27, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\TASKS.md`*

> **Doc rule:** REPLACED each session, never appended. Finished work moves to the completed log.

---

## The Organizing Question

**What's the shortest path to one real issue landing in one real inbox?**

Everything on that path is P0. Everything else waits. The QR scan flow isn't P0 (hand-add test subscribers). The interviewer agent isn't P0 (paste in 素材 by hand).

---

## 🔴 P0 — One issue, end to end

| # | Task | Status |
|---|---|---|
| 1 | `database/models.py` — 19 tables | ✅ deployed |
| 2 | Archive v1 routers, clean `main.py` | ✅ deployed |
| **2b** | **Subscriber schema fix** — drop `market_id`, add `home_market_id` | **← do first** |
| 3 | **Seed data** | ⬜ |
| 4 | **Writer agent** (`content/writer.py`) | ⬜ |
| 5 | **Style guard** (`content/style_guard.py`) | ⬜ build with #4 |
| 6 | Editor login + review queue | ⬜ |
| 7 | Personalizer | ⬜ |
| 8 | Renderer | ⬜ |
| 9 | Dispatcher | ⬜ |
| 10 | Unsubscribe | ⬜ |

### 2b — the schema fix, before anything writes rows

Three edits to `Subscriber` in `database/models.py`:
- Drop `market_id`
- Remove `UniqueConstraint("market_id","email")`; `email` becomes globally unique
- Add `home_market_id` (nullable, FK → markets)

Then in Railway SQL:
```sql
ALTER TABLE subscribers DROP COLUMN IF EXISTS market_id;
```
Safe — the table is empty.

### 3 — seed data

One market, the neighborhood adjacency map, category pairs, three or four vendors with scan codes, one editor, a few readers with different follow patterns.

**Include awkward cases on purpose:** a silent vendor, an unapproved block, a reader with zero follows. Seed data that's too tidy hides the bugs it exists to surface.

Idempotent, runnable on demand, gated so it can't inject test rows into a live market.

**Done means:** paste in three submissions → writer drafts → approve → issue assembles and sends to three test addresses → **each gets a different selection.**

---

## 🟡 P1 — Real vendors can participate

| # | Task |
|---|---|
| 11 | Invitation codes — generate, validate, use tracking |
| 12 | Vendor signup form — code prefill, fixed category list |
| 13 | Magic link + 90-day session |
| 14 | **Interviewer agent** |
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
| 21 | Interest vector + inferred neighborhood + `home_market_id` |
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

- [ ] **⚠️ Rewrite `Privacy.tsx` and `Terms.tsx`** — both describe the Instagram product and Stripe billing. Legal documents currently making false statements. **Before any real reader subscribes.**
- [ ] Delete the orphaned page files: `Signup`, `Setup`, `Help`, `Blog`, `BlogPost_HowMarloThinks`
- [ ] Fold `SUBSCRIBER_MARKET_CHANGE.md` into `DATA_MODEL.md`, then delete it
- [ ] Brown Bag reader-facing page (separate from the Marlo site) — subscribe, featured story

---

## ❓ Decisions Needed From Anna

| Decision | Blocks |
|---|---|
| **Brown Bag sending domain** (not marlo021.ai) | P0 #9 |
| One React app with role routing, or two? | P0 #6 |
| Physical QR format | P2 #20 |

---

## ✅ Completed Log

### August 27, 2026 — Marlo landing page finished
- [x] Rewrote the page for businesses, not makers — *"Some of your best customers will never join your mailing list"*
- [x] Five information layers: stat bar → headline → mechanism → reassurance → routed CTAs
- [x] Added the three sections that answer the real objections: *doesn't this compete with my list*, *what would I even say*, and the vision
- [x] Built `/why-local` — cited sources, Apple MPP caveat, and what the numbers **don't** prove
- [x] Voice pass: short sentences, no em dashes, "brand" not "bakery", American spelling
- [x] Plus Jakarta Sans throughout; Newsreader reserved for mocked Brown Bag content
- [x] Vendor colour system, later resaturated after it read too vintage
- [x] Eight real photos wired in; placeholder system kept for future swaps
- [x] Hero hover animation — the stack fans, picked blocks step forward
- [x] Live interview animation, dealing animation, ticker, floating accents
- [x] Warm cream hero with a white nav band, alternating section backgrounds
- [x] **Decided:** subscribers belong to no market; follows decide what they get

### August 12, 2026 — Design settled, foundation deployed
- [x] Named the publication **Brown Bag**
- [x] Two-agent split: interviewer gathers 素材, writer writes
- [x] Invitation-code vendor signup; `category_pairs` for automatic complements
- [x] Seen is permanent; vendors see drafts before editors; no turn limit on conversations
- [x] Writer agent test (`WRITER_TEST.md`)
- [x] `database/models.py` — 19 tables, deployed
- [x] All v1 routers archived; `main.py` v0.3.0 clean

### August 11 and earlier
- [x] Archived Instagram/Stripe code; rewrote `main.py` and `scheduler.py`
- [x] Consolidated docs 11 → 8
- [x] Pivoted from Instagram tool to consumer newsletter