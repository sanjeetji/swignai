"""Resolve open ai_picks against real prices → the honest screener track record.

For each still-open pick, walk the bars AFTER the signal date and apply the SAME exit
logic as the backtest (stop checked before target; breakeven/trail; time stop). Records
`actual_result` + `actual_r_multiple` so /api/track-record reflects real outcomes —
wins/losses/scratches counted honestly (blueprint/00 #2, blueprint/07).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from ..config import DEFAULT
from ..core.config import settings
from ..core.db import SessionLocal
from ..data.factory import get_provider
from ..models.trading import AIPick
from ..quant.exits import Position, check_bar, classify_exit
from ..services import event_log as ev

logger = logging.getLogger("update_old_picks")

_REASON_TO_RESULT = {"target": "hit_target", "stoploss": "hit_stoploss",
                     "scratch": "scratch", "time": "time_exit"}


def _resolve(pick: AIPick, df) -> tuple[str, float] | None:
    """Return (actual_result, r_multiple) once the pick closes, else None (still open)."""
    entry = float(pick.entry_price or 0)
    stop = float(pick.stop_loss or 0)
    target2 = float(pick.target_2 or 0)
    rps = entry - stop
    if rps <= 0 or df is None or df.empty:
        return None
    future = df[df.index.date > pick.date_generated]
    if future.empty:
        return None
    pos = Position(symbol=pick.stock_symbol, entry=entry, stop=stop, target_2=target2,
                   quantity=1, risk_per_share=rps, entry_index=0)
    for i, (_, bar) in enumerate(future.iterrows()):
        if i >= DEFAULT.max_hold_days:
            er = classify_exit(pos, float(bar["close"]), "time")
            return _REASON_TO_RESULT.get(er.reason, "time_exit"), (er.exit_price - entry) / rps
        res = check_bar(pos, float(bar["high"]), float(bar["low"]), DEFAULT)
        if res is not None:
            return _REASON_TO_RESULT.get(res.reason, res.reason), (res.exit_price - entry) / rps
    return None  # still open within the hold window


async def run() -> dict:
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    resolved = 0
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(AIPick).where(AIPick.actual_result.in_(["still_open", None]))
        )).scalars().all()
        # group price lookups per symbol to avoid repeat downloads
        cache: dict[str, object] = {}
        for pick in rows:
            sym = pick.stock_symbol
            if sym not in cache:
                cache[sym] = provider.get_ohlcv(sym)
            outcome = _resolve(pick, cache[sym])
            if outcome is None:
                continue
            pick.actual_result, pick.actual_r_multiple = outcome[0], round(outcome[1], 3)
            pick.closed_at = datetime.now(timezone.utc)
            resolved += 1
        if resolved:
            await ev.system(db, "picks.resolved", payload={"resolved": resolved})
        await db.commit()
    logger.info("update_old_picks: resolved %s picks", resolved)
    return {"resolved": resolved}
