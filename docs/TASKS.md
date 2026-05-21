# Marlo — Task Board

*Updated: May 21, 2026*

---

## 🔴 IMMEDIATE (next session)

### [P0] Test conversational reply flow
- [ ] Trigger kickoff → get approval email
- [ ] Reply: "Make it less like an ad, more like sharing my work"
- [ ] Verify: Marlo rewrites immediately, no clarifying questions
- [ ] Reply with raw notes/story → verify post generated directly
- [ ] Check Railway logs for `[UserMemory] Updated` after each reply
- [ ] Check DB: `SELECT user_memory FROM businesses WHERE id = '3512ed4f-...'`

### [P0] Test photo upload flow
- [ ] Reply to any Marlo email with a product photo attached
- [ ] Verify: lifestyle image generated (not just enhanced original)
- [ ] Verify: caption matches vendor tone
- [ ] Verify: preview email shows generated image with approve button

---

## 🟡 THIS WEEK

### [P0] Meta app review submission
- [ ] Screen recording of full Instagram connect + post flow
- [ ] Submit for `instagram_business_content_publish` Advanced Access
- [ ] App ID: `918827927853545`

### [P1] Upload app icon to Meta Console
- [ ] Go to `developers.facebook.com/apps/918827927853545/settings/basic/`
- [ ] Upload `logo1024.jpg` (1024x1024)

### [P1] Stripe live mode
- [ ] Switch `STRIPE_SECRET_KEY` → `sk_live_...`
- [ ] Switch `STRIPE_WEBHOOK_SECRET` → live webhook secret
- [ ] Test real payment

---

## 🟢 SOON

- [ ] **Find 3-5 beta users** — Seattle restaurants or pet services
- [ ] **Remove debug_router** before going live with real users
- [ ] **Fix reset endpoint** ForeignKeyViolation (if it recurs)

---

## 🧊 Backlog

- Google Ads integration (code exists, never tested)
- Multi-platform posting (Facebook, TikTok)
- Pricing tier 2 ($149-199 with Google Ads management)
- Email open/click rate tracking
- A/B testing for captions
- White-label via Vendasta
- Add more vendor types to `vendor_profiles.py` as needed

---

## ✅ Completed

| Date | Task |
|---|---|
| May 21 | ENVIRONMENT=production set in Railway |
| May 21 | Sentry network errors suppressed (warning not error) |
| May 21 | scheduler.py is_network_error() + log_error() helpers |
| May 21 | user_memory.py — per-user knowledge base |
| May 21 | reply_handler.py — conversational reply with memory |
| May 21 | vendor_profiles.py — 7 vendor types |
| May 21 | content_safety.py — silent content filter |
| May 21 | inbound.py — routes all replies through reply_handler |
| May 21 | image_gen.py — vendor-aware lifestyle generation |
| May 21 | models.py — user_memory JSONB column |
| May 21 | main.py — startup auto-migration for user_memory |
| May 18 | Instagram posting end-to-end working (meta.py graph.instagram.com + polling) |
| May 18 | meta.py — token decryption, container status polling |
| May 18 | executor.py — correct platform lookup |
| May 18 | INSTAGRAM_APP_SECRET corrected in Railway |
| May 13 | Privacy page live at marlo021.ai/privacy |
| May 13 | Terms page live at marlo021.ai/terms |
| May 13 | Instagram Login OAuth written and deployed |
| May 13 | Meta Console fully configured |
| May 8 | All core email flows working |
| May 8 | Approval flow fixed |
| May 8 | Scheduler kickoff day logic |
| May 8 | fal.ai image generation |
| May 8 | Stripe 14-day trial |