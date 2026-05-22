# Marlo — Task Board

*Updated: May 22, 2026*

---

## 🔴 IMMEDIATE (next session — first thing)

### [P0] Test conversational reply flow end-to-end
Reset was broken (onboarding_step not restored) — now fixed. Re-test:
- [ ] PowerShell reset: `Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-..."`
- [ ] Browser trigger-kickoff
- [ ] Reply with milestone content
- [ ] Verify Railway logs show `[ReplyHandler] Intent: post_request`
- [ ] Verify approve button appears in email
- [ ] Approve → verify post goes live on Instagram

---

## 🟡 THIS WEEK

### [P0] Meta app review submission
- [ ] Screen recording of full Instagram connect + post flow
- [ ] Submit for `instagram_business_content_publish` Advanced Access
- [ ] App ID: `918827927853545`

### [P1] Image quality improvement
- [ ] Switch `fal-ai/flux-pro/v1.1` → `fal-ai/flux-pro/v1.1-ultra` in `image_gen.py`
- [ ] Improve prompt to avoid human figure errors (two laptops etc.)
- [ ] Cost difference: $0.055 → $0.06 per image (negligible)

### [P1] Stripe live mode
- [ ] Switch `STRIPE_SECRET_KEY` → `sk_live_...`
- [ ] Switch `STRIPE_WEBHOOK_SECRET` → live webhook secret

---

## 🟢 SOON

- [ ] **Find 3-5 beta users** — Seattle restaurants or pet services
- [ ] **Remove debug_router** before going live with real users
- [ ] **Test photo upload** with real product photo → lifestyle image

---

## 🧊 Backlog

- Google Ads integration (code exists, never tested)
- Multi-platform posting (Facebook, TikTok)
- Pricing tier 2 ($149-199 with Google Ads)
- Email open/click rate tracking
- Add more vendor types to `vendor_profiles.py` as needed

---

## ✅ Completed This Session (May 22)

- [x] Two-step intent classification in reply_handler (Haiku classify → Sonnet generate)
- [x] Cross-email conversation history (EmailLog.reply_content + load_conversation_history)
- [x] debug_router reset now restores onboarding_completed=True, onboarding_step=5
- [x] billing_router.py Stripe SDK `.get()` fix in handle_payment_failed + handle_payment_succeeded
- [x] Sentry ENVIRONMENT=production set in Railway
- [x] user_memory.py correct file deployed (was accidentally overwritten with migration code)
- [x] migrations/ folder removed (migration now in main.py startup)

## ✅ Completed Previous Sessions

- [x] Instagram posting end-to-end (meta.py graph.instagram.com + polling)
- [x] User memory system (businesses.user_memory JSONB)
- [x] Vendor profiles (7 types, auto-detection)
- [x] Content safety filter
- [x] Lifestyle image generation from product photo
- [x] Scheduler network errors suppressed from Sentry
- [x] Instagram OAuth end-to-end
- [x] All core email flows
- [x] Stripe 14-day trial
- [x] Privacy + Terms pages live