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

## ADR-006: Instagram Login API instead of Facebook Login

**Decision:** Use Instagram Login API (launched July 2024) for all Instagram connections. Facebook Login flow is kept in code but no longer used for new connections.

**Why:**
- Facebook Login requires Instagram to be connected to a Facebook Page at the Graph API level
- This creates impossible friction for non-technical users — they don't have Pages, or Pages have ad policy violations
- Instagram Login requires only an Instagram Business/Creator account — no Facebook Page needed
- User experience: "Log in with Instagram" (one step) vs "Connect Facebook → select Page → select Instagram" (three steps)
- Estimated completion rate: Facebook Login ~10%, Instagram Login ~80% for our target market

**What changed (May 13, 2026):**
- Created new Business-type Meta app (App ID: `918827927853545`, Instagram App ID: `1004448018806665`)
- New endpoints: `GET /integrations/connect/instagram` and `GET /integrations/callback/instagram`
- OAuth URL: `instagram.com/oauth/authorize` (not `facebook.com/dialog/oauth`)
- Token exchange: `api.instagram.com/oauth/access_token` → then exchange for long-lived token via `graph.instagram.com/access_token`
- Account ID: fetched from `graph.instagram.com/me` directly (no Facebook Page lookup)
- Integration stored as `platform="meta"` in DB for backward compatibility with executor
- Posting still uses `MetaIntegration` class but via `graph.instagram.com` host
- Old Facebook Login endpoints (`/connect/meta`, `/callback/meta`) kept for backward compat but not linked from any email

**Credentials in Railway:**
- `INSTAGRAM_APP_ID` — new app
- `INSTAGRAM_APP_SECRET` — new app
- `META_APP_ID` / `META_APP_SECRET` — old app, kept but unused for new connections

**Status:** Code complete and deployed May 13, 2026. End-to-end test pending.

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

---

## ADR-009: Privacy policy as React page, not static HTML

**Decision:** Privacy policy lives at `frontend/src/pages/Privacy.tsx`, served at `marlo021.ai/privacy`.

**Why:**
- Consistent with the rest of the frontend stack (React + Tailwind)
- Matches Marlo brand (black background, lime green accent)
- Required for Meta app review — must be a real, publicly accessible URL
- `docs/privacy.html` (old placeholder) has been deleted — it was never deployed

**Content requirements met for Meta app review:**
- Instagram permissions explained (`instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`)
- Data collection, sharing, retention, deletion described
- User rights (access, correction, deletion, portability) listed
- Contact email: `privacy@marlo021.ai`
- Deauthorize callback URL: `https://api.marlo021.ai/integrations/deauthorize/instagram`
- Data deletion URL: `https://api.marlo021.ai/integrations/delete/instagram`

**Status:** Live at `https://marlo021.ai/privacy` as of May 13, 2026.