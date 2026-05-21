"""
billing_router.py
Handles:
- POST /billing/subscribe       — create subscription after signup
- POST /billing/webhook         — Stripe webhook events
- GET  /billing/status          — get subscription status
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.session import get_db
from database.models import Business, User
from billing.stripe_client import stripe_client
import os, uuid
from datetime import datetime

router = APIRouter(prefix="/billing", tags=["billing"])


def _get(obj, key, default=None):
    """
    Safe getter that works for both Stripe SDK objects and plain dicts.
    Stripe's new SDK returns objects where .get() doesn't work like dicts.
    """
    try:
        if hasattr(obj, key):
            return getattr(obj, key, default)
        if hasattr(obj, '__getitem__'):
            try:
                return obj[key]
            except (KeyError, TypeError):
                return default
        return default
    except Exception:
        return default


def _get_nested(obj, *keys, default=None):
    """Safe nested getter for Stripe objects."""
    current = obj
    for key in keys:
        current = _get(current, key)
        if current is None:
            return default
    return current if current is not None else default


@router.post("/subscribe")
async def create_subscription(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    business_id = body.get("business_id")
    payment_method_id = body.get("payment_method_id")

    if not business_id or not payment_method_id:
        raise HTTPException(status_code=400, detail="Missing business_id or payment_method_id")

    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    business = biz_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    user_result = await db.execute(select(User).where(User.id == business.owner_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = await stripe_client.create_customer_and_subscription(
            email=user.email,
            full_name=user.full_name or user.email,
            payment_method_id=payment_method_id,
            business_id=str(business_id)
        )

        await db.execute(
            update(User)
            .where(User.id == business.owner_id)
            .values(stripe_customer_id=result["customer_id"])
        )
        await db.execute(
            update(Business)
            .where(Business.id == business_id)
            .values(subscription_id=result["subscription_id"])
        )
        await db.commit()

        return {
            "success": True,
            "subscription_id": result["subscription_id"],
            "status": result["status"],
            "trial_end": result["trial_end"],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_client.construct_webhook_event(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    event_type = _get(event, "type")
    data = _get_nested(event, "data", "object")

    if event_type == "customer.subscription.trial_will_end":
        await handle_trial_ending(data, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_cancelled(data, db)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(data, db)
    elif event_type == "invoice.payment_succeeded":
        await handle_payment_succeeded(data, db)

    return {"received": True}


@router.get("/status")
async def get_billing_status(business_id: str, db: AsyncSession = Depends(get_db)):
    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    business = biz_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not hasattr(business, 'subscription_id') or not business.subscription_id:
        return {"status": "no_subscription"}

    try:
        sub = await stripe_client.get_subscription(business.subscription_id)
        return sub
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ── Webhook handlers ──────────────────────────────────────────────────────────

async def handle_trial_ending(subscription, db: AsyncSession):
    business_id = _get_nested(subscription, "metadata", "business_id")
    if not business_id:
        print("[Billing] handle_trial_ending: no business_id in metadata")
        return

    biz_result = await db.execute(select(Business).where(Business.id == business_id))
    business = biz_result.scalar_one_or_none()
    if not business:
        return

    user_result = await db.execute(select(User).where(User.id == business.owner_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return

    from email_system.sender import email_sender
    from email_system.templates import base_template

    trial_end_ts = _get(subscription, "trial_end") or 0
    trial_end_date = datetime.utcfromtimestamp(trial_end_ts).strftime("%B %d, %Y") if trial_end_ts else "in 3 days"
    first_name = (user.full_name or "there").split()[0]

    html = base_template(f"""
    <p style="font-size:16px;font-weight:600;color:#1F2937;margin:0 0 8px 0;">
      ⏰ Your free trial ends {trial_end_date}, {first_name}
    </p>
    <p style="font-size:14px;color:#6B7280;margin:0 0 20px 0;line-height:1.7;">
      Your 14-day free trial of Marlo021 is almost over. On {trial_end_date},
      your card will be charged <strong>$99/month</strong> and your subscription continues automatically.
    </p>
    <div style="background:#F0FDF4;border-radius:8px;padding:16px 20px;margin-bottom:20px;">
      <p style="font-size:14px;color:#15803D;margin:0;line-height:1.7;">
        ✓ Your posts, campaigns, and settings are all saved<br>
        ✓ Marlo will keep running your marketing every day<br>
        ✓ You can cancel anytime before {trial_end_date} to avoid being charged
      </p>
    </div>
    <p style="font-size:14px;color:#6B7280;margin:0 0 16px 0;line-height:1.7;">
      To cancel, reply to this email with:
    </p>
    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:16px;margin-bottom:20px;">
      <p style="font-size:15px;font-weight:600;color:#1F2937;margin:0;font-family:monospace;">
        Cancel my Marlo021 subscription
      </p>
    </div>
    <p style="font-size:13px;color:#9CA3AF;margin:0;line-height:1.6;">
      Otherwise no action needed — your marketing keeps running.
    </p>
    """)

    await email_sender.send(
        to_email=user.email,
        subject=f"Your Marlo021 trial ends {trial_end_date} — what happens next",
        html_body=html,
        email_type="trial_ending",
        business_id=str(business.id),
        db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai"
    )
    print(f"[Billing] Trial ending email sent to {user.email}")


async def handle_subscription_cancelled(subscription, db: AsyncSession):
    business_id = _get_nested(subscription, "metadata", "business_id")
    if not business_id:
        print("[Billing] handle_subscription_cancelled: no business_id in metadata")
        return

    await db.execute(
        update(Business)
        .where(Business.id == business_id)
        .values(subscription_id=None)
    )
    await db.commit()
    print(f"[Billing] Subscription cancelled for business {business_id}")


async def handle_payment_failed(invoice, db: AsyncSession):
    # Use _get() not .get() — Stripe SDK objects don't support .get()
    customer_id = _get(invoice, "customer")
    if not customer_id:
        return

    user_result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return

    biz_result = await db.execute(select(Business).where(Business.owner_id == user.id))
    business = biz_result.scalar_one_or_none()

    from email_system.sender import email_sender
    from email_system.templates import base_template

    first_name = (user.full_name or "there").split()[0]

    html = base_template(f"""
    <p style="font-size:16px;font-weight:600;color:#DC2626;margin:0 0 8px 0;">
      ⚠️ Payment failed, {first_name}
    </p>
    <p style="font-size:14px;color:#6B7280;margin:0 0 16px 0;line-height:1.7;">
      We couldn't charge your card for your Marlo021 subscription.
      Please update your payment method to keep your marketing running.
    </p>
    <p style="font-size:14px;color:#6B7280;margin:0;line-height:1.7;">
      Reply to this email and we'll help you sort it out.
    </p>
    """)

    await email_sender.send(
        to_email=user.email,
        subject="Action required: Marlo021 payment failed",
        html_body=html,
        email_type="payment_failed",
        business_id=str(business.id) if business else None,
        db=db,
        reply_to=f"reply+{business.id}@reply.marlo021.ai" if business else None
    )
    print(f"[Billing] Payment failed email sent to {user.email}")


async def handle_payment_succeeded(invoice, db: AsyncSession):
    # Use _get() not .get() — Stripe SDK objects don't support .get()
    customer_id = _get(invoice, "customer")
    if not customer_id:
        return

    user_result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(subscription_tier="active")
    )
    await db.commit()
    print(f"[Billing] Payment succeeded for {user.email}")