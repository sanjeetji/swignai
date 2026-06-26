"""Paper-trading engine — risk-guarded buy/close + portfolio (blueprint/04,07)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import json

from ..config import DEFAULT
from ..core.db import get_db
from ..core.flags import require_flag
from ..services.tiers import require_access
from ..core.redis import cache_get
from ..core.security import get_current_user
from ..models.trading import PaperTrade
from ..models.user import User
from ..schemas import PaperBuyIn, PaperCloseIn, PaperTrailIn

router = APIRouter(prefix="/api/paper-trade", tags=["paper"])


async def _live_prices() -> dict[str, float]:
    """Latest close per symbol from the scanner cache (fast; no per-request market calls)."""
    cached = await cache_get("scan:latest")
    if not cached:
        return {}
    try:
        data = json.loads(cached)
        return {r["symbol"]: float(r["price"]) for r in data.get("results", []) if r.get("price")}
    except (ValueError, KeyError, TypeError):
        return {}


async def _open_trades(db, user_id):
    rows = await db.execute(
        select(PaperTrade).where(PaperTrade.user_id == user_id, PaperTrade.status == "open")
    )
    return list(rows.scalars().all())


@router.post("/buy")
async def buy(body: PaperBuyIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
              _flag=Depends(require_flag("paper_trading")), _gate=Depends(require_access())):
    risk_per_share = body.entry_price - body.stop_loss
    if risk_per_share <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stop must be below entry")
    rr = (body.target - body.entry_price) / risk_per_share
    if rr < DEFAULT.min_rr - 0.01:   # tolerance: stored pick values are rounded to 2dp
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"R:R {rr:.2f} < required {DEFAULT.min_rr}")

    capital = float(user.capital_amount)
    open_trades = await _open_trades(db, user.id)

    # server-side risk guards (UI guidance is not the gate)
    if len(open_trades) >= DEFAULT.max_open_positions:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Max open positions reached")
    position_size = body.quantity * body.entry_price
    if position_size > capital * DEFAULT.max_position_pct / 100.0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Position exceeds 20% concentration cap")
    live_risk = sum((float(t.entry_price) - float(t.stop_loss_set or t.entry_price)) * t.quantity
                    for t in open_trades)
    new_risk = risk_per_share * body.quantity
    if (live_risk + new_risk) / capital * 100.0 > DEFAULT.max_portfolio_heat_pct:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Would exceed portfolio heat cap")

    trade = PaperTrade(
        user_id=user.id,
        ai_pick_id=uuid.UUID(body.ai_pick_id) if body.ai_pick_id else None,
        stock_symbol=body.stock_symbol, entry_price=body.entry_price,
        entry_date=datetime.now(timezone.utc), quantity=body.quantity,
        position_size_inr=position_size, stop_loss_set=body.stop_loss,
        target_set=body.target, status="open", entry_reason=body.entry_reason,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return {"id": str(trade.id), "status": "open", "position_size": position_size, "rr_ratio": round(rr, 2)}


@router.post("/{trade_id}/close")
async def close(trade_id: str, body: PaperCloseIn, user: User = Depends(get_current_user),
                db: AsyncSession = Depends(get_db)):
    trade = await db.get(PaperTrade, uuid.UUID(trade_id))
    if not trade or trade.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trade not found")
    if trade.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Trade already closed")

    entry = float(trade.entry_price)
    rps = entry - float(trade.stop_loss_set or entry)
    pnl = (body.exit_price - entry) * trade.quantity
    pnl_pct = (body.exit_price - entry) / entry * 100.0
    r_mult = (body.exit_price - entry) / rps if rps > 0 else 0.0
    status_label = ("scratch" if abs(pnl_pct) < 0.5
                    else "closed_profit" if pnl > 0 else "closed_loss")

    trade.exit_price = body.exit_price
    trade.exit_date = datetime.now(timezone.utc)
    trade.pnl_inr = pnl
    trade.pnl_percent = pnl_pct
    trade.r_multiple = r_mult
    trade.status = status_label
    trade.exit_reason = body.exit_reason
    await db.commit()
    return {"id": str(trade.id), "status": status_label, "pnl_inr": round(pnl, 2),
            "r_multiple": round(r_mult, 3)}


@router.post("/{trade_id}/trail")
async def trail(trade_id: str, body: PaperTrailIn, user: User = Depends(get_current_user),
                db: AsyncSession = Depends(get_db)):
    """Ratchet an open trade's stop UP (trailing stop / move-to-breakeven). Never lowers risk's stop."""
    trade = await db.get(PaperTrade, uuid.UUID(trade_id))
    if not trade or trade.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trade not found")
    if trade.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Trade is closed")
    cur = float(trade.stop_loss_set or 0)
    if body.new_stop <= cur:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"New stop must be above current stop ₹{cur}")
    if body.new_stop >= float(trade.entry_price) * 3:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stop is implausibly high")
    trade.stop_loss_set = body.new_stop
    await db.commit()
    return {"id": str(trade.id), "stop": body.new_stop,
            "breakeven": body.new_stop >= float(trade.entry_price)}


@router.get("/portfolio")
async def portfolio(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                    _gate=Depends(require_access())):
    open_trades = await _open_trades(db, user.id)
    capital = float(user.capital_amount)
    live_risk = sum((float(t.entry_price) - float(t.stop_loss_set or t.entry_price)) * t.quantity
                    for t in open_trades)
    prices = await _live_prices()

    def enrich(t: PaperTrade) -> dict:
        entry = float(t.entry_price)
        stop = float(t.stop_loss_set or 0)
        target = float(t.target_set or 0)
        cur = prices.get(t.stock_symbol)
        rps = entry - stop
        out = {"id": str(t.id), "symbol": t.stock_symbol, "entry": entry, "qty": t.quantity,
               "stop": stop, "target": target, "status": t.status,
               "entry_date": str(t.entry_date)[:10], "current_price": cur,
               "breakeven": stop >= entry}
        if cur is not None:
            out["unrealized_inr"] = round((cur - entry) * t.quantity, 2)
            out["unrealized_pct"] = round((cur - entry) / entry * 100.0, 2) if entry else 0
            out["r_now"] = round((cur - entry) / rps, 2) if rps > 0 else 0
            span_t = target - entry
            span_s = entry - stop
            out["pct_to_target"] = round(max(0, min(100, (cur - entry) / span_t * 100.0)), 0) if span_t > 0 else 0
            out["pct_to_stop"] = round(max(0, min(100, (entry - cur) / span_s * 100.0)), 0) if span_s > 0 else 0
        return out

    return {
        "capital": capital,
        "open_positions": len(open_trades),
        "portfolio_heat_pct": round(live_risk / capital * 100.0, 2) if capital else 0,
        "trades": [enrich(t) for t in open_trades],
    }
