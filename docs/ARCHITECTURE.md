# Brown Bag — System Architecture

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\ARCHITECTURE.md`*

> **Naming:** *Brown Bag* is the publication. *Marlo* is the backend (repo, API, internal docs). **"Marlo" in any reader- or vendor-facing output is a bug.**

---

## Three Governing Constraints

**1. The reader never sees the machinery.**
**2. The issue ships every week** — thin material means get more material.
**3. Nothing ships without editor approval.**

---

## Three Surfaces

```
Vendors  → web app   chat, drafts, library    invitation code → magic link → 90-day session
Editors  → web app   queue, roster, editing   real login
Readers  → email     the newsletter           cookie from QR scan
```

Email is the reader delivery channel only. Postmark inbound is **no longer the intake path**.

---

## The Two-Agent Split ★

```
VENDOR ──▶ INTERVIEWER AGENT ──▶ 素材 ──▶ WRITER AGENT ──▶ DRAFT
                                                             │
                                                             ▼
                                                    VENDOR PREVIEW
                                                  (corrects facts)
                                                             │
                                                             ▼
                                                 EDITOR: edit + approve
                                                             │
                                                             ▼
                                                        THE BANK
```

**Vendors are not expected to write.** They supply raw material — what happened, why it mattered, photos. Most people can do that in conversation; almost nobody can do it in prose.

| Agent | Model | Job |
|---|---|---|
| **Interviewer** | Sonnet | Draw out material. Output is 素材, never copy. |
| **Writer** | Sonnet | Turn 素材 into a story that carries the quality bar. |

The writer has what the vendor lacks mid-conversation: time, context, and no social pressure.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), async |
| Frontend | React (TypeScript) — vendor + editor apps |
| Database | PostgreSQL (Railway) |
| Outbound email | Resend — newsletter + vendor reminders |
| AI | Claude Sonnet (interviewer, writer) + Haiku (classify, gap analysis) |
| Images | fal.ai — **enhancement only, never generate** |
| Scheduler | APScheduler |
| ~~Instagram, Stripe, Postmark inbound~~ | archived |

---

## Directory Structure

```
backend/
├── main.py
├── database/
│   ├── models.py                 # per DATA_MODEL.md
│   └── session.py
│
├── vendors/                      # ★ vendor-facing
│   ├── router.py                 # code validation, signup, magic link, session
│   ├── conversation.py           # chat endpoints
│   └── workspace.py              # my stories, library, corrections
│
├── editors/                      # ★ NEW
│   ├── router.py                 # login, queue, roster
│   ├── review.py                 # edit, approve, quality_score
│   ├── codes.py                  # generate + manage invitation codes
│   └── corrections.py            # resolve vendor-flagged facts
│
├── subscribers/                  # ★ NEW
│   ├── router.py                 # scan landing, subscribe, unsubscribe
│   ├── identity.py               # cookie tokens
│   └── interests.py              # scans → interest_vector + inferred_neighborhood
│
├── content/                      # ★ the supply pipeline
│   ├── interviewer.py            # ★ conversation agent — gathers 素材
│   ├── questions.py              # gap-driven question selection
│   ├── gaps.py                   # what's missing: person / stake / scene / detail
│   ├── sensitivity.py            # flags difficult material → human
│   ├── writer.py                 # ★ 素材 → story draft
│   ├── style_guard.py            # rejects marketing voice, invention, overlength
│   └── supply_monitor.py         # approved vs pending vs reader pool depth
│
├── newsletter/                   # ★ NEW
│   ├── assembler.py              # issue skeleton + block pool
│   ├── personalizer.py           # exclude seen → score → select
│   ├── renderer.py               # → HTML
│   └── dispatcher.py             # Resend + write seen_blocks
│
├── agent/
│   ├── vendor_memory.py          # ✅ reused
│   ├── vendor_profiles.py        # ✅ reused
│   ├── content_safety.py         # ✅ reused
│   ├── brain.py                  # ✅ Claude wrapper
│   └── scheduler.py              # ✅ framework; jobs to add
│
├── email_system/
│   ├── sender.py                 # ✅ reused
│   └── templates.py              # ⚠️ rewritten
│
└── archive/                      # 🗄️ dead code

frontend/src/
├── vendor/     # Signup, Chat, MyStories, Library
├── editor/     # Queue, Editor, Roster, Codes, Supply
└── reader/     # Scan, Subscribe, Unsubscribe
```

---

## Flow ① — Invitation Code Signup ★

**We control who joins by controlling code distribution. The vendor's signup is unattended.**

```
EDITOR generates a code
  ├── neighborhood (codes carry location, NOT category)
  ├── max_uses — 100 for a market, 1 for one vendor
  └── label, e.g. "Ballard Farmers Market, spring 2026"
      ↓
Code handed out — to a market manager, or direct to a vendor
      ↓
VENDOR visits /vendor/signup, enters the code
      ↓
Validate: active? not expired? use_count < max_uses?
      ↓
FORM — short by design
  ├── market + neighborhood  PREFILLED from the code
  ├── name, email
  ├── categories            FIXED LIST, multi-select, never free text
  ├── description, booth location, schedule
  └── photo                 OPTIONAL — the interviewer asks later
      ↓
On submit:
  ├── complementary_categories ← DERIVED from category_pairs
  ├── scan_code generated immediately
  ├── use_count += 1
  └── magic link emailed
      ↓
VENDOR IS LIVE. No editor step.
```

**Three choices that make this scalable:**

**Categories from a fixed list.** Free text produces "baked goods," "bakery," "Baked Goods," and "bread + pastry" — four spellings of one category, and interest matching quietly breaks.

**`complementary_categories` derived from `category_pairs`**, not set per vendor. Bread pairs with cheese because of what bread *is*. One maintained table, zero editor work per signup.

**Photo optional.** Requiring one at the form is where people abandon. Sending a photo mid-conversation is natural.

---

## Flow ② — The Conversation

```
scheduler: vendor_reminder_cycle (hourly check)
      ↓
content/questions.py picks the opening question
  ├── rotates question_type
  ├── reads vendor_memory for a specific hook
  └── scales down with silent_cycles:
        0-1 → open question
        2   → narrower
        3+  → "just send a photo, we'll write around it"
      ↓
Email — QUESTION IN THE SUBJECT LINE
  "Cedar Bakery — is the sourdough back this week? [link]"
      ↓
VENDOR ARRIVES (session valid, no login)
      ↓
content/interviewer.py — Sonnet + vendor_memory
      ↓
  LOOP, NO TURN LIMIT:
    ├── content/gaps.py: what's missing? person / stake / scene / detail
    ├── ask toward the gap — ALWAYS reference what they just said
    ├── never generic ("tell me more" is banned)
    ├── NEVER fish for pain — vendor volunteers or it doesn't exist
    ├── content/sensitivity.py flags difficult material
    └── stop when: enough material │ 2 stalled turns │ vendor says done
      ↓
  Conversation PERSISTS — vendor can leave and return
      ↓
Create submission (素材): raw_text verbatim · material_notes · perishable · sensitive
      ↓
Photos → fal.ai enhancement
```

**Escalation:** `silent_cycles >= 2` · `sensitive = true` · thin after a full conversation · vendor followed by many readers

**Sensitive material never auto-drafts.** A human sees it first.

---

## Flow ③ — Writing, Preview, Review

```
submission (素材)
      ↓
content/writer.py — Sonnet
  Bar: is there a person, and is something at stake?
  ├── headline ≤50 chars
  ├── body at slot length (200 or 120)
  ├── one direct quote
  ├── END ON THE CONCRETE THING — never explain the meaning
  └── select image + caption
      ↓
content/style_guard.py — REJECTS ONLY, never writes
  ├── ❌ marketing voice
  ├── ❌ any fact absent from raw_text
  ├── ❌ no person / nothing at stake
  ├── ❌ explains its own meaning
  ├── ❌ over budget
  └── ❌ contains "Marlo"
      ↓
status = vendor_preview
      ↓
VENDOR SEES THE DRAFT (before the editor)
  └── flags corrections → block_corrections
      ↓
status = pending_review
      ↓
EDITOR QUEUE — three lanes:
  ├── new drafts
  ├── vendor corrections
  └── escalations
      ↓
  edit → set quality_score (0-40) → approved
      ↓
approved + not expired + no open corrections = THE BANK
```

**Vendor preview comes first on purpose.** They're the only one who knows whether a fact is wrong, and catching it before the editor spends time is cheaper for everyone.

---

## Flow ④ — Assembly and Send

```
scheduler: send_issue (market local send window)
      ↓
newsletter/assembler.py — pull the bank by block_class
      ↓
For each active subscriber:
      ↓
  newsletter/personalizer.py
    HARD EXCLUDE:
      ├── block.id in seen_blocks[subscriber]   ← permanent
      ├── quality_score < 15
      └── open corrections
    THEN SCORE:
      QUALITY + RELEVANCE + DISCOVERY + PROXIMITY − FATIGUE
      ↓
    Top 3 → slots 2, 3, 5
    Fewer than 3? top up by interest, proximity, quality
    NEVER SHIP SHORT
      ↓
    Fixed: greeting(1) ad(4) events(6) ad(7) referral(8) footer(9)
      ↓
  issue_render — block_ids in order, eligible_pool_size recorded
      ↓
  renderer.py → HTML (4 font sizes, ≤1000 words)
      ↓
  dispatcher.py → Resend
      ↓
  ★ WRITE seen_blocks ROWS — permanent exclusion from here on
```

**Structure check before send:** 9 slots filled, under 1000 words, at least one image.

---

## Flow ⑤ — Scan to Subscribe

```
QR at the stall → /v/A7K2
      ↓
subscribers/identity.py checks sub_token cookie
      │
      ├── No cookie (new)
      │     → Landing: vendor name + photo + what Brown Bag is
      │     → One email field, one UNCHECKED consent box
      │     → create subscriber (consent_at, consent_source)
      │     → cookie (signed, 2 years) + vendor_follow + scan_event
      │     → welcome email
      │
      └── Cookie present (returning)
            → scan_event, scan_count += 1
            → "Added {Vendor}" + follow list
            → zero input, about one second
```

**New device:** no cookie but email exists → link to the existing account. **No password.**

**Every scan updates `inferred_neighborhood`.** Never asked.

---

## Flow ⑥ — Editor Roster

Editors get a vendor roster showing each vendor's story history — a single view that answers both *"who's here"* and *"who's gone quiet."*

Columns: name, neighborhood, categories, last submission, silent cycles, counts of approved / awaiting-review / awaiting-vendor blocks, last story date.

Sorted by silent cycles descending, so the vendors needing attention surface first. Query in `DATA_MODEL.md`.

---

## Scheduler Jobs

| Job | Frequency | Purpose |
|---|---|---|
| `vendor_reminder_cycle` | hourly check | Pick question, email due vendors |
| `vendor_escalation` | daily | Flag silent vendors to the editor queue |
| `supply_monitor` | every 6h | Approved vs pending vs reader pool depth |
| `expire_blocks` | daily | Perishable blocks past `expires_at` |
| `send_issue` | hourly check | Assemble + send at market local time |
| `recompute_interests` | daily | Rebuild `interest_vector`, `inferred_neighborhood` |

**Job conventions** *(learned the hard way)*:
- Import models and services **inside** the job function
- Fresh session: `async with AsyncSessionLocal() as db:` — never reuse
- try/except through `log_error()`
- `datetime.now(timezone.utc)`, never `utcnow()` *(ADR-005)*
- Railway DNS blips → WARNING; real bugs → ERROR *(ADR-013)*

---

## Design Patterns Carried From v1

**Vendor profiles as central config** *(ADR-012)*.

**Compact memory, not raw history** *(ADR-010)*: `vendor_memory` is ~200 tokens of summary. **Now the source of specific follow-up questions** — what makes the interviewer sound like it was listening.

**Background tasks get their own DB session.**

---

## Public Endpoints

| Path | Purpose |
|---|---|
| `GET /v/{scan_code}` | Scan landing |
| `POST /subscribe` | Create subscriber |
| `GET /unsubscribe?token=` | One-click, immediate |
| `POST /vendor/validate-code` | Check an invitation code |
| `POST /vendor/signup` | Signup with code |
| `GET /vendor/auth?token=` | Magic link → session |
| `POST /vendor/message` | Chat turn |
| `POST /vendor/upload` | Photo upload |
| `GET /vendor/stories` | Drafts + published |
| `POST /vendor/correction` | Flag a wrong fact |
| `GET /vendor/library` | Other vendors' published stories |
| `POST /editor/login` | |
| `GET /editor/queue` | Drafts, corrections, escalations |
| `GET /editor/roster` | Vendors + story history |
| `POST /editor/codes` | Generate invitation codes |
| `POST /editor/review/{block_id}` | Edit, approve, quality score |
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
SUBSCRIBER_TOKEN_SECRET=...     ★ subscriber cookies
VENDOR_TOKEN_SECRET=...         ★ vendor magic links + sessions
ENVIRONMENT=production

# Archived
# STRIPE_*  INSTAGRAM_*  META_*  GOOGLE_*  POSTMARK_*
```

---

## Open Questions

- **Brown Bag sending domain**
- One React app with role routing, or separate vendor / editor apps?
- Physical QR format