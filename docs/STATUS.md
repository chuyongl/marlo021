# Brown Bag — Current Status

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**Design is settled** — product, architecture, data model all documented and agreed.

**The foundation is deployed.** 19 tables live in production. All v1 Instagram code is archived. The API boots clean with zero routers, which is correct at this stage.

**Nothing else is built.** No writer, no editor UI, no scan flow, no sending.

---

## ✅ Deployed and Verified (Aug 12)

- `database/models.py` — **19 tables**, live in production
- `main.py` v`0.3.0` — all v1 routers archived, router checklist ready to uncomment
- `agent/scheduler.py` — framework running, zero jobs registered

**Verify anytime:**
```
https://api.marlo021.ai/health           → {"version": "0.3.0"}
https://api.marlo021.ai/health/detailed  → tables_defined: 19
```

---

## 🗄️ Fully Archived

`backend/archive/` — nothing imports from it:

`auth/` · `businesses/` · `approval_router.py` · `router.py` · `debug_router.py` · `inbound.py` · `content_pipeline.py` · `strategy_agent.py` · `executor.py` · `google_ads_agent.py` · `analytics_agent.py` · `meta.py` · `oauth.py` · `google_ads.py` · `billing/`

**Do not build on these.** Old v1 database tables also remain in production, untouched and unread.

---

## 🔴 NEXT — P0 items 3–10

Per `TASKS.md`:

**3.** Seed data — one market, neighborhoods, category pairs, test vendors
**4 + 5.** Writer agent **and** style guard — build together, not sequentially
**6.** Editor login + review queue
**7.** Personalizer
**8.** Renderer
**9.** Dispatcher
**10.** Unsubscribe

**Done means:** paste in three submissions → writer drafts → you approve → an issue assembles and sends to three test addresses → **each gets a different selection.**

---

## ⚠️ Deliberately Deferred: Prompt Quality

**The writer and interviewer prompts are not expected to be good in v1.**

Build the skeleton first, tune the craft later. This is a decision, not an oversight.

The reason is practical: **you can't tune a writing voice against invented material.** The `WRITER_TEST.md` samples were written by Claude imagining how vendors talk. Real conversations will be messier and differently messy, and the prompt refinements that matter will only be visible once real 素材 flows through.

**Expect from P0:** publishable but unremarkable copy. Good enough to prove the loop, not good enough to be proud of.

**The craft pass happens after P1**, when real vendor material exists.

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
| Publication name | **Brown Bag** (provisional, in `markets.publication_name`) |
| Backend system name | Marlo — repo and API only, never user-facing |
| API base | `https://api.marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
| Logs | `railway logs --tail` |

---

## Key Design Decisions (cold-start recall)

- **Two agents:** interviewer gathers 素材, writer writes the story
- **Everything publishable is a block** — one table, one approval lifecycle
- **The bank is a query**, not a table: approved + not expired + no open corrections
- **Seen is permanent** per reader; **fatigue** is a decaying penalty per vendor
- **Vendors see drafts before editors** and can flag corrections
- **Issue ships every week** — never shrink, never skip, get more material
- **Nothing ships without editor approval**
- **Vendors sign up with invitation codes** — live immediately, no activation step