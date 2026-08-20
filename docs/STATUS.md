# Brown Bag — Current Status

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**Design is settled** — product, architecture, data model documented and agreed.

**The foundation is deployed.** 19 tables live in production. All v1 Instagram code archived. The API boots clean with zero routers, which is correct at this stage.

**The Marlo landing page is rebuilt** — it now explains the system rather than selling the old product.

**The pipeline itself is not built.** No writer, no editor UI, no scan flow, no sending.

---

## ✅ Deployed and Verified

**Backend (Aug 12)**
- `database/models.py` — **19 tables**, live
- `main.py` v`0.3.0` — v1 routers archived, router checklist ready to uncomment
- `agent/scheduler.py` — framework running, zero jobs registered

```
https://api.marlo021.ai/health           → {"version": "0.3.0"}
https://api.marlo021.ai/health/detailed  → tables_defined: 19
```

**Frontend (Aug 12)**
- `pages/Landing.tsx` rebuilt — light editorial style, six numbered figures
- `public/index.html` — meta description and theme colour updated

---

## 🎨 Landing Page — What It Is Now

**Audience:** makers deciding whether to join · markets and platforms (Etsy, market managers) · future API partners. Layered so each reads as deep as they need.

**Not a sales page.** No pricing, no signup, no trial. Only CTA is an email address.

**Six figures:**
| Fig | Section |
|---|---|
| — | Hero + headline ticker |
| 01 | Two inboxes, dealt live — the signature |
| 02 | A live interview playing out |
| 03 | The four-stage pipeline |
| 04 | Limits — what the system won't do |
| 05 | Matching — how an issue gets built |
| 06 | Partners + possible API surface |

**The three stated limits** are the trust argument and the most distinctive copy on the page:
- Nothing is published without a person reading it first
- We never write a fact a maker didn't tell us
- We never tell a reader what we've worked out about them

**Design reference:** newform.com — see `LANDING_PAGE_REFERENCE.md`.

---

## 🗄️ Fully Archived

`backend/archive/` — nothing imports from it:
`auth/` · `businesses/` · `approval_router.py` · `router.py` · `debug_router.py` · `inbound.py` · `content_pipeline.py` · `strategy_agent.py` · `executor.py` · `google_ads_agent.py` · `analytics_agent.py` · `meta.py` · `oauth.py` · `google_ads.py` · `billing/`

Old v1 database tables also remain in production, untouched and unread.

---

## 🔴 NEXT — P0 items 3–10

**3.** Seed data — market, neighbourhoods, category pairs, test vendors
**4 + 5.** Writer agent **and** style guard — build together
**6.** Editor login + review queue
**7.** Personalizer · **8.** Renderer · **9.** Dispatcher · **10.** Unsubscribe

**Done means:** paste in three submissions → writer drafts → approve → issue assembles and sends to three test addresses → **each gets a different selection.**

---

## ⚠️ Deliberately Deferred: Prompt Quality

**The writer and interviewer prompts are not expected to be good in v1.** Build the skeleton first, tune the craft later. This is a decision, not an oversight.

**You can't tune a writing voice against invented material.** The `WRITER_TEST.md` samples were imagined. Real conversations will be messier and differently messy.

**Expect from P0:** publishable but unremarkable copy. The craft pass happens after P1, when real 素材 exists.

---

## 🧹 Known Stale, Not Urgent

**Orphaned routes** — `/blog`, `/help`, `/signup`, `/setup` all still describe the Instagram product. The new landing page doesn't link to them, so they're unreachable rather than broken. Clean up in a later pass.

**`Privacy.tsx` and `Terms.tsx` are wrong.** They describe the Instagram product and Stripe billing. The new model has a genuinely different data story — QR scans, inferred interests, vendor content. **These are legal documents currently making false statements** and should be rewritten before any real reader subscribes.

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
- **Vendors see drafts before editors** and can flag corrections
- **Issue ships every week** — never shrink, never skip, get more material
- **Nothing ships without editor approval**
- **Vendors sign up with invitation codes** — live immediately, no activation step