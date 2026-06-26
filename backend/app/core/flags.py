"""Feature flags (blueprint/16) — runtime on/off kill-switches.

`flag_enabled` is the global switch; `require_flag` is a route dependency that 404s
when a flag is off (a gated feature reads as absent, not forbidden). Lookups are light
single-row queries — cache later if a hot path needs it. (Per-tier/role `targeting` is
stored on the flag for the admin UI; enforcement lands when a feature needs it.)
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.platform import FeatureFlag
from .db import get_db


async def flag_enabled(db: AsyncSession, key: str) -> bool:
    f = (await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))).scalar_one_or_none()
    return bool(f and f.enabled)


def require_flag(key: str):
    """Dependency factory: 404 unless the flag is globally enabled."""
    async def _dep(db: AsyncSession = Depends(get_db)):
        if not await flag_enabled(db, key):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not available")
        return True
    return _dep
