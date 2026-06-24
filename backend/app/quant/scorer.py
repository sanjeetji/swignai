"""STAGE 2 — weighted 0-100 score that ranks the survivors (blueprint/04 §4).

Relative strength carries the most weight on purpose — it's the closest thing to a
genuine edge, not the textbook oscillators everyone has. Returns the total plus a
per-factor breakdown for transparency (shown in the UI later).
"""
from __future__ import annotations

import math

import pandas as pd

from ..config import StrategyConfig


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_row(row: pd.Series, cfg: StrategyConfig) -> tuple[float, dict]:
    close = float(row["close"])

    # Relative strength vs index (0..1): 0 at <=0% outperformance, 1 at >=+10%
    rs = float(row.get("rel_strength", 0.0))
    rs_n = _clamp01(rs / 10.0)

    # Trend quality: EMA stack 20>50>200 + slope
    ema20, ema50, ema200 = float(row.get("ema20", 0)), float(row.get("ema50", 0)), float(row.get("ema200", 0))
    stack = 0.0
    if ema20 > ema50:
        stack += 0.4
    if ema50 > ema200:
        stack += 0.4
    if bool(row.get("slope_up", False)):
        stack += 0.2
    trend_n = _clamp01(stack)

    # Setup proximity: closer to recent high = better (0% away -> 1, >=8% away -> 0)
    dist = float(row.get("dist_to_high_pct", 100.0))
    setup_n = _clamp01(1.0 - dist / 8.0)

    # Volume confirmation: 1.0x avg -> 0, >= surge multiple -> 1
    vr = float(row.get("vol_ratio", 0.0))
    denom = max(1e-9, cfg.volume_surge - 1.0)
    volume_n = _clamp01((vr - 1.0) / denom)

    # Momentum: RSI inside [low, high] sweet spot AND MACD>signal
    rsi = float(row.get("rsi", 0.0))
    in_zone = cfg.rsi_low <= rsi <= cfg.rsi_high
    macd_ok = float(row.get("macd", 0.0)) > float(row.get("macd_signal", 0.0))
    momentum_n = (0.6 if in_zone else 0.0) + (0.4 if macd_ok else 0.0)

    # R:R quality: more room to recent high relative to risk = better
    atr = float(row.get("atr", float("nan")))
    rr_n = 0.0
    if math.isfinite(atr) and atr > 0:
        risk_per_share = cfg.atr_stop_mult * atr
        reward = max(0.0, float(row.get("recent_high", close)) - close)
        rr_n = _clamp01((reward / risk_per_share) / cfg.target_2_r) if risk_per_share > 0 else 0.0

    breakdown = {
        "rel_strength": round(rs_n * cfg.w_rel_strength, 2),
        "trend_quality": round(trend_n * cfg.w_trend_quality, 2),
        "setup_proximity": round(setup_n * cfg.w_setup_proximity, 2),
        "volume": round(volume_n * cfg.w_volume, 2),
        "momentum": round(momentum_n * cfg.w_momentum, 2),
        "rr_quality": round(rr_n * cfg.w_rr_quality, 2),
    }
    total = round(sum(breakdown.values()), 2)
    return total, breakdown
