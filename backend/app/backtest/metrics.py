"""Metrics — expectancy first, win-rate is context only (blueprint/05 §4).

Win rate is computed HONESTLY as wins / (wins + losses + scratches) — scratches in
the denominator, never excluded to inflate the number (blueprint/00 non-negotiable #2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean


@dataclass
class Trade:
    symbol: str
    entry_date: str
    exit_date: str
    entry: float
    exit: float
    quantity: int
    r_multiple: float
    pnl_inr: float
    pnl_pct: float
    status: str            # closed_profit / closed_loss / scratch
    reason: str            # target / stoploss / scratch / time
    regime: str
    hold_days: int


def _max_drawdown(equity: list[float]) -> float:
    peak = float("-inf")
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)
    return round(max_dd * 100.0, 2)


def summarize(trades: list[Trade], starting_equity_curve: list[float] | None = None) -> dict:
    n = len(trades)
    if n == 0:
        return {"trades": 0, "note": "no trades generated"}

    wins = [t for t in trades if t.status == "closed_profit"]
    losses = [t for t in trades if t.status == "closed_loss"]
    scratches = [t for t in trades if t.status == "scratch"]

    rs = [t.r_multiple for t in trades]
    gross_profit = sum(t.pnl_inr for t in trades if t.pnl_inr > 0)
    gross_loss = -sum(t.pnl_inr for t in trades if t.pnl_inr < 0)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    # HONEST win rate: scratches counted in the denominator
    decided = len(wins) + len(losses) + len(scratches)
    win_rate = (len(wins) / decided * 100.0) if decided else 0.0

    return {
        "trades": n,
        "expectancy_r": round(mean(rs), 3),          # THE headline
        "win_rate_pct": round(win_rate, 1),          # context only (incl. scratches)
        "wins": len(wins),
        "losses": len(losses),
        "scratches": len(scratches),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else None,
        "total_pnl_inr": round(sum(t.pnl_inr for t in trades), 2),
        "avg_hold_days": round(mean(t.hold_days for t in trades), 1),
        "max_drawdown_pct": _max_drawdown(starting_equity_curve) if starting_equity_curve else None,
        "avg_win_r": round(mean(t.r_multiple for t in wins), 2) if wins else None,
        "avg_loss_r": round(mean(t.r_multiple for t in losses), 2) if losses else None,
    }


def summarize_by_regime(trades: list[Trade]) -> dict:
    out = {}
    for reg in ("bull", "neutral", "bear"):
        sub = [t for t in trades if t.regime == reg]
        if sub:
            out[reg] = summarize(sub)
    return out
