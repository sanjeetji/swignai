"""Subscription tier gating (blueprint/20).

`effective_tier` derives the user's live entitlement from their latest Subscription
(honouring trial/active status + expiry) — not the static user.subscription_tier, so
access lapses automatically when a period ends. `require_tier` is a route dependency that
402s when the plan is too low. A trial grants full (premium-level) access while it lasts.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
    if await _is_admin(db, user):
        return "premium"                    # admins always get full (top-tier) access
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
        if await _is_admin(db, user):
            return user                     # admins bypass every tier gate
        t = await effective_tier(db, user)
        if rank(t) < rank(min_tier):
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                                f"This feature needs the {min_tier.title()} plan. Upgrade in Billing.")
        return user
    return _dep


PAID_GRACE_DAYS = 3   # a lapsed PAID plan stays usable this long (failed-renewal cushion)


async def access_state(db: AsyncSession, user) -> dict:
    """The user's access decision (industry paywall):
      - Free plan (or never subscribed) → permanent basic access (not walled).
      - Trial → full access until it ends; the moment it ends → WALLED.
      - Paid → full access until period end; then a PAID_GRACE_DAYS grace; after that → WALLED.
    Returns {tier, state, walled, days_left, reason}. Admins always have full access.
    """
    if await _is_admin(db, user):
        return {"tier": "premium", "state": "admin", "walled": False, "days_left": None, "reason": None}
    sub = (await db.execute(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
    )).scalars().first()
    now = datetime.now(timezone.utc)
    if not sub:
        # No plan chosen yet → must pick one (the wall offers Free as a one-click option).
        return {"tier": "free", "state": "none", "walled": True, "days_left": None, "reason": "no_plan"}

    end = sub.current_period_end
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    days_until = (end - now).days + 1 if end else None

    if sub.status == "trialing":
        if end is not None and end < now:
            return {"tier": "free", "state": "expired", "walled": True, "days_left": 0, "reason": "trial_ended"}
        return {"tier": "trial", "state": "active", "walled": False, "days_left": days_until, "reason": None}

    if sub.status == "active":
        if sub.plan == "free" or end is None:
            tier = "free" if sub.plan == "free" else sub.plan
            return {"tier": tier, "state": "free" if tier == "free" else "active",
                    "walled": False, "days_left": None, "reason": None}
        if end < now:
            grace_end = end + timedelta(days=PAID_GRACE_DAYS)
            if now < grace_end:
                return {"tier": sub.plan, "state": "grace", "walled": False,
                        "days_left": (grace_end - now).days + 1, "reason": "renewal_due"}
            return {"tier": "free", "state": "expired", "walled": True, "days_left": 0, "reason": "plan_lapsed"}
        return {"tier": sub.plan, "state": "active", "walled": False, "days_left": days_until, "reason": None}

    # canceled / past_due / unknown → no access
    return {"tier": "free", "state": "expired", "walled": True, "days_left": 0, "reason": sub.status}


async def _is_admin(db: AsyncSession, user) -> bool:
    from .rbac import user_roles
    return any(r in ("super_admin", "admin") for r in await user_roles(db, user))


def require_access():
    """Dependency: 402 'subscription_required' when the user is walled (lapsed trial/paid).
    Admins always pass. Use on the authed dashboard data endpoints."""
    async def _dep(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if await _is_admin(db, user):
            return user
        st = await access_state(db, user)
        if st["walled"]:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                                "subscription_required: your plan has ended — choose a plan to continue.")
        return user
    return _dep
