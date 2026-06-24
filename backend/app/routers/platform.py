"""Public platform appearance/config — resolved defaults for first paint (blueprint/14,16)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..models.platform import PlatformSetting, ThemePreset

router = APIRouter(tags=["platform"])


@router.get("/api/platform/appearance")
async def appearance(db: AsyncSession = Depends(get_db)):
    ps = (await db.execute(select(PlatformSetting).limit(1))).scalar_one_or_none()
    presets = (await db.execute(select(ThemePreset).where(ThemePreset.is_enabled == True))).scalars().all()  # noqa: E712
    return {
        "defaults": {
            "mode": ps.default_theme_mode if ps else "system",
            "preset": ps.default_preset if ps else "default",
            "font": ps.default_font if ps else "inter",
            "locale": ps.default_locale if ps else "en",
        },
        "locked": ps.locked_axes if ps else {},
        "enabledLocales": ps.enabled_locales if ps else ["en", "hi"],
        "maintenance": {"on": ps.maintenance_mode if ps else False,
                        "message": ps.maintenance_message if ps else None},
        "presets": [
            {"name": p.name, "label": p.label, "tokensLight": p.tokens_light, "tokensDark": p.tokens_dark}
            for p in presets
        ],
    }
