# Marlo — Task Board

*Updated: August 11, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\TASKS.md`*

> **Doc rule:** REPLACED each session, never appended. Finished work moves to the completed log.

---

## 📐 P0 — Editorial Rules (design, no code)

**Start here next session.** Everything downstream depends on these.

### Issue format
- [ ] Word budget per issue — mix of short and longer, exact shape TBD
- [ ] What sections exist; fixed or variable
- [ ] How many vendors appear per issue
- [ ] How many follows a reader needs for the issue to feel relevant
- [ ] **Reader follows 1 vendor** — what fills the issue?
- [ ] **Reader follows 40** — what gets cut? Does it feel like loss?
- [ ] Minimum material required to assemble at full length

### Content supply
- [ ] Question set for vendors + rotation logic
- [ ] Reserve-bank rules: what qualifies, when to hold vs use
- [ ] Market-level content types (seasonal, how-to, logistics)
- [ ] Supply runway metric and escalation thresholds

**Working assumption only, not a decision:** one deeper story + several short pieces.

---

## ❓ Decisions Needed From Anna

| Decision | Blocks |
|---|---|
| **Newsletter brand name** | Any outbound email |
| **Sending domain** (not marlo021.ai) | Any outbound email |
| Issue format (above) | Assembly and personalization |
| Physical QR format (sticker / table tent / bag) | Vendor onboarding |
| Vendor onboarding: self-serve or bulk import | `vendors/router.py` |

---

## 🏗️ P1 — Core Build

Ordered so real vendor material arrives as early as possible.

- [ ] **Rewrite `database/models.py`** — all new tables per `DATA_MODEL.md`
- [ ] **Content intake** — vendor reply → `content_item` (repurpose `inbound.py`)
- [ ] **Interview + chase** — weekly question, nudge non-responders
- [ ] **Block builder** — `content_item` → `content_block`, written against the P0 spec
- [ ] **Style guard** — reject marketing voice, invented facts, overlength, the word "Marlo"
- [ ] **Scan → subscribe** — `GET /v/{scan_code}`, landing page, consent, cookie, follow
- [ ] **Assembler + personalizer** — issue pool → per-reader selection
- [ ] **Renderer** — newsletter HTML template
- [ ] **Dispatcher** — batch send via Resend
- [ ] **Unsubscribe** — one-click, immediate (legally required)

---

## 🧱 P2 — Supply Infrastructure

- [ ] **Reserve bank** — deposit, tag by season, hold, release
- [ ] **Market content** — vendor-independent pieces written ahead
- [ ] **Supply monitor** — continuous runway tracking + escalation
- [ ] Vendor block approval flow
- [ ] Photo enhancement via fal.ai (real photos only)
- [ ] Interest vector computation from scan history
- [ ] Vendor onboarding page + QR generation

---

## 🎨 P3 — Later

- [ ] Preferences page (mute vendor, change frequency)
- [ ] Open / click tracking
- [ ] Multi-market support
- [ ] Fix missing `await` on `detect_vendor_type_from_industry` in `reply_handler.py`
- [ ] Replace or remove `agent/router.py` and `agent/debug_router.py`
- [ ] Delete `backend/archive/` once we're sure

---

## 🧊 Backlog

- Revenue model (deliberately unresolved)
- Instagram posting — archived; revive only if the newsletter needs a social arm

---

## ✅ Completed Log

### August 11, 2026 — Cleanup and consolidation
- [x] Moved 9 modules + `billing/` to `backend/archive/` via `git mv`
- [x] Rewrote `main.py` — archived routers removed, fault-tolerant router loading, v`0.2.0`
- [x] Rewrote `agent/scheduler.py` — removed all 7 Instagram-era jobs; kept Sentry filter and timezone helpers, generalized for markets
- [x] Verified all 6 remaining routers load
- [x] Consolidated docs 11 → 7; deleted `DECISIONS.md`, `PHASE_2_DIRECTION.md`, `FLOWS.md`, `ERRORS.md`
- [x] Absorbed surviving ADRs into `PRODUCT.md` (principles) and `ARCHITECTURE.md` (patterns)
- [x] Rewrote `API.md` for the newsletter endpoint surface
- [x] Deployed

### August 4, 2026 — Pivot to newsletter
- [x] Redefined the product: consumer newsletter, free both sides, Marlo invisible
- [x] Established "the issue ships every week; the pipeline flexes" as a governing principle
- [x] Designed the four-tier content supply model (fresh / chase / reserve / market)
- [x] Designed scan-to-subscribe: QR → one-time signup → auto-follow, no password
- [x] Designed personalization scoring, including forced discovery of unfollowed vendors
- [x] Added Rule 4 to `COLLABORATION_GUIDE.md` — no unsolicited startup advice
- [x] Set English as the default working language
- [x] Reprioritized: editorial rules are P0, not the pipeline

### August 1, 2026 — Bug fixes (now moot, code archived)
- [x] Fixed `create_pending_action_with_tokens` writing wrong `action_type` / `status` / null `scheduled_post_time`
- [x] Fixed scheduler filtering on `subscription_id`, hiding all free users
- [x] Ran life-moment inference tests on mock data (general store + jewelry)

### Earlier
- [x] Instagram posting end-to-end, OAuth, user memory, vendor profiles, content safety, lifestyle image generation, all core email flows, privacy + terms pages