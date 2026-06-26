"""Auth — register / login / refresh / logout / forgot-reset password, with event-log,
login-history and sessions (blueprint/18,19). JWT access + refresh, refresh bound to a
session (sid) so logout/force-logout revoke it."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.clientinfo import build_client_context
from ..core.config import settings
from ..core.db import get_db
from ..core.security import (create_access_token, create_refresh_token, decode_token,
                             get_current_user, hash_password, oauth2_scheme, verify_password)
from ..models.session import LoginHistory, UserSession
from ..models.user import PasswordResetToken, Role, User, UserRole
from ..schemas import (ForgotPasswordIn, LoginIn, RefreshIn, RegisterIn, ResetPasswordIn,
                       TokenOut, UserOut)
from ..services import event_log as ev
from ..services.email import dev_mode, send_email
from ..services.rbac import user_permissions, user_roles

router = APIRouter(prefix="/api/auth", tags=["auth"])

RESET_TTL_MIN = 60


def _client_ip(req: Request) -> str | None:
    return req.client.host if req.client else None


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def _open_session(db: AsyncSession, user: User, ctx: dict) -> UserSession:
    """Create an active session row (geo + device); its id (sid) binds the access+refresh JWTs.
    The session lives as long as the refresh token, so a valid refresh keeps the user signed in."""
    now = datetime.now(timezone.utc)
    sess = UserSession(
        user_id=user.id, ip=ctx.get("ip"), geo=ctx.get("geo") or {},
        device=ctx.get("device"), browser=ctx.get("browser"), os=ctx.get("os"),
        last_active_at=now, is_active=True,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
    )
    db.add(sess)
    await db.flush()  # populate sess.id
    return sess


def _tokens(user: User, sess: UserSession) -> TokenOut:
    sid = str(sess.id)
    return TokenOut(
        access_token=create_access_token(str(user.id), extra={"sid": sid}),
        refresh_token=create_refresh_token(str(user.id), sid),
    )


@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn, req: Request, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()
    # assign default 'user' role
    role = (await db.execute(select(Role).where(Role.name == "user"))).scalar_one_or_none()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    # record a referral if a valid code was supplied
    from .referral import apply_referral
    await apply_referral(db, body.referral_code, user)
    ctx = await build_client_context(req)
    await ev.security(db, "user.created", user=user, source="api", ip=ctx.get("ip"),
                      resource="user", resource_id=user.id)
    sess = await _open_session(db, user, ctx)
    await db.commit()
    return _tokens(user, sess)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, req: Request, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    ok = bool(user and user.password_hash and verify_password(body.password, user.password_hash))
    ctx = await build_client_context(req)
    db.add(LoginHistory(user_id=(user.id if user else None), ip=ctx.get("ip"), geo=ctx.get("geo") or {},
                        device=ctx.get("device"), success=ok, reason=None if ok else "bad_credentials"))
    if not ok:
        await ev.security(db, "auth.login.failure", level="warning", user=user, ip=ctx.get("ip"))
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.is_blocked:
        await db.commit()  # persist the login-history row before refusing
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account suspended")
    await ev.security(db, "auth.login.success", user=user, ip=ctx.get("ip"))
    sess = await _open_session(db, user, ctx)
    await db.commit()
    return _tokens(user, sess)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a fresh access token (session must still be live)."""
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")
    sid, sub = payload.get("sid"), payload.get("sub")
    sess = await db.get(UserSession, uuid.UUID(sid)) if sid else None
    now = datetime.now(timezone.utc)
    exp = sess.expires_at if sess else None
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if sess is None or not sess.is_active or sess.revoked_at is not None or (exp and exp < now):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or revoked")
    user = await db.get(User, uuid.UUID(sub)) if sub else None
    if user is None or user.is_blocked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User unavailable")
    sess.last_active_at = now
    await db.commit()
    return TokenOut(access_token=create_access_token(str(user.id), extra={"sid": sid}),
                    refresh_token=body.refresh_token)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                 token: str | None = Depends(oauth2_scheme)):
    """Revoke the current session (the sid carried by the access token)."""
    sid = decode_token(token).get("sid") if token else None
    if sid:
        sess = await db.get(UserSession, uuid.UUID(sid))
        if sess and sess.is_active:
            sess.is_active = False
            sess.revoked_at = datetime.now(timezone.utc)
            await ev.security(db, "auth.logout", user=user)
            await db.commit()
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordIn, db: AsyncSession = Depends(get_db)):
    """Email a one-time reset link. Always returns 200 (never reveals if an email exists)."""
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    out: dict = {"ok": True, "message": "If that email exists, a reset link has been sent."}
    if user and not user.is_blocked:
        raw = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user.id, token_hash=_hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_TTL_MIN),
        ))
        await ev.security(db, "auth.password.reset_requested", user=user)
        await db.commit()
        link = f"{settings.REVALIDATE_URL.rsplit('/api', 1)[0]}/reset-password?token={raw}"
        await send_email(user.email, "Reset your SwingAI password",
                         f"Reset your password (valid {RESET_TTL_MIN} min): {link}")
        if dev_mode():               # surface the token in dev so it's testable without email
            out["dev_token"] = raw
    return out


@router.post("/reset-password", response_model=TokenOut)
async def reset_password(body: ResetPasswordIn, req: Request, db: AsyncSession = Depends(get_db)):
    """Consume a reset token, set the new password, and revoke all existing sessions."""
    row = (await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash_token(body.token))
    )).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    exp = row.expires_at if row else None
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if row is None or row.used_at is not None or (exp and exp < now):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")
    user = await db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")
    user.password_hash = hash_password(body.new_password)
    row.used_at = now
    # revoke every existing session — a reset logs the user out everywhere
    for s in (await db.execute(select(UserSession).where(UserSession.user_id == user.id))).scalars():
        s.is_active = False
        s.revoked_at = now
    await ev.security(db, "auth.password.reset_completed", level="warning", user=user)
    ctx = await build_client_context(req)
    sess = await _open_session(db, user, ctx)   # sign them in on the new password
    await db.commit()
    return _tokens(user, sess)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return UserOut(
        id=str(user.id), email=user.email, name=user.name,
        capital_amount=float(user.capital_amount), risk_pct=float(user.risk_pct),
        subscription_tier=user.subscription_tier, two_factor_enabled=bool(user.totp_enabled),
        roles=await user_roles(db, user),
        permissions=sorted(await user_permissions(db, user)),
    )
