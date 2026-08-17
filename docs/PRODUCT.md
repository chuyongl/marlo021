# Brown Bag — Product Definition

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\PRODUCT.md`*

---

## Naming

| Name | What it is | Who sees it |
|---|---|---|
| **Brown Bag** | The newsletter. The public brand. | Readers, vendors, everyone |
| **Marlo** | The backend system that runs it. | Nobody outside the team |

**"Marlo" appearing in any reader- or vendor-facing output is a bug.**

*Brown Bag is provisional — chosen Aug 12. Keep it in config, not hardcoded.*

---

## What Brown Bag Is

**A weekly email newsletter for local readers, built from what local vendors tell us about their lives and their work.**

- **Readers:** local consumers. Free.
- **Vendors:** local businesses. Free. Self-signup, editor-activated.
- **Editors:** edit and approve every block before it can ship.
- **Revenue:** ads (two slots per issue).

---

## Governing Principles

### 1. The reader never sees the machinery
Brown Bag is the only name that appears. No mention of the system, the agents, or how any of it works.

### 2. The issue ships every week
Structure and length stay constant. Thin material means **get more material** — never shrink or skip.

### 3. Nothing ships without editor approval
Every block passes an editor. **The bank contains only approved blocks.** Assembly then runs automatically.

### 4. Vendors are collaborators, not sources
Vendors see their drafts **before** editor review. They can correct facts at any time, including after publication. It's their life being written about.

### 5. No passwords for readers or vendors
Readers: signed cookie from the QR scan. Vendors: magic link, then a 90-day session — **one click on first visit, then the site just opens.** Only editors have real logins.

### 6. Never reveal an inference
If the system infers something about a reader — interests, location, habits — **that inference never appears in the copy.**

Say "the cheese stall is back this week." Never "since you've been buying bread."

**Off-limits regardless of derivability:** pregnancy, health conditions, anything about children.

⚠️ **Washington My Health My Data Act:** inferences about health from purchase or scan behavior are regulated data.

---

## Who Uses What

| Role | Interface | How they get in |
|---|---|---|
| **Readers** | Email only | Scan a QR at a vendor stall |
| **Vendors** | Web app — chat, drafts, library | Self-signup with email → editor activates → magic link |
| **Editors** | Web app — review queue, editing | Hand-provisioned; real login |

---

## The Two-Agent Split ★

**This is the core of how content gets made.**

```
VENDOR                INTERVIEWER AGENT           WRITER AGENT         EDITOR
  │                          │                         │                 │
  │  conversation, photos    │                         │                 │
  │ ◀──────────────────────▶ │                         │                 │
  │                          │                         │                 │
  │                    素材 (raw material)              │                 │
  │                          │ ──────────────────────▶ │                 │
  │                          │                         │  writes story   │
  │                          │                         │ ──────────────▶ │
  │  ◀─── sees draft, can correct facts ─────────────────────────────────│
  │                          │                         │        edits    │
  │                          │                         │        approves │
  │                          │                         │                 ▼
  │                          │                         │            THE BANK
```

**Vendors are not expected to write well.** Their job is to supply good raw material — details, photos, what happened, why it mattered. Most people can do that in conversation and almost nobody can do it in prose.

**The interviewer agent gathers.** Its output is 素材, not copy.

**The writer agent writes.** It carries the quality bar. It has time, context, and no social pressure — everything the vendor lacks mid-conversation.

**The editor edits and approves.** Final craft and final gate.

---

## Content Standards

### The bar

> **Is there a person, and is something at stake for them?**
> **Would a stranger want to know how it turned out?**

Aim for the standard of a good magazine piece. Not fancy prose — **stakes, specificity, and restraint.**

**A story works when it has:**
- **A person with something at stake.** Not "the bakery" — a woman who started at 3am for eleven years. The stake can be small. It can't be absent.
- **Specificity that carries feeling.** Not "a hard season." The tomatoes split after the third day of rain, she picked them anyway, made forty jars of something she'd never made before. **The detail is the emotion.**
- **Restraint at the end.** End on the concrete thing. Never "and that's what community is all about." **A story that explains its own meaning is dead.**

### Reject outright
- No person in it
- Nothing at stake, nothing changed
- Explains its own meaning
- Reads like the vendor is selling

### Difficult material belongs here

The best local stories live in struggle, love, illness, loss, and failure. A farmer whose dog died. Someone who started baking after a divorce. A stall that nearly closed.

**Two hard guardrails:**

**It must be the vendor's story to tell.** Their own illness, yes. A customer's, no — Brown Bag can't verify consent it never witnessed.

**The vendor offers it; the agent never fishes for pain.** "What's been hard lately?" is fine. "How are you coping since your mother died?" is not — even if `vendor_memory` knows. **The vendor volunteers, or it doesn't exist.**

Where difficulty becomes active crisis — mental health, anything where publishing could hurt someone — **the agent escalates to a human and does not draft.**

### Voice rules
- No marketing language ("don't miss out," "limited time," "hurry in")
- No manufactured urgency
- The vendor's own words beat any paraphrase
- **Never invent a fact.** Every sentence traces to something the vendor said
- If deleting a sentence costs the reader nothing, delete it

---

## The Vendor Conversation

**No turn limit.** An editor working with a writer doesn't get one exchange, and neither does this. Vendors will talk for twenty minutes about their own life if the questions are good.

**What makes people quit isn't length — it's vagueness.** *"Tell me more." "Can you elaborate?" "Anything else?"* is homework. A specific question that shows you were listening is a conversation.

**Rules for the interviewer:**
- **Every question references something the vendor just said.** No generic prompts.
- **Track what's missing** — a person? a stake? a concrete scene? — and ask toward the gap.
- **If two exchanges in a row add nothing, stop** and take what's there.
- **The vendor can end it anytime.** "That's all I've got" is a complete answer.
- **Never fish for pain.**

**The conversation persists.** Vendors answer between customers. Three questions now, more after closing, finish tomorrow. **Nothing has to be completed in one sitting.**

### Stories don't run out

Evergreen material is **not** a finite inventory. Life keeps producing stories:

- What went wrong this week
- What surprised you
- The question you get asked constantly
- Why this batch is different
- The customer who's been coming eleven years
- The dog that sat in the pumpkins

**The constraint is the vendor noticing that something is a story** — most people don't think the dog counts. That's a prompting problem, not a supply problem, and it's solvable.

**The vendor library helps more than prompt engineering.** A vendor who reads another vendor's dog-in-the-pumpkin story learns *that counts*, and recalibrates what to bring.

**Harvest hard at signup** — not because it's the only chance, but because a new vendor has a backlog of untold stories.

---

## Vendor Collaboration

Vendors get a persistent workspace with three views:

| View | What's there |
|---|---|
| **This week** | The open conversation with the interviewer |
| **My stories** | Drafts and published pieces — **drafts visible before editor review** |
| **Library** | Published stories from other vendors in the market |

**Vendors request corrections; they don't edit directly.** They flag what's wrong — *"it's the north field, not the old orchard"* — and it becomes a task in the editor queue.

**Why the split:** direct editing would break the audit trail from published copy back to `raw_text`, and it would make the editor gate meaningless. But the vendor's facts must be respected, so their corrections are binding.

**A correction on an approved block pulls it from the bank** until resolved. Shipping a known-wrong fact about someone's own business is worse than a thin issue — the one case that overrides "ships every week."

---

## Issue Structure

**Fixed skeleton. ~980 words, hard ceiling 1,000.**

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

**Typography: exactly four sizes.** Small (footer), medium (body), large (titles), XL (logo).
**Story titles ≤50 characters.**

---

## The Story Bank

**Stories are written once and shown to many readers.** A bank of ~20 approved stories serves everyone; each reader sees 3.

**But a story is permanently consumed for the reader who saw it.** ★

| Rule | Scope | Duration |
|---|---|---|
| **Seen** | Per story, per reader | **Permanent — hard exclusion** |
| **Fatigue** | Per vendor, per reader | Temporary — score penalty |

These are different rules. Fatigue stops a reader seeing the same *vendor* too often. Seen stops them ever getting the same *story* twice.

**The supply consequence:** each reader burns 3 stories permanently per issue. A bank of 20 gives an individual reader about **7 weeks** before they've seen everything. After that they're only eligible for stories added since.

**So 3–5 new stories per issue is a floor, not an aspiration.** Below it, long-tenured readers — the loyal ones — slowly run out and start receiving bottom-of-barrel content while new readers get the best of it.

| | Weekly cadence |
|---|---|
| Bank size (steady state) | ~20 stories |
| **New stories per issue** | **3–5 minimum** |
| Vendors in rotation | 12+ |

---

## Story Selection

```
EXCLUDE if seen before          ← hard, permanent, runs first
EXCLUDE if quality_score < 15

score = QUALITY + RELEVANCE + DISCOVERY + PROXIMITY − FATIGUE
```

| Component | Range | Basis |
|---|---|---|
| **QUALITY** | 0–40 | Set by the editor at approval |
| **RELEVANCE** | 0–100 | Followed vendor +60, scan count to +25, recency +15, interest match ×40 |
| **DISCOVERY** | 0–25 | Complementary category +25, same category +10 |
| **PROXIMITY** | 0–20 | Same neighborhood +20, adjacent +12, same city +6 |
| **FATIGUE** | penalty | Last issue −40, last 3 issues −15 |

**Proximity is neighborhood-based, not city.** Ballard and Rainier Beach are both "Seattle" and forty minutes apart. Vendors pick their neighborhood from a dropdown at signup; adjacency comes from a maintained list.

**Reader location is inferred, never asked** — the most common neighborhood among followed vendors.

**Complementary beats same-category** deliberately. A baker's follower would rather hear about cheese than a rival bakery.

**When a reader follows too few vendors** — the common case — slots fill with unseen stories ranked by interest, proximity, and quality. **Never ship short.**

---

## Editorial Review

**Every block needs approval before entering the bank.**

Editors work a queue on the site with three lanes:
- **New drafts** from the writer agent
- **Vendor corrections** on drafts and published blocks
- **Escalations** — silent vendors, sensitive material, thin conversations

Approval happens **as material arrives**, not in a rush before send.

---

## Supply Monitoring

| Approved | Pending | Diagnosis |
|---|---|---|
| Low | High | **Editors are the bottleneck** |
| Low | Low | **Vendors are the bottleneck** |
| Healthy | — | Quiet |

Plus a third signal: **readers running low on unseen stories.** Early warning that the bank is stagnating for your most loyal people.

---

## The Only Metric That Matters

**Do readers open it, and do they stay.**

Readers don't pay, so their only expression is unsubscribing. **Unsubscribe rate is the only honest feedback this product gets.**

---

## Scope

**In:** one area (Seattle / Bellevue) · weekly · two ad slots · editor-written greeting · vendor self-signup with editor activation

**Out for MVP:** location-based greeting · recap section · variable frequency · SMS · multi-city · reader preferences page

---

## Backlog

- AI agent for local news when expanding beyond Seattle
- SMS reminders (needs 10DLC registration)
- Reader preferences (mute vendor, change frequency)
- Open/click tracking

---

## Open Questions

- **Brown Bag sending domain** — can't be marlo021.ai
- One React app with role routing, or separate vendor / editor apps?
- Physical QR format
- Is "Brown Bag" final? Treat as provisional.

---

## Company

- **Founder:** Anna (Chuyong Liu)
- **Stack:** FastAPI + React, Railway, PostgreSQL, Anthropic Claude, Resend, fal.ai
- **Status:** design settled; build starting