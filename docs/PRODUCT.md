# Brown Bag — Product Definition

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\PRODUCT.md`*

---

## Naming

| Name | What it is | Who sees it |
|---|---|---|
| **Brown Bag** | The newsletter. The public brand. | Readers, vendors, everyone |
| **Marlo** | The backend system that runs it. | Nobody outside the team |

**"Marlo" appearing in any reader- or vendor-facing output is a bug.** The repo, the API, and the docs are Marlo. The product is Brown Bag.

*Brown Bag is provisional — chosen Aug 12, may change. Keep it in config, not hardcoded.*

---

## What Brown Bag Is

**A weekly email newsletter for local consumers, assembled from stories that local vendors tell us.**

Not software sold to merchants. **Brown Bag is the publication.**

- **Readers:** local consumers. Free.
- **Vendors:** local businesses. Free. Hand-provisioned.
- **Editors:** approve every block before it can ship.
- **Revenue:** ads (two slots per issue).

---

## Governing Principles

### 1. The reader never sees the machinery
Brown Bag is the only name that appears. No mention of the system, the agent, or how any of it works.

### 2. The issue ships every week
Structure and length stay constant. If material is thin, **get more material** — never shrink or skip. Consistency is what makes a newsletter a habit.

### 3. Nothing ships without editor approval
Every block — story, ad, greeting, events, static — passes an editor before entering the bank. **The bank contains only approved blocks.** Assembly then runs automatically, no human in the critical path.

### 4. No passwords for readers or vendors
Readers: signed cookie from the QR scan, or a signed token in an email link. Vendors: magic links. **Only editors have real logins**, because only editors can approve.

### 5. Never reveal an inference
If the system infers something about a reader — interests, location, habits — **that inference never appears in the copy.**

Say "the cheese stall is back this week." Never "since you've been buying bread." Same targeting, no surveillance feeling.

*Reference case: Target inferred a teenager's pregnancy from purchases and mailed baby coupons before her family knew. The lesson was never reveal, not never infer.*

**Off-limits regardless of derivability:** pregnancy, health conditions, anything about children.

⚠️ **Washington My Health My Data Act:** inferences about health drawn from purchase or scan behavior are regulated data. Scan history must never drive health-adjacent inference.

---

## Who Uses What

| Role | Interface | How they get in |
|---|---|---|
| **Readers** | Email only | Scan a QR at a vendor stall |
| **Vendors** | Web app — chat with the agent, upload photos | Hand-provisioned; magic link |
| **Editors** | Web app — review queue, approve/reject | Hand-provisioned; real login |

**This replaces v1's "email is the only interface."** Email is now the reader delivery channel only. Vendors and editors work on the site.

---

## Issue Structure

**Fixed skeleton. ~980 words, hard ceiling 1,000.** Every reader gets the same shape; the contents vary.

| # | Block | Budget | Personalized? |
|---|---|---|---|
| 1 | Greeting | ~120 w | No — same for everyone (MVP) |
| 2 | Story #1 | ≤200 w | Yes |
| 3 | Story #2 | ≤200 w | Yes |
| 4 | Ad #1 | ≤80 w | No |
| 5 | Story #3 | ≤120 w | Yes — shorter, reader fatigue |
| 6 | Events list | — | Yes — followed vendors only |
| 7 | Ad #2 | ~40 w | No |
| 8 | Referral | — | No |
| 9 | Footer | — | No |

**Typography: exactly four sizes.** Small (footer), medium (story body), large (story titles), XL (logo).
**Story titles ≤50 characters** (~8 words).

---

## The Story Bank

**Stories are written once and selected many times.** A bank of ~20 approved stories serves every reader; each reader sees 3.

Stories are not consumed when used — reader A seeing one doesn't remove it for reader B, or for reader A three weeks later.

| | Weekly cadence |
|---|---|
| Bank size (steady state) | ~20 stories |
| New stories per issue | 3–5 |
| Vendors in rotation | 12+ |

**Why 12+ vendors:** the fatigue rule rests a vendor for ~3 issues after they appear. Fewer than 12 and readers see the same names repeatedly.

**Evergreen material is finite per vendor.** You can only tell someone's origin story once. The bank fills fast when a vendor joins, then slows to perishable updates. **Harvest hard at onboarding** — 3–4 evergreen pieces while setting them up. **Vendor growth and content supply are the same problem.**

---

## Story Selection

```
score = QUALITY + RELEVANCE + DISCOVERY + GEOGRAPHY − FATIGUE
```

| Component | Range | Basis |
|---|---|---|
| **QUALITY** | 0–40 | Set by the editor at approval. Same for every reader. |
| **RELEVANCE** | 0–100 | Followed vendor +60, scan count up to +25, recency +15, interest match ×40 |
| **DISCOVERY** | 0–25 | Complementary category +25, same category +10 |
| **GEOGRAPHY** | 0–20 | Vendor city matches reader's inferred city (top-up only) |
| **FATIGUE** | penalty | Last issue −40, last 3 issues −15 |

**Hard floor: QUALITY below 15 never ships**, regardless of follows. A boring story from a followed vendor is worse than a good story from a stranger — the reader concludes the newsletter is dull, not that their baker had a slow week.

**Complementary beats same-category** deliberately. Someone following a baker would rather hear about the cheese stall than a competing bakery.

**When a reader follows too few vendors** — the common case, since most scan once — slots fill with unfollowed stories ranked by interest, geography, and quality. **Never ship short.**

**Reader location is inferred, never asked.** Derived from the cities of vendors they follow. Someone who scanned three Bellevue stalls is a Bellevue reader. No form field; sharpens with every scan.

---

## Content Standards

Every block must make the reader feel at least one of: **useful, beautiful, interesting, human.**

**Hard rule: never invent a fact.** Every sentence traces to something a vendor actually said.

**A story is strong enough to ship if it has at least two of:**
- A **specific detail** — name, number, place, time
- A **person** — someone did something
- A **change** — different from last week or last year
- A **why** — a reason behind a choice

*"We have apples this week"* has none.
*"First press of the season, a week early because of the heat"* has three.

**Voice rules:**
- No marketing language ("don't miss out," "limited time," "hurry in")
- No manufactured urgency
- The vendor's own words beat any paraphrase
- If deleting a sentence costs the reader nothing, delete it

---

## The Vendor Conversation

Vendors chat with an AI agent on the site. The agent asks, they answer, photos welcome.

**The agent pushes back gently, once.** If a story is thin, it asks **one** specific follow-up — a question it already half-knows the answer to, from `vendor_memory`.

Not: *"Can you tell me more about the apples?"*
But: *"Are these from the old orchard you mentioned, or a different block?"*

Answerable in six words, and it produces something usable.

**One follow-up maximum.** Two and the agent becomes a chore. Vendors quit over homework.

**The ask scales down with silence.** A reliable vendor gets an open question. A vendor quiet three weeks gets *"just send a photo, we'll write around it."* Lower the bar until they clear it.

**Reminders go by email.** SMS is a later upgrade — it needs A2P 10DLC carrier registration with a multi-week lead time.

**The reminder carries the question, not a generic nudge:**

> *Cedar Bakery — is the sourdough back this week, or still on pause? Two minutes: [link]*

The vendor knows the answer before they click. This means the agent picks the question *before* sending, not when the vendor arrives.

---

## Editorial Review

**Every block needs approval before entering the bank.** Stories, ads, greeting, events, static — all of them.

Editors work a review queue on the site. Approval happens **at the block level as material arrives**, not in a rush before send.

**Human escalation triggers:**
- Vendor silent 2+ cycles
- One follow-up used and the story is still below bar
- Vendor followed by many readers (high cost of absence)
- Bank running low

---

## Supply Monitoring

Two-sided, because the two numbers diagnose different problems:

| Approved | Pending | Diagnosis |
|---|---|---|
| Low | High | **Editors are the bottleneck** — nudge editors |
| Low | Low | **Vendors are the bottleneck** — chase vendors |
| Healthy | — | Quiet |

---

## The Only Metric That Matters

**Do readers open it, and do they stay.**

Readers don't pay, so their only expression is unsubscribing. **Unsubscribe rate is the only honest feedback this product gets.**

---

## Scope

**In:**
- One area: Seattle / Bellevue
- Weekly, everyone on the same cadence
- Two ad slots per issue
- Editor-written greeting, same for all readers

**Out for MVP:**
- ❌ Location-based greeting (Seattle-only, so one greeting serves everyone)
- ❌ "Recap since last touch" section
- ❌ Variable send frequency
- ❌ Vendor self-serve signup
- ❌ Vendor approval of their own block
- ❌ SMS
- ❌ Multi-city

---

## Backlog

- **AI agent for local news** — when expanding beyond Seattle, an agent gathers local content and preps it for editor review. Greeting becomes a location-matched block class.
- SMS reminders (needs 10DLC registration)
- Reader preferences page (mute vendor, change frequency)
- Open/click tracking
- Multi-market

---

## Open Questions

- **Sending domain** for Brown Bag — can't be marlo021.ai
- Physical QR format: sticker, table tent, printed on bags?
- One web app with role routing, or two (vendor / editor)?
- Is "Brown Bag" final? Treat as provisional; keep in config.

---

## Company

- **Founder:** Anna (Chuyong Liu)
- **Stack:** FastAPI + React, Railway, PostgreSQL, Anthropic Claude, Resend, fal.ai
- **Status:** design settled; build starting