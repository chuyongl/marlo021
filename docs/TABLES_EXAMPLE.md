# Brown Bag — Tables With Real Data

*A companion to `DATA_MODEL.md`. Same 19 tables, filled in with one coherent example so the structure is easier to hold in your head.*

**The scenario:** Cedar Bakery and Hollow Ridge Farm sign up in Ballard. A reader named Sam scans Cedar's QR at the market. One issue goes out.

---

# 1. CONFIGURATION

## `markets` — the publication itself

| id | name | slug | publication_name | from_email | send_day | send_hour | timezone |
|---|---|---|---|---|---|---|---|
| `m-001` | Seattle | seattle | **Brown Bag** | hello@brownbag.co | Thursday | 17 | America/Los_Angeles |

**`neighborhoods`** (JSONB in the same row):
```json
{
  "Ballard":   {"adjacent": ["Fremont","Magnolia","Greenwood"], "city": "Seattle"},
  "Fremont":   {"adjacent": ["Ballard","Wallingford"],          "city": "Seattle"},
  "Greenwood": {"adjacent": ["Ballard","Phinney Ridge"],        "city": "Seattle"}
}
```

One row. This whole table will likely have one row for a year.

---

## `invitation_codes` — who's allowed to sign up

| id | code | neighborhood | label | max_uses | use_count | is_active |
|---|---|---|---|---|---|---|
| `ic-001` | `CEDAR-4K2M` | Ballard | Cedar Bakery recruit | 1 | **1** | true |
| `ic-002` | `HOLLOW-9XR3` | Ballard | Hollow Ridge recruit | 1 | **1** | true |
| `ic-003` | `PIKE-7T4W` | Ballard | Pike Fish — not signed up yet | 1 | **0** | true |

`ic-003` has `use_count = 0` — sent out, nobody has used it. Once used it becomes unusable, since `use_count >= max_uses`.

---

## `category_pairs` — what goes with what

| category | complements | display_name |
|---|---|---|
| `bakery` | `["cheese","jam","coffee","butter"]` | Bakery & Bread |
| `produce` | `["cheese","bakery","flowers"]` | Fruit & Vegetables |
| `cheese` | `["bakery","jam","wine"]` | Cheese & Dairy |
| `flowers` | `["produce","candles","honey"]` | Flowers & Plants |

**Why this exists:** when Cedar signs up and picks `bakery`, the system copies `["cheese","jam","coffee","butter"]` into their `complementary_categories`. No editor involved. That's what makes discovery scoring work without per-vendor setup.

---

# 2. ACCOUNTS

## `vendors`

| id | name | email | scan_code | neighborhood | city | categories | complementary_categories | silent_cycles | last_submitted_at |
|---|---|---|---|---|---|---|---|---|---|
| `v-001` | Cedar Bakery | mei@cedar.com | **`A7K2`** | Ballard | Seattle | `["bakery"]` | `["cheese","jam","coffee","butter"]` | 0 | 2026-08-10 |
| `v-002` | Hollow Ridge Farm | dan@hollow.com | **`B3M9`** | Ballard | Seattle | `["produce"]` | `["cheese","bakery","flowers"]` | 0 | 2026-08-11 |
| `v-003` | Pike Fish Co | joe@pike.com | **`C8P1`** | Ballard | Seattle | `["seafood"]` | `["produce","bakery"]` | **3** | 2026-07-15 |

`v-003` hasn't submitted in a month — `silent_cycles = 3`. Next reminder gets the easy ask: *"just send a photo, we'll write around it."*

**`vendor_memory`** on Cedar (JSONB):
```json
{
  "voice": "plain, self-deprecating, short sentences",
  "known_facts": ["daughter is 12", "makes chili oil", "sells out early"],
  "recent_topics": ["TikTok video, 90k views", "sourdough on pause"],
  "updated_at": "2026-08-10"
}
```

This is what lets the interviewer ask *"is the sourdough back?"* instead of *"anything new?"*

---

## `vendor_sessions`

| id | vendor_id | session_token | magic_token | magic_used_at | expires_at |
|---|---|---|---|---|---|
| `vs-001` | `v-001` | `sess_8f2a…` | `mg_x9k2…` | 2026-08-08 09:14 | 2026-11-06 |
| `vs-002` | `v-002` | `sess_2b7c…` | `mg_p4m1…` | 2026-08-09 16:32 | 2026-11-07 |

Mei clicked her magic link on Aug 8. The session runs to Nov 6 — **90 days of the site just opening.**

---

## `editors`

| id | email | name | market_ids | is_active |
|---|---|---|---|---|
| `e-001` | anna@brownbag.co | Anna | `["m-001"]` | true |

The only role with a password.

---

# 3. CONTENT INTAKE — 素材

## `conversations`

| id | vendor_id | cycle_start | status | opening_question | gaps_remaining | turns | stalled_turns |
|---|---|---|---|---|---|---|---|
| `c-001` | `v-001` | 2026-08-10 | **submitted** | "Is the sourdough back this week?" | `[]` | 7 | 0 |
| `c-002` | `v-002` | 2026-08-10 | **submitted** | "How did the rain treat you?" | `["quote"]` | 4 | 0 |
| `c-003` | `v-003` | 2026-08-10 | **abandoned** | "Anything new at the stall?" | `["person","stake","scene"]` | 2 | **2** |

**`c-003` is the important row.** Two exchanges, nothing landed, `stalled_turns = 2` → stop. Status `abandoned`, **no submission created.**

That's a correct outcome, not a bug. A vendor with nothing to say is normal; the bank carries the gap. If the system treated this as failure it would manufacture filler.

---

## `messages` — for conversation `c-001`

| id | conversation_id | role | content | image_urls |
|---|---|---|---|---|
| `msg-01` | `c-001` | agent | "Is the sourdough back this week, or still on pause?" | `[]` |
| `msg-02` | `c-001` | vendor | "Not yet. But we sold out of chili oil by 11, that never happens" | `[]` |
| `msg-03` | `c-001` | agent | "Sold out by 11 — how many jars did you bring?" | `[]` |
| `msg-04` | `c-001` | vendor | "40. Last month I made 60 and had 20 left so I thought 40 was safe. Wrong." | `[]` |
| `msg-05` | `c-001` | agent | "Any idea what changed?" | `[]` |
| `msg-06` | `c-001` | vendor | "Someone posted a video of me at the July demo. 90,000 views. I don't have TikTok" | `["fal.ai/img_a1.jpg"]` |
| `msg-07` | `c-001` | vendor | "My daughter made me watch it four times. She's twelve." | `[]` |

Seven rows, one conversation. `msg-07` is the line the story turns on — and it arrived because `msg-05` was specific.

---

## `submissions` — 素材, never edited

| id | vendor_id | conversation_id | perishable | sensitive | status |
|---|---|---|---|---|---|
| `sub-001` | `v-001` | `c-001` | **true** | false | drafted |
| `sub-002` | `v-002` | `c-002` | **false** | false | drafted |

**`sub-001.raw_text`** — the transcript, verbatim:
```
Not yet. But we sold out of chili oil by 11, that never happens.
40. Last month I made 60 and had 20 left so I thought 40 was safe. Wrong.
Someone posted a video of me at the July demo. 90,000 views. I don't have TikTok.
My daughter made me watch it four times. She's twelve.
```

**`sub-001.material_notes`** (JSONB):
```json
{
  "person": "Mei, and her 12-year-old daughter",
  "stake": "sold out early, unexpectedly",
  "scene": "queue before setup finished",
  "quotes": ["I don't have TikTok", "She's twelve"]
}
```

**`perishable = true`** — sold out *this week*. Short shelf life.
**`sub-002.perishable = false`** — the farmer's tomato sauce story keeps for months.

**This table is the audit trail.** Every published sentence must trace back to `raw_text`. That's how "never invent a fact" becomes checkable rather than aspirational.

---

# 4. PUBLISHABLE CONTENT

## `sponsors`

| id | name | link_url | active_from | active_until | is_active |
|---|---|---|---|---|---|
| `sp-001` | Ballard Hardware | ballardhardware.com | 2026-08-01 | 2026-09-30 | true |

---

## `blocks` — the heart of it

| id | class | vendor_id | status | headline | quality_score | perishable | expires_at |
|---|---|---|---|---|---|---|---|
| `b-001` | **story** | `v-001` | **approved** | She's not famous. She's out of chili oil. | **34** | true | 2026-08-18 |
| `b-002` | **story** | `v-002` | **approved** | A third of the tomatoes split. Now there's sauce. | **26** | false | NULL |
| `b-003` | **story** | `v-002` | **approved** | Eleven years of the same Saturday | **31** | false | NULL |
| `b-004` | **story** | `v-001` | pending_review | The peppercorns kept the neighbors up | 0 | true | 2026-08-18 |
| `b-005` | **story** | `v-003` | **rejected** | — | 0 | true | NULL |
| `b-010` | **ad** | NULL | **approved** | Ballard Hardware | 0 | false | 2026-09-30 |
| `b-011` | **greeting** | NULL | **approved** | Week of August 12 | 0 | true | 2026-08-18 |
| `b-012` | **static** | NULL | **approved** | Know someone who'd like this? | 0 | false | NULL |
| `b-013` | **events** | NULL | **approved** | This week at the market | 0 | true | 2026-08-18 |

**Read this table carefully — it's where the design lives:**

**Rows `b-001` through `b-013` are all the same kind of thing.** A story, an ad, the greeting, the referral footer. Same table, same status column, same approval gate.

**`quality_score` only matters for stories.** An ad doesn't compete for a slot, so its score is 0 and irrelevant.

**`b-005` was rejected** — that's the "everything's fresh, we'd love to see everyone" submission. Style guard caught it: no person, nothing at stake, marketing voice.

**`b-004` is written but unapproved.** It exists, it's fine, but it's **not in the bank** because no editor has looked at it yet.

**`expires_at`:** `b-001` dies Aug 18 (sold out *this week*). `b-002` has NULL — the sauce story is good indefinitely.

**`b-001.body`** — the finished story:
```
Mei sold out by 11 on Saturday. She usually goes till two.

She'd made forty jars. Last month she made sixty and carried twenty home,
so forty seemed like the sensible number. There was a line before she
finished setting up.

A woman in the queue held up her phone to show her why: a video of Mei at
the July demo, toasting peppercorns, filmed by someone she never noticed.
Ninety thousand views. She doesn't have TikTok.
```
**`b-001.quote`:** `"She said mom you're famous, and I said I'm not famous, I'm out of chili oil."`

---

## `block_corrections`

| id | block_id | vendor_id | note | status | resolved_at |
|---|---|---|---|---|---|
| `bc-001` | `b-003` | `v-002` | "It's twelve years, not eleven" | **open** | NULL |

**One open correction, and `b-003` is out of the bank** until Anna fixes it — even though its status is still `approved`.

This is the one case that overrides *"the issue ships every week."* Shipping a known-wrong fact about someone's own business is worse than a thin issue.

---

## ★ What "the bank" actually is

No table. Just this question:

```sql
SELECT * FROM blocks
WHERE status = 'approved'
  AND (expires_at IS NULL OR expires_at > now())
  AND id NOT IN (SELECT block_id FROM block_corrections WHERE status = 'open')
```

Run against the rows above, on Aug 12:

| Block | In the bank? | Why |
|---|---|---|
| `b-001` | ✅ | approved, expires Aug 18 |
| `b-002` | ✅ | approved, never expires |
| `b-003` | ❌ | **open correction** |
| `b-004` | ❌ | not approved yet |
| `b-005` | ❌ | rejected |
| `b-010` | ✅ | approved ad |
| `b-011` `b-012` `b-013` | ✅ | approved |

**Nothing had to move.** `b-003` left the bank the moment the correction was filed, and returns the moment it's resolved. No cleanup job, no copying rows.

---

# 5. READERS

## `subscribers`

| id | email | status | consent_source | inferred_neighborhood | inferred_city | created_at |
|---|---|---|---|---|---|---|
| `s-001` | sam@gmail.com | active | **`qr_scan:A7K2`** | **Ballard** | Seattle | 2026-07-20 |
| `s-002` | jo@gmail.com | active | `qr_scan:B3M9` | Ballard | Seattle | 2026-08-01 |
| `s-003` | rae@gmail.com | unsubscribed | `qr_scan:A7K2` | Ballard | Seattle | 2026-06-15 |

**`s-001.interest_vector`:**
```json
{"bakery": 0.75, "produce": 0.25, "updated_at": "2026-08-11"}
```

Sam never filled in a form. That vector comes entirely from which stalls he scanned. `inferred_neighborhood = Ballard` for the same reason.

---

## `scan_events` — the raw signal

| id | subscriber_id | vendor_id | scanned_at | is_signup |
|---|---|---|---|---|
| `se-001` | `s-001` | `v-001` | 2026-07-20 10:12 | **true** |
| `se-002` | `s-001` | `v-001` | 2026-07-27 09:48 | false |
| `se-003` | `s-001` | `v-002` | 2026-08-03 11:05 | false |
| `se-004` | `s-001` | `v-001` | 2026-08-10 10:30 | false |

Sam scanned Cedar three times and Hollow Ridge once. The first scan created his account; the rest took one second each — recognized, vendor added, nothing typed.

---

## `vendor_follows` — what the scans imply

| id | subscriber_id | vendor_id | scan_count | last_scanned_at | is_muted |
|---|---|---|---|---|---|
| `vf-001` | `s-001` | `v-001` | **3** | 2026-08-10 | false |
| `vf-002` | `s-001` | `v-002` | **1** | 2026-08-03 | false |

Sam follows Cedar three times as hard as Hollow Ridge. That difference shows up directly in scoring.

---

## `seen_blocks` — permanent exclusion

| subscriber_id | block_id | seen_at |
|---|---|---|
| `s-001` | `b-020` | 2026-08-05 |
| `s-001` | `b-021` | 2026-08-05 |
| `s-001` | `b-022` | 2026-08-05 |

Three stories from last week's issue. **Sam will never see any of them again**, no matter how well they'd score.

**Different from fatigue:**
- *Seen* — this **story**, this reader, **forever**
- *Fatigue* — this **vendor**, this reader, **a temporary penalty that decays**

---

# 6. DELIVERY

## `issues` — the pool, not the email

| id | market_id | issue_number | send_date | status | bank_size_at_assembly | sent_count |
|---|---|---|---|---|---|---|
| `i-006` | `m-001` | 6 | 2026-08-13 | **sent** | 18 | 247 |

One row for the whole week. 18 blocks in the bank, 247 emails sent — **and no two identical.**

---

## `issue_renders` — what each person actually got

| id | issue_id | subscriber_id | block_ids | followed_story_count | eligible_pool_size | total_words | unsubscribed_from_this |
|---|---|---|---|---|---|---|---|
| `r-001` | `i-006` | `s-001` | `[b-011, b-001, b-002, b-010, b-014, b-013, b-016, b-012, b-017]` | **2** | 14 | 942 | false |
| `r-002` | `i-006` | `s-002` | `[b-011, b-002, b-018, b-010, b-001, b-013, b-016, b-012, b-017]` | **1** | 15 | 918 | false |

**Look at the difference.** Sam gets `b-001` (Cedar — he follows them, 3 scans) in slot 2. Jo gets `b-002` first instead, because she follows Hollow Ridge. **Same issue, same bank, different emails.**

Slots 1, 4, 6, 7, 8, 9 are identical for both — greeting, ads, events, referral, footer.

**`eligible_pool_size = 14`** means Sam had 14 unseen stories to choose from. When that number drops toward 3, he's running out — the early warning that the bank is stagnating for a long-tenured reader.

---

## `email_logs`

| id | vendor_id | subscriber_id | email_type | to_email | sent_at |
|---|---|---|---|---|---|
| `el-001` | `v-001` | NULL | vendor_reminder | mei@cedar.com | 2026-08-09 08:00 |
| `el-002` | NULL | `s-001` | newsletter_issue | sam@gmail.com | 2026-08-13 17:02 |
| `el-003` | `v-003` | NULL | vendor_reminder | joe@pike.com | 2026-08-09 08:00 |

---

# The whole flow in one line

```
invitation_code → vendor (+scan_code) → conversation → messages →
submission (素材) → block → editor approves → THE BANK →
issue → personalizer excludes seen, scores rest → issue_render →
email → seen_blocks
```

---

# Three things to remember

**1. `blocks` holds everything publishable.** A story, an ad, the footer — all one table, one approval gate. That's what makes "nothing ships without approval" enforceable in a single place.

**2. The bank is a question, not a list.** `b-003` left it the moment a correction was filed and returns the moment it's fixed. Nothing had to remember to move it.

**3. `issues` is the pool; `issue_renders` is the email.** One issue, 247 different emails. Without that split there's no personalization and no way to answer *"why did this person leave?"*