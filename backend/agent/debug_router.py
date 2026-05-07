"""
debug_router.py
Debug endpoints for testing Marlo's full flow without waiting for scheduled times.
⚠️ REMOVE OR DISABLE BEFORE GOING LIVE WITH REAL USERS.
"""

from fastapi import APIRouter
from database.session import AsyncSessionLocal
from database.models import Business, User, AgentAction, PlatformIntegration
from sqlalchemy import select
import os

router = APIRouter(prefix="/debug", tags=["debug"], include_in_schema=False)

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")


@router.get("/businesses")
async def list_businesses():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Business))
            businesses = result.scalars().all()
            return [{
                "id": str(b.id),
                "name": b.name,
                "industry": b.industry,
                "onboarding_step": b.onboarding_step,
                "onboarding_completed": b.onboarding_completed,
                "subscription_id": b.subscription_id,
                "posting_schedule": b.posting_schedule,
                "posts_per_week": b.posts_per_week,
                "timezone": b.preferred_post_timezone or b.timezone,
            } for b in businesses]
    except Exception as e:
        return {"error": str(e)}


@router.get("/trigger-kickoff/{business_id}")
async def trigger_kickoff(business_id: str):
    try:
        from agent.content_pipeline import content_pipeline
        from agent.google_ads_agent import google_ads_agent
        from agent.strategy_agent import strategy_agent
        from agent.scheduler import get_posting_schedule, build_scheduled_post_time
        from email_system.sender import email_sender
        from database.models import EmailLog
        import uuid as _uuid
        from datetime import datetime, timezone

        async with AsyncSessionLocal() as db:
            biz_result = await db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz:
                return {"error": f"Business {business_id} not found"}

            user_result = await db.execute(select(User).where(User.id == biz.owner_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return {"error": "User not found"}

            first_name = (user.full_name or "").split()[0] or "there"

            integrations_result = await db.execute(
                select(PlatformIntegration).where(
                    PlatformIntegration.business_id == biz.id,
                    PlatformIntegration.is_active == True
                )
            )
            integrations = integrations_result.scalars().all()
            connected  = [p.platform for p in integrations]
            has_google = "google" in connected
            platforms  = ["instagram"]

            business_dict = {
                "name": biz.name,
                "industry": biz.industry or "",
                "description": biz.description or "",
                "tone_of_voice": biz.tone_of_voice or "warm and authentic",
                "target_audience": biz.target_audience or "local customers",
                "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
            }

            posting_schedule = get_posting_schedule(biz)
            posts_count = len(posting_schedule)

            try:
                strategy = await strategy_agent.decide(
                    "weekly_content", {"business": business_dict}, business_id
                )
                # Only use key_message — avoids internal prompt language leaking to users
                strategy_summary = strategy.get("key_message", f"Building authentic content for {biz.name}.")
            except Exception:
                strategy = {}
                strategy_summary = f"Building authentic content for {biz.name}."

            posts = await content_pipeline.generate_week_of_content(
                business_id=business_id,
                db=db,
                platforms=platforms,
            )
            while len(posts) < posts_count:
                posts.append(posts[-1].copy() if posts else {})
            posts = posts[:posts_count]
            for i, post in enumerate(posts):
                post["scheduled_day"] = posting_schedule[i]

            google_campaign = None
            if has_google:
                try:
                    ads_strategy = await strategy_agent.decide(
                        "google_ads", {"business": business_dict}, business_id
                    )
                    google_campaign = await google_ads_agent.generate_campaign(
                        business=business_dict,
                        strategy=ads_strategy,
                        business_id=business_id,
                    )
                except Exception as e:
                    print(f"[Debug] Google Ads error: {e}")

            stored_actions = []
            for post in posts:
                action = AgentAction(
                    id=_uuid.uuid4(),
                    business_id=biz.id,
                    action_type=f"post_{post.get('platform', 'instagram')}",
                    action_parameters=post,
                    approval_token=str(_uuid.uuid4()),
                    decline_token=str(_uuid.uuid4()),
                    status="pending",
                    requires_approval=True,
                    scheduled_post_time=build_scheduled_post_time(biz, post["scheduled_day"]),
                    scheduled_day=post["scheduled_day"],
                    approval_email_sent=False,
                    created_at=datetime.utcnow(),
                )
                db.add(action)
                stored_actions.append(action)

            ads_stored = None
            if google_campaign:
                ads_stored = AgentAction(
                    id=_uuid.uuid4(),
                    business_id=biz.id,
                    action_type="google_ads_campaign",
                    action_parameters=google_campaign,
                    approval_token=str(_uuid.uuid4()),
                    decline_token=str(_uuid.uuid4()),
                    status="pending",
                    requires_approval=True,
                    scheduled_post_time=datetime.now(timezone.utc),
                    scheduled_day=posting_schedule[0],
                    approval_email_sent=False,
                    created_at=datetime.utcnow(),
                )
                db.add(ads_stored)

            await db.commit()

            visual = strategy.get("visual_direction", "") if isinstance(strategy, dict) else ""
            image_guide = [{
                "day": posting_schedule[i],
                "description": visual or f"A photo showing {biz.name} in action — real photos always outperform AI-generated ones.",
            } for i in range(posts_count)]

            first_day = posting_schedule[0]
            first_action = next(
                (a for a in stored_actions if a.scheduled_day == first_day),
                stored_actions[0] if stored_actions else None
            )

            if not first_action:
                return {"error": "No posts generated"}

            kickoff_check = await db.execute(
                select(EmailLog).where(
                    EmailLog.business_id == biz.id,
                    EmailLog.email_type == "first_kickoff",
                )
            )
            is_first_kickoff = kickoff_check.scalar_one_or_none() is None

            if is_first_kickoff:
                await email_sender.send_first_kickoff(
                    business_id=business_id,
                    user_email=user.email,
                    first_name=first_name,
                    business_name=biz.name,
                    first_post=first_action.action_parameters,
                    first_post_day=first_day,
                    first_approve_token=first_action.approval_token,
                    first_decline_token=first_action.decline_token,
                    google_campaign=google_campaign,
                    ads_approve_token=ads_stored.approval_token if ads_stored else None,
                    ads_decline_token=ads_stored.decline_token if ads_stored else None,
                    posting_schedule=posting_schedule,
                    strategy_summary=strategy_summary,
                    image_guide=image_guide,
                    db=db,
                )
                email_type_sent = "first_kickoff"
            else:
                await email_sender.send_weekly_kickoff(
                    business_id=business_id,
                    user_email=user.email,
                    first_name=first_name,
                    business_name=biz.name,
                    first_post=first_action.action_parameters,
                    first_post_day=first_day,
                    first_approve_token=first_action.approval_token,
                    first_decline_token=first_action.decline_token,
                    google_campaign=google_campaign,
                    ads_approve_token=ads_stored.approval_token if ads_stored else None,
                    ads_decline_token=ads_stored.decline_token if ads_stored else None,
                    posting_schedule=posting_schedule,
                    strategy_summary=strategy_summary,
                    image_guide=image_guide,
                    last_week_stats={"approved": 0, "skipped": 0, "expired": 0},
                    db=db,
                )
                email_type_sent = "weekly_kickoff"

            first_action.approval_email_sent = True
            if ads_stored:
                ads_stored.approval_email_sent = True
            await db.commit()

            return {
                "status": "success",
                "email_sent": email_type_sent,
                "business": biz.name,
                "posts_generated": posts_count,
                "posting_schedule": posting_schedule,
                "first_post_day": first_day,
                "has_google_campaign": google_campaign is not None,
            }

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/resend-kickoff/{business_id}")
async def resend_kickoff(business_id: str):
    try:
        from agent.scheduler import get_posting_schedule
        from agent.strategy_agent import strategy_agent
        from email_system.sender import email_sender

        async with AsyncSessionLocal() as db:
            biz_result = await db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz:
                return {"error": "Business not found"}

            user_result = await db.execute(select(User).where(User.id == biz.owner_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return {"error": "User not found"}

            posting_schedule = get_posting_schedule(biz)
            first_day = posting_schedule[0]
            first_name = (user.full_name or "").split()[0] or "there"

            first_action_result = await db.execute(
                select(AgentAction).where(
                    AgentAction.business_id == biz.id,
                    AgentAction.scheduled_day == first_day,
                    AgentAction.action_type != "google_ads_campaign",
                    AgentAction.status == "pending",
                ).order_by(AgentAction.created_at.desc())
            )
            first_action = first_action_result.scalars().first()
            if not first_action:
                return {"error": f"No pending {first_day} post found — run /debug/trigger-kickoff first"}

            ads_result = await db.execute(
                select(AgentAction).where(
                    AgentAction.business_id == biz.id,
                    AgentAction.action_type == "google_ads_campaign",
                    AgentAction.status == "pending",
                ).order_by(AgentAction.created_at.desc())
            )
            ads_action = ads_result.scalars().first()

            business_dict = {
                "name": biz.name, "industry": biz.industry or "",
                "description": biz.description or "",
                "tone_of_voice": biz.tone_of_voice or "warm and authentic",
                "target_audience": biz.target_audience or "local customers",
                "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
            }

            try:
                strategy = await strategy_agent.decide(
                    "weekly_content", {"business": business_dict}, business_id
                )
                strategy_summary = strategy.get("key_message", f"Building authentic content for {biz.name}.")
            except Exception:
                strategy = {}
                strategy_summary = f"Building authentic content for {biz.name}."

            visual = strategy.get("visual_direction", "") if isinstance(strategy, dict) else ""
            image_guide = [{
                "day": d,
                "description": visual or f"A photo showing {biz.name} in action.",
            } for d in posting_schedule]

            await email_sender.send_first_kickoff(
                business_id=business_id,
                user_email=user.email,
                first_name=first_name,
                business_name=biz.name,
                first_post=first_action.action_parameters or {},
                first_post_day=first_day,
                first_approve_token=first_action.approval_token,
                first_decline_token=first_action.decline_token,
                google_campaign=ads_action.action_parameters if ads_action else None,
                ads_approve_token=ads_action.approval_token if ads_action else None,
                ads_decline_token=ads_action.decline_token if ads_action else None,
                posting_schedule=posting_schedule,
                strategy_summary=strategy_summary,
                image_guide=image_guide,
                db=db,
            )

            return {"status": "success", "email_sent": "first_kickoff", "to": user.email}

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/trigger-analytics/{business_id}")
async def trigger_analytics(business_id: str):
    try:
        from agent.analytics_agent import analytics_agent
        from email_system.sender import email_sender

        async with AsyncSessionLocal() as db:
            biz_result = await db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz:
                return {"error": "Business not found"}

            user_result = await db.execute(select(User).where(User.id == biz.owner_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return {"error": "User not found"}

            first_name = (user.full_name or "").split()[0] or "there"
            insights = await analytics_agent.generate_weekly_insights(business_id=business_id, db=db)

            await email_sender.send_weekly_analytics(
                business_id=business_id,
                user_email=user.email,
                first_name=first_name,
                business_name=biz.name,
                insights=insights,
                db=db,
            )

            return {
                "status": "success",
                "email_sent": "weekly_analytics",
                "to": user.email,
                "headline_metric": insights.get("headline_metric"),
            }

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/test-post/{business_id}")
async def test_instagram_post(business_id: str):
    try:
        from agent.executor import executor

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentAction).where(
                    AgentAction.business_id == business_id,
                    AgentAction.action_type == "post_instagram",
                    AgentAction.status == "pending",
                ).order_by(AgentAction.created_at.desc())
            )
            action = result.scalars().first()

            if not action:
                return {"error": "No pending Instagram post found — run /debug/trigger-kickoff first"}

            result = await executor.run(action, db)
            return {
                "status": "attempted",
                "result": result,
                "action_id": str(action.id),
                "scheduled_day": action.scheduled_day,
                "caption_preview": (action.action_parameters or {}).get("caption", "")[:100],
            }

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/actions/{business_id}")
async def list_actions(business_id: str):
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentAction).where(
                    AgentAction.business_id == business_id,
                ).order_by(AgentAction.created_at.desc())
            )
            actions = result.scalars().all()
            return [{
                "id": str(a.id),
                "action_type": a.action_type,
                "status": a.status,
                "scheduled_day": a.scheduled_day,
                "scheduled_post_time": str(a.scheduled_post_time) if a.scheduled_post_time else None,
                "approval_email_sent": a.approval_email_sent,
                "approve_url": f"{BASE_URL}/actions/approve?token={a.approval_token}",
                "decline_url": f"{BASE_URL}/actions/decline?token={a.decline_token}",
                "caption_preview": (a.action_parameters or {}).get("caption", "")[:80],
                "created_at": str(a.created_at),
            } for a in actions]
    except Exception as e:
        return {"error": str(e)}


@router.get("/send-approval/{business_id}/{day}")
async def send_approval_email(business_id: str, day: str):
    try:
        from email_system.sender import email_sender

        async with AsyncSessionLocal() as db:
            biz_result = await db.execute(select(Business).where(Business.id == business_id))
            biz = biz_result.scalar_one_or_none()
            if not biz:
                return {"error": "Business not found"}

            user_result = await db.execute(select(User).where(User.id == biz.owner_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return {"error": "User not found"}

            action_result = await db.execute(
                select(AgentAction).where(
                    AgentAction.business_id == business_id,
                    AgentAction.scheduled_day == day,
                    AgentAction.status == "pending",
                ).order_by(AgentAction.created_at.desc())
            )
            action = action_result.scalars().first()
            if not action:
                return {"error": f"No pending {day} post found"}

            first_name = (user.full_name or "").split()[0] or "there"
            await email_sender.send_post_approval(
                business_id=business_id,
                user_email=user.email,
                first_name=first_name,
                business_name=biz.name,
                post=action.action_parameters or {},
                scheduled_day=day,
                approve_token=action.approval_token,
                decline_token=action.decline_token,
                db=db,
            )
            action.approval_email_sent = True
            await db.commit()

            return {"status": "success", "email_sent": f"post_approval_{day.lower()}", "to": user.email}

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.delete("/reset/{business_id}")
async def reset_business(business_id: str):
    try:
        from sqlalchemy import delete
        from database.models import EmailLog

        async with AsyncSessionLocal() as db:
            deleted_actions = await db.execute(
                delete(AgentAction).where(AgentAction.business_id == business_id)
            )
            deleted_logs = await db.execute(
                delete(EmailLog).where(EmailLog.business_id == business_id)
            )
            await db.commit()

            return {
                "status": "reset complete",
                "actions_deleted": deleted_actions.rowcount,
                "email_logs_deleted": deleted_logs.rowcount,
            }

    except Exception as e:
        return {"error": str(e)}