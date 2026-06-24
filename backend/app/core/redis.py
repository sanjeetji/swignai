"""Redis cache — optional in dev, used for picks/explanations/quotes/sessions (blueprint/07).

Lazily connects; if REDIS_URL is unset or unreachable, callers fall back to the DB
(graceful degradation — blueprint/07 §4). Never let cache failure break a request.
"""
from __future__ import annotations

from .config import settings

_client = None


def get_redis():
    global _client
    if settings.REDIS_URL is None:
        return None
    if _client is None:
        try:
            import redis.asyncio as redis
            _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            return None
    return _client


async def cache_get(key: str) -> str | None:
    r = get_redis()
    if r is None:
        return None
    try:
        return await r.get(key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl: int | None = None) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.set(key, value, ex=ttl)
    except Exception:
        pass
