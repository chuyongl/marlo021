# Marlo — Task Board

*Updated: August 4, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\TASKS.md`*

> **Doc rule:** REPLACED each session, never appended. Finished work moves to the completed log.

---

## 🔧 P0-A — Cleanup (finish first, mechanical)

- [ ] Run `git mv` to move archived files into `backend/archive/`
- [ ] **Rewrite `main.py`** — drop router registrations for archived modules
- [ ] **Rewrite `scheduler.py`** — drop archived imports and their jobs
- [ ] Verify the app boots locally
- [ ] Commit and push; confirm Railway deploys green

⚠️ **Do not push mid-way.** The app won't start until `main.py` and `scheduler.py` are clean.

---

## 📐 P0-B — Editorial Rules (design, no code)

**This is the real P0.** Content generation can be done unscalably at first; the rules cannot be missing.

### Issue format
- [ ] Word budget per issue — mix of short and longer, exact shape TBD
- [ ] What sections exist; fixed or variable
- [ ] How many vendors appear per issue
- [ ] How many follows a reader needs for the issue to feel relevant
- [ ] **Reader follows 1 vendor** — what fills the issue?
- [ ] **Reader follows 40** — what gets cut? Does it feel like loss?
- [ ] Minimum material required to assemble at full length

### Content supply design
- [ ] Question set for vendors + rotation logic
- [ ] Reserve-bank rules: what qualifies, when to hold vs use
- [ ] Market-level content types (seasonal, how-to, logistics)
- [ ] Supply runway metric and escalation thresholds

**Working assumption only, not a decision:** one deeper story + several short pieces.

**Best way to decide these: get real material from a few real vendors and edit it by hand.** Rules written against imagined replies won't survive.

---

## 🏗️ P1 — Core Build

Ordered so real vendor material arrives as early as possible.

- [ ] **Rewrite `database/models.py`** — all new tables per `DATA_MODEL.md`
- [ ] **Content intake** — vendor reply → `content_item` (repurpose `inbound.py`)
- [ ] **Interview + chase** — weekly question, nudge non-responders
- [ ] **Block builder** — `content_item` → `content_block`, written against the P0-B spec
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
- [ ] Delete `backend/archive/` once we're sure
- [ ] Remove `debug_router.py` before real readers

---

## ❓ Decisions Needed From Anna

| Decision | Blocks |
|---|---|
| **Newsletter brand name** | Any outbound email |
| **Sending domain** (not marlo021.ai) | Any outbound email |
| Issue format (P0-B above) | Assembly and personalization |
| Physical QR format | Vendor onboarding |
| Vendor onboarding: self-serve or bulk import | `vendors/router.py` |

---

## 🧊 Backlog

- Revenue model (deliberately unresolved)
- Prediction / personalization engine — see `PHASE_2_DIRECTION.md` (shelved)
- Instagram posting — archived, revive only if the newsletter needs a social arm

---

## ✅ Completed Log

### August 4, 2026 — Pivot to newsletter
- [x] Redefined the product: consumer newsletter, free both sides, Marlo invisible
- [x] Established "the issue ships every week; the pipeline flexes" as a governing principle
- [x] Designed the four-tier content supply model (fresh / chase / reserve / market)
- [x] Rewrote `PRODUCT.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`
- [x] Designed scan-to-subscribe: QR → one-time signup → auto-follow, no password
- [x] Designed personalization scoring, including forced discovery of unfollowed vendors
- [x] Added Rule 4 to `COLLABORATION_GUIDE.md` — no unsolicited startup advice
- [x] Set English as the default working language
- [x] Decided to archive rather than delete old code
- [x] Reprioritized: editorial rules are P0, not the pipeline

### August 1, 2026 — Bug fixes (now moot)
- [x] Fixed `create_pending_action_with_tokens` writing wrong `action_type` / `status` / null `scheduled_post_time`
- [x] Fixed scheduler filtering on `subscription_id`, hiding all free users
- [x] Standardized doc filenames
- [x] Ran life-moment inference tests on mock data (general store + jewelry)

*(Both fixes were on the Instagram path, now archived. Retained for history.)*

### Earlier
- [x] Instagram posting end-to-end, OAuth, user memory, vendor profiles, content safety, lifestyle image generation, all core email flows, privacy + terms pages