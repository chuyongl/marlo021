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