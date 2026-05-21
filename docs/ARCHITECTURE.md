# Marlo — System Architecture

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), async/await throughout |
| Frontend | React (TypeScript) |
| Database | PostgreSQL (Railway managed) |
| Hosting | Railway (backend + frontend + DB on same project) |
| Email sending | Resend (transactional) + Postmark (inbound replies) |
| AI brain | Anthropic Claude (claude-sonnet-4-6 for brain/replies, claude-haiku-4-5-20251001 for safety/memory) |
| Image generation | fal.ai (Flux Pro v1.1 for generation, Flux Pro v1.1-ultra for image-to-image) |
| Billing | Stripe (test mode, switching to live) |
| Scheduler | APScheduler (in-process, not Temporal) |
| Instagram posting | Instagram Login API (graph.instagram.com) |

## Project Structure

```
C:\Users\Octopus\Documents\marlo\
├── backend/
│   ├── main.py                    # FastAPI app, router registration, startup migrations
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models (includes user_memory JSONB)
│   │   └── session.py             # DB session management
│   ├── auth/
│   │   └── router.py              # JWT auth, login, register
│   ├── businesses/
│   │   └── router.py              # Business CRUD + settings endpoints
│   ├── agent/
│   │   ├── brain.py               # Claude AI wrapper (think + generate_content)
│   │   ├── content_pipeline.py    # Weekly post generation pipeline
│   │   ├── strategy_agent.py      # Weekly strategy decisions
│   │   ├── analytics_agent.py     # Performance insights
│   │   ├── executor.py            # Execute approved actions
│   │   ├── scheduler.py           # APScheduler jobs
│   │   ├── approval_router.py     # Approve/decline endpoints
│   │   ├── debug_router.py        # Debug/testing endpoints (remove before launch)
│   │   ├── guardrails.py          # Safety checks before execution
│   │   ├── reply_handler.py       # ★ NEW: Conversational email reply handler
│   │   ├── user_memory.py         # ★ NEW: Per-user knowledge base (read/write/update)
│   │   ├── vendor_profiles.py     # ★ NEW: Vendor type configs (7 types)
│   │   └── content_safety.py      # ★ NEW: Content safety filter
│   ├── email_system/
│   │   ├── sender.py              # Email send functions
│   │   ├── templates.py           # All email HTML templates
│   │   ├── inbound.py             # ★ UPDATED: Routes replies through reply_handler
│   │   └── onboarding_handler.py  # Parse onboarding email replies
│   ├── integrations/
│   │   ├── oauth.py               # Instagram/Google/Mailchimp OAuth
│   │   ├── meta.py                # Instagram posting via graph.instagram.com
│   │   ├── image_gen.py           # ★ UPDATED: vendor-aware lifestyle image generation
│   │   └── google_ads.py          # Google Ads integration
│   └── billing/
│       └── stripe_client.py       # Stripe subscription management
├── frontend/
│   └── src/
│       └── pages/
│           └── Signup.tsx
└── docs/
```

## Database Models

### Business
Core entity. One per customer.
```
id, owner_id, name, industry, description, tone_of_voice, target_audience,
monthly_ad_budget, onboarding_step (1-4), onboarding_completed,
subscription_id, posting_schedule (array), posts_per_week,
briefing_time (kickoff day name), preferred_post_time, preferred_post_timezone,
timezone, email_notifications,
user_memory (JSONB) ← NEW: per-user knowledge base
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
OAuth tokens. `platform="meta"` for Instagram (stored this way for backward compat).
```
id, business_id, platform (meta/google_ads/mailchimp),
access_token (encrypted), refresh_token (encrypted),
platform_account_id (Instagram Business Account ID),
scopes, is_active, created_at
```

## Key Data Flows

### Email Reply Flow (★ NEW)
```
User replies to any Marlo email
  → POST /email/inbound (Postmark)
  → inbound.py: handle_conversational_reply()
  → user_memory.load_memory(business) — ~200 tokens of context
  → reply_handler.handle_reply(message, business, memory, vendor_type, pending_action)
    → content_safety.check_content_safety() — Haiku, fast
    → vendor_profiles.get_vendor_profile(vendor_type)
    → Claude Sonnet: EXECUTE FIRST, never ask >1 question
    → returns {response_text, revised_post, action_type}
  → if revised_post: update pending AgentAction parameters
  → send email with approve buttons
  → asyncio.create_task(update_memory_async()) — async, doesn't block
    → Haiku summarizes conversation → merges into user_memory
    → saves back to businesses.user_memory JSONB
```

### Photo Upload Flow (★ UPDATED)
```
User replies to email with photo attached
  → inbound.py: handle_photo_upload()
  → upload photo to fal.ai storage → get URL
  → detect vendor_type from business.industry
  → image_gen.generate_lifestyle_from_product(product_url, vendor_type)
    → Claude generates scene prompt using vendor profile rules
    → fal.ai flux-pro-v1.1-ultra image-to-image (strength=0.78)
    → returns commercial lifestyle image URL
  → reply_handler generates caption in vendor's tone
  → create AgentAction with lifestyle image URL
  → send preview email with approve button
```

### Weekly Content Flow
```
Kickoff day 9pm local
  → strategy_agent.decide() → key_message
  → content_pipeline.generate_week_of_content() → N posts
  → AgentAction per post (status: pending)
  → send weekly_kickoff email
  → User approves → status: executed
  → execute_approved_posts scheduler → scheduled_post_time reached
  → executor.run() → meta.post_to_instagram() → Instagram
```

## New Agent Layer: Vendor Profiles

7 vendor types in `vendor_profiles.py`. Each defines:
- `content_pillars` — what topics to post about
- `image_style` — visual aesthetic (mood, lighting, palette, backgrounds)
- `lifestyle_scene_rules` — how to transform product photos (scene types, model guidance, props)
- `caption_tone` — writing style for captions
- `hashtag_clusters` — hashtag groups to rotate
- `photo_prompts` — weekly photo suggestions

**Types:** `maker_jewelry`, `maker_ceramics`, `maker_candles`, `food_bakery`, `food_cafe`, `farmer_market`, `service_local`, `creative_professional`

Adding a new type = add one entry to `VENDOR_PROFILES` dict. Nothing else changes.

## New Agent Layer: User Memory

Replaces raw conversation history. Stored as JSONB in `businesses.user_memory`.

```json
{
  "vendor_type": "maker_jewelry",
  "content_preferences": {
    "likes": ["founder voice", "milestone stories"],
    "dislikes": ["salesy tone"],
    "style_notes": "short sentences, personal narrative"
  },
  "recent_context": "Building Marlo, just shipped Instagram posting.",
  "pending_topics": ["vendor categorization feature"],
  "updated_at": "2026-05-21"
}
```

**Token cost:** ~200 tokens per call vs ~2000 for raw history. Updated asynchronously after each reply using Haiku.

## Scheduler Jobs

| Job | Trigger | What it does |
|---|---|---|
| weekly_content_generation | Every 1 hour | Checks kickoff day at 9pm local, generates posts |
| post_approval_and_expiry | Every 1 hour | Sends day-before approval emails, expires pending |
| execute_approved_posts | Every 15 min | Posts approved content at scheduled_post_time |
| expire_stale_actions | Every 30 min | Marks 3-day-old pending as expired |
| onboarding_reminder | Every 1 hour | Sends 72h reminder if stuck on step 4 |
| weekly_analytics | Every 1 hour | Sends Friday 2pm analytics email |
| subscription_health_check | Daily 2am UTC | Deactivates canceled Stripe subscriptions |

**Network error handling:** Railway DNS blips (`[Errno -3]`) are logged as `WARNING` (not captured by Sentry). Real errors log as `ERROR` (Sentry captures).

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://...
ANTHROPIC_API_KEY=sk-ant-...
FAL_API_KEY=...
RESEND_API_KEY=re_...
POSTMARK_SERVER_TOKEN=...
STRIPE_SECRET_KEY=sk_test_... (switch to sk_live_ before launch)
STRIPE_WEBHOOK_SECRET=whsec_...
INSTAGRAM_APP_ID=1004448018806665
INSTAGRAM_APP_SECRET=...
META_APP_ID=918827927853545
META_APP_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
APP_BASE_URL=https://api.marlo021.ai
FRONTEND_URL=https://marlo021.ai
JWT_SECRET_KEY=...
TOKEN_ENCRYPTION_KEY=...   ← used to encrypt/decrypt OAuth tokens
ENVIRONMENT=production     ← NEW: controls Sentry environment tag
```