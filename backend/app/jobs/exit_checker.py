"""Exit checker (3:45 PM IST) — resolve open paper trades vs latest price (blueprint/07).

For each open paper trade, fetch the latest quote and apply stop/target rules. Uses
the same honest classification (scratch band) as the picker's exit logic. Idempotent.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from ..core.config import settings
from ..core.db import SessionLocal
from ..data.factory import get_provider
from ..models.trading import PaperTrade
from ..models.watchlist import PriceAlert
from ..services import event_log as ev
from ..services.notify import push as push_notification

logger = logging.getLogger("exit_checker")


def _latest_price(provider, symbol: str) -> float | None:
    try:
        df = provider.get_ohlcv(symbol)
        if df is None or df.empty:
            return None
        return float(df["close"].iloc[-1])
    except Exception:
        return None


async def run() -> dict:
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    closed = 0
    async with SessionLocal() as db:
        rows = (await db.execute(select(PaperTrade).where(PaperTrade.status == "open"))).scalars().all()
        for t in rows:
            px = _latest_price(provider, t.stock_symbol)
            if px is None:
                continue
            entry = float(t.entry_price)
            stop = float(t.stop_loss_set or 0)
            target = float(t.target_set or 0)
            hit = None
            if stop and px <= stop:
                hit, exit_px = "stoploss", stop
            elif target and px >= target:
                hit, exit_px = "target", target
            if not hit:
                continue
            rps = entry - stop if stop else 0
            pnl = (exit_px - entry) * t.quantity
            pnl_pct = (exit_px - entry) / entry * 100 if entry else 0
            t.exit_price, t.exit_date = exit_px, datetime.now(timezone.utc)
            t.pnl_inr, t.pnl_percent = pnl, pnl_pct
            t.r_multiple = (exit_px - entry) / rps if rps > 0 else 0
            t.status = ("scratch" if abs(pnl_pct) < 0.5
                        else "closed_profit" if pnl > 0 else "closed_loss")
            t.exit_reason = hit
            await push_notification(db, t.user_id, f"trade.{hit}", {
                "symbol": t.stock_symbol, "exit": round(exit_px, 2),
                "pnl_inr": round(pnl, 2), "r_multiple": round(t.r_multiple or 0, 2), "outcome": t.status,
            })
            closed += 1
        if closed:
            await ev.system(db, "exit_checker.triggered", payload={"closed": closed})
        await db.commit()
        fired = await _check_alerts(db, provider)
    logger.info("exit_checker: closed %s trades, fired %s alerts", closed, fired)
    return {"closed": closed, "alerts": fired}


async def _check_alerts(db, provider) -> int:
    """Fire any active price alert whose target has been crossed (once, then deactivate)."""
    alerts = (await db.execute(select(PriceAlert).where(PriceAlert.is_active == True))).scalars().all()  # noqa: E712
    if not alerts:
        return 0
    px_cache: dict[str, float | None] = {}
    fired = 0
    for a in alerts:
        if a.symbol not in px_cache:
            px_cache[a.symbol] = _latest_price(provider, a.symbol)
        px = px_cache[a.symbol]
        if px is None:
            continue
        crossed = (a.direction == "above" and px >= a.target_price) or \
                  (a.direction == "below" and px <= a.target_price)
        if not crossed:
            continue
        a.is_active = False
        a.triggered_at = datetime.now(timezone.utc)
        await push_notification(db, a.user_id, "price.alert", {
            "symbol": a.symbol, "direction": a.direction,
            "target": round(a.target_price, 2), "price": round(px, 2),
        })
        fired += 1
    if fired:
        await db.commit()
    return fired
