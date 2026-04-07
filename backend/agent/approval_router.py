from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from database.session import get_db
from database.models import AgentAction, Business, User
from agent.executor import executor

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
<p style="color:#9CA3AF;font-size:13px;">You can close this tab.</p>
</body></html>"""

EXPIRED_PAGE = """<html><body style="font-family:-apple-system,sans-serif;text-align:center;
padding:60px 20px;background:#FFF7ED;">
<div style="font-size:56px;margin-bottom:16px;">⏰</div>
<h2 style="color:#C2410C;margin:0 0 8px 0;">This link has expired.</h2>
<p style="color:#6B7280;">Approval links are valid for 48 hours.<br>
Reply to your morning email to ask Marlo to resend it.</p>
</body></html>"""

@router.get("/approve")
async def approve_action(token: str, db: AsyncSession = Depends(get_db)):
    """One-click approval — no login required. User taps link in email."""
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

    # Load business for budget check
    biz_result = await db.execute(select(Business).where(Business.id == action.business_id))
    business = biz_result.scalar_one_or_none()
    monthly_budget = float(business.monthly_ad_budget or 300) if business else 300

    # Execute the action
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
        override_approval=True  # Skip the approval check since user approved via email
    )

    action.status = "executed"
    action.approved_at = datetime.utcnow()
    action.outcome = exec_result
    await db.commit()

    action_type = action.action_type or "action"
    message = f"Marlo is on it! Your {action_type.replace('_', ' ')} is being handled."
    return HTMLResponse(SUCCESS_PAGE.format(message=message))

@router.get("/decline")
async def decline_action(token: str, db: AsyncSession = Depends(get_db)):
    """One-click decline — no login required."""
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
    await db.commit()
    return HTMLResponse(DECLINED_PAGE)