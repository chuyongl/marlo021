# Marlo — Product Overview

*Last updated: August 1, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\PRODUCT.md`*

---

## What Is Marlo

Marlo is an autonomous AI marketing agent for small businesses. Everything happens via email — no dashboard, no login required. Users manage their entire marketing by reading and replying to emails.

**One-line pitch:** "Your competitor just hired a social media manager. Marlo is yours — for $99/month."

---

## Target Customer

**Primary focus right now: independent makers, starting with jewelry.**

Narrowed from "any local SMB" because makers have a specific, acute pain: they make beautiful physical objects and have no idea how to show them off consistently online.

- 1-10 person micro-businesses
- Core segments: makers (jewelry, ceramics, candles), food (bakery, cafe), local services, small professional services
- Tech-savviness: low — they use email and Instagram, nothing more
- Pain: 73% of small business owners have no confidence their marketing is working
- Time spent on marketing: average 20 hours/week (they hate it)

---

## Pricing

**Current mode: FREE.** Not charging anyone yet. Stripe is deliberately parked until one real user completes the full loop.

Planned pricing once we start charging:

| Tier | Price | Includes |
|---|---|---|
| Main | $99/month | Instagram posting, content generation, weekly plan |
| Trial | Free 14 days | Full access, no credit card required at signup |
| Tier 2 (future) | $149–199 | Adds Google Ads |

---

## Core Value Proposition

1. **Zero learning curve** — users already know how to use email
2. **Fully autonomous** — Marlo generates content, schedules posts, sends weekly plans
3. **One-click approval** — users approve or skip posts from their inbox
4. **No dashboard** — everything in email, nothing to log into

---

## What Makes Marlo Different

Every competitor (Buffer, Hootsuite, Mailchimp, Madgicx) requires a dashboard. Marlo is the only product operating 100% via email interaction. Genuine blue ocean position — no direct competitors identified as of May 2026.

---

## Key Metrics to Track

**While free (now):**
- Does the user reply to Marlo's emails?
- Does the user approve the posts?

Two behavioral signals. Everything else is premature.

**Once charging:**
- Trial → paid conversion rate (target: >30%)
- Monthly churn (SMB SaaS benchmark 4.8–8.1% — we need <5%)
- Time to first value (target: <7 days)
- Posts approved vs skipped ratio (proxy for content quality)

---

## Current Status (August 2026)

- **Product:** functionally complete, in bug-fixing phase
- **Users:** 0 — goal is one hand-onboarded real jewelry seller
- **Instagram posting:** working (Instagram Login API, posts publish on schedule)
- **Vendor types:** 10, with AI-powered auto-detection
- **Stripe:** test mode, intentionally not in use
- **Open blockers:** three bug fixes deployed Aug 1, untested — see `STATUS.md`

---

## Where Marlo Is Heading

A Phase 2 direction is under consideration: an add-on marketing intelligence layer that reads a merchant's order data, predicts what each customer needs next, and writes segments into their existing email tool. Ideation only, nothing built. See `PHASE_2_DIRECTION.md`.

---

## Company

- **Founder:** Anna (Chuyong Liu)
- **Stage:** Pre-revenue, free MVP, seeking first real user
- **Stack:** FastAPI + React, Railway, PostgreSQL, Anthropic Claude, fal.ai