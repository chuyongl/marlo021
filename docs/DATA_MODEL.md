# Marlo — Data Model

*Last updated: August 4, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\DATA_MODEL.md`*

> ⚠️ **Fully rewritten August 4, 2026.** The old model was "post Instagram for merchants." The new one is "send a local newsletter to consumers." Most old tables are deprecated — see migration notes at the end.

---

## Core Shape

```
market (a farmers market or an area)
  ├── vendors (merchants, each a scan point)
  │     ├── content_items (raw material the vendor sent)
  │     └── content_blocks (edited, placeable modules)
  ├── subscribers (consumer readers)
  │     ├── scan_events (every QR scan)
  │     └── vendor_follows (relationship + strength)
  └── issues (one per week)
        └── issue_renders (the personalized version each person got)
```

**In one line: scanning creates following, and following decides what you see.**

---

## markets

One market or geographic area. One newsletter per market.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | string | e.g. "Bellevue Farmers Market" |
| slug | string | For URLs, e.g. `bellevue` |
| newsletter_name | string | **Public-facing brand** (not "Marlo") — TBD |
| from_email | string | Sender address |
| timezone | string | IANA timezone |
| send_day | string | e.g. "Thursday" |
| send_hour | int | Local hour, e.g. 17 |
| is_active | bool | |
| created_at | datetime | |

---

## vendors

Merchants. Replaces the old `businesses` table.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| market_id | UUID | FK → markets.id |
| name | string | Vendor name |
| slug | string | For URLs |
| **scan_code** | string | **Unique short code on the QR**, e.g. `A7K2` |
| owner_email | string | Where material comes from |
| owner_name | string | |
| categories | array | e.g. `["bakery","bread","pastry"]` — drives interest matching |
| vendor_type | string | Maps to `vendor_profiles.py` |
| description | string | A sentence or two, in the vendor's own words |
| booth_location | string | e.g. "Third row, east side" |
| schedule_note | string | e.g. "Saturdays only" |
| photo_url | string | Vendor header image |
| vendor_memory | JSONB | Voice, preferences, known facts (was `user_memory`) |
| is_active | bool | |
| joined_at | datetime | |

**`scan_code` must be short, unambiguous, and not enumerable.**
Recommended: 4–5 characters, excluding easily confused ones (0/O, 1/I/l), random rather than sequential.
URL form: `https://marlo021.ai/v/A7K2`

---

## subscribers

Consumer readers. **This concept does not exist in the current database.**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| market_id | UUID | FK → markets.id |
| email | string | Unique within a market |
| first_name | string | Optional, not required at signup |
| **auth_token** | string | Signed token stored in the long-lived cookie |
| status | string | `active` / `paused` / `unsubscribed` / `bounced` |
| consent_at | datetime | **Timestamp of explicit consent (legally required)** |
| consent_source | string | e.g. `qr_scan:A7K2` — where they consented |
| first_vendor_id | UUID | Who they scanned first — attribution |
| interest_vector | JSONB | Interest weights derived from scan behavior |
| send_frequency | string | `weekly` / `biweekly` / `monthly` |
| last_sent_at | datetime | |
| last_opened_at | datetime | |
| created_at | datetime | |
| unsubscribed_at | datetime | |

**`interest_vector` shape:**
```json
{
  "bakery": 0.9,
  "produce": 0.6,
  "flowers": 0.3,
  "updated_at": "2026-08-04"
}
```
Computed by aggregating the `categories` of scanned vendors. **The reader never fills in a form.**

---

## scan_events

Every QR scan. **This is the most important raw signal in the system.**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| subscriber_id | UUID | FK → subscribers.id; NULL on a first-ever scan |
| vendor_id | UUID | FK → vendors.id |
| scanned_at | datetime | |
| is_signup | bool | Did this scan produce the signup |
| user_agent | string | Rough device info |
| session_token | string | Temporary identifier before signup |

**Dedup rule:** same subscriber + same vendor + same day counts as one interest signal (all raw rows are still stored).

---

## vendor_follows

The following relationship. Created automatically by scanning — no user action required.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| subscriber_id | UUID | FK → subscribers.id |
| vendor_id | UUID | FK → vendors.id |
| source | string | `scan` / `manual` / `editorial` |
| scan_count | int | How many times scanned — **strength signal** |
| first_scanned_at | datetime | |
| last_scanned_at | datetime | |
| is_muted | bool | Reader can mute a vendor |

**Strength = scan count + recency.** A vendor scanned five times outranks one scanned once.

---

## content_items

**Raw material** from vendors. Unedited.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| vendor_id | UUID | FK → vendors.id |
| source | string | `email_reply` / `interview_answer` / `photo_upload` |
| raw_text | text | The vendor's exact words, **stored verbatim** |
| image_urls | array | Attached photos |
| prompt_id | UUID | If answering a question, points to it |
| received_at | datetime | |
| used_in_issue_id | UUID | Marked once used, prevents repeats |
| status | string | `new` / `used` / `skipped` / `expired` |

**Rule: `raw_text` is never modified.** Edited versions live in `content_blocks`. This means every published sentence can be traced back to what the vendor actually said.

---

## interview_prompts

Questions Marlo asks vendors.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| vendor_id | UUID | FK → vendors.id |
| question | text | e.g. "What do you have this week that you didn't last week?" |
| asked_at | datetime | |
| answered_at | datetime | |
| content_item_id | UUID | The answer it produced |
| question_type | string | `whats_new` / `story` / `behind_scenes` / `seasonal` |

**One question per week, maximum.** Ask more and vendors stop replying.

---

## content_blocks

Edited, placeable modules. **This is the unit that gets rearranged per reader.**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| issue_id | UUID | FK → issues.id |
| vendor_id | UUID | FK → vendors.id; NULL for editorial blocks |
| content_item_id | UUID | Source material |
| block_type | string | See type table below |
| headline | string | One line |
| body | text | Edited copy |
| quote | text | The vendor's own words, quoted directly |
| image_url | string | |
| image_caption | string | |
| categories | array | Inherited from vendor, used for matching |
| word_count | int | **Used to cap total issue length** |
| approved_by_vendor | bool | Vendor signed off on their own block |
| editorial_weight | int | Manual boost, default 0 |

**Block types:**

| Type | Purpose | Typical length |
|---|---|---|
| `whats_new` | What's new this week | 30–60 words |
| `vendor_story` | The person behind the stall | 80–150 words |
| `heads_up` | Running low / last week / hours changed | 20–40 words |
| `how_to` | How to use, cook, or store it | 60–120 words |
| `market_note` | Market-wide notice (weather, parking, events) | 30–60 words |
| `photo_feature` | Image-led, minimal text | 10–25 words |

---

## issues

One issue for one market. **An issue is a content pool, not the final email.**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| market_id | UUID | FK → markets.id |
| issue_number | int | Incrementing |
| period_start | date | Week covered |
| period_end | date | |
| status | string | `draft` / `assembled` / `sending` / `sent` / `skipped` |
| block_count | int | |
| assembled_at | datetime | |
| sent_at | datetime | |
| skip_reason | string | **If material was too thin, record why** |

**Key design point: an issue may hold 20 blocks, but each reader sees 5–7.**

---

## issue_renders

**The personalized version each subscriber received.**

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| issue_id | UUID | FK → issues.id |
| subscriber_id | UUID | FK → subscribers.id |
| block_ids | array | **Which blocks, in order** |
| block_scores | JSONB | Score per block, for debugging |
| total_words | int | |
| sent_at | datetime | |
| opened_at | datetime | |
| clicked_vendor_ids | array | Which vendors they clicked |
| unsubscribed_from_this | bool | **Unsubscribed from this issue — the key negative signal** |

**Why store this:** without it there's no way to answer "why did this person leave?" `block_ids` + `unsubscribed_from_this` is the only data that can diagnose content quality.

---

## email_logs

Kept from the old model, simplified.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| vendor_id | UUID | For vendor-directed email |
| subscriber_id | UUID | For reader-directed email |
| email_type | string | See below |
| sent_at | datetime | |
| reply_content | text | Vendor's reply body |
| metadata | JSON | |

**Email types:** `vendor_welcome`, `interview_prompt`, `interview_reminder`, `block_approval`, `subscriber_welcome`, `newsletter_issue`

---

## Personalization Scoring

Each block is scored against each subscriber; top N are selected.

```
score = 0

# Followed vendor — strongest signal
if block.vendor_id in subscriber's follows:
    score += 100
    score += min(follow.scan_count, 5) * 10       # more scans, higher weight
    if follow.last_scanned_at within 30 days:
        score += 20

# Interest match — not followed, but category fits
else:
    affinity = cosine(block.categories, subscriber.interest_vector)
    score += affinity * 50

# Diversity penalty — appeared in their last issue
if block.vendor_id appeared in this subscriber's previous render:
    score -= 40

# Market-wide notices go to everyone
if block.block_type == "market_note":
    score += 200

# Manual editorial boost
score += block.editorial_weight * 10

# Not approved by the vendor — excluded outright
if not block.approved_by_vendor and block.vendor_id is not None:
    score = -999
```

**Selection rules:**
- Take the top 5–7 by score
- **Force at least one non-followed vendor** — discovery; prevents the feed narrowing over time
- Total word count ≤ 400
- At least 2 images, at most 4
- `market_note` always goes first

---

## Key Queries

```sql
-- Unsubscribe rate per issue — the only honest quality signal
SELECT
  i.issue_number,
  COUNT(*) AS sent,
  SUM(CASE WHEN r.unsubscribed_from_this THEN 1 ELSE 0 END) AS unsubs,
  ROUND(100.0 * SUM(CASE WHEN r.unsubscribed_from_this THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS unsub_rate
FROM issue_renders r
JOIN issues i ON i.id = r.issue_id
GROUP BY i.issue_number
ORDER BY i.issue_number DESC;

-- Which blocks appear in issues people left from — find toxic content
SELECT b.id, b.headline, b.block_type, v.name,
       COUNT(*) AS appeared_in_unsub_issues
FROM issue_renders r
JOIN content_blocks b ON b.id = ANY(r.block_ids)
LEFT JOIN vendors v ON v.id = b.vendor_id
WHERE r.unsubscribed_from_this = true
GROUP BY b.id, b.headline, b.block_type, v.name
ORDER BY appeared_in_unsub_issues DESC;

-- Scan conversion — which vendor's QR brings the most signups
SELECT v.name, v.scan_code,
       COUNT(*) FILTER (WHERE s.is_signup) AS signups,
       COUNT(*) AS total_scans
FROM scan_events s
JOIN vendors v ON v.id = s.vendor_id
GROUP BY v.name, v.scan_code
ORDER BY signups DESC;
```

---

## Migration From the Old Model

| Old table | Disposition |
|---|---|
| `businesses` | → becomes `vendors`. Drop `subscription_id`, `posting_schedule`, `posts_per_week`, `briefing_time`, `onboarding_step`. `user_memory` → `vendor_memory` |
| `users` | Keep, for vendor login if needed |
| `agent_actions` | **Deprecated.** No "pending Instagram post" concept anymore |
| `platform_integrations` | **Deprecated.** No OAuth |
| `content_feedback` | **Deprecated.** Feedback now comes from `issue_renders` |
| `email_logs` | Keep; add `subscriber_id` |

**Migration method:** same as before — auto-create tables on startup in `main.py`. Create all new tables; leave old tables in place but unused (deprecate, don't drop).

---

## Legal Requirements (mandatory, not optional)

- `consent_at` and `consent_source` are **required** and recorded at signup
- Every newsletter needs a one-click unsubscribe link (CAN-SPAM)
- Unsubscribes take effect immediately
- Vendors must never see subscriber email addresses — **aggregate counts only**
- ⚠️ Washington My Health My Data Act: inferring health status from food purchases is regulated data. **Scan history must not be used for any health-related inference** — be careful with categories like gluten-free and baby food