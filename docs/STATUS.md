# Marlo — Current Status

*Last updated: August 1, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** This file is REPLACED each session, never appended. One "Last updated" date only.

---

## 🎯 Where Things Stand

Two tracks running at once. Be explicit about which one you're working on.

**Track 1 — Marlo v1 (Instagram content, free MVP).** Code exists. Three bugs fixed Aug 1, untested. Goal: one hand-onboarded jewelry seller through the full loop.

**Track 2 — Phase 2 (prediction engine / add-on marketing layer).** Ideation only, nothing built. See `PHASE_2_DIRECTION.md`.

Not yet decided whether Track 1 continues, folds into Track 2, or gets parked.

---

## 🔴 FIRST THING NEXT SESSION — untested code is live

Three bugs diagnosed and fixed Aug 1. **Committed and deployed. None tested.**

| Bug | Fix | Status |
|---|---|---|
| BUG-1 — reply-created posts never publish | `executor.py` — `create_pending_action_with_tokens` now writes `action_type="post_instagram"`, `status="pending"`, and a real `scheduled_post_time` | Deployed, UNTESTED |
| BUG-2 — approval email not sent | Downstream of BUG-3; fixed by the same change | Deployed, UNTESTED |
| BUG-3 — scheduler blind to free users | `scheduler.py` — three jobs no longer filter on `subscription_id != None` | Deployed, UNTESTED |

**Also in the same commit:**
- `execute_approved_posts` no longer marks a post published when the executor returns `no_handler` / `skipped` (previously a failed post looked successful forever and never retried)
- `expire_stale_actions` now also sweeps legacy `pending_approval` rows
- `executor.run()` accepts legacy `create_post` rows so anything already stuck in the DB can still publish
- New log line: `weekly_content_generation checking N live businesses`

### ⚠️ ERRORS.md correction needed
`ERRORS.md` files the symptom `{"status": "no_handler", "action_type": "create_post"}` under *"platform_account_id is NULL."* **That diagnosis was wrong.** The real cause was `create_pending_action_with_tokens` writing `action_type="create_post"`, which `executor.run()` had no handler for. Update that entry.

### Test sequence when ready
1. PowerShell reset
2. Browser trigger-kickoff
3. Reply to the kickoff email with content
4. Check `/debug/actions` — the new post must show `action_type: post_instagram`, `status: pending`, and a non-null `scheduled_post_time`. All three correct = BUG-1 dead.
5. Approve → status flips to `executed`
6. Wait one 15-min cycle → check Instagram

Expected log: `[Executor] Pending action created — type=post_instagram day=... time=...`

---

## ✅ Working End-to-End (verified as of May 28)

- All 4 onboarding emails
- `first_kickoff` and `weekly_kickoff` emails
- Instagram OAuth (Instagram Login API) — @marlo021.ai
- Instagram posting — scheduler auto-posts at `scheduled_post_time`
- Post approval flow — approve → `executed` → scheduler posts
- fal.ai image generation — Flux for lifestyle, Ideogram for text-heavy (`software_saas`)
- Privacy policy + Terms live, Meta Console configured
- Sentry network errors suppressed, `ENVIRONMENT=production`
- User memory system (`businesses.user_memory` JSONB)
- Vendor profiles — 10 types, AI-powered auto-detection
- Content safety filter
- Reply flow — `onboarding_completed` checked first, Haiku classify → Sonnet generate, Approve & Schedule button, vendor-aware image generation, cross-email history

---

## ⚠️ Deployed, Not Tested

- **The three bug fixes above** ← highest priority
- Ideogram model for `software_saas`
- `health_wellness` and `retail_fashion` vendor types
- AI-powered vendor detection (async Haiku fallback)
- Photo upload → lifestyle image flow (never tested with a real product photo)

---

## 🐛 Known Latent Bug (not urgent)

`agent/reply_handler.py`, inside `handle_reply()` — the fallback line calls `detect_vendor_type_from_industry(...)` **without `await`**. That function became async on May 28. If the fallback fires, `vendor_type` becomes a coroutine object instead of a string. Rarely fires because `inbound.py` always passes a vendor type in. Fix next time that file is touched.

---

## 🔴 Not Yet Done

**Track 1:**
- Test the three bug fixes
- Onboard one real jewelry seller by hand
- Meta app review — screen recording + Advanced Access
- Remove `debug_router.py` before real users go live

**Track 2:**
- Get real order data for the gift-classifier notebook test
- Verify Shopify protected customer data approval requirements

---

## 🧊 Out of Scope Right Now

Stripe live mode, 14-day trial logic, all billing work, Google Ads integration.

---

## Key Facts

| Item | Value |
|---|---|
| Test business ID | `3512ed4f-9dae-499e-9f5d-fdb0d85269ef` |
| Instagram | @marlo021.ai (ID: `26745567421768455`) |
| Instagram App ID | `1004448018806665` |
| Meta App ID | `918827927853545` |
| ⚠️ CONFIRM | `1664730228042130` appeared in July 30 Meta Console work — which app ID is live? |
| API base | `https://api.marlo021.ai` |
| Frontend | `https://marlo021.ai` |

---

## Debug Commands

```powershell
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"
```

```
https://api.marlo021.ai/debug/trigger-kickoff/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
https://api.marlo021.ai/debug/actions/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
https://api.marlo021.ai/debug/test-post/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
```

**Logs:** `railway logs --tail`