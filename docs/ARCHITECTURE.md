# Marlo — System Architecture

*Last updated: August 4, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\ARCHITECTURE.md`*

> ⚠️ **Fully rewritten August 4, 2026.** Old architecture generated and published Instagram posts. New one runs a content supply pipeline → edits → personalizes → sends a newsletter.

---

## Two Governing Constraints

**1. Marlo is the engine, not the brand.**
Neither vendors nor readers know Marlo exists. **The string "Marlo" appearing anywhere customer-facing is a bug.**

**2. The issue ships every week. The pipeline flexes to meet it.**
If vendor material is thin, the answer is **get more material** — never shrink or skip the issue. This drives most of the design below.

---

## Content Supply — The Core Problem

A newsletter that depends on vendors replying will fail, because vendors won't reply reliably. **The system needs enough material every week regardless of who responds.**

```
TIER 1 — Fresh vendor replies (best, unreliable)
  Weekly question → vendor replies with what's new
  Plan for 20–40% response.

TIER 2 — Chase (recovers some of Tier 1)
  Non-responders get one nudge
  Vendors silent 3+ weeks get an easier ask
  ("Just send a photo — no words needed")

TIER 3 — Reserve bank (the buffer that makes weekly possible)
  Evergreen material captured earlier and deliberately held back
  Origin stories, how-to pieces, profiles, process explanations
  Harvested during onboarding and during good weeks
  Tagged by season so it can be released when it fits

TIER 4 — Market-level content (depends on no vendor)
  What's in season, weather, hours, parking, events
  How to store / cook / choose something
  Written ahead, scheduled
```

**The reserve bank is load-bearing.** Design consequence: **during good weeks the system deliberately holds material back rather than using everything.**

Supply is monitored continuously, not discovered on send day. `supply_monitor.py` counts usable material, reports runway in days, and escalates through the tiers before send day arrives.

---

## Stack

| Layer | Technology | Change |
|---|---|---|
| Backend | FastAPI (Python 3.12), async | unchanged |
| Frontend | React (TypeScript) | new purpose: scan landing + preferences |
| Database | PostgreSQL (Railway) | unchanged |
| Hosting | Railway | unchanged |
| Outbound email | Resend | unchanged |
| Inbound email | Postmark | unchanged (vendor replies) |
| AI | Claude Sonnet (editing) + Haiku (classify) | unchanged |
| Images | fal.ai | **enhancement only — never generate** |
| Scheduler | APScheduler | unchanged |
| ~~Instagram, Stripe, Google Ads~~ | — | **archived** |

**Image policy:** real vendor photos, enhanced (crop, brighten, denoise). **No AI-generated imagery.** One fake bread photo destroys a local newsletter's credibility.

**Why APScheduler, not Temporal** *(carried from ADR-002)*: Temporal needs separate worker infrastructure. In-process APScheduler is sufficient at this scale. **Revisit if:** Railway restarts start causing missed sends, or the job count grows past what one process should own.

---

## Directory Structure

```
C:\Users\Octopus\Documents\marlo\
├── backend/
│   ├── main.py                      # FastAPI app, routers, startup migrations
│   ├── database/
│   │   ├── models.py                # rewritten per DATA_MODEL.md
│   │   └── session.py
│   │
│   ├── vendors/                     # ← was businesses/
│   │   └── router.py                # vendor signup, profile, QR generation
│   │
│   ├── subscribers/                 # ★ NEW
│   │   ├── router.py                # scan landing, signup, unsubscribe, preferences
│   │   ├── identity.py              # cookie token issue + verify
│   │   └── interests.py             # scan_events → interest_vector
│   │
│   ├── content/                     # ★ NEW — the supply pipeline
│   │   ├── supply_monitor.py        # tracks runway, triggers escalation
│   │   ├── interview.py             # weekly question, chase logic
│   │   ├── extractor.py             # vendor reply → content_item
│   │   ├── reserve.py               # evergreen bank: deposit, hold, release
│   │   ├── market_content.py        # vendor-independent content
│   │   ├── block_builder.py         # content_item → content_block
│   │   └── style_guard.py           # rejects marketing voice, invention, overlength
│   │
│   ├── newsletter/                  # ★ NEW
│   │   ├── assembler.py             # material → issue (block pool)
│   │   ├── personalizer.py          # score, select, order → issue_render
│   │   ├── renderer.py              # issue_render → HTML
│   │   └── dispatcher.py            # batch send + logging
│   │
│   ├── agent/
│   │   ├── reply_handler.py         # ✅ reused
│   │   ├── vendor_memory.py         # ✅ reused (was user_memory.py)
│   │   ├── vendor_profiles.py       # ✅ reused
│   │   ├── content_safety.py        # ✅ reused
│   │   ├── scheduler.py             # ✅ framework reused, all jobs replaced
│   │   ├── brain.py                 # ✅ reused
│   │   ├── approval_router.py       # ⚠️ repurposed: vendor approves own block
│   │   └── debug_router.py          # keep; remove before launch
│   │
│   ├── email_system/
│   │   ├── inbound.py               # ✅ reused: content intake
│   │   ├── sender.py                # ✅ reused
│   │   └── templates.py             # ⚠️ rewritten: newsletter layout
│   │
│   ├── integrations/
│   │   └── image_gen.py             # ⚠️ repurposed: enhancement only
│   │
│   └── archive/                     # 🗄️ DEAD CODE — not imported anywhere
│       ├── README.md
│       ├── content_pipeline.py, strategy_agent.py, executor.py
│       ├── google_ads_agent.py, analytics_agent.py
│       ├── meta.py, oauth.py, google_ads.py
│       └── billing/
│
├── frontend/src/pages/
│   ├── Scan.tsx, Subscribe.tsx, Preferences.tsx, VendorSignup.tsx
└── docs/
```

**`backend/archive/` is reference only.** Nothing imports from it. Do not build on it.

---

## Design Patterns Carried From v1

These were learned the hard way and still apply.

**Vendor profiles as central config** *(ADR-012)*: all vendor-type-specific behavior lives in `vendor_profiles.py` as one dict. Adding a vendor type = adding one entry, nothing else changes. Now also determines **which fields matter for that vendor type** when editing content.

**Compact memory, not raw history** *(ADR-010)*: `vendor_memory` is a small JSONB summary (~200 tokens), not a growing transcript (~2000 and unbounded). Updated asynchronously with Haiku after each exchange.

**`reply_handler` for conversation, `brain.think()` for autonomous decisions** *(ADR-011)*: `brain.think()` returns structured action JSON and has no conversational memory — it asks clarifying questions every turn. All vendor email replies go through `reply_handler`.

**Network errors suppressed from Sentry** *(ADR-013)*: Railway has occasional DNS blips. `is_network_error(e)` in `scheduler.py` routes these to `WARNING`; real bugs still log `ERROR` and reach Sentry. Without this, one outage generates dozens of alerts and causes alert fatigue.

**Datetime convention** *(ADR-005)*: **always use `datetime.now(timezone.utc)`** in new code. v1 mixed naive `utcnow()` and aware datetimes, which caused comparison crashes. All new tables use aware datetimes throughout.

**Background tasks get their own DB session**: never pass a request's `db` session into `asyncio.create_task()` — the session closes when the request ends. Always `async with AsyncSessionLocal() as db:` inside the task.

---

## Flow ① — Content Supply

```
CONTINUOUS: supply_monitor.py
  Counts usable material for the coming issue
  Reports runway in days → escalates through tiers if short

TIER 1 — weekly question
  content/interview.py picks one question per vendor
  Rotates question_type; never the same kind back-to-back
      ↓
TIER 2 — chase
  48h silent → one nudge
  3 weeks silent → easier ask ("just a photo")
      ↓
TIER 3 — reserve release
  content/reserve.py pulls evergreen material matching the season
      ↓
TIER 4 — market content
  seasonal, how-to, logistics — depends on no vendor

VENDOR REPLY (any time)
  POST /email/inbound (Postmark)
      ↓
  content/extractor.py
      ├── content_safety check
      ├── photos → fal.ai enhancement
      ├── reply_handler interprets
      ├── create content_item (raw_text verbatim)
      └── ★ classify: use now, or deposit to reserve?
```

**The classification step makes weekly delivery possible.** "Peaches this week" ships now; "I started this stall after my mother died" is banked for a thin week.

---

## Flow ② — Editing

```
scheduler: assemble_issue (day before send)
      ↓
content/block_builder.py edits each item
      ├── choose block_type
      ├── write headline
      ├── edit body, preserving the vendor's voice
      ├── pull one direct quote
      └── select image + caption
      ↓
content/style_guard.py checks each block
      ├── ❌ marketing voice ("don't miss," "limited time," "hurry")
      ├── ❌ any fact not in the source material → reject
      ├── ❌ over length → compress
      └── ❌ contains "Marlo" → reject
      ↓
Email each vendor their own block + approve button
      ↓
approved_by_vendor = true
```

**`style_guard.py` only rejects. It never writes.**

---

## Flow ③ — Personalized Send

```
scheduler: send_issue (market local send time)
      ↓
For each active subscriber:
  newsletter/personalizer.py scores every block
  (formula in DATA_MODEL.md)
      ↓
  Select per the issue format spec
  ⚠️ Format is TBD — see PRODUCT.md
      ↓
  Create issue_render (block_ids + order)
      ↓
  renderer.py → HTML → dispatcher.py → Resend
```

**Why persist issue_render:** without it there's no way to answer "why did this person unsubscribe?"

---

## Flow ④ — Scan to Subscribe

```
QR at the stall → https://marlo021.ai/v/A7K2
      ↓
subscribers/identity.py checks sub_token cookie
      │
      ├── No cookie (new)
      │     → Landing: vendor name + photo + what they'll get
      │     → One email field, one unchecked consent box
      │     → create subscriber (consent_at, consent_source)
      │     → set cookie (signed, 2 years)
      │     → create vendor_follow, log scan_event
      │     → welcome email
      │
      └── Cookie present (returning)
            → log scan_event, scan_count += 1
            → "Added [Vendor]" + follow list
            → zero input, about one second
```

**New device:** no cookie but email exists → link to the existing account. **No password — the email address is the identity.**

**Dedup:** same person + vendor + day = one interest signal (all raw events stored).

---

## Scheduler Jobs

| Job | Frequency | What it does |
|---|---|---|
| `supply_monitor` | every 6h | Count material, report runway, escalate |
| `weekly_vendor_interview` | hourly check | Ask each vendor one question |
| `interview_chase` | daily | Nudge non-responders; easier ask for long-silent |
| `assemble_issue` | hourly check | Build the block pool |
| `request_block_approval` | after assembly | Email vendors their block |
| `send_issue` | hourly check | Send at market local time |
| `recompute_interests` | daily | Rebuild interest_vector |
| `reserve_health` | weekly | Report reserve depth; warn if thin |

---

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://...
ANTHROPIC_API_KEY=sk-ant-...
FAL_API_KEY=...
RESEND_API_KEY=re_...
POSTMARK_SERVER_TOKEN=...
APP_BASE_URL=https://api.marlo021.ai
FRONTEND_URL=https://marlo021.ai
JWT_SECRET_KEY=...
SUBSCRIBER_TOKEN_SECRET=...        ★ NEW: signs subscriber cookies
ENVIRONMENT=production

# Archived — no longer used
# STRIPE_*  INSTAGRAM_*  META_*  GOOGLE_*
```

---

## Open Questions

**Blocking:**
- **Issue format** — sections, word budget, vendors per issue, behavior at very low/high follow counts. All of Flow ③ depends on it.
- **Newsletter brand name** and **sending domain** (can't be marlo021.ai)

**Non-blocking:**
- Physical QR format
- Vendor onboarding: self-serve or bulk import