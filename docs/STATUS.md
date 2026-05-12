# Marlo — Current Status

*Last updated: May 8, 2026 — Session with Claude*

---

## What's Working ✅

### Core Email Flow
- All 4 onboarding emails send correctly
- `first_kickoff` email (first week) ✅
- `weekly_kickoff` email (recurring) ✅
- `post_approval` email (per posting day, day before) ✅
- `weekly_analytics` email (Friday 2pm local) ✅
- 72-hour onboarding reminder ✅
- One-click approve/skip (no login required) ✅
- Unsubscribe (CAN-SPAM compliant) ✅
- Decline feedback buttons ✅

### Content Generation
- AI generates 3-7 posts/week based on posting schedule ✅
- Strategy agent decides weekly theme ✅
- Per-day image guide (creative director style) ✅
- fal.ai image generation ✅

### User Settings (via email buttons)
- Kickoff day picker (Mon-Sun) ✅
- Posting days picker (toggle days) ✅
- Both update DB immediately ✅

### Approval Flow
- Approve → status: pending → executed ✅
- Skip → status: pending → rejected ✅
- Feedback collected on skips ✅

### Scheduler
- Fires on user's chosen kickoff day (not hardcoded Sunday) ✅
- Approval emails sent day-before at 2pm local ✅
- Stale actions expire after 3 days ✅

### Billing
- Stripe test mode ✅
- 14-day free trial ✅
- Subscription health check ✅

---

## What's Blocked ⛔

### Instagram Posting (main blocker)
**Problem:** `platform_account_id` is NULL in `platform_integrations` table for Meta.

**Root cause:** Current OAuth uses Facebook Login which requires Instagram to be connected to a Facebook Page at the API level (`/me/accounts` must return `instagram_business_account`). The `Marlo` Facebook Page and `marlo021.ai` Instagram are not linked at the Graph API level, even though they appear connected in Accounts Center.

**Additional blocker:** Meta Business Suite shows "Business Account Not Allowed to Advertise" which blocks the Instagram connection flow entirely.

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