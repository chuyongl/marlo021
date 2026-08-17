# Brown Bag — System Architecture

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\ARCHITECTURE.md`*

> **Naming:** *Brown Bag* is the publication. *Marlo* is the backend system (repo name, API, internal docs). **"Marlo" in any reader- or vendor-facing output is a bug.**

---

## Three Governing Constraints

**1. The reader never sees the machinery.** Brown Bag is the only name that appears.

**2. The issue ships every week.** Structure is fixed. Thin material means get more material, never shrink or skip.

**3. Nothing ships without editor approval.** Every block passes a human before entering the bank. Assembly then runs with no human in the critical path.

---

## Three Surfaces

```
Vendors  → web app    chat with agent, upload photos       magic link
Editors  → web app    review queue, approve/reject         real login
Readers  → email      the newsletter                       cookie from QR scan
```

**This replaces v1's "email is the only interface."** Email is now the reader delivery channel only. `email_system/inbound.py` (Postmark) is **no longer the content intake pipe** — intake moved to the vendor web app.

---

## Stack

| Layer | Technology | Change |
|---|---|---|
| Backend | FastAPI (Python 3.12), async | unchanged |
| Frontend | React (TypeScript) | **major expansion** — vendor + editor apps |
| Database | PostgreSQL (Railway) | unchanged |
| Hosting | Railway | unchanged |
| Outbound email | Resend | newsletter + vendor reminders |
| AI | Claude Sonnet (conversation, drafting) + Haiku (classify, strength check) | unchanged |
| Images | fal.ai | **enhancement only — never generate** |
| Scheduler | APScheduler | unchanged |
| ~~Postmark inbound~~ | — | no longer the intake path |
| ~~Instagram, Stripe, Google Ads~~ | — | archived |

**Image policy:** real vendor photos, enhanced (crop, brighten, denoise). **No AI-generated imagery.** One fake bread photo destroys a local newsletter's credibility.

**Why APScheduler, not Temporal** *(ADR-002)*: in-process is sufficient at this scale. Revisit if Railway restarts cause missed sends.

---

## Directory Structure

```
backend/
├── main.py                       # app, routers, startup migrations
├── database/
│   ├── models.py                 # rewritten per DATA_MODEL.md
│   └── session.py
│
├── vendors/                      # ★ vendor-facing
│   ├── router.py                 # magic link auth, profile
│   ├── conversation.py           # chat endpoints
│   └── provisioning.py           # admin: create vendor, generate scan_code
│
├── editors/                      # ★ NEW
│   ├── router.py                 # login, review queue
│   └── review.py                 # approve / reject / set quality_score
│
├── subscribers/                  # ★ NEW
│   ├── router.py                 # scan landing, subscribe, unsubscribe
│   ├── identity.py               # cookie token issue + verify
│   └── interests.py              # scan_events → interest_vector + inferred_city
│
├── content/                      # ★ NEW — the supply pipeline
│   ├── agent.py                  # the interviewing agent
│   ├── questions.py              # question selection + rotation
│   ├── strength.py               # detail / person / change / why check
│   ├── drafter.py                # submission → draft block
│   ├── style_guard.py            # rejects marketing voice, invention, overlength
│   └── supply_monitor.py         # two-sided: approved vs pending
│
├── newsletter/                   # ★ NEW
│   ├── assembler.py              # issue skeleton + block pool
│   ├── personalizer.py           # score, select → issue_render
│   ├── renderer.py               # issue_render → HTML
│   └── dispatcher.py             # batch send via Resend
│
├── agent/
│   ├── vendor_memory.py          # ✅ reused (was user_memory.py)
│   ├── vendor_profiles.py        # ✅ reused
│   ├── content_safety.py         # ✅ reused
│   ├── brain.py                  # ✅ reused: Claude wrapper
│   ├── scheduler.py              # ✅ framework; jobs to be added
│   └── reply_handler.py          # ⚠️ salvage prompting patterns for agent.py
│
├── email_system/
│   ├── sender.py                 # ✅ reused
│   ├── templates.py              # ⚠️ rewritten: newsletter + reminders
│   └── inbound.py                # ⚠️ no longer intake; keep for bounces
│
├── integrations/
│   └── image_gen.py              # ⚠️ enhancement only
│
└── archive/                      # 🗄️ dead code, not imported

frontend/src/
├── vendor/                       # ★ chat, photo upload, history
├── editor/                       # ★ review queue, supply dashboard
└── reader/                       # ★ Scan.tsx, Subscribe.tsx, Unsubscribe.tsx
```

---

## Flow ① — Vendor Conversation

```
scheduler: vendor_reminder_cycle (hourly check)
      ↓
For each vendor due this cycle:
  content/questions.py picks the opening question
    ├── rotates question_type, never same kind twice running
    ├── reads vendor_memory for a specific hook
    └── scales down with silent_cycles:
          0-1 → open question
          2   → narrower, easier
          3+  → "just send a photo, we'll write around it"
      ↓
  Create conversation, store opening_question
      ↓
  Email reminder — QUESTION IN THE SUBJECT LINE
    "Cedar Bakery — is the sourdough back this week? Two minutes: [link]"
      ↓
  Link = single-use magic link → logs them straight in

VENDOR ARRIVES ON SITE
      ↓
  content/agent.py — Claude Sonnet, holds vendor_memory
      ↓
  Vendor answers, may attach photos (phone camera)
      ↓
  content/strength.py — Haiku, checks for
    detail / person / change / why
      ↓
  ≥2 signals → accept, create submission
      ↓
  <2 signals AND followups_used == 0
      → ONE specific follow-up, informed by vendor_memory
        NOT "tell me more"
        BUT "are these from the old orchard you mentioned?"
      ↓
  Still thin → accept as a short block, move on
     ⚠️ HARD CAP: one follow-up. Two makes the agent a chore.
      ↓
  Classify perishable vs evergreen → submission
      ↓
  Photos → fal.ai enhancement → store URLs
```

**Escalation to a human editor:**
`silent_cycles >= 2` · follow-up used and still thin · vendor followed by many readers · bank running low

---

## Flow ② — Drafting and Review

```
submission created
      ↓
content/drafter.py — Claude Sonnet
  ├── choose slot length (200 or 120 words)
  ├── headline ≤50 chars
  ├── body in the vendor's voice
  ├── pull one direct quote
  └── select image + caption
      ↓
content/style_guard.py — REJECTS ONLY, never writes
  ├── ❌ marketing voice ("don't miss," "limited time," "hurry")
  ├── ❌ any fact absent from submission.raw_text → reject
  ├── ❌ over the slot budget → compress
  └── ❌ contains "Marlo" → reject
      ↓
block created, status = pending_review
      ↓
EDITOR REVIEW QUEUE (web app)
  ├── approve → set quality_score (0-40) → status = approved
  └── reject  → reason recorded, back to drafter or discarded
      ↓
approved + not expired = IN THE BANK
```

**The bank is a query, not a table:** `status='approved' AND (expires_at IS NULL OR expires_at > now())`.

**Review happens as material arrives**, not in a rush before send. That's why editors gate blocks, not issues.

---

## Flow ③ — Assembly and Send

```
scheduler: send_issue (market local send_day + send_hour)
      ↓
newsletter/assembler.py
  Pull the bank, grouped by block_class
  Create issue record
      ↓
For each active subscriber:
      ↓
  newsletter/personalizer.py
    Score every story block (formula in DATA_MODEL.md)
      QUALITY + RELEVANCE + DISCOVERY + GEOGRAPHY − FATIGUE
      quality_score < 15 → never ships
      ↓
    Top 3 → slots 2, 3, 5
    Fewer than 3 eligible?
      → top up: interest match, then geography, then quality
      → NEVER ship short. Structure is fixed.
      ↓
    Fixed blocks: greeting (1), ad (4), events (6), ad (7),
                  referral (8), footer (9)
    Events filtered to the reader's follows
      ↓
  Create issue_render — block_ids in slot order
      ↓
  renderer.py → HTML  (4 font sizes, ≤1000 words)
      ↓
  dispatcher.py → Resend
```

**Structure check before send:** 9 slots filled, word count under 1000, at least one image. A render failing the check is logged and repaired, never sent malformed.

---

## Flow ④ — Scan to Subscribe

```
QR at the stall → /v/A7K2
      ↓
subscribers/identity.py checks sub_token cookie
      │
      ├── No cookie (new)
      │     → Landing: vendor name + photo + what Brown Bag is
      │     → One email field, one UNCHECKED consent box
      │     → create subscriber (consent_at, consent_source)
      │     → cookie (signed, 2 years)
      │     → vendor_follow + scan_event
      │     → welcome email
      │
      └── Cookie present (returning)
            → scan_event, scan_count += 1
            → "Added {Vendor}" + follow list
            → zero input, about one second
```

**New device:** no cookie but email exists → link to the existing account. **No password — the email is the identity.**

**Every scan updates `inferred_city`** — the most common city among followed vendors. Reader location is never asked for.

---

## Scheduler Jobs

| Job | Frequency | Purpose |
|---|---|---|
| `vendor_reminder_cycle` | hourly check | Pick question, send reminder to due vendors |
| `vendor_escalation` | daily | Flag silent vendors to the editor queue |
| `supply_monitor` | every 6h | Approved vs pending; alert the right party |
| `expire_blocks` | daily | Perishable blocks past `expires_at` |
| `send_issue` | hourly check | Assemble + send at market local time |
| `recompute_interests` | daily | Rebuild `interest_vector`, `inferred_city` |

**Job conventions** *(learned the hard way, keep them)*:
- Import models and services **inside** the job function, never at module top
- Open a fresh session: `async with AsyncSessionLocal() as db:` — never reuse one from elsewhere
- Wrap in try/except, route through `log_error()`
- `datetime.now(timezone.utc)`, never `utcnow()` *(ADR-005)*
- Railway DNS blips → WARNING (no Sentry); real bugs → ERROR *(ADR-013)*

---

## Design Patterns Carried From v1

**Vendor profiles as central config** *(ADR-012)*: type-specific behavior in one dict. Adding a type = one entry.

**Compact memory, not raw history** *(ADR-010)*: `vendor_memory` is ~200 tokens of summary, not a growing transcript. Updated asynchronously with Haiku. **Now doubles as the source of specific follow-up questions.**

**Background tasks get their own DB session**: never pass a request's session into `create_task()`.

---

## Public Endpoints

| Path | Purpose |
|---|---|
| `GET /v/{scan_code}` | Scan landing |
| `POST /subscribe` | Create subscriber |
| `GET /unsubscribe?token=` | One-click, immediate |
| `GET /vendor/auth?token=` | Magic link login |
| `POST /vendor/message` | Chat turn |
| `POST /vendor/upload` | Photo upload |
| `POST /editor/login` | Editor auth |
| `GET /editor/queue` | Pending review |
| `POST /editor/review/{block_id}` | Approve / reject + quality score |
| `GET /editor/supply` | Supply dashboard |

---

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://...
ANTHROPIC_API_KEY=sk-ant-...
FAL_API_KEY=...
RESEND_API_KEY=re_...
APP_BASE_URL=https://api.marlo021.ai
FRONTEND_URL=...                ★ Brown Bag domain — TBD
JWT_SECRET_KEY=...
SUBSCRIBER_TOKEN_SECRET=...     ★ signs subscriber cookies
VENDOR_TOKEN_SECRET=...         ★ signs vendor magic links
ENVIRONMENT=production

# Archived
# STRIPE_*  INSTAGRAM_*  META_*  GOOGLE_*  POSTMARK_*
```

---

## Open Questions

- **Brown Bag sending domain** — can't be marlo021.ai; readers shouldn't see Marlo
- One React app with role routing, or separate vendor / editor apps?
- Physical QR format