from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update
from pydantic import BaseModel
from typing import Optional, List
from database.session import get_db
from database.models import Business, User
from auth.router import get_current_user
import uuid
import asyncio

router = APIRouter(prefix="/businesses", tags=["businesses"])


class BusinessCreate(BaseModel):
    name: str
    industry: str
    monthly_ad_budget: float
    description: Optional[str] = None
    tone_of_voice: Optional[str] = None
    target_audience: Optional[str] = None
    website_url: Optional[str] = None
    timezone: Optional[str] = None
    preferred_post_timezone: Optional[str] = None


@router.post("/", status_code=201)
async def create_business(
    data: BusinessCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    business = Business(id=uuid.uuid4(), owner_id=current_user.id, **data.model_dump())
    db.add(business)
    await db.commit()
    await db.refresh(business)

    user_result = await db.execute(select(User).where(User.id == current_user.id))
    user = user_result.scalar_one_or_none()
    first_name = (user.full_name or user.email.split("@")[0]).split()[0]

    from email_system.sender import email_sender
    async def send_email_background():
        from database.session import AsyncSessionLocal
        async with AsyncSessionLocal() as new_db:
            await email_sender.send_onboarding_step(
                step=1,
                business_id=str(business.id),
                user_email=user.email,
                first_name=first_name,
                business_name=business.name,
                db=new_db
            )
    asyncio.create_task(send_email_background())

    return {"id": str(business.id), "name": business.name}


@router.get("/")
async def list_businesses(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    businesses = result.scalars().all()
    return [{"id": str(b.id), "name": b.name, "onboarding_completed": b.onboarding_completed} for b in businesses]


# ─── KICKOFF DAY ─────────────────────────────────────────────────────────────

@router.get("/settings/kickoff-day", include_in_schema=False)
async def set_kickoff_day(
    business_id: str,
    day: str,
    db: AsyncSession = Depends(get_db)
):
    """Called when user clicks a kickoff day button in the email."""
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day not in valid_days:
        return HTMLResponse("<h2>Invalid day.</h2>", status_code=400)

    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    biz = biz_result.scalar_one_or_none()
    if not biz:
        return HTMLResponse("<h2>Business not found.</h2>", status_code=404)

    await db.execute(
        sql_update(Business)
        .where(Business.id == business_id)
        .values(briefing_time=day)
    )
    await db.commit()

    return HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="font-family:-apple-system,sans-serif;text-align:center;padding:60px 24px;background:#f9f9f9;">
      <div style="max-width:400px;margin:0 auto;background:#fff;border-radius:16px;padding:40px;border:1px solid #e5e7eb;">
        <div style="font-size:48px;margin-bottom:16px;">✅</div>
        <h2 style="color:#111;margin:0 0 8px 0;">Kickoff day updated!</h2>
        <p style="color:#6b7280;margin:0 0 20px 0;">Your weekly plan will now arrive every <strong style="color:#111;">{day}</strong>.</p>
        <p style="color:#9ca3af;font-size:13px;margin:0;">You can close this tab.</p>
      </div>
    </body></html>
    """)


# ─── POSTING SCHEDULE ────────────────────────────────────────────────────────

@router.get("/settings/posting-schedule", include_in_schema=False)
async def set_posting_schedule(
    business_id: str,
    days: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Called when user toggles posting days in the kickoff email.
    days param is comma-separated: "Monday,Wednesday,Friday"
    """
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_order = {d: i for i, d in enumerate(valid_days)}

    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    biz = biz_result.scalar_one_or_none()
    if not biz:
        return HTMLResponse("<h2>Business not found.</h2>", status_code=404)

    selected = [d.strip() for d in days.split(",") if d.strip() in valid_days]
    if not selected:
        return HTMLResponse("<h2>No valid days selected.</h2>", status_code=400)

    selected = sorted(selected, key=lambda d: day_order[d])

    await db.execute(
        sql_update(Business)
        .where(Business.id == business_id)
        .values(
            posting_schedule=selected,
            posts_per_week=len(selected),
        )
    )
    await db.commit()

    days_display = " · ".join(selected)

    return HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="font-family:-apple-system,sans-serif;text-align:center;padding:60px 24px;background:#f9f9f9;">
      <div style="max-width:400px;margin:0 auto;background:#fff;border-radius:16px;padding:40px;border:1px solid #e5e7eb;">
        <div style="font-size:48px;margin-bottom:16px;">✅</div>
        <h2 style="color:#111;margin:0 0 8px 0;">Posting schedule updated!</h2>
        <p style="color:#6b7280;margin:0 0 8px 0;">Marlo will now post on:</p>
        <p style="color:#111;font-weight:600;font-size:18px;margin:0 0 20px 0;">{days_display}</p>
        <p style="color:#9ca3af;font-size:13px;margin:0;">Changes take effect from your next weekly plan. You can close this tab.</p>
      </div>
    </body></html>
    """)