# Brown Bag — Data Model

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\DATA_MODEL.md`*

> **Naming:** *Brown Bag* is the publication. *Marlo* is the backend system. No table, column, or user-visible string should contain "Marlo."

---

## Core Shape

```
market
  ├── vendors (hand-provisioned, each a scan point, each has a city)
  │     ├── conversations → messages   (chat with the AI agent)
  │     └── submissions               (raw material from those chats)
  ├── editors                          (hand-provisioned, real login)
  ├── blocks                           ★ everything publishable is a block
  ├── subscribers                      (readers)
  │     ├── scan_events
  │     └── vendor_follows
  └── issues
        └── issue_renders              (what each reader actually got)
```

**Two ideas carry the whole model:**

1. **Everything publishable is a block.** Stories, ads, greeting, events, referral, footer — one table, one approval lifecycle. They differ in how they're *selected*, not how they're *approved*.
2. **The bank is "blocks with status = approved."** Not a separate table. Assembly reads from it; nothing enters without an editor.

---

## markets

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| name | string | e.g. "Seattle" |
| slug | string | URL segment |
| **publication_name** | string | **"Brown Bag"** — provisional, keep in config not code |
| from_email | string | Sender address |
| from_name | string | Display name on the email |
| timezone | string | IANA |
| send_day | string | e.g. "Thursday" |
| send_hour | int | Local hour, e.g. 17 |
| is_active | bool | |

**`publication_name` lives in the database on purpose.** The name is provisional; changing it should be a config edit, not a code change.

---

## vendors

**Hand-provisioned.** No self-serve signup.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | FK → markets |
| name | string | |
| slug | string | |
| **scan_code** | string | Short code on the QR, e.g. `A7K2` |
| **city** | string | e.g. "Bellevue" — **drives reader location inference** |
| neighborhood | string | Optional, finer grain |
| categories | array | e.g. `["bakery","bread"]` — interest matching |
| **complementary_categories** | array | e.g. `["cheese","jam","coffee"]` — discovery scoring |
| vendor_type | string | Maps to `vendor_profiles.py` |
| contact_email | string | Magic link + reminders |
| description | string | Their own words |
| booth_location | string | |
| schedule_note | string | e.g. "Saturdays only" |
| photo_url | string | |
| vendor_memory | JSONB | Voice, known facts, prior topics — **fuels the agent's follow-up questions** |
| **reply_pattern** | JSONB | Learned cadence: typical response day and lag |
| **last_submitted_at** | datetime | Drives reminders and escalation |
| **silent_cycles** | int | Consecutive cycles with no submission |
| is_active | bool | |
| created_at | datetime | |

**`scan_code`:** 4–5 chars, excluding confusable characters (0/O, 1/I/l), random not sequential.
URL: `https://{brownbag_domain}/v/A7K2`

**`complementary_categories` is filled by hand at provisioning.** A human knows bread pairs with cheese. Cheap to type; expensive to infer.

---

## vendor_magic_links

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| vendor_id | UUID | FK → vendors |
| token | string | Signed, single-use |
| expires_at | datetime | 7 days typical |
| used_at | datetime | NULL until clicked |
| purpose | string | `reminder` / `manual_invite` |

---

## editors

**Hand-provisioned. Real login** — editors can approve, so this is the one place a password is warranted.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| email | string | Unique |
| hashed_password | string | bcrypt |
| name | string | |
| market_ids | array | Which markets they can review |
| is_active | bool | |

---

## conversations / messages

**conversations**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| vendor_id | UUID | FK → vendors |
| cycle_start | date | Which week this belongs to |
| status | string | `open` / `submitted` / `abandoned` |
| opening_question | text | **Chosen before the reminder is sent** |
| question_type | string | `whats_new` / `story` / `behind_scenes` / `seasonal` |
| followups_used | int | **Hard cap: 1** |
| escalated_at | datetime | When a human was flagged in |

**messages**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| conversation_id | UUID | FK → conversations |
| role | string | `agent` / `vendor` |
| content | text | |
| image_urls | array | Photos from phone camera |
| created_at | datetime | |

---

## submissions

Raw material out of a conversation. **Never edited** — the audit trail from published copy back to what the vendor actually said.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| vendor_id | UUID | FK → vendors |
| conversation_id | UUID | FK → conversations |
| raw_text | text | **Verbatim, never modified** |
| image_urls | array | |
| **perishable** | bool | True = time-sensitive; False = evergreen, bank it |
| **strength_signals** | array | Which of `detail` / `person` / `change` / `why` are present |
| status | string | `new` / `drafted` / `discarded` |
| created_at | datetime | |

**`perishable` decides shelf life.** "Peaches this week" expires in days. "Why I left nursing to make cheese" is good for a year.

**`strength_signals`** is the agent's read on whether a story clears the bar. Two or more = strong enough. Drives whether the agent spends its one follow-up.

---

## blocks ★

**Everything publishable.** One table, one lifecycle, five selection behaviors.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | FK → markets |
| **block_class** | string | `story` / `ad` / `greeting` / `events` / `static` |
| vendor_id | UUID | FK → vendors; NULL for non-story blocks |
| submission_id | UUID | Source material; NULL for ads and editorial |
| sponsor_id | UUID | FK → sponsors; ads only |
| **status** | string | See lifecycle below |
| headline | string | ≤50 chars |
| body | text | |
| quote | text | Vendor's exact words, quoted |
| image_urls | array | |
| image_caption | string | |
| word_count | int | Enforced against the slot budget |
| categories | array | Inherited from vendor |
| **quality_score** | int | **0–40, set by the editor at approval** |
| **perishable** | bool | Inherited from submission |
| **expires_at** | datetime | Perishable blocks only |
| editor_id | UUID | Who approved or rejected |
| reviewed_at | datetime | |
| reject_reason | string | |
| times_used | int | Across all readers, for reporting |
| created_at | datetime | |

**Lifecycle:**

```
draft ──▶ pending_review ──▶ approved ──▶ (in the bank) ──▶ expired
                        └──▶ rejected
```

**"The bank" = `status = 'approved'` AND (`expires_at` IS NULL OR `expires_at` > now).** Not a separate table.

**Selection by class:**

| Class | How it's chosen |
|---|---|
| `story` | Scored per reader |
| `ad` | Fixed slot, same for everyone |
| `greeting` | Same for everyone (MVP). Location-matched later. |
| `events` | Filtered to the reader's follows |
| `static` | Always included — referral, social, footer |

---

## sponsors

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | FK → markets |
| name | string | |
| contact_email | string | |
| link_url | string | Click destination |
| active_from | date | |
| active_until | date | |
| is_active | bool | |

---

## subscribers

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | FK → markets |
| email | string | Unique within market |
| auth_token | string | Signed, stored in cookie |
| status | string | `active` / `unsubscribed` / `bounced` |
| **consent_at** | datetime | **Legally required** |
| **consent_source** | string | e.g. `qr_scan:A7K2` |
| first_vendor_id | UUID | Attribution |
| interest_vector | JSONB | Derived from scans |
| **inferred_city** | string | **Computed from followed vendors — never asked** |
| last_sent_at | datetime | |
| last_opened_at | datetime | |
| created_at | datetime | |
| unsubscribed_at | datetime | |

**No `send_frequency`** — everyone is weekly for MVP.

**`interest_vector`:**
```json
{ "bakery": 0.9, "produce": 0.6, "flowers": 0.3, "updated_at": "2026-08-12" }
```

**`inferred_city`:** most common `city` among followed vendors. No form field; sharpens with every scan.

---

## scan_events

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| subscriber_id | UUID | NULL on a first-ever scan |
| vendor_id | UUID | FK → vendors |
| scanned_at | datetime | |
| is_signup | bool | |
| session_token | string | Pre-signup identifier |

**Dedup:** same subscriber + vendor + day counts once as an interest signal. All raw rows retained.

---

## vendor_follows

Created automatically by scanning. No user action.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| subscriber_id | UUID | FK → subscribers |
| vendor_id | UUID | FK → vendors |
| scan_count | int | **Strength signal** |
| first_scanned_at | datetime | |
| last_scanned_at | datetime | **Recency signal** |
| is_muted | bool | |

---

## issues

**A content pool, not an email.**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | FK → markets |
| issue_number | int | |
| send_date | date | |
| status | string | `assembling` / `sending` / `sent` |
| bank_size_at_assembly | int | Diagnostics |
| sent_count | int | |
| assembled_at | datetime | |
| sent_at | datetime | |

---

## issue_renders

**What each subscriber actually received.**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| issue_id | UUID | FK → issues |
| subscriber_id | UUID | FK → subscribers |
| **block_ids** | array | Which blocks, in slot order |
| block_scores | JSONB | Per-block score, for debugging |
| **followed_story_count** | int | How many came from followed vendors |
| total_words | int | |
| sent_at | datetime | |
| opened_at | datetime | |
| clicked_vendor_ids | array | |
| **unsubscribed_from_this** | bool | **The key negative signal** |

**Why persist this:** without it there's no answering "why did this person leave?" `block_ids` + `unsubscribed_from_this` is the only data that can diagnose content quality.

**`followed_story_count`** measures whether personalization is working. If most readers sit at 0, the follow model isn't earning its complexity.

---

## Story Scoring

Applied to `block_class = 'story'` only.

```python
score = 0

# ── QUALITY (0-40) — reader-independent, set by editor
score += block.quality_score

# ── RELEVANCE (0-100)
if block.vendor_id in reader_follows:
    score += 60
    score += min(follow.scan_count, 5) * 5          # up to +25
    if follow.last_scanned_at within 30 days:
        score += 15
score += cosine(block.categories, interest_vector) * 40

# ── DISCOVERY (0-25)
if block.vendor.categories ∩ complementary_of(followed):
    score += 25
elif block.vendor.categories ∩ categories_of(followed):
    score += 10

# ── GEOGRAPHY (top-up only)
if block.vendor.city == subscriber.inferred_city:
    score += 20

# ── FATIGUE
if block.vendor_id in reader's last render:
    score -= 40
elif block.vendor_id in reader's last 3 renders:
    score -= 15

# ── HARD FLOOR
if block.quality_score < 15:
    score = -999                                    # never ships
```

**Selection:** top 3 by score → slots 2, 3, 5 (200 / 200 / 120 words).

**Complementary outranks same-category deliberately.** A baker's follower would rather hear about cheese than a rival bakery.

**If the bank yields fewer than 3 eligible stories**, top up with unfollowed stories ranked by interest, geography, and quality. **Never ship short** — the structure is fixed.

---

## Supply Monitoring

```sql
-- Approved vs pending, by class
SELECT block_class, status, COUNT(*)
FROM blocks
WHERE market_id = :market
  AND status IN ('pending_review','approved')
  AND (expires_at IS NULL OR expires_at > now())
GROUP BY block_class, status;

-- Vendors in rotation (fatigue needs 12+)
SELECT COUNT(DISTINCT vendor_id)
FROM blocks
WHERE status = 'approved' AND block_class = 'story'
  AND (expires_at IS NULL OR expires_at > now());

-- Vendors falling silent
SELECT name, last_submitted_at, silent_cycles
FROM vendors
WHERE is_active AND silent_cycles >= 2
ORDER BY silent_cycles DESC;
```

| Approved | Pending | Meaning |
|---|---|---|
| Low | High | **Editors** are the bottleneck |
| Low | Low | **Vendors** are the bottleneck |
| Healthy | — | Quiet |

---

## Key Queries

```sql
-- Unsubscribe rate per issue — the only honest quality signal
SELECT i.issue_number, COUNT(*) AS sent,
       SUM(CASE WHEN r.unsubscribed_from_this THEN 1 ELSE 0 END) AS unsubs
FROM issue_renders r
JOIN issues i ON i.id = r.issue_id
GROUP BY i.issue_number ORDER BY i.issue_number DESC;

-- Which blocks appear in issues people left from
SELECT b.id, b.headline, v.name, COUNT(*) AS in_unsub_issues
FROM issue_renders r
JOIN blocks b ON b.id = ANY(r.block_ids)
LEFT JOIN vendors v ON v.id = b.vendor_id
WHERE r.unsubscribed_from_this
GROUP BY b.id, b.headline, v.name
ORDER BY in_unsub_issues DESC;

-- Is personalization working?
SELECT followed_story_count, COUNT(*)
FROM issue_renders
GROUP BY followed_story_count ORDER BY followed_story_count;

-- Scan conversion by vendor
SELECT v.name, v.scan_code,
       COUNT(*) FILTER (WHERE s.is_signup) AS signups,
       COUNT(*) AS total_scans
FROM scan_events s JOIN vendors v ON v.id = s.vendor_id
GROUP BY v.name, v.scan_code ORDER BY signups DESC;
```

---

## Deprecated From v1

`businesses`, `agent_actions`, `platform_integrations`, `content_feedback` — all belong to the archived Instagram product. Leave in place, unused.

`users` → keep only if editor auth reuses it; otherwise superseded by `editors`.

**Migration:** new tables via `create_all` on startup.

---

## Legal

- `consent_at` and `consent_source` required at signup
- One-click unsubscribe in every issue (CAN-SPAM), immediate effect
- Vendors never see subscriber emails — aggregate counts only
- ⚠️ Scan history must never drive health-adjacent inference (WA My Health My Data)