"""
stripe_client.py
Stripe API wrapper for Marlo021 billing.
Handles: customer creation, subscription with trial, cancellation, webhooks.
"""
import stripe
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
TRIAL_DAYS = 14


class StripeClient:

    async def create_customer_and_subscription(
        self,
        email: str,
        full_name: str,
        payment_method_id: str,
        business_id: str
    ) -> dict:
        """
        Create a Stripe customer, attach payment method, and start a
        subscription with a 14-day trial.
        Returns: { customer_id, subscription_id, status }
        """
        # 1. Create customer
        customer = stripe.Customer.create(
            email=email,
            name=full_name,
            payment_method=payment_method_id,
            invoice_settings={"default_payment_method": payment_method_id},
            metadata={"business_id": business_id}
        )

        # 2. Create subscription with trial
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": PRICE_ID}],
            trial_period_days=TRIAL_DAYS,
            payment_settings={
                "payment_method_types": ["card"],
                "save_default_payment_method": "on_subscription"
            },
            expand=["latest_invoice.payment_intent"],
            metadata={"business_id": business_id}
        )

        return {
            "customer_id": customer.id,
            "subscription_id": subscription.id,
            "status": subscription.status,  # "trialing"
            "trial_end": subscription.trial_end,
        }

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """
        Cancel a subscription at period end (user keeps access until billing period ends).
        """
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "cancel_at": subscription.cancel_at,
        }

    async def cancel_subscription_immediately(self, subscription_id: str) -> dict:
        """Cancel a subscription immediately (for admin use)."""
        subscription = stripe.Subscription.delete(subscription_id)
        return {"subscription_id": subscription.id, "status": subscription.status}

    async def get_subscription(self, subscription_id: str) -> dict:
        """Get subscription details."""
        sub = stripe.Subscription.retrieve(subscription_id)
        return {
            "id": sub.id,
            "status": sub.status,
            "trial_end": sub.trial_end,
            "current_period_end": sub.current_period_end,
            "cancel_at_period_end": sub.cancel_at_period_end,
        }

    def construct_webhook_event(self, payload: bytes, sig_header: str) -> object:
        """Verify and construct a Stripe webhook event."""
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)


stripe_client = StripeClient()