# Marlo — Data Model

All tables live in PostgreSQL on Railway.

---

## businesses

The core entity. One row per customer business.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| owner_id | UUID | FK → users.id |
| name | string | Business name (e.g. "Anna's Cafe") |
| industry | string | e.g. "restaurant", "pet services" |
| description | string | What the business does, in their words |
| tone_of_voice | string | e.g. "warm and casual", "professional" |
| target_audience | string | e.g. "local families in Seattle" |
| monthly_ad_budget | float | Monthly ad spend in USD |
| onboarding_step | int | 1-4, tracks where user is in onboarding |
| onboarding_completed | bool | True once user replies to email 4 |
| subscription_id | string | Stripe subscription ID (NULL = no active sub) |
| posting_schedule | array | Days to post e.g. ["Monday","Wednesday","Friday"] |
| posts_per_week | int | Number of posts per week (derived from posting_schedule) |
| briefing_time | string | User's chosen kickoff day e.g. "Sunday" |
| preferred_post_time | string | Time to post e.g. "09:00" |
| preferred_post_timezone | string | IANA timezone e.g. "America/Los_Angeles" |
| timezone | string | User's detected timezone (from signup) |
| email_notifications | bool | False if user unsubscribed |

**Key notes:**
- Always read posting_schedule via `get_posting_schedule(biz)` helper — handles NULL/invalid values
- `briefing_time` stores the kickoff day name (not a time)
- `subscription_id` being NULL means account is inactive — scheduler skips these

---

## users

Auth entity. One row per person who signed up.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| email | string | Login email, unique |
| hashed_password | string | bcrypt hash |
| full_name | string | Display name |
| is_active | bool | Always true unless manually disabled |
| created_at | datetime | Signup time |

---

## agent_actions

Every post or campaign Marlo wants to take. This is the heart of the approval system.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| business_id | UUID | FK → businesses.id |
| action_type | string | `post_instagram`, `post_facebook`, `google_ads_campaign` |
| status | string | See status values below |
| action_parameters | JSON | Post content: caption, image_url, hashtags, scheduled_day, platform |
| approval_token | UUID | Token in approve link — one-click, no login |
| decline_token | UUID | Token in decline link |
| token_expires_at | datetime | When tokens expire (48h from creation) |
| requires_approval | bool | Always true for posts |
| approval_email_sent | bool | Prevents sending approval email twice |
| approved_at | datetime | When user clicked approve/decline |
| executed_at | datetime | When post was actually published |
| scheduled_post_time | datetime | When to publish (aware datetime, UTC) |
| scheduled_day | string | Day name e.g. "Monday" |
| outcome | JSON | Result from Meta API after posting |
| agent_reasoning | string | Why Marlo chose this action |
| created_at | datetime | When action was created (naive UTC) |

**Status values:**
- `pending` — waiting for user approval
- `executed` — user approved, waiting for scheduled_post_time OR already posted
- `rejected` — user declined
- `expired` — never approved, auto-expired after 3 days

**Important:** `status = "executed"` does NOT mean the post is live. It means approved. The scheduler checks `executed_at IS NULL AND scheduled_post_time <= now()` to find posts that need to actually be published.

---

## platform_integrations

OAuth tokens for connected platforms.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| business_id | UUID | FK → businesses.id |
| platform | string | `meta`, `google_ads`, `mailchimp` |
| access_token | string | Encrypted OAuth access token |
| refresh_token | string | Encrypted OAuth refresh token (if applicable) |
| platform_account_id | string | **Critical for Instagram posting** — Instagram Business Account ID |
| scopes | array | OAuth scopes granted |
| is_active | bool | False if disconnected |
| created_at | datetime | When connected |

**Critical note on platform_account_id:**
For `platform = "meta"`, this must be the Instagram Business Account ID (not Facebook User ID or Page ID). This is what gets passed to `meta.post_to_instagram(ig_account_id, ...)`. If NULL, Instagram posting will fail silently.

---

## email_logs

Every email sent. Used for deduplication — prevents sending the same email twice.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| business_id | UUID | FK → businesses.id |
| email_type | string | e.g. `first_kickoff`, `weekly_kickoff`, `onboarding_1`, `post_approval_monday` |
| sent_at | datetime | When sent |
| metadata | JSON | Extra info (recipient, subject, etc.) |

**Email type values:**
- `onboarding_1` through `onboarding_4`
- `onboarding_4_reminder`
- `first_kickoff` — only sent once, ever
- `weekly_kickoff` — sent every kickoff day after first
- `post_approval_{day}` — e.g. `post_approval_monday`
- `weekly_analytics`

---

## content_feedback

User approve/decline decisions. Used for future ML improvements.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| business_id | UUID | FK → businesses.id |
| action_id | UUID | FK → agent_actions.id |
| decision | string | `approved` or `declined` |
| reason | string | Decline reason: `wrong_tone`, `not_relevant`, `poor_quality`, `wrong_timing`, `other` |
| content_type | string | e.g. `post_instagram` |
| platform | string | e.g. `instagram` |
| created_at | datetime | When decision was made |

---

## Key SQL Queries

```sql
-- Check a business's integrations
SELECT platform, platform_account_id, is_active
FROM platform_integrations
WHERE business_id = 'your-business-id';

-- See all pending actions
SELECT id, action_type, status, scheduled_day, scheduled_post_time
FROM agent_actions
WHERE business_id = 'your-business-id'
ORDER BY created_at DESC;

-- Check email history
SELECT email_type, sent_at
FROM email_logs
WHERE business_id = 'your-business-id'
ORDER BY sent_at DESC;

-- Find businesses ready for weekly content
SELECT id, name, briefing_time, posting_schedule
FROM businesses
WHERE onboarding_completed = true
AND subscription_id IS NOT NULL;
```