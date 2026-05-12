# Marlo — Key User Flows

Detailed step-by-step narratives of every major flow. Read this to understand how the pieces connect.

---

## Flow 1: New User Signup → First Post Live

This is the full happy path. Every step matters.

### Step 1: Signup
- User visits `marlo021.ai` and fills out signup form
- Frontend auto-detects timezone via `Intl.DateTimeFormat().resolvedOptions().timeZone`
- `POST /businesses/` creates Business + User records
- `onboarding_step = 1`, `onboarding_completed = false`
- **Email 1 sent:** "Connect Google Ads" with two buttons: Connect or Skip

### Step 2: Google Ads (optional)
- **If connects:** `GET /integrations/connect/google` → OAuth → callback saves tokens → `onboarding_step = 2`
- **If skips:** `GET /integrations/skip-google` → `onboarding_step = 2`
- **Email 2 sent:** "Connect Facebook & Instagram"

### Step 3: Instagram (critical)
- **If connects:** `GET /integrations/connect/meta` (currently Facebook Login, migrating to Instagram Login)
  - OAuth callback saves access_token + fetches Instagram Business Account ID
  - Stores `platform_account_id` in `platform_integrations`
  - `onboarding_step = 3`
- **If skips:** `onboarding_step = 3`
- **Email 3 sent:** "Connect Mailchimp"

### Step 4: Mailchimp (optional)
- Connect or skip → `onboarding_step = 4`
- **Email 4 sent:** "Tell Marlo about your business"
- User **replies** to this email with their business description

### Step 5: Onboarding Complete
- Postmark receives inbound reply → `POST /email/inbound`
- `onboarding_handler` parses the reply
- Updates business: `description`, `tone_of_voice`, `target_audience`
- Sets `onboarding_completed = true`
- Scheduler now includes this business in weekly content generation

### Step 6: First Kickoff Email
- Scheduler runs every hour, checks if it's user's kickoff day (from `biz.briefing_time`) at 9pm local
- `strategy_agent.decide()` → weekly key message
- `content_pipeline.generate_week_of_content()` → 3 posts (or however many days selected)
- One `AgentAction` created per post (status: `pending`)
- **first_kickoff email sent** with:
  - Week's strategy summary
  - Monday post preview + Approve/Skip buttons
  - Kickoff day picker (buttons)
  - Posting days picker (toggle buttons)
  - Image guide (one creative direction per day)

### Step 7: User Approves First Post
- User clicks "✓ Approve Monday post" in email
- `GET /actions/approve?token=xxx`
- `approval_router` checks status is `pending`
- Updates status → `executed`
- Returns HTML confirmation page

### Step 8: Post Goes Live
- `execute_approved_posts` scheduler job runs every 15 minutes
- Finds actions where `status = "executed" AND executed_at IS NULL AND scheduled_post_time <= now()`
- Calls `executor.run(action, db)`
- `executor.run()` maps `post_instagram` → calls `meta.post_to_instagram(ig_account_id, image_url, caption)`
- Meta API publishes to Instagram
- `action.executed_at = now()`

---

## Flow 2: Weekly Recurring Flow

After onboarding, this repeats every week.

```
User's kickoff day, 9pm local
  ↓
scheduler: weekly_content_generation fires
  ↓
Generate 3 posts → 3 AgentActions (pending)
  ↓
Send weekly_kickoff email (with last week stats)
  ↓
Day before each post, 2pm local
  ↓
scheduler: post_approval_and_expiry fires
  ↓
Send post_approval email for next day's post
  ↓
User approves → status: executed
  ↓
Post day, at preferred_post_time (e.g. 9am)
  ↓
scheduler: execute_approved_posts fires
  ↓
Post goes live on Instagram
  ↓
Friday 2pm local
  ↓
scheduler: weekly_analytics fires
  ↓
Send analytics email (performance summary + AI insights)
```

---

## Flow 3: User Changes Kickoff Day

1. User clicks a day button in kickoff email (e.g. "Wednesday")
2. `GET /businesses/settings/kickoff-day?business_id=xxx&day=Wednesday`
3. Updates `biz.briefing_time = "Wednesday"`
4. Returns HTML: "Kickoff day updated! Your weekly plan will now arrive every Wednesday."
5. Next week's content generation fires on Wednesday at 9pm local instead of Sunday

---

## Flow 4: User Changes Posting Days

1. User clicks posting day toggles in kickoff email
2. Email buttons call `GET /businesses/settings/posting-schedule?business_id=xxx&days=Tuesday,Thursday`
3. Updates `biz.posting_schedule = ["Tuesday", "Thursday"]` and `posts_per_week = 2`
4. Returns HTML: "Posting schedule updated! Marlo will now post on: Tuesday · Thursday"
5. Takes effect from next weekly plan

---

## Flow 5: User Skips a Post

1. User clicks "✗ Skip" in approval email
2. `GET /actions/decline?token=xxx`
3. Status → `rejected`
4. Returns HTML: "Got it — skipped." + optional feedback buttons
5. If user clicks a feedback reason → `GET /actions/feedback?action_id=xxx&reason=wrong_tone`
6. Reason stored in `content_feedback.reason` for future ML improvement

---

## Flow 6: Post Expires (User Never Responds)

1. Post day arrives, action is still `pending`
2. `post_approval_and_expiry` scheduler job expires the previous day's action
3. Action status → `expired`
4. `expire_stale_actions` job runs every 30 min as safety net — expires anything `pending` for 3+ days

---

## Flow 7: Onboarding Reminder

1. User receives email 4 but doesn't reply for 72 hours
2. `onboarding_reminder` scheduler job checks every hour
3. Finds businesses where `onboarding_step = 4` and email 4 was sent 72-96 hours ago
4. Sends reminder email (same as email 4 with `is_reminder = True`)
5. Only sends once (checks for existing `onboarding_4_reminder` in email_logs)

---

## Flow 8: Subscription Canceled

1. User cancels in Stripe or payment fails
2. Stripe sends webhook → `POST /billing/webhook`
3. Or: daily health check at 2am UTC queries Stripe API
4. If subscription status is `canceled`, `unpaid`, or `incomplete_expired`
5. Sets `biz.subscription_id = None`
6. Scheduler skips businesses where `subscription_id IS NULL`
7. No more emails, no more posts

---

## Edge Cases to Know

### What if trigger-kickoff is called twice?
`debug_router.trigger_kickoff` clears all pending actions before generating new ones. Safe to call multiple times.

### What if user approves after post time has passed?
`execute_approved_posts` checks `scheduled_post_time <= now()`. If time has passed, it posts immediately on next 15-min cycle.

### What if Meta API fails during posting?
`executor.run()` returns error dict. `executed_at` stays NULL. Scheduler will retry on next 15-min cycle.

### What if user has no active Meta integration?
`executor.run()` returns `{"status": "skipped", "reason": "No active Meta integration found"}`.