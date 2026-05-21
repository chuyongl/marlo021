# Marlo — Current Status

*Last updated: May 21, 2026*

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
- Meta Console configured (domains, privacy URL, data deletion callback)
- Sentry network errors suppressed (Railway DNS blips no longer spam alerts)
- `ENVIRONMENT=production` set in Railway

---

## ⚠️ Code Written, Not Fully Tested

- **Conversational reply handler** (`reply_handler.py`) — deployed, not yet tested with real email replies
- **User memory** (`user_memory.py`) — deployed, `user_memory` column added via startup migration
- **Vendor profiles** (`vendor_profiles.py`) — deployed, auto-detection from industry string
- **Content safety** (`content_safety.py`) — deployed, not tested with harmful input
- **Lifestyle image generation** (`image_gen.generate_lifestyle_from_product`) — deployed, not yet tested with real product photo
- `post_approval` email — scheduler logic written, not triggered in testing
- `weekly_analytics` email — endpoint exists, not verified in full flow
- 72-hour onboarding reminder — logic written
- Decline feedback buttons — endpoint exists
- Stale action expiry (3-day) — logic written
- Google Ads campaign generation — code exists, never tested

---

## 🔴 Not Yet Done

- **Test conversational reply flow** — reply to approval email, verify memory + post revision works
- **Test photo upload** — reply to email with product photo, verify lifestyle image generates
- **Meta app review** — needs screen recording, submit for Advanced Access
- **Stripe live mode** — switch `sk_test_` to `sk_live_`
- **Beta users** — 3-5 Seattle small businesses

---

## Key Facts

- Test account ID: `3512ed4f-9dae-499e-9f5d-fdb0d85269ef`
- Instagram: @marlo021.ai (ID: 26745567421768455)
- Instagram App ID: `1004448018806665`
- Meta App ID: `918827927853545`
- Instagram stored as `platform="meta"` in DB

## Debug Commands

```powershell
# Reset test account
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"

# Trigger kickoff
# browser: https://api.marlo021.ai/debug/trigger-kickoff/3512ed4f-9dae-499e-9f5d-fdb0d85269ef

# Check actions
# browser: https://api.marlo021.ai/debug/actions/3512ed4f-9dae-499e-9f5d-fdb0d85269ef

# Test Instagram post directly
# browser: https://api.marlo021.ai/debug/test-post/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
```