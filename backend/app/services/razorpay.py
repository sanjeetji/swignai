"""Razorpay payments (blueprint/20) — order creation + signature verification.

Creds resolve vault (Integrations tab) → .env, like every other integration. Uses the
REST API directly (basic auth) + HMAC verification — no SDK dependency. All amounts in
paise on the wire (₹1 = 100 paise).
"""
from __future__ import annotations

import hashlib
import hmac

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from .integrations import secret_for, vault

_ORDERS_URL = "https://api.razorpay.com/v1/orders"


async def creds(db: AsyncSession | None) -> tuple[str | None, str | None, str | None]:
    """(key_id, key_secret, webhook_secret) — vault overrides .env."""
    _, cfg = await vault(db, "razorpay")
    key_id = cfg.get("key_id") or settings.RAZORPAY_KEY_ID
    key_secret = await secret_for(db, "razorpay", settings.RAZORPAY_KEY_SECRET)
    webhook_secret = cfg.get("webhook_secret") or settings.RAZORPAY_WEBHOOK_SECRET
    return key_id, key_secret, webhook_secret


def configured() -> bool:
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


async def create_order(db, amount_inr: float, receipt: str) -> dict:
    key_id, key_secret, _ = await creds(db)
    if not (key_id and key_secret):
        raise RuntimeError("Razorpay not configured — set RAZORPAY_KEY_ID/SECRET or the Integrations vault")
    import requests
    r = requests.post(
        _ORDERS_URL, auth=(key_id, key_secret),
        json={"amount": int(round(amount_inr * 100)), "currency": "INR", "receipt": receipt,
              "payment_capture": 1},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def _sign(message: str, secret: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_payment(order_id: str, payment_id: str, signature: str, key_secret: str) -> bool:
    """Razorpay Checkout signature: HMAC_SHA256(order_id|payment_id, key_secret)."""
    expected = _sign(f"{order_id}|{payment_id}", key_secret)
    return hmac.compare_digest(expected, signature or "")


def verify_webhook(raw_body: bytes, signature: str, webhook_secret: str) -> bool:
    expected = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
