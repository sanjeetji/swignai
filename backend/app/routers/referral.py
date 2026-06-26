"""Referrals (blueprint/14 growth) — your shareable code + who you've referred."""
from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user
from ..models.referral import Referral, ReferralCode
from ..models.user import User

router = APIRouter(prefix="/api/me/referral", tags=["referral"])

_ALPHABET = string.ascii_uppercase + string.digits


async def ensure_code(db: AsyncSession, user: User) -> str:
    """Return the user's referral code, allocating a unique one on first request."""
    rc = await db.get(ReferralCode, user.id)
    if rc:
        return rc.code
    for _ in range(12):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(8))
        exists = (await db.execute(select(ReferralCode).where(ReferralCode.code == code))).scalar_one_or_none()
        if not exists:
            db.add(ReferralCode(user_id=user.id, code=code))
            await db.commit()
            return code
    raise RuntimeError("could not allocate referral code")


async def apply_referral(db: AsyncSession, code: str | None, new_user: User) -> None:
    """Record that `new_user` was referred via `code` (no-op if missing/invalid/self)."""
    if not code:
        return
    rc = (await db.execute(select(ReferralCode).where(ReferralCode.code == code.upper().strip()))).scalar_one_or_none()
    if not rc or rc.user_id == new_user.id:
        return
    db.add(Referral(referrer_user_id=rc.user_id, referred_user_id=new_user.id,
                    code=rc.code, joined_at=datetime.now(timezone.utc)))


def _mask(email: str) -> str:
    name, _, domain = email.partition("@")
    return f"{name[:3]}***@{domain}" if domain else "—"


@router.get("")
async def my_referral(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    code = await ensure_code(db, user)
    rows = (await db.execute(
        select(Referral).where(Referral.referrer_user_id == user.id).order_by(Referral.created_at.desc())
    )).scalars().all()
    referred = []
    for r in rows:
        u = await db.get(User, r.referred_user_id)
        referred.append({"email": _mask(u.email) if u else "—", "at": str(r.created_at)[:10]})
    return {"code": code, "count": len(rows), "referred": referred}
