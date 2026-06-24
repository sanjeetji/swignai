"""STAGE 3 — the risk engine: stop, targets, position size, portfolio guards (blueprint/04 §5).

This is the product's actual value (Layer 1). Every number is deterministic.
The user never sizes by gut — size is computed from capital and a fixed risk %.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from ..config import StrategyConfig


@dataclass
class TradePlan:
    entry: float
    stop: float
    target_1: float
    target_2: float
    risk_per_share: float
    rr_ratio: float
    quantity: int
    position_size: float
    risk_amount: float


def build_trade_plan(row: pd.Series, capital: float, cfg: StrategyConfig) -> TradePlan | None:
    """Build a deterministic trade plan for an entry near `close`.

    Stop = the tighter-justified of (swing low) or (entry - mult*ATR).
    Returns None if inputs are invalid or no positive-risk stop exists.
    """
    entry = float(row["close"])
    atr = float(row.get("atr", float("nan")))
    swing_low = float(row.get("swing_low", float("nan")))
    if not math.isfinite(entry) or not math.isfinite(atr) or atr <= 0:
        return None

    atr_stop = entry - cfg.atr_stop_mult * atr
    # tighter-justified: the higher stop (smaller risk) of the two valid candidates
    candidates = [s for s in (swing_low, atr_stop) if math.isfinite(s) and s < entry]
    if not candidates:
        return None
    stop = max(candidates)
    risk_per_share = entry - stop
    if risk_per_share <= 0:
        return None

    target_1 = entry + cfg.target_1_r * risk_per_share
    target_2 = entry + cfg.target_2_r * risk_per_share
    rr_ratio = (target_1 - entry) / risk_per_share  # == target_1_r

    risk_amount = capital * (cfg.risk_pct / 100.0)
    quantity = int(math.floor(risk_amount / risk_per_share))

    # enforce max position size (cap quantity)
    max_pos_value = capital * (cfg.max_position_pct / 100.0)
    if quantity * entry > max_pos_value:
        quantity = int(math.floor(max_pos_value / entry))

    position_size = quantity * entry
    return TradePlan(
        entry=round(entry, 2),
        stop=round(stop, 2),
        target_1=round(target_1, 2),
        target_2=round(target_2, 2),
        risk_per_share=round(risk_per_share, 4),
        rr_ratio=round(rr_ratio, 2),
        quantity=quantity,
        position_size=round(position_size, 2),
        risk_amount=round(risk_amount, 2),
    )


def portfolio_heat_pct(open_risk_amounts: list[float], capital: float) -> float:
    """Sum of live risk across open positions, as % of capital."""
    if capital <= 0:
        return 0.0
    return sum(open_risk_amounts) / capital * 100.0


def can_open(open_risk_amounts: list[float], new_risk_amount: float, capital: float, cfg: StrategyConfig) -> bool:
    if len(open_risk_amounts) >= cfg.max_open_positions:
        return False
    projected = portfolio_heat_pct(open_risk_amounts + [new_risk_amount], capital)
    return projected <= cfg.max_portfolio_heat_pct
