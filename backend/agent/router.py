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