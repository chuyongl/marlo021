# Marlo — Architecture Decision Records

---

## ADR-001: Email as the only interface (no dashboard)

**Decision:** All user interactions happen via email. No web dashboard.

**Why:** Target users (1-10 person SMBs) have low tech adoption. They already use email daily. No competitor does this.

**Trade-offs:** Complex operations can't be done via email. If email goes to spam, entire experience breaks.

**Status:** Core to product identity. Do not change.

---

## ADR-002: APScheduler instead of Temporal

**Decision:** Use APScheduler (in-process) for all scheduled jobs.

**Why:** Temporal requires separate worker infrastructure. APScheduler is sufficient at <100 businesses.

**When to revisit:** 100+ active businesses or Railway restarts causing missed sends.

---

## ADR-003: One-click approval (no login required)

**Decision:** Approve/decline links work without authentication.

**Why:** Login friction causes abandonment. Security risk is low — worst case someone approves/declines a post.

---

## ADR-004: strategy_summary uses only key_message

**Decision:** Emails show `strategy.key_message`, not full strategy object.

**Why:** Full strategy object contains internal prompt fields that sound robotic to users.

**Status:** Fixed May 8. Do not revert.

---

## ADR-005: datetime conventions

**Decision:** `created_at` uses `datetime.utcnow()` (naive). `scheduled_post_time` uses `datetime.now(timezone.utc)` (aware).

**For new code:** Always use `datetime.now(timezone.utc)`. The inconsistency is tech debt, not a pattern to follow.

---

## ADR-006: Instagram Login API instead of Facebook Login

**Decision:** Use Instagram Login API for all Instagram connections.

**Why:** Facebook Login requires connecting to a Facebook Page — creates impossible friction for non-technical users. Instagram Login requires only an Instagram Business/Creator account.

**What changed (May 13):**
- New endpoints: `/integrations/connect/instagram` and `/integrations/callback/instagram`
- Token endpoint: `api.instagram.com/oauth/access_token` → `graph.instagram.com/access_token`
- Integration stored as `platform="meta"` for backward compat with executor
- Posting via `graph.instagram.com` (not `graph.facebook.com`)

**Status:** Working end-to-end as of May 21, 2026.

---

## ADR-007: Posting schedule stored as array

**Decision:** `Business.posting_schedule` is a JSON array of day names.

**Usage:** Always read via `get_posting_schedule(biz)` helper in scheduler.py.

---

## ADR-008: Content approval is two-step

**Decision:** Approve click → status `executed`. Scheduler posts at `scheduled_post_time`.

**Why:** Immediate posting would mean posts go live at unpredictable times. Two-step lets users approve early and post at the right time.

**Important:** Never call executor at approval time. Only `executor.run()` called by scheduler.

---

## ADR-009: Legal pages as React components

**Decision:** Privacy Policy and Terms of Service are React pages, not static HTML.

**Pages:** `marlo021.ai/privacy` and `marlo021.ai/terms`

**Status:** Live as of May 13, 2026.

---

## ADR-010: User memory instead of conversation history (★ NEW)

**Decision:** Each business has a compact `user_memory` JSONB field. Replies use this instead of raw conversation history.

**Why:**
- Raw history = ~2000 tokens per call, grows unboundedly
- User memory = ~200 tokens, stable size, more accurate
- Memory captures what matters: preferences, style notes, context
- Updated asynchronously after each reply using Haiku (cheap)

**Structure:**
```json
{
  "vendor_type": "maker_jewelry",
  "content_preferences": {"likes": [], "dislikes": [], "style_notes": ""},
  "recent_context": "one sentence",
  "pending_topics": [],
  "updated_at": "YYYY-MM-DD"
}
```

**Migration:** Added via startup auto-migration in `main.py`. Safe to run on every deploy.

---

## ADR-011: reply_handler separate from brain.think() (★ NEW)

**Decision:** Email replies use `reply_handler.handle_reply()`. Autonomous agent actions use `brain.think()`.

**Why:**
- `brain.think()` returns JSON with actions array — designed for agent decisions
- Email replies need conversational output, not structured actions
- `brain.think()` had no conversation memory, causing it to ask clarifying questions every turn
- `reply_handler` uses user_memory for context, is instructed to execute first and never ask >1 question

**Rule:** `brain.think()` = scheduler, campaigns, autonomous decisions. `reply_handler` = all email replies from users.

---

## ADR-012: Vendor profiles as central config (★ NEW)

**Decision:** All vendor-type-specific logic lives in `vendor_profiles.py` as a single dict.

**Why:**
- Content strategy, image style, caption tone, hashtags all differ by vendor type
- Centralizing means: adding a new vendor type = add one dict entry, nothing else changes
- Used by: `reply_handler`, `image_gen`, `inbound`, `user_memory`

**Current types:** `maker_jewelry`, `maker_ceramics`, `maker_candles`, `food_bakery`, `food_cafe`, `farmer_market`, `service_local`, `creative_professional`

**Detection:** `detect_vendor_type_from_industry(industry_string)` auto-detects from business.industry. Can be overridden by user_memory.vendor_type.

---

## ADR-013: Network errors suppressed from Sentry (★ NEW)

**Decision:** Railway infrastructure errors (DNS failures, connection timeouts) log as `WARNING`, not `ERROR`, so Sentry doesn't capture them.

**Why:** Railway has occasional network blips. These are not code bugs and don't need developer attention. Previously they were generating dozens of Sentry alerts per outage, causing alert fatigue.

**Implementation:** `is_network_error(e)` helper in `scheduler.py` checks for known transient error strings. `log_error(context, e)` routes accordingly.

**Real bugs** (non-network errors) still log as `ERROR` and are captured by Sentry.