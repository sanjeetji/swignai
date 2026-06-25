"""Lightweight per-IP rate limiter (blueprint/19 §5).

Dev/single-instance: in-memory sliding window. At scale, swap the counter store for
Redis (same interface). Applied to auth + sensitive paths via middleware in main.py;
fails open (never blocks legitimate traffic if the limiter itself errors).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

_WINDOW = 60.0
_hits: dict[str, deque] = defaultdict(deque)


def allow(key: str, limit: int) -> bool:
    now = time.time()
    q = _hits[key]
    cutoff = now - _WINDOW
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True
