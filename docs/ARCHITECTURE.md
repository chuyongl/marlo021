# Marlo — System Architecture

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), async/await throughout |
| Frontend | React (TypeScript) |
| Database | PostgreSQL (Railway managed) |
| Hosting | Railway (backend + frontend + DB on same project) |
| Email sending | Resend (transactional) + Postmark (inbound replies) |
| AI brain | Anthropic Claude (claude-sonnet-4-20250514 for brain, claude-haiku-4-5-20251001 for agents) |
| Image generation | fal.ai |
| Billing | Stripe (test mode, switching to live) |
| Scheduler | APScheduler (in-process, not Temporal) |
| Instagram posting | Meta Graph API (migrating to Instagram Login API) |

## Project Structure

```
C:\Users\Octopus\Documents\marlo\
├── backend/
│   ├── main.py                    # FastAPI app, router registration
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   └── session.py             # DB session management
│   ├── auth/
│   │   └── router.py              # JWT auth, login, register
│   ├── businesses/
│   │   └── router.py              # Business CRUD + settings endpoints
│   ├── agent/
│   │   ├── brain.py               # Claude AI wrapper
│   │   ├── content_pipeline.py    # Post generation
│   │   ├── strategy_agent.py      # Weekly strategy decisions
│   │   ├── analytics_agent.py     # Performance insights
│   │   ├── executor.py            # Execute approved actions
│   │   ├── scheduler.py           # APScheduler jobs
│   │   ├── approval_router.py     # Approve/decline endpoints
│   │   ├── debug_router.py        # Debug/testing endpoints
│   │   └── guardrails.py          # Safety checks before execution
│   ├── email_system/
│   │   ├── sender.py              # Email send functions
│   │   ├── templates.py           # All email HTML templates
│   │   └── onboarding_handler.py  # Parse email replies
│   ├── integrations/
│   │   ├── oauth.py               # Google/Meta/Mailchimp OAuth
│   │   ├── meta.py                # Instagram posting via Meta API
│   │   └── google_ads.py          # Google Ads integration
│   └── billing/
│       └── stripe_client.py       # Stripe subscription management
├── frontend/
│   └── src/
│       └── pages/
│           └── Signup.tsx         # Main signup page
└── docs/                          # ← YOU ARE HERE
```

## Database Models

### Business
Core entity. One per customer.
```
id, owner_id, name, industry, description, tone_of_voice, target_audience,
monthly_ad_budget, onboarding_step (1-4), onboarding_completed,
subscription_id, posting_schedule (array), posts_per_week,
briefing_time (kickoff day name), preferred_post_time, preferred_post_timezone,
timezone, email_notifications
```

### User
Auth entity.
```
id, email, hashed_password, full_name, is_active, created_at
```

### AgentAction
Every post or campaign Marlo wants to take.
```
id, business_id, action_type (post_instagram/google_ads_campaign),
status (pending/executed/rejected/expired),
action_parameters (JSON: caption, image_url, hashtags, scheduled_day),
approval_token, decline_token, token_expires_at,
requires_approval, approval_email_sent, approved_at, executed_at,
scheduled_post_time, scheduled_day, outcome, agent_reasoning
```

### PlatformIntegration
OAuth tokens for connected platforms.
```
id, business_id, platform (meta/google_ads/mailchimp),
access_token (encrypted), refresh_token (encrypted),
platform_account_id (Instagram Business Account ID — critical for posting),
scopes, is_active, created_at
```

### EmailLog
Every email sent, for deduplication.
```
id, business_id, email_type, sent_at, metadata
```

### ContentFeedback
User approve/decline decisions for ML feedback loop.
```
id, business_id, action_id, decision (approved/declined), reason,
content_type, platform, created_at
```

## Key Data Flows

### Weekly Content Flow
```
Sunday 9pm local (user's chosen kickoff day)
  → strategy_agent.decide() → key_message for the week
  → content_pipeline.generate_week_of_content() → N posts
  → AgentAction created for each post (status: pending)
  → send_weekly_kickoff() or send_first_kickoff()
  → User clicks Approve → status: executed
  → scheduler execute_approved_posts() fires every 15 min
  → scheduled_post_time reached → executor.run() → Meta API → Instagram
```

### Onboarding Flow
```
Signup → Email 1 (connect Google Ads or skip)
  → Email 2 (connect Instagram/Facebook or skip)
  → Email 3 (connect Mailchimp or skip)
  → Email 4 (reply with business info)
  → onboarding_handler parses reply
  → onboarding_completed = true
  → scheduler starts generating weekly content
```

### Approval Flow
```
Email with Approve button
  → GET /actions/approve?token=xxx
  → approval_router checks status in ("pending", "pending_approval")
  → status → "executed"
  → execute_approved_posts() fires at scheduled_post_time
  → executor.run() → meta.post_to_instagram(ig_account_id, image_url, caption)
```

## Scheduler Jobs (APScheduler, in-process)

| Job | Trigger | What it does |
|---|---|---|
| weekly_content_generation | Every 1 hour | Checks if it's user's kickoff day at 9pm local, generates posts |
| post_approval_and_expiry | Every 1 hour | Sends day-before approval emails, expires old pending actions |
| execute_approved_posts | Every 15 min | Posts approved content at scheduled_post_time |
| expire_stale_actions | Every 30 min | Marks 3-day-old pending actions as expired |
| onboarding_reminder | Every 1 hour | Sends 72h reminder if stuck on step 4 |
| weekly_analytics | Every 1 hour | Sends Friday 2pm analytics email |
| subscription_health_check | Daily 2am UTC | Deactivates canceled Stripe subscriptions |

## Key Technical Decisions

### Why APScheduler not Temporal
Temporal adds infrastructure complexity. APScheduler runs in-process on Railway, simpler for early stage. Can migrate to Temporal when we have 100+ businesses.

### Why email not dashboard
Zero learning curve for non-technical SMB owners. They already use email. Biggest differentiator in the market.

### Why created_at uses utcnow() (naive) but scheduled_post_time uses timezone.utc (aware)
SQLAlchemy/PostgreSQL inconsistency inherited from early code. Do not mix in new code — use timezone.utc consistently for any new datetime fields.

### Why strategy_summary uses only key_message
Prevents internal prompt fields (Tone/CTA) from leaking into user-facing emails. strategy_summary should always be human-readable.

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://...
ANTHROPIC_API_KEY=sk-ant-...
FAL_API_KEY=...
RESEND_API_KEY=re_...
POSTMARK_SERVER_TOKEN=...
STRIPE_SECRET_KEY=sk_test_... (switch to sk_live_ before launch)
STRIPE_WEBHOOK_SECRET=whsec_...
META_APP_ID=...
META_APP_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
APP_BASE_URL=https://api.marlo021.ai
FRONTEND_URL=https://marlo021.ai
JWT_SECRET_KEY=...
```