"""Nightly: rebuild user_analytics from closed paper trades (blueprint/07,20).

Persists each user's expectancy / win% / profit factor / discipline so admin and
business-analytics views read a snapshot instead of recomputing per request. The
live /api/analytics endpoint shares the same `services.analytics` math, so the
stored row and the on-the-fly number can never diverge. Idempotent upsert by user_id.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from ..core.db import SessionLocal
from ..models.trading import PaperTrade, UserAnalytics
from ..services.analytics import avg_holding_days, best_sector, discipline_score, summarize_trades

logger = logging.getLogger("recompute_analytics")


async def run() -> dict:
    updated = 0
    async with SessionLocal() as db:
        trades = (await db.execute(select(PaperTrade))).scalars().all()
        by_user: dict = {}
        for t in trades:
            by_user.setdefault(t.user_id, []).append(t)

        for user_id, rows in by_user.items():
            s = summarize_trades(rows)
            ua = await db.get(UserAnalytics, user_id)
            if ua is None:
                ua = UserAnalytics(user_id=user_id)
                db.add(ua)
            ua.total_trades = s.get("trades", 0)
            ua.winning_trades = s.get("wins", 0)
            ua.win_rate_pct = s.get("win_rate_pct", 0) or 0
            ua.expectancy_r = s.get("expectancy_r", 0) or 0
            ua.profit_factor = s.get("profit_factor")
            ua.total_pnl_inr = s.get("total_pnl_inr", 0) or 0
            ua.avg_holding_days = avg_holding_days(rows)
            ua.best_sector = best_sector(rows)
            ua.discipline_score = discipline_score(rows)
            ua.last_updated = datetime.now(timezone.utc)
            updated += 1

        await db.commit()
    logger.info("recompute_analytics: %d user(s) updated", updated)
    return {"users_updated": updated}
