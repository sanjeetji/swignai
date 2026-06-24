"""Auth & RBAC — JWT, password hashing, current-user + permission dependencies.

Mirrors the OmniMark pattern (python-jose + passlib; permission-based checks
enforced server-side — blueprint/19). 2FA (pyotp) hooks are added in the auth router.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import get_db

# pbkdf2_sha256 (pure-Python, no native bcrypt quirks) as default; bcrypt kept for
# verifying any legacy/imported hashes. Both are secure.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# --- passwords ---
def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(p: str, hashed: str) -> bool:
    return pwd_context.verify(p, hashed)


# --- tokens ---
def create_access_token(sub: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN),
        "type": "access",
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])


# --- current user / RBAC dependencies ---
async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from ..models.user import User  # local import to avoid cycles
    from sqlalchemy import select

    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user = await db.get(User, uuid.UUID(user_id)) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    if user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account suspended")
    return user


def require_permissions(*perms: str):
    """Dependency factory: ensure the current user has ALL given permissions."""
    async def _dep(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        from ..services.rbac import user_permissions
        have = await user_permissions(db, user)
        missing = [p for p in perms if p not in have]
        if missing:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Missing permission(s): {', '.join(missing)}"
            )
        return user
    return _dep
