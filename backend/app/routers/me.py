"""Self-service — preferences, 2FA, sessions, DPDP export/delete (blueprint/14,18,19,09)."""
from __future__ import annotations

from datetime import datetime, timezone

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user
from ..models.platform import UserPreference
from ..models.session import UserSession
from ..models.user import User
from ..services import event_log as ev

router = APIRouter(prefix="/api/me", tags=["me"])


# ---------------- preferences (theme/font/locale override) ----------------
class PrefsIn(BaseModel):
    theme_mode: str | None = None
    theme_preset: str | None = None
    font: str | None = None
    locale: str | None = None


@router.get("/preferences")
async def get_prefs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = await db.get(UserPreference, user.id)
    if not p:
        return {"theme_mode": None, "theme_preset": None, "font": None, "locale": None}
    return {"theme_mode": p.theme_mode, "theme_preset": p.theme_preset, "font": p.font, "locale": p.locale}


@router.put("/preferences")
async def set_prefs(body: PrefsIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = await db.get(UserPreference, user.id)
    if not p:
        p = UserPreference(user_id=user.id)
        db.add(p)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    return {"ok": True}


# ---------------- 2FA (TOTP) ----------------
class TotpVerifyIn(BaseModel):
    code: str


@router.post("/2fa/setup")
async def totp_setup(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = pyotp.random_base32()
    user.totp_secret = secret
    await db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="SwingAI")
    return {"secret": secret, "otpauth_uri": uri}  # show once; user scans into authenticator


@router.post("/2fa/verify")
async def totp_verify(body: TotpVerifyIn, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    if not user.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Run 2FA setup first")
    if not pyotp.TOTP(user.totp_secret).verify(body.code, valid_window=1):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid code")
    user.totp_enabled = True
    await ev.security(db, "auth.2fa.enabled", user=user)
    await db.commit()
    return {"enabled": True}


@router.post("/2fa/disable")
async def totp_disable(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.totp_enabled = False
    user.totp_secret = None
    await ev.security(db, "auth.2fa.disabled", level="warning", user=user)
    await db.commit()
    return {"enabled": False}


# ---------------- sessions ----------------
@router.get("/sessions")
async def my_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(UserSession).where(UserSession.user_id == user.id, UserSession.is_active == True)  # noqa: E712
    )).scalars().all()
    return {"sessions": [
        {"id": str(s.id), "ip": s.ip, "geo": s.geo, "device": s.device,
         "last_active_at": str(s.last_active_at) if s.last_active_at else None} for s in rows
    ]}


@router.post("/logout-all")
async def logout_all(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(UserSession).where(UserSession.user_id == user.id))).scalars().all()
    for s in rows:
        s.is_active = False
        s.revoked_at = datetime.now(timezone.utc)
    await ev.security(db, "session.logout_all", user=user)
    await db.commit()
    return {"revoked": len(rows)}


# ---------------- DPDP: export + delete ----------------
@router.get("/export")
async def export_my_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await ev.emit(db, "data.export.completed", category="data", user=user)
    await db.commit()
    return {"profile": {"email": user.email, "name": user.name,
                        "capital_amount": float(user.capital_amount), "risk_pct": float(user.risk_pct),
                        "subscription_tier": user.subscription_tier}}


@router.delete("")
async def delete_my_account(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await ev.emit(db, "data.deletion.completed", category="data", level="warning", user=user,
                  resource="user", resource_id=user.id)
    await db.delete(user)  # cascades to user-owned rows (blueprint/06 FKs)
    await db.commit()
    return {"deleted": True}
