"""Health + platform meta (public)."""
from __future__ import annotations

from fastapi import APIRouter

from ..core.config import settings
from .. import brand

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    return {"status": "ok", "env": settings.ENV, "service": "swingai-api"}


@router.get("/api/platform/brand")
async def platform_brand():
    """Public brand snapshot — frontend reads this so the name lives in ONE place."""
    return brand.brand_dict()
