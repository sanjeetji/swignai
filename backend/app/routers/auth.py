"""Auth — register / login / me, with event-log + login-history + sessions (blueprint/18,19)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.clientinfo import build_client_context
from ..core.config import settings
from ..core.db import get_db
from ..core.security import (create_access_token, get_current_user, hash_password,
                             verify_password)
from ..models.session import LoginHistory, UserSession
from ..models.user import Role, User, UserRole
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..services import event_log as ev
from ..services.rbac import user_permissions, user_roles

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(req: Request) -> str | None:
    return req.client.host if req.client else None


async def _open_session(db: AsyncSession, user: User, ctx: dict) -> UserSession:
    """Create an active session row (geo + device); caller embeds its id (sid) in the JWT."""
    now = datetime.now(timezone.utc)
    sess = UserSession(
        user_id=user.id, ip=ctx.get("ip"), geo=ctx.get("geo") or {},
        device=ctx.get("device"), browser=ctx.get("browser"), os=ctx.get("os"),
        last_active_at=now, is_active=True,
        expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN),
    )
    db.add(sess)
    await db.flush()  # populate sess.id
    return sess


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
    ctx = await build_client_context(req)
    await ev.security(db, "user.created", user=user, source="api", ip=ctx.get("ip"),
                      resource="user", resource_id=user.id)
    sess = await _open_session(db, user, ctx)
    await db.commit()
    return TokenOut(access_token=create_access_token(str(user.id), extra={"sid": str(sess.id)}))


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
    return TokenOut(access_token=create_access_token(str(user.id), extra={"sid": str(sess.id)}))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return UserOut(
        id=str(user.id), email=user.email, name=user.name,
        capital_amount=float(user.capital_amount), risk_pct=float(user.risk_pct),
        subscription_tier=user.subscription_tier,
        roles=await user_roles(db, user),
        permissions=sorted(await user_permissions(db, user)),
    )
