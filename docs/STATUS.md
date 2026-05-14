# Marlo — Current Status

*Last updated: May 13, 2026 — Session with Claude*

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
- Privacy policy page live at `marlo021.ai/privacy`

---

## Code Written, Not Fully Tested ⚠️
*Logic exists but not manually verified end-to-end*

- **Instagram Login OAuth** — code written and deployed, not yet tested end-to-end
  - `GET /integrations/connect/instagram` → redirects to instagram.com/oauth/authorize
  - `GET /integrations/callback/instagram` → exchanges code, fetches ig_account_id from `/me`, stores as platform="meta"
  - Deauthorize + data deletion endpoints added (required for Meta app review)
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

### Instagram Posting — pending end-to-end test
**Status:** Code complete, deployed. Not yet tested with real Instagram account.

**What was done (May 13):**
- Created new Business-type Meta app (App ID: `918827927853545`)
- Added Instagram Login product → API setup with Instagram login
- Added redirect URI: `https://api.marlo021.ai/integrations/callback/instagram`
- Wrote full OAuth flow in `oauth.py`
- Updated `executor.py` to use `graph.instagram.com`
- Updated all onboarding emails to say "Connect Instagram" (no Facebook required)

**To unblock:** Test end-to-end tomorrow (see TASKS.md)

**New Meta app credentials in Railway:**
- `INSTAGRAM_APP_ID` = `1004448018806665`
- `INSTAGRAM_APP_SECRET` = (set in Railway)

**Old Meta app** (`1664730228042130`) — kept in Railway as `META_APP_ID`/`META_APP_SECRET` for legacy `/connect/meta` endpoint. Not used for new connections.

---

## What's Pending (not blocked, just not done) ⏳

- Upload app icon to new Meta app (1024x1024, failed yesterday due to Meta bug — retry)
- Stripe switch to live mode
- Meta app submission for `instagram_business_content_publish` Advanced Access
- Find 3-5 beta users (target: Seattle restaurants or pet services)

---

## Recent Fixes (May 13, 2026)

| Fix | File | Description |
|---|---|---|
| Privacy page | `frontend/src/pages/Privacy.tsx` | New page at /privacy, Tailwind CSS, Meta app review compliant |
| Privacy route | `frontend/src/App.tsx` | Added `/privacy` route |
| Instagram Login OAuth | `backend/integrations/oauth.py` | New connect/callback/deauthorize/delete endpoints |
| executor Instagram | `backend/agent/executor.py` | Instagram posting now uses graph.instagram.com |
| Onboarding email 2 | `backend/email_system/templates.py` | "Connect Instagram" replaces "Connect Facebook & Instagram" |
| Email subject lines | `backend/email_system/sender.py` | Subject lines updated to reflect Instagram Login flow |

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