from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from database.session import get_db
from auth.router import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])

class ContentRequest(BaseModel):
    business_id: str
    theme: Optional[str] = None
    platforms: Optional[list] = None

class EmailRequest(BaseModel):
    business_id: str
    brief: str

@router.post("/content/generate-week")
async def generate_week_content(
    req: ContentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from agent.content_pipeline import content_pipeline
    posts = await content_pipeline.generate_week_of_content(
        req.business_id, db, req.platforms, req.theme
    )
    return {"posts": posts, "count": len(posts)}

@router.post("/content/generate-email")
async def generate_email(
    req: EmailRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from agent.content_pipeline import content_pipeline
    campaign = await content_pipeline.generate_email_campaign(
        req.business_id, req.brief, db
    )
    return campaign

# ─── ADD THIS TO businesses/router.py ────────────────────────────────────────
# Add this endpoint alongside the existing business routes.
# It handles the day picker buttons in the kickoff email.

from fastapi.responses import HTMLResponse as _HTMLResponse

@router.get("/settings/kickoff-day", include_in_schema=False)
async def set_kickoff_day(
    business_id: str,
    day: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Called when user clicks a day button in the kickoff email.
    Updates the business's kickoff_day preference.
    This controls which day of the week the weekly kickoff email is sent.
    """
    from sqlalchemy import update as sql_update

    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day not in valid_days:
        return _HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9;">
        <div style="font-size:48px">❌</div>
        <h2>Invalid day selected.</h2>
        <p style="color:#666;">Please go back and try again.</p>
        </body></html>
        """, status_code=400)

    # Verify business exists
    biz_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    biz = biz_result.scalar_one_or_none()
    if not biz:
        return _HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#f9f9f9;">
        <div style="font-size:48px">❌</div>
        <h2>Business not found.</h2>
        </body></html>
        """, status_code=404)

    # Update the timezone/kickoff preference
    # We store the kickoff day in the Business model
    # For now we update preferred_post_timezone note field as kickoff_day
    # until we add a dedicated kickoff_day column
    await db.execute(
        sql_update(Business)
        .where(Business.id == business_id)
        .values(briefing_time=day)  # repurpose briefing_time to store kickoff day
    )
    await db.commit()

    return _HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 text-align:center;padding:60px 24px;background:#f9f9f9;">
      <div style="max-width:400px;margin:0 auto;background:#fff;border-radius:16px;
                  padding:40px;border:1px solid #e5e7eb;">
        <div style="font-size:48px;margin-bottom:16px;">✅</div>
        <h2 style="color:#111;margin:0 0 8px 0;">Kickoff day updated!</h2>
        <p style="color:#6b7280;margin:0 0 20px 0;">
          Your weekly plan will now arrive every <strong style="color:#111;">{day}</strong>.
        </p>
        <p style="color:#9ca3af;font-size:13px;margin:0;">You can close this tab.</p>
      </div>
    </body>
    </html>
    """)