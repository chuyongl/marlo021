# Marlo — Current Status

*Last updated: May 8, 2026 — Session with Claude*

---

## Tested End-to-End ✅
*Manually verified working in production*

- All 4 onboarding emails send and render correctly
- `first_kickoff` email sends with correct content
- `weekly_kickoff` email sends (after first_kickoff logged)
- Kickoff day picker — clicking day button updates DB, shows confirmation page
- Posting days picker — clicking days updates DB, shows confirmation page
- Approve button → status changes `pending` → `executed` (verified in DB)
- AI generates 3 posts per week with captions + images
- Per-day image guide renders differently per day
- Strategy summary shows `key_message` (not internal prompt fields)
- fal.ai image generation works
- Stripe 14-day trial starts on signup

---

## Code Written, Not Fully Tested ⚠️
*Logic exists but not manually verified end-to-end*

- `post_approval` email — scheduler logic written, not triggered in testing
- `weekly_analytics` email — endpoint exists, not verified in full flow
- 72-hour onboarding reminder — scheduler logic written, never waited 72h to verify
- Unsubscribe link — endpoint exists, not clicked and verified in DB
- Decline feedback buttons — endpoint exists, not verified feedback saves to DB
- Skip post → `rejected` status — endpoint exists, not explicitly tested
- Stale action expiry (3-day) — logic written, not waited 3 days to verify
- Approval emails sent day-before — scheduler logic written, not triggered in testing
- Subscription health check — logic written, not tested with real canceled subscription
- Google Ads campaign generation — code exists, never tested with real Google account

---

## What's Blocked ⛔

### Instagram Posting (main blocker)
**Problem:** `platform_account_id` is NULL in `platform_integrations` table for Meta.

**Root cause:** Current OAuth uses Facebook Login which requires Instagram to be connected to a Facebook Page at the API level. The `Marlo` Facebook Page and `marlo021.ai` Instagram are not linked at the Graph API level. Additionally, Meta Business Suite shows "Business Account Not Allowed to Advertise" which blocks the Instagram connection flow entirely.

**Solution:** Switch to **Instagram Login API** (launched July 2024):
- No Facebook Page required
- User logs in directly with Instagram credentials
- OAuth URL: `instagram.com/oauth/authorize`
- Scopes: `instagram_business_basic,instagram_business_content_publish,instagram_business_manage_insights`
- API host: `graph.instagram.com`
- Account ID: from `/me` directly

**Files to change:**
- `backend/integrations/oauth.py` — new connect/callback endpoints for Instagram Login
- `backend/agent/executor.py` — use `graph.instagram.com` host for posting
- Onboarding email — change "Connect Facebook" to "Connect Instagram"

**Estimated time:** 2-3 hours

---

## What's Pending (not blocked, just not done) ⏳

- Privacy policy page at `marlo021.ai/privacy` (required for Meta app review)
- Stripe switch to live mode
- Meta app submission for `instagram_business_content_publish` Advanced Access
- Find 3-5 beta users (target: Seattle restaurants or pet services)

---

## Recent Fixes (May 8, 2026)

| Fix | File | Description |
|---|---|---|
| Approval status check | `approval_router.py` | Was checking `pending_approval` only, now checks `pending` too |
| Duplicate actions | `debug_router.py` | Clears pending actions before regenerating (idempotency) |
| Kickoff day | `scheduler.py` | Reads `biz.briefing_time` instead of hardcoded Sunday |
| Posting schedule 404 | `businesses/router.py` | Added `/settings/posting-schedule` endpoint |
| Image guide | `scheduler.py`, `debug_router.py` | Creative director style, tied to strategy |
| Two emails on trigger | `debug_router.py` | Fixed email log check for first_kickoff vs weekly_kickoff |

---

## Test Account

```
Business ID: 3512ed4f-9dae-499e-9f5d-fdb0d85269ef
Name: Marlo021
Owner: Anna
Timezone: America/Los_Angeles
Subscription: sub_1TUXgo3Vpxkw6ncooW5w2F5w
Onboarding: completed
```

## Debug Commands

```powershell
# Reset test account
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"

# Trigger kickoff email
# browser: https://api.marlo021.ai/debug/trigger-kickoff/3512ed4f-9dae-499e-9f5d-fdb0d85269ef

# Check actions
# browser: https://api.marlo021.ai/debug/actions/3512ed4f-9dae-499e-9f5d-fdb0d85269ef

# Test Instagram post
# browser: https://api.marlo021.ai/debug/test-post/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
```