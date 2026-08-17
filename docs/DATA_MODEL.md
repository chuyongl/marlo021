# Brown Bag — Data Model

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\DATA_MODEL.md`*

> **Naming:** *Brown Bag* is the publication. *Marlo* is the backend. No user-visible string contains "Marlo."

---

## Core Shape

```
market
  ├── invitation_codes                   ★ the gate — we generate, we distribute
  ├── vendors (self-signup via code, live immediately)
  │     ├── conversations → messages     (interviewer agent)
  │     └── submissions                  (素材 — raw material)
  ├── editors
  ├── blocks                             ★ everything publishable
  │     └── block_corrections            (vendor-flagged fact fixes)
  ├── subscribers
  │     ├── scan_events
  │     ├── vendor_follows
  │     └── seen_blocks                  ★ permanent exclusion set
  └── issues
        └── issue_renders
```

**Four ideas carry the model:**

1. **The invitation code is the gate.** Control who signs up by controlling code distribution. No per-vendor editor work.
2. **Everything publishable is a block.** One table, one approval lifecycle.
3. **The bank is a query:** `status='approved' AND not expired AND no open corrections`.
4. **Seen is permanent.** A story shown to a reader is never eligible for that reader again — distinct from vendor fatigue, which is a temporary penalty.

---

## markets

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| name | string | e.g. "Seattle" |
| slug | string | |
| **publication_name** | string | **"Brown Bag"** — in DB so renaming is config, not code |
| from_email / from_name | string | Sender identity |
| timezone | string | IANA |
| send_day / send_hour | string / int | Local send window |
| **neighborhoods** | JSONB | Dropdown list + adjacency map |
| is_active | bool | |

**`neighborhoods` shape:**
```json
{
  "Ballard":  {"adjacent": ["Fremont","Magnolia","Greenwood"], "city": "Seattle"},
  "Fremont":  {"adjacent": ["Ballard","Wallingford","Queen Anne"], "city": "Seattle"},
  "Bellevue": {"adjacent": ["Kirkland","Redmond"], "city": "Bellevue"}
}
```

Powers the signup dropdown **and** proximity scoring. Hand-maintained — one afternoon for Seattle, and local knowledge beats any dataset.

---

## invitation_codes ★

**The gate.** We generate codes and hand them out; vendors self-serve from there.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | FK → markets |
| **code** | string | e.g. `BALLARD26` — human-readable, spoken aloud, printed |
| **neighborhood** | string | **Prefilled into signup. Codes carry location, not category.** |
| label | string | Internal note, e.g. "Ballard Farmers Market, spring 2026" |
| **max_uses** | int | NULL = unlimited |
| **use_count** | int | Incremented on each signup |
| expires_at | datetime | Optional |
| created_by | UUID | FK → editors |
| is_active | bool | Kill switch |
| created_at | datetime | |

**Two shapes in practice:**

| Type | Config | Use |
|---|---|---|
| **Bulk** | `max_uses = 100` | Hand to a market manager; their whole vendor list self-serves |
| **Single** | `max_uses = 1` | One specific vendor you're recruiting |

**Codes carry market + neighborhood only.** Category is the vendor's own choice from the list — a code covering a whole market can't presume what each stall sells.

---

## category_pairs ★

Makes `complementary_categories` automatic. **A property of the category, not the vendor.**

| Column | Type | Description |
|---|---|---|
| category | string | PK part, e.g. `bakery` |
| complements | array | e.g. `["cheese","jam","coffee","butter"]` |

Maintained once. Every vendor picking `bakery` inherits the pairings — **zero editor work per signup**, which is what makes the flow scalable.

---

## vendors

**Self-signup with a valid code. Live immediately.**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | From the code |
| **invitation_code_id** | UUID | FK → invitation_codes — attribution |
| name | string | |
| slug | string | |
| **email** | string | **Unique. Identity + magic links + reminders** |
| status | string | `active` / `paused` / `removed` |
| **scan_code** | string | **Generated at signup**, e.g. `A7K2` |
| **neighborhood** | string | **Prefilled from the code**, vendor can change |
| city | string | Derived from the neighborhood map |
| **categories** | array | **Fixed list, multi-select — never free text** |
| complementary_categories | array | **Derived from `category_pairs`** |
| vendor_type | string | Maps to `vendor_profiles.py` |
| description | string | Their own words |
| booth_location | string | |
| schedule_note | string | e.g. "Saturdays only" |
| photo_url | string | **Optional at signup** — the interviewer asks later |
| vendor_memory | JSONB | Voice, known facts, prior topics |
| reply_pattern | JSONB | Learned cadence |
| last_submitted_at | datetime | Drives reminders |
| silent_cycles | int | Consecutive cycles with nothing |
| created_at | datetime | |

**Categories must come from a fixed list.** Free text produces "baked goods," "bakery," "Baked Goods," and "bread + pastry" — four spellings of one category, and interest matching quietly breaks.

**Photo optional at signup.** Requiring one is where people abandon the form. Sending a photo mid-conversation is natural; uploading one to a signup form is a chore.

---

## vendor_sessions

Magic link once, then a long session. **One click on first visit, then the site just opens.**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| vendor_id | UUID | FK → vendors |
| **session_token** | string | Signed cookie, **90-day expiry** |
| magic_token | string | Single-use, 7-day expiry |
| magic_used_at | datetime | |
| last_seen_at | datetime | |
| created_at | datetime | |

---

## editors

**Hand-provisioned. Real login** — editors approve, so a password is warranted here.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| email | string | Unique |
| hashed_password | string | bcrypt |
| name | string | |
| market_ids | array | |
| is_active | bool | |

---

## conversations / messages

**No turn limit.** Conversations persist across sessions — vendors answer between customers.

**conversations**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| vendor_id | UUID | FK → vendors |
| cycle_start | date | |
| status | string | `open` / `submitted` / `abandoned` |
| opening_question | text | **Chosen before the reminder is sent** |
| question_type | string | `whats_new` / `story` / `behind_scenes` / `seasonal` |
| **gaps_remaining** | array | Still missing: `person` / `stake` / `scene` / `detail` |
| turns | int | Analytics only, **not capped** |
| stalled_turns | int | Exchanges adding nothing — 2 means stop |
| escalated_at | datetime | |
| escalation_reason | string | `silent` / `sensitive` / `thin` |

**messages**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| conversation_id | UUID | FK → conversations |
| role | string | `agent` / `vendor` |
| content | text | |
| image_urls | array | |
| created_at | datetime | |

---

## submissions

**素材 — raw material, not copy.** Never edited. The audit trail from published text back to what the vendor said.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| vendor_id / conversation_id | UUID | |
| **raw_text** | text | **Verbatim transcript, never modified** |
| image_urls | array | |
| perishable | bool | Time-sensitive vs evergreen |
| **material_notes** | JSONB | What the interviewer found: person, stake, scene, quotes |
| **sensitive** | bool | **Blocks auto-drafting — routes to a human** |
| status | string | `new` / `drafted` / `discarded` |
| created_at | datetime | |

---

## blocks ★

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | |
| **block_class** | string | `story` / `ad` / `greeting` / `events` / `static` |
| vendor_id | UUID | NULL for non-story |
| submission_id | UUID | Source 素材 |
| sponsor_id | UUID | Ads only |
| **status** | string | See lifecycle |
| headline | string | ≤50 chars |
| body | text | |
| quote | text | Vendor's exact words |
| image_urls / image_caption | | |
| word_count | int | |
| categories | array | |
| **quality_score** | int | **0–40, set by the editor** |
| perishable | bool | |
| expires_at | datetime | |
| **vendor_viewed_at** | datetime | When the vendor saw the draft |
| editor_id / reviewed_at | | |
| reject_reason | string | |
| times_used | int | |
| created_at | datetime | |

**Lifecycle:**

```
draft ──▶ vendor_preview ──▶ pending_review ──▶ approved ──▶ expired
              │                            └──▶ rejected
              └── vendor can flag corrections at any point, including post-approval
```

**Selection by class:**

| Class | How chosen |
|---|---|
| `story` | Scored per reader |
| `ad` | Fixed slot, same for all |
| `greeting` | Same for all (MVP) |
| `events` | Filtered to reader's follows |
| `static` | Always included |

---

## block_corrections

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| block_id / vendor_id | UUID | |
| **note** | text | e.g. "north field, not the old orchard" |
| status | string | `open` / `resolved` / `dismissed` |
| resolved_by / resolved_at | | FK → editors |
| created_at | datetime | |

**An open correction pulls an approved block from the bank** until resolved.

---

## sponsors

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | |
| name / contact_email / link_url | string | |
| active_from / active_until | date | |
| is_active | bool | |

---

## subscribers

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | |
| email | string | Unique within market |
| auth_token | string | Signed cookie |
| status | string | `active` / `unsubscribed` / `bounced` |
| **consent_at / consent_source** | | **Legally required** |
| first_vendor_id | UUID | Attribution |
| interest_vector | JSONB | From scans |
| **inferred_neighborhood** | string | **Most common among followed vendors — never asked** |
| inferred_city | string | |
| last_sent_at / last_opened_at | datetime | |
| created_at / unsubscribed_at | datetime | |

---

## seen_blocks ★

**Permanent exclusion.** A story shown once is never eligible for that reader again.

| Column | Type | Description |
|---|---|---|
| subscriber_id | UUID | PK part |
| block_id | UUID | PK part |
| seen_at | datetime | |

**Why a table and not a scan of `issue_renders`:** checked for every block against every subscriber on every send. Needs an indexed lookup, not an array scan.

| Rule | Scope | Effect |
|---|---|---|
| **Seen** | Story × reader | Hard exclusion, forever |
| **Fatigue** | Vendor × reader | Score penalty, decays |

---

## scan_events / vendor_follows

**scan_events**

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| subscriber_id | UUID | NULL on first-ever scan |
| vendor_id | UUID | |
| scanned_at | datetime | |
| is_signup | bool | |
| session_token | string | Pre-signup identifier |

**vendor_follows** — created automatically by scanning.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| subscriber_id / vendor_id | UUID | |
| scan_count | int | **Strength** |
| first_scanned_at / last_scanned_at | datetime | **Recency** |
| is_muted | bool | |

**Dedup:** same subscriber + vendor + day = one interest signal.

---

## issues / issue_renders

**issues** — a content pool, not an email.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_id | UUID | |
| issue_number | int | |
| send_date | date | |
| status | string | `assembling` / `sending` / `sent` |
| bank_size_at_assembly | int | |
| sent_count | int | |
| assembled_at / sent_at | datetime | |

**issue_renders** — what each reader actually got.

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| issue_id / subscriber_id | UUID | |
| **block_ids** | array | Blocks in slot order |
| block_scores | JSONB | Debugging |
| **followed_story_count** | int | How many from followed vendors |
| **eligible_pool_size** | int | **Unseen stories they had to choose from** |
| total_words | int | |
| sent_at / opened_at | datetime | |
| clicked_vendor_ids | array | |
| **unsubscribed_from_this** | bool | **Key negative signal** |

**`eligible_pool_size` is the early warning.** Dropping toward 3 for long-tenured readers means the bank is stagnating for the people you'd notice losing last.

---

## Story Scoring

```python
# ── HARD EXCLUSIONS (run first)
if block.id in seen_blocks[subscriber]:   EXCLUDE   # permanent
if block.quality_score < 15:              EXCLUDE
if block has open corrections:            EXCLUDE

score = 0
score += block.quality_score                        # QUALITY 0-40

# ── RELEVANCE (0-100)
if block.vendor_id in follows:
    score += 60
    score += min(follow.scan_count, 5) * 5          # to +25
    if follow.last_scanned_at within 30 days:
        score += 15
score += cosine(block.categories, interest_vector) * 40

# ── DISCOVERY (0-25)
if vendor.categories ∩ complementary_of(followed):  score += 25
elif vendor.categories ∩ categories_of(followed):   score += 10

# ── PROXIMITY (0-20)
if vendor.neighborhood == subscriber.inferred_neighborhood:      score += 20
elif vendor.neighborhood in adjacent_to(subscriber.inferred_n):  score += 12
elif vendor.city == subscriber.inferred_city:                    score += 6

# ── FATIGUE (vendor-level, temporary)
if vendor_id in reader's last render:        score -= 40
elif vendor_id in reader's last 3 renders:   score -= 15
```

**Selection:** top 3 → slots 2, 3, 5 (200 / 200 / 120 words).
**Fewer than 3 eligible:** top up by interest, proximity, quality. **Never ship short.**
**After send:** write `seen_blocks` rows for every story delivered.

---

## Key Queries

```sql
-- ★ VENDOR ROSTER — every vendor with their story history
SELECT v.name, v.neighborhood, v.categories,
       v.last_submitted_at, v.silent_cycles,
       COUNT(b.id) FILTER (WHERE b.status = 'approved')       AS approved,
       COUNT(b.id) FILTER (WHERE b.status = 'pending_review') AS awaiting_review,
       COUNT(b.id) FILTER (WHERE b.status = 'vendor_preview') AS awaiting_vendor,
       MAX(b.created_at)                                      AS last_story
FROM vendors v
LEFT JOIN blocks b ON b.vendor_id = v.id
WHERE v.market_id = :market AND v.status = 'active'
GROUP BY v.id, v.name, v.neighborhood, v.categories,
         v.last_submitted_at, v.silent_cycles
ORDER BY v.silent_cycles DESC, v.last_submitted_at ASC NULLS FIRST;

-- Invitation code usage
SELECT code, label, neighborhood, use_count, max_uses,
       (SELECT COUNT(*) FROM vendors WHERE invitation_code_id = ic.id) AS signups
FROM invitation_codes ic
WHERE market_id = :market AND is_active
ORDER BY created_at DESC;

-- Supply: approved vs pending by class
SELECT block_class, status, COUNT(*)
FROM blocks
WHERE market_id = :market
  AND status IN ('vendor_preview','pending_review','approved')
  AND (expires_at IS NULL OR expires_at > now())
GROUP BY block_class, status;

-- Readers running out of unseen stories (the loyalty warning)
SELECT s.email, s.created_at, r.eligible_pool_size
FROM issue_renders r JOIN subscribers s ON s.id = r.subscriber_id
WHERE r.issue_id = :latest AND r.eligible_pool_size < 6
ORDER BY r.eligible_pool_size ASC;

-- Open corrections blocking blocks
SELECT b.headline, v.name, c.note, c.created_at
FROM block_corrections c
JOIN blocks b ON b.id = c.block_id
JOIN vendors v ON v.id = c.vendor_id
WHERE c.status = 'open' ORDER BY c.created_at;

-- Unsubscribe rate per issue
SELECT i.issue_number, COUNT(*) AS sent,
       SUM(CASE WHEN r.unsubscribed_from_this THEN 1 ELSE 0 END) AS unsubs
FROM issue_renders r JOIN issues i ON i.id = r.issue_id
GROUP BY i.issue_number ORDER BY i.issue_number DESC;
```

---

## Deprecated From v1

`businesses`, `agent_actions`, `platform_integrations`, `content_feedback` — archived Instagram product. Leave in place, unused.

**Migration:** new tables via `create_all` on startup.

---

## Legal

- `consent_at` / `consent_source` required at signup
- One-click unsubscribe in every issue (CAN-SPAM), immediate
- Vendors never see subscriber emails — aggregate counts only
- ⚠️ Scan history must never drive health-adjacent inference (WA My Health My Data)