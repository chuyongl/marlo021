# Marlo — Task Board

*Updated: May 13, 2026*

---

## 🔥 In Progress (Tomorrow)

### [P0] Test Instagram Login end-to-end
**Why:** Code is written and deployed — need to verify it actually works before finding beta users.
**Steps:**
- [ ] Reset test account: `DELETE /debug/reset/3512ed4f...`
- [ ] Go to onboarding flow, click "Connect Instagram"
- [ ] Log in with marlo021.ai Instagram credentials
- [ ] Verify `platform_account_id` populated in DB:
  ```sql
  SELECT platform_account_id FROM platform_integrations
  WHERE business_id = '3512ed4f-...' AND platform = 'meta';
  ```
- [ ] Trigger kickoff: `browser → /debug/trigger-kickoff/3512ed4f...`
- [ ] Approve a post
- [ ] Verify post appears on Instagram
- [ ] If fails → check Railway logs, debug from there

---

## 📋 Up Next (This Week)

### [P0] Upload app icon to new Meta app
**Why:** Required for Meta app review submission. Failed May 13 due to Meta upload bug.
**Steps:**
- [ ] Go to `developers.facebook.com/apps/918827927853545/settings/basic/`
- [ ] Upload `logo1024.jpg` as app icon
- [ ] Save

### [P0] Meta app review submission
**Why:** `instagram_business_content_publish` needs Advanced Access before real users can connect.
**Depends on:** Instagram end-to-end test passing + app icon uploaded
**Steps:**
- [ ] Prepare screen recording of full Instagram connect + post flow
- [ ] Submit for review in Meta Developer Console (App ID: `918827927853545`)
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
- Rename `/skip-meta` → `/skip-instagram` for clarity

---

## ✅ Completed

| Date | Task |
|---|---|
| May 13 | Privacy policy page live at marlo021.ai/privacy |
| May 13 | New Business-type Meta app created (App ID: 918827927853545) |
| May 13 | Instagram Login product added to new Meta app |
| May 13 | Redirect URI configured in Meta Developer Console |
| May 13 | Instagram Login OAuth endpoints written and deployed (oauth.py) |
| May 13 | executor.py updated to use graph.instagram.com |
| May 13 | Onboarding email 2 updated — "Connect Instagram" no Facebook required |
| May 13 | Email subject lines updated to reflect Instagram Login flow |
| May 13 | INSTAGRAM_APP_ID + INSTAGRAM_APP_SECRET added to Railway |
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