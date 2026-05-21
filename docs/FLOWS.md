# Marlo — Key User Flows

---

## Flow 1: New User Signup → First Post Live

### Step 1: Signup
- User visits `marlo021.ai`, fills signup form
- Frontend auto-detects timezone
- `POST /businesses/` creates Business + User records
- `onboarding_step = 1`
- **Email 1 sent:** "Connect Google Ads" — Connect or Skip

### Step 2–4: Platform Connections (all optional)
- Google Ads → Instagram → Mailchimp
- Each step: connect via OAuth or skip
- `onboarding_step` increments each time

### Step 5: Onboarding Complete
- Email 4: "Tell Marlo about your business" — user replies
- Postmark receives reply → `POST /email/inbound`
- `onboarding_handler` parses reply, updates business profile
- `onboarding_completed = true`, `user_memory` initialized
- Scheduler now includes this business

### Step 6: First Kickoff Email
- Scheduler checks kickoff day at 9pm local
- `strategy_agent` + `content_pipeline` generate N posts
- `AgentAction` per post (status: `pending`)
- `first_kickoff` email sent with strategy, post preview, approve buttons

### Step 7–8: Approve → Post Live
- User clicks Approve → `status: executed`
- `execute_approved_posts` scheduler (every 15min) finds `executed_at IS NULL AND scheduled_post_time <= now()`
- `executor.run()` → `meta.post_to_instagram()` → Instagram
- `executed_at` set

---

## Flow 2: Weekly Recurring Flow

```
Kickoff day 9pm local → generate posts → weekly_kickoff email
Day before each post → post_approval email
User approves → status: executed
Post day at preferred_post_time → scheduler posts to Instagram
Friday 2pm → weekly_analytics email
```

---

## Flow 3: User Replies to Email (★ UPDATED)

All post-onboarding replies now go through `reply_handler`.

```
User replies to any Marlo email
  ↓
POST /email/inbound (Postmark)
  ↓
inbound.py → handle_conversational_reply()
  ↓
Load user_memory (~200 tokens of context)
  ↓
Find most recent pending AgentAction (if any)
  ↓
reply_handler.handle_reply(message, business, memory, vendor_type, pending_action)
  ↓
content_safety.check_content_safety() — fast Haiku check
  ↓
[if blocked] → redirect message, stop
  ↓
[if clear] → Claude Sonnet with compact context
  Rules: EXECUTE FIRST. Never ask >1 question. Never use third person.
  ↓
Returns: {response_text, revised_post, action_type}
  ↓
[if post_revision] → update pending action's caption/hashtags
                   → send email with revised post + approve buttons
[if new_post]      → create new AgentAction
                   → send email with new post + approve buttons
[if conversation]  → send plain reply
  ↓
asyncio.create_task(update_memory_async())
  → Haiku summarizes conversation
  → merges into businesses.user_memory JSONB
  → saves async (doesn't block response)
```

**Key behaviors:**
- User says "make it less salesy" → rewrites immediately, no questions
- User pastes raw notes/story → turns it into a post, no questions
- User says "use what I told you" → uses it directly
- Memory persists preferences across sessions (dislikes/likes/style)

---

## Flow 4: User Sends Product Photo (★ UPDATED)

```
User replies to email with photo attached
  ↓
inbound.py → handle_photo_upload()
  ↓
Decode base64 → save temp JPEG → upload to fal.ai → get original_url
  ↓
detect vendor_type from business.industry
  (e.g. "jewelry" → maker_jewelry, "bakery" → food_bakery)
  ↓
image_gen.generate_lifestyle_from_product(original_url, vendor_type)
  ↓
  Claude reads vendor profile's lifestyle_scene_rules:
    - scene_types (ranked options)
    - model_guidance (how to use hands/people)
    - props, composition, platform_notes
  → generates detailed scene prompt
  ↓
  fal.ai flux-pro-v1.1-ultra image-to-image
    image_url=original_url, strength=0.78
    (0=keep original, 1=ignore; 0.78 transforms scene, keeps product)
  → returns lifestyle_url
  ↓
reply_handler generates caption in vendor's caption_tone
  ↓
hashtags sampled from vendor's hashtag_clusters
  ↓
create AgentAction with lifestyle_url as image_url
  ↓
send preview email:
  - Shows generated lifestyle image
  - Caption + hashtags
  - Approve / Skip buttons
  - "See original photo" collapsible
  - Instructions for requesting changes
```

**Fallback:** if fal.ai image-to-image fails → enhance original with clarity-upscaler → use that instead.

---

## Flow 5: Approve / Skip / Feedback

- **Approve:** `GET /actions/approve?token=xxx` → status `executed` → posts at scheduled_post_time
- **Skip:** `GET /actions/decline?token=xxx` → status `rejected` → feedback buttons shown
- **Feedback reason:** `GET /actions/feedback?action_id=xxx&reason=wrong_tone` → saved to content_feedback

---

## Flow 6: Post Expiry

- `post_approval_and_expiry` job expires previous day's pending action at scheduled window
- `expire_stale_actions` job is safety net — expires anything pending 3+ days
- Expired posts are never posted, no notification to user

---

## Flow 7: Onboarding Reminder

- User stuck on step 4 (hasn't replied) for 72-96 hours
- `onboarding_reminder` scheduler fires once
- Sends same email 4 with `is_reminder=True`
- Only sends once (checked via email_logs)

---

## Flow 8: Subscription Canceled

- Stripe webhook or daily health check detects `canceled`/`unpaid`
- `biz.subscription_id = None`
- Scheduler skips the business — no more emails or posts

---

## Edge Cases

| Situation | Behavior |
|---|---|
| User approves after scheduled time passed | Posts immediately on next 15-min cycle |
| Meta API fails during posting | `executed_at` stays NULL, retried next cycle |
| No active Meta integration | executor returns `status: skipped` |
| Railway network blip | Scheduler catches error, logs as WARNING (not Sentry), retries next cycle |
| user_memory is NULL | Initialized from business profile on first reply |
| Product photo fal.ai fails | Falls back to clarity-upscaler enhancement of original |
| Content safety blocked | Non-preachy redirect message, no action taken |