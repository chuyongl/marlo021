# Marlo — Error Runbook

Known bugs, error patterns, and how to fix them. When something breaks, check here first.

---

## Instagram / Meta Errors

### ❌ platform_account_id is NULL → Instagram posting fails
**Symptom:** `/debug/test-post` returns `{"status": "no_handler", "action_type": "create_post"}` or `{"status": "skipped", "reason": "No active Meta integration found"}`

**Check:**
```sql
SELECT platform, platform_account_id, is_active
FROM platform_integrations
WHERE business_id = 'your-id';
```

**Root cause:** OAuth completed but Instagram Business Account ID was never fetched/stored.

**Current fix (in progress):** Migrating from Facebook Login to Instagram Login API.
- Facebook Login requires Instagram linked to Facebook Page at Graph API level
- Instagram Login API (launched July 2024) fetches account ID directly from `/me`
- No Facebook Page required

**Temporary workaround (for testing):** Manually set the ID in Railway DB:
```sql
UPDATE platform_integrations
SET platform_account_id = 'YOUR_IG_ACCOUNT_ID'
WHERE business_id = 'your-id' AND platform = 'meta';
```
To find your Instagram account ID: use Meta Graph API Explorer → User Token → query `/me?fields=id` while logged in as the Instagram account.

---

### ❌ Meta OAuth "Invalid Scopes" error
**Symptom:** Facebook OAuth dialog shows "This content isn't available right now — Invalid Scopes: instagram_business_basic..."

**Root cause:** Mixing Facebook Login scopes with Instagram Login scopes. They're incompatible.

**Fix:** In `oauth.py`, `META_SCOPES` must only contain Facebook Login compatible scopes:
```python
META_SCOPES = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish,instagram_manage_insights"
```
Never mix in `instagram_business_*` scopes with Facebook Login flow.

**Status:** Fixed May 8, 2026.

---

### ❌ Meta Business Suite "Business Account Not Allowed to Advertise"
**Symptom:** Clicking "Connect Instagram" in Meta Business Suite shows this error.

**Root cause:** The Meta Business Account has an advertising policy violation. Blocks Instagram connection in Business Suite UI.

**Fix:** This is why we're switching to Instagram Login API — it bypasses Business Suite entirely. Users connect directly with Instagram credentials.

**Status:** Workaround in progress (Instagram Login migration).

---

## Approval Flow Errors

### ❌ Approve button shows "This action was already handled" but status is still pending
**Symptom:** User clicks approve, sees success page saying "already handled", but `/debug/actions` shows status still `pending`.

**Root cause:** `approval_router.py` was checking `action.status != "pending_approval"` — our actions use `"pending"` not `"pending_approval"`.

**Fix:** Change check to:
```python
if action.status not in ("pending", "pending_approval"):
    return HTMLResponse(SUCCESS_PAGE.format(message="This action was already handled."))
```

**Status:** Fixed May 8, 2026.

---

### ❌ executor.execute_action() called at approval time → error
**Symptom:** Approve button throws 500 error or returns unexpected result.

**Root cause:** Old `approval_router.py` called `executor.execute_action()` which doesn't match our current executor interface.

**Fix:** Approval only sets `status = "executed"`. Never call executor at approval time. Scheduler's `execute_approved_posts` handles actual posting.

**Status:** Fixed May 8, 2026.

---

## Scheduler / Content Errors

### ❌ Two kickoff emails sent on trigger
**Symptom:** User receives two emails when `/debug/trigger-kickoff` is called.

**Root cause:** Called trigger-kickoff twice without resetting email_logs. Second call sees `first_kickoff` already sent → sends `weekly_kickoff`. Both send simultaneously.

**Fix:** Always reset before re-triggering in testing:
```powershell
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/YOUR-ID"
```

**Status:** Known behavior. Not a code bug — correct behavior for production. Only happens in testing when trigger called multiple times.

---

### ❌ Kickoff fires on wrong day (always Sunday)
**Symptom:** Weekly content generation ignores user's chosen kickoff day.

**Root cause:** Scheduler had hardcoded `if local_weekday != 6` (Sunday).

**Fix:** In `scheduler.py` `weekly_content_generation()`:
```python
kickoff_day = biz.briefing_time or "Sunday"
kickoff_weekday = DAY_TO_WEEKDAY.get(kickoff_day, 6)
if local_weekday != kickoff_weekday or local_hour != 21:
    continue
```

**Status:** Fixed May 8, 2026.

---

### ❌ Duplicate actions created (6 actions instead of 3)
**Symptom:** `/debug/actions` shows duplicate posts for each day.

**Root cause:** `trigger-kickoff` was called multiple times without clearing old pending actions.

**Fix:** `debug_router.trigger_kickoff` now clears all pending actions before generating:
```python
await db.execute(
    sql_delete(AgentAction).where(
        AgentAction.business_id == biz.id,
        AgentAction.status == "pending",
    )
)
await db.commit()
```

**Status:** Fixed May 8, 2026.

---

### ❌ Posting schedule returns 404
**Symptom:** Clicking posting day buttons in email returns `{"detail": "Not Found"}`.

**Root cause:** `/businesses/settings/posting-schedule` endpoint was missing from `businesses/router.py`.

**Fix:** Endpoint added to `businesses/router.py`.

**Status:** Fixed May 8, 2026.

---

## Email Errors

### ❌ strategy_summary leaks internal prompt fields
**Symptom:** Kickoff email shows "Tone: warm. CTA: drive foot traffic." instead of a human-readable message.

**Root cause:** `strategy_summary` was built from the full strategy dict including internal fields.

**Fix:** Only use `strategy.get("key_message", ...)`:
```python
strategy_summary = strategy.get("key_message", f"Building authentic content for {biz.name}.")
```

**Status:** Fixed (earlier session).

---

### ❌ created_at datetime naive/aware mismatch
**Symptom:** SQLAlchemy throws `TypeError: can't compare offset-naive and offset-aware datetimes`

**Root cause:** Some fields use `datetime.utcnow()` (naive) and some use `datetime.now(timezone.utc)` (aware). Comparing them causes errors.

**Fix for created_at fields:** Use `datetime.utcnow()` to stay consistent with existing schema.
**Fix for scheduled_post_time:** Use `datetime.now(timezone.utc)` (aware).
**Never mix** naive and aware datetimes in the same comparison.

**Status:** Partially fixed. Tech debt — migrate all to aware datetimes eventually.

---

## Database Errors

### ❌ AsyncSession used after close
**Symptom:** `sqlalchemy.exc.InvalidRequestError: This Session's connection has been closed`

**Root cause:** Passing a DB session from a request handler into a background `asyncio.create_task()`.

**Fix:** Always create a new session in background tasks:
```python
async def background_task():
    async with AsyncSessionLocal() as db:
        # use db here
asyncio.create_task(background_task())
```
Never pass the request's `db` session into `create_task`.

**Status:** Known pattern. Follow it for all background tasks.

---

## How to Debug a New Issue

1. Check Railway logs: `railway logs --tail`
2. Check `/debug/actions/{business_id}` for action status
3. Check DB directly in Railway Postgres Query tab
4. Add `print()` statements temporarily — they appear in Railway logs
5. If email not received: check Resend dashboard for delivery status
6. If OAuth fails: use Graph API Explorer at `developers.facebook.com/tools/explorer`
7. If scheduler not firing: check APScheduler logs at startup for "Started. Jobs:"