# Marlo — API Reference

Base URL: `https://api.marlo021.ai`

---

## Auth

### POST /auth/register
Register a new user.
```json
Body: { "email": "...", "password": "...", "full_name": "..." }
Response: { "id": "uuid", "email": "..." }
```

### POST /auth/login
Login. Returns JWT token.
```
Content-Type: application/x-www-form-urlencoded
Body: username=email@example.com&password=...
Response: { "access_token": "...", "token_type": "bearer" }
```
⚠️ Field name is `username` not `email` (OAuth2 standard).

---

## Businesses

### POST /businesses/
Create a business. Triggers onboarding email 1.
```json
Body: {
  "name": "string",
  "industry": "string",
  "monthly_ad_budget": 300,        // example only — user enters any number (e.g. 50, 500, 2000)
  "description": "optional",
  "tone_of_voice": "optional",
  "target_audience": "optional",
  "timezone": "America/Los_Angeles",           // auto-detected from browser via Intl.DateTimeFormat()
  "preferred_post_timezone": "America/Los_Angeles"  // same — not hardcoded, reflects user's actual location
}
Response: { "id": "uuid", "name": "string" }
```
Note: all values above are examples only. `timezone` and `preferred_post_timezone` are auto-detected on the frontend using `Intl.DateTimeFormat().resolvedOptions().timeZone` — they reflect whatever timezone the user's browser reports at signup.

### GET /businesses/
List businesses for current user.

### GET /businesses/settings/kickoff-day
**Called from email button.** Updates user's kickoff day.
```
Query: business_id=uuid&day=Sunday
Response: HTML page ("Kickoff day updated!")
```

### GET /businesses/settings/posting-schedule
**Called from email button.** Updates posting days.
```
Query: business_id=uuid&days=Monday,Wednesday,Friday
Response: HTML page ("Posting schedule updated!")
```

---

## Actions (Approval)

### GET /actions/approve
**Called from email button.** Approves a pending action.
```
Query: token=uuid
Response: HTML page ("Done! Your post will go live at the scheduled time.")
```
Status flow: `pending` → `executed`

### GET /actions/decline
**Called from email button.** Declines a pending action.
```
Query: token=uuid
Response: HTML page ("Got it — skipped.") + feedback buttons
```
Status flow: `pending` → `rejected`

### GET /actions/feedback
Records reason for decline.
```
Query: action_id=uuid&reason=wrong_tone|not_relevant|poor_quality|wrong_timing|other
Response: HTML page ("Thanks for the feedback!")
```

### GET /actions/unsubscribe
One-click unsubscribe (CAN-SPAM required).
```
Query: token=base64_encoded_business_id
Response: HTML page ("Unsubscribed.")
```

---

## Integrations (OAuth)

### GET /integrations/connect/google
Starts Google Ads OAuth flow.
```
Query: business_id=uuid
Response: Redirect to Google OAuth
```

### GET /integrations/callback/google
Google OAuth callback. Saves tokens, advances onboarding to step 2, sends email 2.

### GET /integrations/skip-google
User skips Google Ads. Advances to step 2, sends email 2.
```
Query: business_id=uuid
```

### GET /integrations/connect/meta
Starts Facebook Login OAuth flow (to be replaced with Instagram Login).
```
Query: business_id=uuid
Response: Redirect to Facebook OAuth
```

### GET /integrations/callback/meta
Meta OAuth callback. Saves tokens + Instagram account ID, advances to step 3, sends email 3.

### GET /integrations/skip-meta
User skips Meta. Advances to step 3, sends email 3.

### GET /integrations/connect/mailchimp
Starts Mailchimp OAuth (or skips if not configured).

### GET /integrations/callback/mailchimp
Mailchimp callback. Advances to step 4, sends email 4.

### GET /integrations/skip-mailchimp
User skips Mailchimp. Advances to step 4, sends email 4.

---

## Email Inbound

### POST /email/inbound
Postmark webhook for inbound email replies.
Parses business info from email 4 replies, sets `onboarding_completed = true`.

---

## Billing (Stripe)

### POST /billing/create-checkout
Creates Stripe checkout session for signup.

### POST /billing/webhook
Stripe webhook handler (subscription created/canceled/payment failed).

---

## Debug Endpoints (⚠️ Remove before public launch)

All require no auth. Prefix: `/debug/`

### GET /debug/businesses
List all businesses with settings.

### GET /debug/trigger-kickoff/{business_id}
Generate this week's posts + send kickoff email.
- Clears all pending actions first (idempotent)
- Sends `first_kickoff` or `weekly_kickoff` based on email history
```json
Response: {
  "status": "success",
  "email_sent": "first_kickoff",
  "posts_generated": 3,
  "posting_schedule": ["Monday", "Wednesday", "Friday"]
}
```

### GET /debug/resend-kickoff/{business_id}
Resend kickoff email without regenerating content.

### GET /debug/trigger-analytics/{business_id}
Send analytics email immediately.

### GET /debug/test-post/{business_id}
Attempt real Instagram post with latest pending action.

### GET /debug/actions/{business_id}
List all actions with status, approve/decline URLs, caption previews.

### GET /debug/send-approval/{business_id}/{day}
Send approval email for a specific day (e.g., Monday).

### DELETE /debug/reset/{business_id}
Delete all actions and email logs. Full reset.
```powershell
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/{id}"
```