"""Canonical per-user trading analytics (blueprint/20).

Shared by the live `/api/analytics` endpoint and the nightly `recompute_analytics`
job so the stored snapshot can never diverge from what the user sees. Win% counts
wins/(wins+losses+scratches); expectancy is mean R; everything is net (pnl already
net-of-cost on the trade rows).
"""
from __future__ import annotations

from statistics import mean

from ..data.sectors import sector_for


def summarize_trades(trades) -> dict:
    """Headline metrics from a user's PaperTrade rows (open rows ignored)."""
    closed = [t for t in trades if t.status != "open"]
    if not closed:
        return {"trades": 0, "note": "insufficient data — no closed trades yet"}
    wins = [t for t in closed if t.status == "closed_profit"]
    losses = [t for t in closed if t.status == "closed_loss"]
    scratches = [t for t in closed if t.status == "scratch"]
    rs = [float(t.r_multiple or 0) for t in closed]
    gp = sum(float(t.pnl_inr or 0) for t in closed if (t.pnl_inr or 0) > 0)
    gl = -sum(float(t.pnl_inr or 0) for t in closed if (t.pnl_inr or 0) < 0)
    decided = len(wins) + len(losses) + len(scratches)
    return {
        "trades": len(closed),
        "expectancy_r": round(mean(rs), 3),                       # headline
        "win_rate_pct": round(len(wins) / decided * 100, 1),      # incl. scratches
        "wins": len(wins), "losses": len(losses), "scratches": len(scratches),
        "profit_factor": round(gp / gl, 2) if gl > 0 else None,
        "total_pnl_inr": round(sum(float(t.pnl_inr or 0) for t in closed), 2),
    }


def discipline_score(trades) -> float | None:
    """0–100: share of closed trades where the plan was followed (held winners to
    target, respected stops). None when there are no closed trades."""
    closed = [t for t in trades if t.status in ("closed_profit", "closed_loss", "scratch")]
    if not closed:
        return None
    winners = [t for t in closed if t.status == "closed_profit"]
    losers = [t for t in closed if t.status == "closed_loss"]
    winners_early = [t for t in winners
                     if t.target_set and t.exit_price and float(t.exit_price) < float(t.target_set)]
    stop_breaks = [t for t in losers
                   if t.stop_loss_set and t.exit_price and float(t.exit_price) < float(t.stop_loss_set) * 0.995]
    return round(100 * (1 - (len(winners_early) + len(stop_breaks)) / len(closed)), 2)


def avg_holding_days(trades) -> float | None:
    closed = [t for t in trades if t.status != "open" and t.exit_date]
    if not closed:
        return None
    return round(sum((t.exit_date - t.entry_date).days for t in closed) / len(closed), 1)


def best_sector(trades) -> str | None:
    """Sector with the highest net P&L across the user's closed trades."""
    pnl: dict[str, float] = {}
    for t in trades:
        if t.status == "open":
            continue
        sec = sector_for(t.stock_symbol)
        if sec:
            pnl[sec] = pnl.get(sec, 0.0) + float(t.pnl_inr or 0)
    if not pnl:
        return None
    return max(pnl, key=pnl.get)
