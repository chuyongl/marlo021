# Brown Bag — Current Status

*Last updated: August 27, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**Design settled. Foundation deployed. Marlo's landing page is finished.**

**The pipeline is not built.** No seed data, no writer, no editor UI, no scan flow, no sending.

---

## 🔴 FIRST THING NEXT SESSION

### Apply the subscriber schema change, then seed

We decided to **remove `market_id` from `subscribers`** (see below) but `models.py` still has the old shape. **This must land before the seed script**, or the seed writes rows against a schema we've already agreed is wrong.

Three edits to `database/models.py`:
1. Drop `market_id` from `Subscriber`
2. `email` becomes globally unique — remove the `UniqueConstraint("market_id","email")`
3. Add `home_market_id` (nullable, FK → markets) — derived, not chosen

Then drop the stale column in Railway's SQL console. The table is empty, so this is clean:
```sql
ALTER TABLE subscribers DROP COLUMN IF EXISTS market_id;
```

Then P0 #3, seed data.

---

## 📐 Decision: Subscribers Are Not Owned By A Market

**The problem:** a traveler who scans in Seattle and New York became **two rows with the same email**. Two newsletters every week, two unsubscribe links, two interest vectors that never learn from each other. Silent — nothing errors.

**The insight:** `market_id` on a subscriber was a fiction. Nobody chooses a market; they scan a stall. **The market is a property of the vendor.**

**The change:** drop it. A person follows vendors; vendors belong to markets; what lands in the inbox is decided by follows. The traveler gets **one email**, mostly Seattle with one New York story — arguably the better product.

**`home_market_id`** is a derived tiebreak, recomputed with the interest vector. It only decides which greeting and which ads a reader sees. Ties go to most recently scanned.

**Location tracking is unchanged.** It always came from `inferred_neighborhood`, computed from followed vendors' neighborhoods. Two guards worth keeping in mind when we build scoring:
- Weight by follow count and recency, so one trip doesn't flip someone's home neighborhood
- **Proximity scores 0 across markets.** "Is Ballard near Williamsburg" has no answer; each market has its own map

Full note in `SUBSCRIBER_MARKET_CHANGE.md` — fold into `DATA_MODEL.md` and delete when that file is next updated.

---

## ✅ Deployed and Verified

**Backend**
- `database/models.py` — 19 tables live
- `main.py` v`0.3.0` — v1 routers archived, router checklist ready to uncomment
- `agent/scheduler.py` — framework running, zero jobs (correct for now)

```
https://api.marlo021.ai/health           → {"version": "0.3.0"}
https://api.marlo021.ai/health/detailed  → tables_defined: 19
```

**Frontend — Marlo landing page, done**
- Business-focused copy: *"Some of your best customers will never join your mailing list. They'll read this one."*
- Five information layers: stat bar → headline → mechanism → reassurance → routed CTAs
- Three sections answering the real objections: *doesn't this compete with my list*, *what would I even say*, and the vision
- `/why-local` — cited sources, the Apple MPP caveat, and what the numbers **don't** prove
- Plus Jakarta Sans throughout; Newsreader reserved for mocked Brown Bag content only
- Saturated vendor colour system (amber, leaf, coral, sky, plum)
- Eight real photos wired in
- Hero hover: the stack fans, picked blocks step forward
- Live interview animation, dealing animation, headline ticker

---

## 🔴 NEXT — P0 items 3–10

| # | Task |
|---|---|
| 3 | **Seed data** — market, neighborhoods, category pairs, test vendors, editor, readers |
| 4 + 5 | **Writer agent + style guard** — build together |
| 6 | Editor login + review queue |
| 7 | Personalizer |
| 8 | Renderer |
| 9 | Dispatcher |
| 10 | Unsubscribe |

**Done means:** paste in three submissions → writer drafts → approve → issue assembles and sends to three test addresses → **each gets a different selection.**

**Seed should include awkward cases on purpose:** a silent vendor, an unapproved block, and a reader with zero follows. Otherwise it hides the bugs it exists to surface.

---

## ⚠️ Deliberately Deferred: Prompt Quality

v1 writer output will be publishable but unremarkable. **You can't tune a writing voice against invented material.** The craft pass happens after P1, when real 素材 exists.

---

## 🧹 Known Stale

**`Privacy.tsx` and `Terms.tsx` describe the Instagram product and Stripe billing.** They are legal documents currently making false statements. **Must be rewritten before any real reader subscribes.**

Orphaned page files still in `src/pages/` but unrouted: `Signup`, `Setup`, `Help`, `Blog`, `BlogPost_HowMarloThinks`.

---

## 🚧 Blocking Decisions

| Question | Blocks |
|---|---|
| **Brown Bag sending domain** — can't be marlo021.ai | Any outbound email (P0 #9) |
| One React app with role routing, or separate vendor / editor apps? | Editor UI (P0 #6) |
| Physical QR format | Vendor rollout (P2) |

---

## Reference

| Item | Value |
|---|---|
| Publication | **Brown Bag** (provisional, in `markets.publication_name`) |
| Backend system | Marlo — repo and API only, never user-facing |
| API base | `https://api.marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
| Run frontend | `cd frontend` then `npm start` |
| Logs | `railway logs --tail` |

---

## Key Design Decisions (cold-start recall)

- **Two agents:** interviewer gathers 素材, writer writes the story
- **Everything publishable is a block** — one table, one approval lifecycle
- **The bank is a query**, not a table: approved + not expired + no open corrections
- **Seen is permanent** per reader; **fatigue** is a decaying penalty per vendor
- **Subscribers belong to no market** — follows decide what they get
- **Vendors see drafts before editors** and can flag corrections
- **Issue ships every week** — never shrink, never skip, get more material
- **Nothing ships without editor approval**
- **Vendors sign up with invitation codes** — live immediately, no activation step