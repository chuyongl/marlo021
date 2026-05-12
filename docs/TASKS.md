# Marlo — Task Board

*Updated: May 8, 2026*

---

## 🔥 In Progress (Today)

### [P0] Switch to Instagram Login API
**Why:** Facebook Login requires Page-Instagram connection at API level — creates impossible friction for non-technical users. Instagram Login removes this entirely.
**Files:** `backend/integrations/oauth.py`, `backend/agent/executor.py`
**Steps:**
- [ ] Add Instagram Login product in Meta Developer Console
- [ ] New `GET /integrations/connect/instagram` endpoint
- [ ] New `GET /integrations/callback/instagram` callback
- [ ] Store `access_token` + `ig_account_id` from `/me`
- [ ] Update executor to use `graph.instagram.com`
- [ ] Update onboarding email copy ("Connect Instagram" not "Connect Facebook")
- [ ] Test end-to-end: connect → approve post → post live on Instagram

### [P0] Set up /docs knowledge base
**Why:** AI-native dev workflow — any agent or developer reads /docs to understand full product.
**Files:** `docs/` folder in repo
**Steps:**
- [x] PRODUCT.md
- [x] ARCHITECTURE.md
- [x] STATUS.md
- [x] DECISIONS.md
- [x] TASKS.md (this file)
- [ ] .cursorrules
- [ ] Push to GitHub

---

## 📋 Up Next (This Week)

### [P0] Privacy policy page
**Why:** Required for Meta app review submission.
**Files:** New page at `marlo021.ai/privacy`
**Estimate:** 1 hour

### [P0] Test real Instagram post end-to-end
**Depends on:** Instagram Login OAuth working
**Steps:**
- [ ] Connect `marlo021.ai` Instagram via new OAuth
- [ ] Run debug/trigger-kickoff
- [ ] Approve post
- [ ] Verify post appears on Instagram

### [P1] Meta app review submission
**Why:** `instagram_business_content_publish` needs Advanced Access before real users can connect.
**Steps:**
- [ ] Prepare demo video of app flow
- [ ] Submit for review in Meta Developer Console
- [ ] Wait 1-2 weeks for approval

### [P1] Stripe live mode
**Steps:**
- [ ] Switch `STRIPE_SECRET_KEY` to `sk_live_...`
- [ ] Switch `STRIPE_WEBHOOK_SECRET` to live webhook secret
- [ ] Test real payment
- [ ] Update Railway env vars

---

## 🎯 Next 2 Weeks

### [P1] Find 3-5 beta users
**Target:** Seattle area restaurants or pet services
**Why restaurants:** Perfect use case for "photo → email → post" flow
**Why pet services:** Least served market, highest willingness to pay
**Channels:**
- [ ] Personal network
- [ ] Direct outreach to local Instagram accounts with low posting frequency
- [ ] Build-in-public content (cheapest CAC)

### [P2] .cursorrules file
**Why:** Consistent AI coding across sessions and future developers
**Content:** Coding patterns, what NOT to do, FastAPI conventions, async rules

### [P2] Weekly analytics email improvements
**Current:** Basic stats, AI-generated insights
**Needed:** Make insights more actionable ("Your Wednesday posts get 40% more engagement — keep that day")

---

## 🧊 Backlog (Future)

- Google Ads integration (currently connected but not generating campaigns)
- Multi-platform posting (Facebook, TikTok)
- Pricing tier 2 ($149-199 with Google Ads management)
- Email open/click rate tracking
- A/B testing for captions
- Post revision via email reply (was working in earlier version, needs re-testing)
- White-label via Vendasta channel partners

---

## ✅ Completed

| Date | Task |
|---|---|
| May 8 | Fix approval_router status check (pending vs pending_approval) |
| May 8 | Fix debug_router idempotency (clear pending before regenerating) |
| May 8 | Scheduler reads user's kickoff day (not hardcoded Sunday) |
| May 8 | Add posting-schedule endpoint to businesses/router.py |
| May 8 | Image guide — creative director style, tied to strategy |
| May 8 | Fix two emails sent on trigger (email log check) |
| May 8 | Set up /docs knowledge base |
| Earlier | All 4 onboarding emails |
| Earlier | first_kickoff and weekly_kickoff emails |
| Earlier | post_approval email |
| Earlier | weekly_analytics email |
| Earlier | Stripe 14-day trial |
| Earlier | fal.ai image generation |
| Earlier | Kickoff day picker in email |
| Earlier | Posting days picker in email |
| Earlier | Timezone auto-detect on signup |