"""Subscription tier gating (blueprint/20).

`effective_tier` derives the user's live entitlement from their latest Subscription
(honouring trial/active status + expiry) — not the static user.subscription_tier, so
access lapses automatically when a period ends. `require_tier` is a route dependency that
402s when the plan is too low. A trial grants full (premium-level) access while it lasts.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user
from ..models.billing import Subscription

# higher = more access. trial == premium-level while active.
TIER_RANK = {"free": 0, "pro": 1, "premium": 2, "trial": 2}


def rank(tier: str) -> int:
    return TIER_RANK.get(tier, 0)


async def effective_tier(db: AsyncSession, user) -> str:
    sub = (await db.execute(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
    )).scalars().first()
    if not sub:
        return "free"
    end = sub.current_period_end
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end is not None and end < datetime.now(timezone.utc):
        return "free"                       # period lapsed
    if sub.status == "trialing":
        return "trial"
    if sub.status == "active":
        return sub.plan
    return "free"


def require_tier(min_tier: str):
    """Dependency: 402 unless the user's effective tier ≥ min_tier."""
    async def _dep(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        t = await effective_tier(db, user)
        if rank(t) < rank(min_tier):
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                                f"This feature needs the {min_tier.title()} plan. Upgrade in Billing.")
        return user
    return _dep
