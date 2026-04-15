from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    description: str
    tone_of_voice: str
    target_audience: str
    monthly_ad_budget: float
    website_url: Optional[str] = None

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

    # Get user details for onboarding email
    user_result = await db.execute(select(User).where(User.id == current_user.id))
    user = user_result.scalar_one_or_none()
    first_name = (user.full_name or user.email.split("@")[0]).split()[0]

    # Send onboarding email 1 in the background
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

    return {"business_id": str(business.id), "name": business.name}

@router.get("/")
async def list_businesses(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    businesses = result.scalars().all()
    return [{"id": str(b.id), "name": b.name, "onboarding_completed": b.onboarding_completed} for b in businesses]