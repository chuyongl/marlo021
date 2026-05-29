# Marlo — Current Status

*Last updated: May 22, 2026*

---

## ✅ Working End-to-End

- All 4 onboarding emails
- `first_kickoff` and `weekly_kickoff` emails
- Instagram OAuth (Instagram Login API) — connected as @marlo021.ai
- Instagram posting — `meta.py` uses `graph.instagram.com`, container polling, token decryption ✅
- Post approval flow — approve → `executed` → scheduler posts at `scheduled_post_time`
- fal.ai image generation
- Stripe 14-day trial
- Privacy policy (`marlo021.ai/privacy`) and Terms (`marlo021.ai/terms`)
- Meta Console configured
- Sentry network errors suppressed
- `ENVIRONMENT=production` set in Railway
- User memory system deployed (`businesses.user_memory` JSONB column added)
- Vendor profiles deployed (7 types, auto-detected from industry)
- Content safety filter deployed
- Photo upload → lifestyle image generation working (tested)

---

## ⚠️ Code Deployed, Not Fully Tested

- **Conversational reply handler** — intent classification works, but approve buttons not yet confirmed end-to-end
  - Root cause found: `debug_router.py` reset wasn't restoring `onboarding_completed=True` → replies were going to `handle_onboarding_question` instead of `handle_conversational_reply`
  - Fix deployed: reset now sets `onboarding_step=5, onboarding_completed=True`
  - **Next session: re-test reply flow with clean reset**
- Cross-email conversation history — deployed, not yet tested
- `billing_router.py` Stripe webhook fix — deployed

---

## 🔴 Not Yet Done

- **Confirm reply flow works end-to-end** — reset → kickoff → reply with content → approve button appears
- **Test photo upload** with real product photo
- **Meta app review** — needs screen recording, submit for Advanced Access
- **Stripe live mode** — switch `sk_test_` to `sk_live_`
- **Beta users** — 3-5 Seattle small businesses
- **Image quality** — switch to `flux-pro/v1.1-ultra`, improve prompts for human figures

---

## Key Facts

- Test account ID: `3512ed4f-9dae-499e-9f5d-fdb0d85269ef`
- Instagram: @marlo021.ai (ID: 26745567421768455)
- Instagram App ID: `1004448018806665`
- Meta App ID: `918827927853545`
- Instagram stored as `platform="meta"` in DB

## Debug Commands

```powershell
# Reset (PowerShell only — DELETE method)
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"

# Trigger kickoff
# browser: https://api.marlo021.ai/debug/trigger-kickoff/3512ed4f-9dae-499e-9f5d-fdb0d85269ef

# Check actions
# browser: https://api.marlo021.ai/debug/actions/3512ed4f-9dae-499e-9f5d-fdb0d85269ef

# Test Instagram post directly
# browser: https://api.marlo021.ai/debug/test-post/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
```

# Marlo — Current Status

*Last updated: May 28, 2026*

---

## ✅ Working End-to-End

- All 4 onboarding emails
- `first_kickoff` and `weekly_kickoff` emails
- Instagram OAuth — connected as @marlo021.ai
- Instagram posting — scheduler auto-posts at scheduled_post_time ✅
- Post approval flow — approve → `executed` → scheduler posts
- fal.ai image generation — Flux for lifestyle, Ideogram for text-heavy (software_saas)
- Stripe 14-day trial
- Privacy policy + Terms pages live
- Meta Console configured
- Sentry network errors suppressed, `ENVIRONMENT=production`
- User memory system (`businesses.user_memory` JSONB)
- Vendor profiles — 10 types, AI-powered auto-detection
- Content safety filter
- **Reply flow working end-to-end** ✅
  - `onboarding_completed` check first (critical routing fix)
  - Two-step intent classification: Haiku classifies → Sonnet generates
  - Approve & Schedule button appears correctly
  - Auto-generates image for new posts (vendor-aware model selection)
  - Cross-email conversation history via EmailLog
- Wednesday post published on schedule ✅
- Friday post approved, scheduled ✅

---

## ⚠️ Deployed, Not Yet Tested

- Ideogram model for `software_saas` vendor type
- `health_wellness` and `retail_fashion` vendor types
- AI-powered vendor detection (async Haiku fallback for ambiguous industries)

---

## 🔴 Not Yet Done

- Meta app review — needs screen recording, submit for Advanced Access
- Stripe live mode — switch `sk_test_` → `sk_live_`
- Beta users — 3-5 Seattle small businesses
- Verify Ideogram image quality for SaaS mockups

---

## Key Facts

- Test account ID: `3512ed4f-9dae-499e-9f5d-fdb0d85269ef`
- Instagram: @marlo021.ai (ID: 26745567421768455)
- Instagram App ID: `1004448018806665`
- Meta App ID: `918827927853545`
- "Professional Services" → now correctly detects as `software_saas`

## Debug Commands

```powershell
# Reset (PowerShell — DELETE method)
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"
```
```
# Browser
https://api.marlo021.ai/debug/trigger-kickoff/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
https://api.marlo021.ai/debug/actions/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
https://api.marlo021.ai/debug/test-post/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
```