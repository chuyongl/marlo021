# Brown Bag — Current Status

*Last updated: October 15, 2026*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**The whole pilot product is built and deployed on marlo021.ai** (API on api.marlo021.ai, version `0.4.0`): public website, vendor app, editor app, the weekly issue, and a live report for market organizers. Everything runs from one site; no extra hosting.

The site starts with **five sample vendors** (marked "Sample") and their stories so every page has something to show. Remove them in Editor → Settings before real readers arrive.

---

## Entry Points

| Who | Where | How they get in |
|---|---|---|
| Readers | `/` , `/stories`, `/s/{slug}` | No login |
| Shoppers at a market (shared QR) | `/m/pike-place` | Tick vendors, enter email once |
| Shoppers at a stall (vendor QR) | `/v/{scan_code}` | Enter email once |
| Vendors | `/vendor` | Join at `/vendor/join` with a code (`PIKEPILOT`, `SEATTLE26`), then magic link |
| Editors | `/editor` | First time: setup code (given to Anna in chat), then email + password |
| Market organizers | `/report/{token}` | Private link from Editor → Markets & codes |
| Pitch pages | `/for-markets`, `/for-vendors` | Contact forms land in Editor → Inbox |

---

## What Was Built (Oct 15)

**Backend** (`backend/`)
- `content/interviewer.py`, `content/writer.py` — interviewer (gap-driven, one question at a time, stall rule enforced in code, nothing-here exit, sensitive → human) and writer + style guard (fact check against the transcript, one retry)
- `content/pipeline.py` — conversation → 素材 → draft (background) → vendor preview → editor
- `vendors/router.py` — signup with code, magic link, weekly conversation, quick updates, drafts, corrections, hide/show, reach numbers, library, Instagram caption
- `editors/router.py` — setup/login, overview with supply diagnosis, review queue (drafts, corrections, escalations, reader photos), vendors (add, login links, conversations, email this week's questions), codes, venues + report links, issue (greeting, preview, test, send), readers by source, inbox, settings, remove samples
- `public/router.py` — home/stories/story/vendor/venue pages, follow (one email, many vendors, signup_source recorded), unfollow, unsubscribe, reader shares with photo upload, nominations, leads, media, click tracking (`/r/{token}`), market report
- `newsletter/issue.py` — personalized selection (seen = permanent, quality ≥ 15, follow/complement/proximity/fatigue scoring), email render, send with seen_blocks + issue_renders
- `database/migrate.py` — startup schema upkeep (adds missing columns generically, subscriber market_id decision applied); `database/seed.py` — first-boot Seattle market, 3 venues, codes, samples
- New tables: venues, media, reader_shares, link_clicks, nominations, leads

**Frontend** (`frontend/src/`)
- New Brown Bag site replacing the Marlo landing: Home, Stories, Story, Vendor page, Market page (shared QR), Share, Nominate, Unsubscribe, For vendors, For markets, Report, Privacy and Terms (rewritten for Brown Bag), Why local (rebranded)
- Vendor app (`/vendor`): This week (interview + quick update), Stories (check drafts, Instagram image + caption), Readers, Share (QR, printable table card, messages for regulars and neighbor vendors), Profile
- Editor app (`/editor`): Overview, Review, This week's issue, Vendors, Markets & codes, Readers, Inbox, Settings

**Tested locally** against Postgres with a fake AI: full reader → vendor → editor → issue → report flow in a browser, plus a migration test on the old database shape.

---

## ⚠️ Deployed, Not Yet Verified Live

- **Real AI calls.** Interviewer, writer and guard have only run with the fake AI locally. First real test: sign up as a vendor and answer the question.
- **Email.** Sends use `FROM_EMAIL` (Railway) or the address in Editor → Settings. Must be a domain verified in Resend. If emails fail, every place that sends a link also shows a copyable link.
- **Weekly send is manual.** Editor → This week's issue → Send. No scheduler job yet.

---

## 🔴 Next

1. Anna tries every entry point (see the guide given in chat)
2. Run the interviewer on real vendors; tune question quality from transcripts (Editor → Vendors → Open → Recent conversations)
3. Decide the sending domain and verify it in Resend
4. Remove sample content before the first real issue
5. Pike Place conversation using `/for-markets` and a report link

---

## Reference

| Item | Value |
|---|---|
| API | `https://api.marlo021.ai` (`/health` → 0.4.0) |
| Site | `https://marlo021.ai` |
| Deploy | push to `main` → Railway builds backend and frontend |
| Interview test harness | `backend/tools/interview_harness.py` (needs `ANTHROPIC_API_KEY`) |
