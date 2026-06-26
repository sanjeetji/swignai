"""Billing (blueprint/20) — Razorpay subscriptions. Plans → order → verify → activate.

Flow: client GETs /plans, POSTs /create-order (server makes a Razorpay order), opens
Razorpay Checkout, then POSTs /verify with the signed result; we verify the HMAC, record
the Payment, and activate the Subscription + user tier. A webhook is the safety net.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user
from ..models.billing import Payment, Subscription
from ..models.user import User
from ..schemas import CreateOrderIn, VerifyPaymentIn
from ..services import event_log as ev
from ..services import razorpay

router = APIRouter(prefix="/api/billing", tags=["billing"])

PLANS = {
    "pro": {"name": "Pro", "price_inr": 499,
            "features": ["Daily picks + full scanner", "Paper trading + journal", "Personal analytics & alerts"]},
    "premium": {"name": "Premium", "price_inr": 999,
                "features": ["Everything in Pro", "Priority data refresh", "Early access to new features"]},
}


@router.get("/plans")
async def plans():
    return {"plans": [{"id": k, **v} for k, v in PLANS.items()], "currency": "INR",
            "enabled": razorpay.configured()}


@router.get("/subscription")
async def my_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = (await db.execute(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
    )).scalars().first()
    return {"tier": user.subscription_tier,
            "status": sub.status if sub else "none",
            "current_period_end": str(sub.current_period_end) if sub and sub.current_period_end else None}


@router.post("/create-order")
async def create_order(body: CreateOrderIn, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    plan = PLANS.get(body.plan)
    if not plan:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown plan")
    key_id, _, _ = await razorpay.creds(db)
    try:
        order = await razorpay.create_order(db, plan["price_inr"], receipt=f"{body.plan}:{user.id}")
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Payment gateway error: {str(e)[:120]}")
    return {"order_id": order["id"], "amount": order["amount"], "currency": order["currency"],
            "key_id": key_id, "plan": body.plan, "name": "SwingAI", "prefill_email": user.email}


@router.post("/verify")
async def verify(body: VerifyPaymentIn, user: User = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    plan = PLANS.get(body.plan)
    if not plan:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown plan")
    _, key_secret, _ = await razorpay.creds(db)
    if not key_secret or not razorpay.verify_payment(
            body.razorpay_order_id, body.razorpay_payment_id, body.razorpay_signature, key_secret):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment signature verification failed")

    db.add(Payment(user_id=user.id, amount_inr=plan["price_inr"], status="captured",
                   razorpay_payment_id=body.razorpay_payment_id))
    sub = (await db.execute(select(Subscription).where(Subscription.user_id == user.id))).scalars().first()
    if sub is None:
        sub = Subscription(user_id=user.id)
        db.add(sub)
    sub.plan = body.plan
    sub.status = "active"
    sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
    user.subscription_tier = body.plan
    await ev.emit(db, "billing.subscription.activated", category="billing", user=user,
                  payload={"plan": body.plan, "amount": plan["price_inr"]})
    await db.commit()
    return {"ok": True, "tier": body.plan, "current_period_end": str(sub.current_period_end)}


@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Razorpay webhook — verifies the signature (safety net for missed client confirmations)."""
    raw = await request.body()
    _, _, webhook_secret = await razorpay.creds(db)
    sig = request.headers.get("x-razorpay-signature", "")
    if not webhook_secret or not razorpay.verify_webhook(raw, sig, webhook_secret):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature")
    await ev.emit(db, "billing.webhook.received", category="billing", source="webhook")
    await db.commit()
    return {"ok": True}
