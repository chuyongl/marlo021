# Marlo — Product Definition

*Last updated: August 4, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\PRODUCT.md`*

> ⚠️ **Major pivot, August 4, 2026.** Marlo was an Instagram marketing tool sold to small businesses at $99/month. It is not that anymore.

---

## What Marlo Is

**An email newsletter written for local consumers, built from material supplied by many local businesses.**

Marlo is not software sold to merchants. **Marlo is the publication.**

- **Reader:** local consumers
- **Content source:** many local vendors
- **How it's made:** Marlo assembles and edits material vendors provide
- **Price:** free for vendors, free for readers
- **Revenue:** from elsewhere (TBD, out of scope)

---

## Governing Principles

### 1. Marlo is invisible
Readers receive a local newsletter with its own name. Vendors receive an email from the market. **The string "Marlo" appearing anywhere customer-facing is a bug.**

### 2. The issue ships every week
**The newsletter is a commitment to the reader.** Structure and length stay constant. If vendor material is thin, the answer is **get more material** — never shrink the issue, never skip a week.

Consistency is what makes a newsletter a habit. A reader who doesn't know whether it's coming stops expecting it. The cost of this principle lands entirely on the supply side, which is why content supply is the hardest part of the product.

### 3. Email is the only interface
No dashboard, for vendors or readers. Everyone already uses email daily; nothing new to learn, nothing to log into.

*Carried from ADR-001 (May 2026). Survived the pivot — still core to the product's identity.*

**Trade-off, accepted:** complex operations are impossible. If email lands in spam, the whole experience breaks.

### 4. No passwords, ever
Readers are identified by a signed cookie or a signed token in an email link. **The email address is the identity.** Vendors approve their content by clicking a tokenized link.

*Carried from ADR-003.* Login friction causes abandonment, and the security exposure is small — worst case, someone approves a block or unsubscribes an address they control access to.

### 5. Never reveal an inference
If the system ever infers something about a reader — interests, habits, situation — **that inference must never appear in the copy.**

Say "peaches are in this week." Never "since you've been buying stone fruit." Same targeting, no surveillance feeling.

*Carried from the shelved Phase 2 work. The reference case: Target inferred a teenager's pregnancy from purchases and mailed baby coupons before her family knew. The lesson was never reveal, not never infer.*

**Off-limits categories regardless of derivability:** pregnancy, health conditions, anything about children.

⚠️ **Legal, Washington State:** the My Health My Data Act treats inferences about health drawn from purchase behavior as regulated data. **Scan history must never drive health-adjacent inference** — be careful with categories like gluten-free and baby food.

---

## The Three-Sided Relationship

```
Vendors                Marlo                 Readers
   │                     │                      │
   │  reply with material│                      │
   │  ──────────────────▶│                      │
   │                     │  assemble + edit     │
   │                     │  ───────────────────▶│
   │                     │                      │
   │                     │  unsubscribe anytime◀│
```

**Vendors supply material. Marlo supplies editing. Readers supply attention.**

---

## Content Supply — The Hard Part

Vendors will not reply reliably. **The system must produce a full issue anyway.** Four tiers, drawn in order:

| Tier | Source | Reliability |
|---|---|---|
| **1** | Fresh vendor replies to the weekly question | Low — plan for 20–40% |
| **2** | Chasing non-responders; easier asks for the long-silent | Recovers some of Tier 1 |
| **3** | **Reserve bank** — evergreen material captured earlier, held back | High, but finite |
| **4** | **Market-level content** — seasonal, how-to, logistics | Fully reliable, vendor-independent |

**The reserve bank is load-bearing.** During good weeks the system deliberately holds material back rather than spending it. That buffer is what makes weekly delivery possible.

**Supply is monitored continuously, not discovered on send day.** The system should always know its runway in days and escalate early.

---

## The Only Metric That Matters

**Do readers open it, and do they stay.**

Readers don't pay, so their only expression is unsubscribing. **Unsubscribe rate is the only honest feedback this product gets.**

---

## Content Standards

Every issue must make the reader feel at least one of:

| Standard | What it looks like here |
|---|---|
| **Useful** | Who has what, when it arrives, what's running out |
| **Beautiful** | Real photos, clean layout, consistent visual system |
| **Interesting** | The vendor's actual words, unexpected detail, no marketing voice |
| **Human** | Who's making what, why, what happened this week |

**Hard rule: Marlo never invents a fact.** Every sentence traces back to something a vendor actually said or did.

**Voice rules:**
- No marketing language ("don't miss out," "limited time," "hurry in")
- No manufactured urgency
- The vendor's own words beat Marlo's paraphrase
- If deleting a sentence costs the reader nothing, delete it

---

## Issue Format — OPEN, NOT YET DECIDED

⚠️ **These are the P0 design decisions. Nothing downstream can be finalized without them.**

Deliberately unanswered — they should be decided against real vendor material, not in the abstract:

- How long does one issue feel? Mix of short and longer pieces, exact budget TBD
- What sections exist, and are they fixed or variable?
- How many vendors appear in one issue?
- How many follows does a reader need for the issue to feel relevant?
- **Reader follows only 1 vendor** — what fills the rest?
- **Reader follows 40** — what gets cut? Does it feel like loss?
- Minimum material required to assemble at full length

**Working assumption only:** one deeper story plus several short pieces. **Not a decision. Do not build against it.**

---

## Reader and Geography

- **Geography:** one area first (Seattle / Bellevue)
- **Reader:** someone who shops local and wants to know who has what
- **Vendor types:** makers, food, bakery, coffee, produce, local services

**One newsletter per area.** Locality is the product.

---

## Explicitly Not Doing

- ❌ No SaaS, no subscription revenue
- ❌ No dashboard
- ❌ Not posting Instagram for merchants
- ❌ No ad slots (for now)
- ❌ No expansion beyond one area until it works
- ❌ Stripe shelved

---

## Code Status

**Archived** (`backend/archive/`, not imported anywhere):
`content_pipeline.py`, `strategy_agent.py`, `executor.py`, `google_ads_agent.py`, `analytics_agent.py`, `meta.py`, `oauth.py`, `google_ads.py`, `billing/`

**Reused:** `inbound.py`, `reply_handler.py`, `sender.py`, `templates.py`, `content_safety.py`, `user_memory.py` → `vendor_memory.py`, `vendor_profiles.py`, `scheduler.py`, `brain.py`, one-click approval, photo upload

**New:** subscriber model, scan flow, content supply pipeline, block builder, style guard, personalizer, renderer

See `ARCHITECTURE.md` and `DATA_MODEL.md`.

---

## Open Questions

**Blocking:**
- Issue format (above)
- Newsletter brand name
- Sending domain (can't be marlo021.ai)

**Non-blocking:**
- Physical QR format: sticker, table tent, printed on bags?
- Vendor onboarding: self-serve or bulk import

---

## Company

- **Founder:** Anna (Chuyong Liu)
- **Stack:** FastAPI + React, Railway, PostgreSQL, Anthropic Claude, Resend, Postmark, fal.ai
- **Status:** mid-pivot; docs consolidated, code cleanup pending, newsletter build not started