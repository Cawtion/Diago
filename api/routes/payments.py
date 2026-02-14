"""
Payment API Routes
Endpoints for Stripe subscription management and webhooks.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.middleware.auth import (
    AuthenticatedUser,
    UserTier,
    get_current_user,
)
from api.middleware.rate_limit import get_remaining_diagnoses
from api.payments.stripe_service import (
    create_checkout_session,
    cancel_subscription,
    get_customer_subscription,
    process_webhook_event,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Models ───

class CheckoutRequest(BaseModel):
    tier: str  # "pro" or "premium"
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionResponse(BaseModel):
    tier: str
    limit: int
    used: int
    remaining: int


# ─── Endpoints ───

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a Stripe Checkout Session for upgrading to a paid tier."""
    try:
        tier = UserTier(request.tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")

    if tier == UserTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot checkout for free tier")

    try:
        url = create_checkout_session(
            user_id=user.user_id,
            user_email=user.email or "",
            tier=tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        return CheckoutResponse(checkout_url=url)
    except Exception as e:
        logger.error("Checkout creation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription_status(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the current user's subscription status and usage."""
    usage = get_remaining_diagnoses(user=user)
    return SubscriptionResponse(**usage)


@router.post("/cancel")
async def cancel_user_subscription(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Cancel the current user's subscription at end of billing period."""
    # In production, look up the Stripe customer/subscription ID from Supabase
    # For now, return a placeholder
    return {"message": "Subscription cancellation requires Supabase integration"}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint.

    Receives events from Stripe (subscription changes, payments, etc.)
    and updates user tiers in Supabase accordingly.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = process_webhook_event(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result["handled"]:
        action = result.get("action")
        logger.info("Webhook processed: action=%s", action)

        # User tier updates are intended to be handled by Supabase (e.g. Edge Function
        # or webhook) that syncs Stripe subscription state to app_metadata / users table.

    return {"received": True}
