"""On-demand ISR revalidation (blueprint/08).

Pings the Next marketing app to rebuild specific ISR pages right after data changes
(new daily picks, CMS edits) instead of waiting for the per-page timed revalidate.
Best-effort: a failed or unreachable frontend never breaks the calling job/request.
Uses requests in a worker thread so the async event loop isn't blocked.
"""
from __future__ import annotations

import asyncio
import logging

from ..core.config import settings

logger = logging.getLogger("revalidate")

# Marketing locales (next-intl) — keep in sync with apps/marketing/src/i18n.ts.
LOCALES = ("en", "hi")


async def revalidate(paths: list[str]) -> dict:
    paths = [p for p in dict.fromkeys(paths) if p]  # dedupe, drop empties, keep order
    if not paths:
        return {"revalidated": 0}

    def _post() -> int:
        import requests
        r = requests.post(
            settings.REVALIDATE_URL, json={"paths": paths},
            headers={"x-revalidate-token": settings.REVALIDATE_TOKEN}, timeout=8,
        )
        return r.status_code

    try:
        code = await asyncio.to_thread(_post)
        logger.info("revalidate %d paths -> HTTP %s", len(paths), code)
        return {"revalidated": len(paths), "status": code}
    except Exception as e:  # frontend down / network — non-fatal
        logger.warning("revalidate failed: %s", e)
        return {"revalidated": 0, "error": str(e)}


def picks_paths(symbols: list[str]) -> list[str]:
    """Locale-expanded paths to refresh after a daily-pick run: home, indexes, each pick."""
    paths: list[str] = []
    for loc in LOCALES:
        paths += [f"/{loc}", f"/{loc}/stocks", f"/{loc}/sectors", f"/{loc}/track-record"]
        paths += [f"/{loc}/stocks/{s}" for s in symbols]
    return paths
