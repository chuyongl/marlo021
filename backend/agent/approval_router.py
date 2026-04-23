from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from database.session import get_db
from database.models import AgentAction, Business, User, ContentFeedback
from agent.executor import executor
import uuid

router = APIRouter(prefix="/actions", tags=["approvals"])

SUCCESS_PAGE = """<html><body style="font-family:-apple-system,sans-serif;text-align:center;
padding:60px 20px;background:#F0FDF4;">
<div style="font-size:56px;margin-bottom:16px;">✅</div>
<h2 style="color:#15803D;margin:0 0 8px 0;">Done!</h2>
<p style="color:#6B7280;margin:0 0 24px 0;">{message}</p>
<p style="color:#9CA3AF;font-size:13px;">You can close this tab.</p>
</body></html>"""

DECLINED_PAGE = """<html><body style="font-family:-apple-system,sans-serif;text-align:center;
padding:60px 20px;background:#F9FAFB;">
<div style="font-size:56px;margin-bottom:16px;">👍</div>
<h2 style="color:#374151;margin:0 0 8px 0;">Got it — skipped.</h2>
<p style="color:#6B7280;margin:0 0 24px 0;">Marlo won't take that action.</p>
{feedback_buttons}
<p style="color:#9CA3AF;font-size:13px;margin-top:24px;">You can close this tab.</p>
</body></html>"""

EXPIRED_PAGE = """<html><body style="font-family:-apple-system,sans-serif;text-align:center;
padding:60px 20px;background:#FFF7ED;">
<div style="font-size:56px;margin-bottom:16px;">⏰</div>
<h2 style="color:#C2410C;margin:0 0 8px 0;">This link has expired.</h2>
<p style="color:#6B7280;">Approval links are valid for 48 hours.<br>
Reply to your morning email to ask Marlo to resend it.</p>
</body></html>"""

UNSUBSCRIBE_PAGE = """<html><body style="font-family:-apple-system,sans-serif;text-align:center;
padding:60px 20px;background:#F9FAFB;">
<div style="font-size:56px;margin-bottom:16px;">👋</div>
<h2 style="color:#374151;margin:0 0 8px 0;">Unsubscribed.</h2>
<p style="color:#6B7280;">You won't receive any more emails from Marlo.</p>
<p style="color:#9CA3AF;font-size:13px;">You can close this tab.</p>
</body></html>"""

FEEDBACK_PAGE = """<html><body style="font-family:-apple-system,sans-serif;text-align:center;
padding:60px 20px;background:#F9FAFB;">
<div style="font-size:56px;margin-bottom:16px;">🙏</div>
<h2 style="color:#374151;margin:0 0 8px 0;">Thanks for the feedback!</h2>
<p style="color:#6B7280;">Marlo will use this to improve future content.</p>
<p style="color:#9CA3AF;font-size:13px;">You can close this tab.</p>
</body></html>"""

def _feedback_buttons(action_id: str, base_url: str) -> str:
    reasons = [
        ("wrong_tone", "Wrong tone"),
        ("not_relevant", "Not relevant"),
        ("poor_quality", "Poor quality"),
        ("wrong_timing", "Wrong timing"),
        ("other", "Other"),
    ]
    buttons = " ".join([
        f'<a href="{base_url}/actions/feedback?action_id={action_id}&reason={code}" '
        f'style="display:inline-block;background:#F3F4F6;color:#374151;padding:8px 16px;'
        f'border-radius:20px;text-decoration:none;font-size:13px;margin:4px;">{label}</a>'
        for code, label in reasons
    ])
    return f"""<div style="margin-top:16px;">
      <p style="color:#9CA3AF;font-size:13px;margin:0 0 10px 0;">
        Help Marlo improve — why did you skip this? (optional)
      </p>
      {buttons}
    </div>"""

@router.get("/approve")
async def approve_action(token: str, db: AsyncSession = Depends(get_db)):
    """One-click approval — no login required."""
    result = await db.execute(
        select(AgentAction).where(AgentAction.approval_token == token)
    )
    action = result.scalar_one_or_none()

    if not action:
        return HTMLResponse(EXPIRED_PAGE, status_code=404)

    if action.token_expires_at and datetime.utcnow() > action.token_expires_at:
        return HTMLResponse(EXPIRED_PAGE)

    if action.status != "pending_approval":
        return HTMLResponse(SUCCESS_PAGE.format(message="This action was already handled."))

    biz_result = await db.execute(select(Business).where(Business.id == action.business_id))
    business = biz_result.scalar_one_or_none()
    monthly_budget = float(business.monthly_ad_budget or 300) if business else 300

    exec_result = await executor.execute_action(
        {
            "type": action.action_type,
            "parameters": action.action_parameters,
            "reasoning": action.agent_reasoning,
            "platform": (action.action_parameters or {}).get("platform", "")
        },
        str(action.business_id),
        monthly_budget,
        db,
        override_approval=True
    )

    action.status = "executed"
    action.approved_at = datetime.utcnow()
    action.outcome = exec_result

    # Record feedback
    feedback = ContentFeedback(
        id=uuid.uuid4(),
        business_id=action.business_id,
        action_id=action.id,
        decision="approved",
        content_type=action.action_type,
        platform=(action.action_parameters or {}).get("platform"),
        created_at=datetime.utcnow()
    )
    db.add(feedback)
    await db.commit()

    action_type = action.action_type or "action"
    message = f"Marlo is on it! Your {action_type.replace('_', ' ')} is being handled."
    return HTMLResponse(SUCCESS_PAGE.format(message=message))

@router.get("/decline")
async def decline_action(token: str, db: AsyncSession = Depends(get_db)):
    """One-click decline — no login required."""
    import os
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

    result = await db.execute(
        select(AgentAction).where(AgentAction.decline_token == token)
    )
    action = result.scalar_one_or_none()

    if not action:
        return HTMLResponse(EXPIRED_PAGE, status_code=404)

    if action.token_expires_at and datetime.utcnow() > action.token_expires_at:
        return HTMLResponse(EXPIRED_PAGE)

    action.status = "rejected"
    action.approved_at = datetime.utcnow()

    # Record feedback (reason collected separately via /feedback endpoint)
    feedback = ContentFeedback(
        id=uuid.uuid4(),
        business_id=action.business_id,
        action_id=action.id,
        decision="declined",
        content_type=action.action_type,
        platform=(action.action_parameters or {}).get("platform"),
        created_at=datetime.utcnow()
    )
    db.add(feedback)
    await db.commit()

    buttons = _feedback_buttons(str(action.id), base_url)
    return HTMLResponse(DECLINED_PAGE.format(feedback_buttons=buttons))

@router.get("/feedback")
async def record_feedback(
    action_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Record the reason for a decline — called from optional feedback buttons."""
    try:
        result = await db.execute(
            select(ContentFeedback)
            .where(ContentFeedback.action_id == action_id)
            .where(ContentFeedback.decision == "declined")
        )
        feedback = result.scalar_one_or_none()
        if feedback:
            feedback.reason = reason
            await db.commit()
    except Exception as e:
        print(f"[Feedback] Error recording reason: {e}")

    return HTMLResponse(FEEDBACK_PAGE)

@router.get("/unsubscribe")
async def unsubscribe(token: str, db: AsyncSession = Depends(get_db)):
    """One-click unsubscribe — required by CAN-SPAM law."""
    import base64
    try:
        business_id = base64.urlsafe_b64decode(token.encode()).decode()
    except Exception:
        return HTMLResponse(UNSUBSCRIBE_PAGE)

    await db.execute(
        update(Business)
        .where(Business.id == business_id)
        .values(email_notifications=False)
    )
    await db.commit()
    return HTMLResponse(UNSUBSCRIBE_PAGE)