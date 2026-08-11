# Marlo — Current Status

*Last updated: August 4, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**Marlo pivoted on August 4, 2026.** It is no longer an Instagram tool sold to merchants. It is now a **local newsletter for consumers**, built from vendor-supplied material. Free for everyone. Marlo itself is invisible to both sides.

Docs are rewritten. Code cleanup is in progress. **The newsletter build has not started.**

---

## 🔴 IN PROGRESS — Cleanup (finish before anything else)

Old Instagram/Stripe code is being moved to `backend/archive/`.

**⚠️ The app will not boot until imports are fixed.** `main.py` registers routers from archived files, and `scheduler.py` imports `executor`, `strategy_agent`, `content_pipeline`, and `google_ads_agent`.

- [x] Decide: archive rather than delete
- [ ] Run the `git mv` commands
- [ ] **Rewrite `main.py`** — remove archived router registrations
- [ ] **Rewrite `scheduler.py`** — remove archived imports and the jobs that used them
- [ ] Verify local boot, then push

**Do not push until `main.py` and `scheduler.py` are clean, or Railway will fail to start.**

---

## 🔴 NEXT — P0 Design Work (no code)

These are decisions, not builds. **They block everything downstream.**

**Issue format** — the hardest and most important:
- Word budget and shape (mix of short and longer)
- Sections: which exist, fixed or variable
- Vendors per issue
- Minimum follows for an issue to feel relevant
- Behavior when a reader follows only 1 vendor
- Behavior when a reader follows 40
- Minimum material to assemble a full-length issue

**Content supply design:**
- What questions to ask vendors, and in what rotation
- What counts as reserve-bank material vs use-now
- What market-level content exists (seasonal, how-to, logistics)
- How supply runway is measured and when to escalate

**Working assumption only, not a decision:** one deeper story plus several short pieces.

---

## ✅ Still Working (from v1, being reused)

- Email sending via Resend
- Inbound email via Postmark — **this becomes the content intake pipe**
- `reply_handler.py` — understands vendor replies
- One-click approval by email token
- Photo upload → fal.ai
- `vendor_profiles.py`, `content_safety.py`, `user_memory.py`
- APScheduler framework
- Railway deploy, Postgres, Sentry config

---

## 🗄️ Archived (reference only, not imported)

`backend/archive/` — `content_pipeline.py`, `strategy_agent.py`, `executor.py`, `google_ads_agent.py`, `analytics_agent.py`, `meta.py`, `oauth.py`, `google_ads.py`, `billing/`

**Do not build on these.** They belong to the Instagram-posting era.

---

## 🆕 Not Built Yet

Everything in the new architecture:
- New database models (`markets`, `vendors`, `subscribers`, `scan_events`, `vendor_follows`, `content_items`, `content_blocks`, `issues`, `issue_renders`)
- Scan → subscribe flow
- Content supply pipeline (supply monitor, interview + chase, reserve bank, market content)
- Block builder + style guard
- Personalizer + renderer + dispatcher
- Frontend pages (Scan, Subscribe, Preferences, VendorSignup)

---

## 🚧 Blocking Open Questions

| Question | Blocks |
|---|---|
| **Issue format** | All assembly and personalization work |
| **Newsletter brand name** | Any outbound email |
| **Sending domain** (not marlo021.ai) | Any outbound email |

---

## 🐛 Carried-Over Bugs (from the Instagram era)

Three bug fixes were deployed Aug 1 and never tested. **They are now moot** — they lived in `executor.py` and `scheduler.py` on the Instagram posting path, which is archived. No action needed unless that path is ever revived.

`reply_handler.py` still has a missing `await` on `detect_vendor_type_from_industry` in its fallback branch. **Still relevant** — that file is being reused. Fix when next touched.

---

## Quick Reference

| Item | Value |
|---|---|
| API base | `https://api.marlo021.ai` |
| Frontend | `https://marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
| Logs | `railway logs --tail` |