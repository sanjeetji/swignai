"""generate_explanation(pick) — Redis-cached Hinglish narration (blueprint/03 §6).

Flow: cache hit → return; else resolve the active LLM provider (vault → .env) and call
it off-thread; on any failure or unsafe output → fall back to the template (which always
passes the safety guard). Caching keyed by symbol+date means ~N calls/day regardless of
user count, so free tiers are plenty.
"""
from __future__ import annotations

import asyncio
import json

from . import base, templates

_SYSTEM = ("Translate the given trade numbers into under 60 words of Hinglish "
           "(~60% Hindi, 40% English). Describe the conditions; NEVER command buy/sell. "
           "End with exactly: Yeh educational analysis hai, investment advice nahi.")


def _cache_key(pick: dict) -> str:
    return f"explanation:{pick.get('symbol')}:{pick.get('date', 'today')}"


async def generate_explanation(pick: dict, *, db=None, use_cache: bool = True) -> str:
    from ..core.redis import cache_get, cache_set

    key = _cache_key(pick)
    if use_cache:
        cached = await cache_get(key)
        if cached:
            return cached

    text = templates.render(pick)  # safe default
    try:
        provider = await base.resolve_provider(db)
        if not isinstance(provider, base.NullProvider):
            user = json.dumps(pick.get("plan", {})) + f" symbol={pick.get('symbol')} rsi={pick.get('rsi')}"
            out = await asyncio.to_thread(provider.complete, _SYSTEM, user, 160)
            if out and templates.is_safe(out):
                text = out
    except Exception:
        pass  # any failure → keep the safe template

    if use_cache:
        await cache_set(key, text, ttl=60 * 60 * 24)  # 24h
    return text
