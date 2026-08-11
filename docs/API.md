# Marlo — API Reference

*Last updated: August 4, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\API.md`*

> ⚠️ **Fully rewritten August 4, 2026.** The old API served Instagram posting, OAuth, and Stripe. All of it is archived. **Nothing below is built yet** except where noted — this is the target surface, written so implementation has a spec to build against.

Base URL: `https://api.marlo021.ai`

---

## Design Rules

**1. No passwords anywhere.** Readers are identified by a signed cookie or a signed token in an email link. The email address is the identity.

**2. Marlo never appears in a response.** Any user-visible string containing "Marlo" is a bug. Reader-facing pages use the newsletter's brand name.

**3. Tokens are signed, not guessable.** Unsubscribe, preferences, and vendor approval links carry HMAC-signed tokens. No token, no access.

**4. Reader-facing endpoints return HTML, not JSON.** They're opened from a phone camera or an email client, not called by code.

---

## Reader Endpoints

### GET /v/{scan_code}
**The product's front door.** Opened by scanning a QR code at a vendor's stall.

```
Path:     scan_code — 4-5 char vendor code, e.g. "A7K2"
Response: HTML
Cookie:   reads sub_token if present
```

**Two behaviors:**

| Cookie state | What happens |
|---|---|
| **Absent** (new reader) | Landing page: vendor name, photo, what they'll receive. One email field, one unchecked consent box. |
| **Present** (returning) | Logs the scan, increments `vendor_follow.scan_count`, shows "Added {vendor}" plus the current follow list. **No input required, ~1 second.** |

Always writes a `scan_event`. Dedup: same reader + same vendor + same day counts once as an interest signal, though every raw event is stored.

**Invalid or inactive `scan_code`:** generic "this code isn't active" page. Never reveal whether the code ever existed.

---

### POST /subscribe
Creates a subscriber. Called from the scan landing page.

```json
Body: {
  "email": "...",
  "scan_code": "A7K2",
  "consent": true
}
Response: HTML confirmation
Sets:     sub_token cookie (signed, 2-year expiry)
```

**Required behavior:**
- `consent` must be `true` — reject otherwise. **Never pre-check the box in the UI.**
- Record `consent_at` and `consent_source` (e.g. `qr_scan:A7K2`)
- Create `vendor_follow` for the scanned vendor
- Set `first_vendor_id` for attribution
- Send welcome email

**Email already exists:** link the session to the existing subscriber and add the follow. **Do not error, do not create a duplicate, do not reveal that the address was already registered.**

---

### GET /unsubscribe?token={t}
One-click unsubscribe. **Legally required (CAN-SPAM).**

```
Query:    token — signed subscriber token
Response: HTML confirmation
```

Must take effect immediately — no confirmation step, no login, no "are you sure." Sets `status = "unsubscribed"` and `unsubscribed_at`.

If the link came from a specific issue, set `issue_renders.unsubscribed_from_this = true` for that render. **This is the only signal that can diagnose content quality — do not skip it.**

Offer a lighter option on the confirmation page (pause, or reduce frequency), but only *after* the unsubscribe has already taken effect.

---

### GET /preferences?token={t}
Manage follows and frequency. No login.

```
Query:    token — signed subscriber token
Response: HTML
```

Reader can mute individual vendors (`vendor_follow.is_muted`), change `send_frequency`, or unsubscribe.

---

## Vendor Endpoints

### GET /vendor/join
Vendor onboarding page.

⚠️ **Open question:** self-serve signup, or bulk import by the market? This endpoint's shape depends on that decision.

---

### GET /vendor/approve?token={t}
Vendor approves their own block in the upcoming issue.

```
Query:    token — signed, scoped to one content_block
Response: HTML
```

Sets `approved_by_vendor = true`. Unapproved blocks score `-999` and never ship.

**Reuses the one-click-approval pattern from v1** — this mechanism already works and is worth keeping.

---

### GET /vendor/qr/{vendor_id}
Returns the printable QR image for a vendor's `scan_code`.

```
Response: PNG or SVG
```

---

## Inbound Email

### POST /email/inbound
**Postmark webhook. This is the content intake pipe.** ✅ *Already working from v1.*

```
Body:     Postmark inbound payload
Response: {"status": "received"}
```

Flow:
1. Identify the vendor from the `+address` in the recipient
2. Run `content_safety` check
3. Photos → fal.ai enhancement → store URLs
4. `reply_handler` interprets the reply
5. Create `content_item` with `raw_text` stored **verbatim, never modified**
6. **Classify: use now, or deposit to the reserve bank?**
7. Send a short confirmation back to the vendor

Step 6 is the piece that makes weekly delivery possible — time-sensitive material ships this week, evergreen material is banked for a thin week.

---

## Internal / Debug

Prefix `/debug/`, no auth. **Remove before real readers.**

The v1 debug endpoints are archived along with the Instagram code. New ones needed:

| Endpoint | Purpose |
|---|---|
| `GET /debug/supply` | Current material count and runway in days |
| `GET /debug/issue/{market_id}` | Preview the assembled block pool |
| `GET /debug/render/{subscriber_id}` | Preview one reader's personalized issue |
| `GET /debug/reserve` | Reserve bank depth by season/type |

`/debug/render` matters most — it's the only way to see what an individual reader actually receives before sending.

---

## Not Carried Over

Archived along with their code. Do not reimplement without a deliberate decision:

| Old endpoint group | Reason |
|---|---|
| `/auth/*` | No passwords in the new model |
| `/businesses/*` | Replaced by `/vendor/*` |
| `/actions/approve`, `/decline`, `/feedback` | Instagram approval flow |
| `/integrations/*` | No OAuth |
| `/billing/*` | Free product |
| Old `/debug/*` | Built around Instagram posting |

---

## Open Questions

- **Sending domain** — outbound mail can't come from marlo021.ai; readers shouldn't see Marlo. Affects every link in every email.
- **Scan URL host** — should the QR point at a branded short domain rather than marlo021.ai?
- Vendor onboarding shape (self-serve vs bulk import)