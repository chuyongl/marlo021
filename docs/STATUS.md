# Marlo — Current Status

*Last updated: August 11, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**Marlo pivoted to a local consumer newsletter.** Free for vendors and readers. Marlo itself is invisible to both sides — readers get a newsletter with its own brand, vendors get an email from the market.

**Docs consolidated: 11 → 7.** **Code cleanup: done and deployed.**
**The newsletter build has not started.**

---

## ✅ Cleanup Complete (Aug 11)

- Instagram/Stripe/Google-Ads code moved to `backend/archive/` via `git mv` (history preserved)
- `main.py` rewritten — archived routers removed, version bumped to `0.2.0`
- `agent/scheduler.py` rewritten — all 7 Instagram-era jobs removed
- All 6 remaining routers verified loading: `auth`, `email_system.inbound`, `agent.approval_router`, `businesses.router`, `agent.router`, `agent.debug_router`
- Docs deleted: `DECISIONS.md`, `PHASE_2_DIRECTION.md`, `FLOWS.md`, `ERRORS.md` — surviving content absorbed into `PRODUCT.md` and `ARCHITECTURE.md`
- Pushed and deployed

**Verify live:** `https://api.marlo021.ai/health` should return version `0.2.0`.

---

## 🔴 NEXT — P0: Editorial Rules (design, no code)

**This is the real P0.** Content generation can be done unscalably at first; the rules cannot be missing.

**Issue format:**
- Word budget and shape — mix of short and longer pieces
- What sections exist; fixed or variable
- How many vendors appear per issue
- How many follows a reader needs for the issue to feel relevant
- **Reader follows 1 vendor** — what fills the rest?
- **Reader follows 40** — what gets cut? Does it feel like loss?
- Minimum material to assemble at full length

**Content supply:**
- Question set for vendors + rotation logic
- Reserve-bank rules: what qualifies as evergreen, when to hold vs use
- Market-level content types (seasonal, how-to, logistics)
- Supply runway metric and escalation thresholds

**Working assumption only, not a decision:** one deeper story + several short pieces.

**Best way to decide these:** get real material from a few real vendors and edit it by hand. Rules written against imagined replies won't survive contact.

---

## 🚧 Blocking Open Questions

| Question | Blocks |
|---|---|
| **Issue format** | All assembly and personalization work |
| **Newsletter brand name** | Any outbound email |
| **Sending domain** (not marlo021.ai) | Any outbound email — readers shouldn't see Marlo |

---

## ✅ Working (reused from v1)

- Email sending via Resend
- Inbound email via Postmark — **this becomes the content intake pipe**
- `reply_handler.py` — understands vendor replies
- One-click approval by email token
- Photo upload → fal.ai
- `vendor_profiles.py`, `content_safety.py`, `user_memory.py`
- APScheduler framework (running, zero jobs registered — correct for now)
- Railway deploy, Postgres, Sentry

---

## 🗄️ Archived (`backend/archive/`, not imported)

`content_pipeline.py`, `strategy_agent.py`, `executor.py`, `google_ads_agent.py`, `analytics_agent.py`, `meta.py`, `oauth.py`, `google_ads.py`, `billing/`

**Do not build on these.**

---

## 🆕 Not Built Yet

- New DB models (`markets`, `vendors`, `subscribers`, `scan_events`, `vendor_follows`, `content_items`, `content_blocks`, `issues`, `issue_renders`)
- Scan → subscribe flow
- Content supply pipeline (supply monitor, interview + chase, reserve bank, market content)
- Block builder + style guard
- Personalizer + renderer + dispatcher
- Frontend pages (Scan, Subscribe, Preferences, VendorSignup)

---

## 🐛 Known Issues

**`debug_router` and `agent/router`** load fine but may reference archived modules inside functions. They'll fail at call time, not import time. Low priority — both are being replaced.

**`reply_handler.py`** has a missing `await` on `detect_vendor_type_from_industry` in its fallback branch. **Still relevant** — that file is being reused. Fix when next touched.

**Old Instagram bug fixes (Aug 1)** were never tested and are now moot — they lived in archived code.

---

## Quick Reference

| Item | Value |
|---|---|
| API base | `https://api.marlo021.ai` |
| Frontend | `https://marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
| Logs | `railway logs --tail` |
| Health check | `GET /health` → should show `0.2.0` |