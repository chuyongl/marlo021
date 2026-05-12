# Marlo — Architecture Decision Records

Each decision recorded here explains WHAT we chose and WHY. Future developers (human or AI) should read this before suggesting changes.

---

## ADR-001: Email as the only interface (no dashboard)

**Decision:** All user interactions happen via email. No web dashboard.

**Why:** 
- Target users (1-10 person SMBs) have low tech adoption
- They already use email daily — zero learning curve
- 75% of SaaS users churn in the first week because of complexity
- No competitor does this — genuine market differentiation

**Trade-offs accepted:**
- Complex operations (fine-grained ad targeting) can't be done via email
- If email goes to spam, entire product experience breaks

**Status:** Core to product identity. Do not change.

---

## ADR-002: APScheduler instead of Temporal

**Decision:** Use APScheduler (in-process) for all scheduled jobs.

**Why:**
- Temporal requires a separate worker process + infrastructure
- At <100 businesses, APScheduler is sufficient
- Simpler Railway deployment (one service not two)

**Trade-offs accepted:**
- Scheduler stops if Railway service restarts (brief gap in execution)
- Harder to scale to 1000+ businesses

**When to revisit:** When we have 100+ active businesses or Railway restarts are causing missed sends.

---

## ADR-003: One-click approval (no login required)

**Decision:** Approve/decline links work without any authentication.

**Why:**
- Requiring login before approving a post adds friction
- Non-technical users forget passwords
- Security risk is low — worst case is someone spoofs a link and approves/declines a post

**Trade-offs accepted:**
- Anyone with the link can approve/decline
- Links don't expire (currently) — could be tightened

---

## ADR-004: strategy_summary uses only key_message

**Decision:** Weekly kickoff emails show `strategy.key_message`, not full strategy object.

**Why:**
- Full strategy object contains internal prompt fields (Tone, CTA) that sound robotic to users
- `key_message` is human-readable and motivating
- Example: "Building trust by showing the real humans behind the business" vs "Tone: warm. CTA: drive foot traffic."

**Status:** Fixed May 8. Do not revert.

---

## ADR-005: datetime conventions

**Decision:** `created_at` uses `datetime.utcnow()` (naive). `scheduled_post_time` uses `datetime.now(timezone.utc)` (aware).

**Why (historical):** Early code used naive datetimes. `scheduled_post_time` was added later and used aware datetimes. Changing all of them risks breaking comparisons.

**For new code:** Always use `datetime.now(timezone.utc)` (aware). The inconsistency is a tech debt to clean up, not a pattern to follow.

---

## ADR-006: Facebook Login → Instagram Login migration

**Decision:** Migrate Meta OAuth from Facebook Login to Instagram Login API.

**Why:**
- Facebook Login requires Instagram to be connected to a Facebook Page
- This creates massive friction for non-technical users (they don't have Pages, or Pages have ad violations)
- Instagram Login (launched July 2024) requires only an Instagram Business/Creator account
- User experience: "Log in with Instagram" vs "Connect Facebook, then select Page, then select Instagram"
- For our target market (non-technical SMB owners), Facebook Login has ~10% completion rate; Instagram Login should be ~80%

**What changes:**
- OAuth URL: `instagram.com/oauth/authorize` (not `facebook.com/dialog/oauth`)
- Scopes: `instagram_business_basic,instagram_business_content_publish,instagram_business_manage_insights`
- API host: `graph.instagram.com` for posting
- No Facebook Page required — account ID comes from `/me` directly

**Status:** IN PROGRESS as of May 8, 2026.

---

## ADR-007: Posting schedule stored as array

**Decision:** `Business.posting_schedule` is a PostgreSQL array of day names (e.g., `["Monday", "Wednesday", "Friday"]`).

**Why:**
- Flexible (can be 1-7 days)
- Human-readable
- Easy to display in emails as day buttons

**Usage:** Always read via `get_posting_schedule(biz)` helper in `scheduler.py` — it handles NULL/empty/invalid values with sensible defaults.

---

## ADR-008: Content approval is two-step

**Decision:** User clicks Approve → status becomes `executed`. Then scheduler posts at `scheduled_post_time`.

**Why:**
- Immediate posting on approval would mean posts go live at unpredictable times
- Users expect posts to go live at their chosen time (e.g., Monday 9am)
- Two-step: user approves early → Marlo posts at the right time

**Important:** `executor.py` has an `execute_action()` method that was previously called at approval time. This was removed. Only `executor.run()` is called by the scheduler. Do not re-add immediate execution at approval.