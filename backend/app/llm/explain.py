"""generate_explanation(pick) — Redis-cached Hinglish narration (blueprint/03 §6).

Flow: cache hit → return; else try the configured LLM provider; on any failure or
unsafe output → fall back to the template (which always passes the safety guard).
Caching keyed by symbol+date means ~N calls/day total regardless of user count.
"""
from __future__ import annotations

import json

from . import base, templates


def _cache_key(pick: dict) -> str:
    return f"explanation:{pick.get('symbol')}:{pick.get('date', 'today')}"


async def generate_explanation(pick: dict, *, use_cache: bool = True) -> str:
    from ..core.redis import cache_get, cache_set

    key = _cache_key(pick)
    if use_cache:
        cached = await cache_get(key)
        if cached:
            return cached

    text = templates.render(pick)  # safe default
    try:
        provider = base.get_provider()
        out = provider.complete(
            system="Translate the given trade numbers into <60 words of Hinglish "
                   "(~60% Hindi). Describe conditions, never command buy/sell. "
                   "End with: Yeh educational analysis hai, investment advice nahi.",
            user=json.dumps(pick.get("plan", {})) + f" symbol={pick.get('symbol')}",
            max_tokens=160,
        )
        if templates.is_safe(out):
            text = out
    except Exception:
        pass  # NullProvider / any failure → keep the template

    if use_cache:
        await cache_set(key, text, ttl=60 * 60 * 24)  # 24h
    return text
