"""STAGE 1 — knockout filters. Must pass ALL (blueprint/04 §3).

These define whether a stock is a *valid* candidate at all — no scoring, no partial
credit. A row that fails any filter is rejected.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..config import StrategyConfig
from . import risk


@dataclass
class FilterResult:
    passed: bool
    flags: dict           # name -> bool, for transparency/UI
    reason: str = ""      # first failing filter


def passes_knockouts(row: pd.Series, cfg: StrategyConfig) -> FilterResult:
    close = float(row["close"])
    flags: dict = {}

    flags["liquidity"] = bool(row.get("turnover_cr", float("nan")) >= cfg.min_turnover_cr)
    flags["weekly_tide"] = bool(close > row.get("weekly_ema", float("nan")))
    flags["daily_trend"] = bool(close > row.get("ema50", float("nan")) and bool(row.get("slope_up", False)))
    flags["not_extended"] = bool(row.get("ext_above_slope_pct", float("inf")) <= cfg.max_extension_pct)
    atr_pct = float(row.get("atr_pct", float("nan")))
    flags["volatility_ok"] = bool(cfg.atr_min_pct <= atr_pct <= cfg.atr_max_pct)

    # valid stop must allow R:R >= min_rr
    plan = risk.build_trade_plan(row, capital=100000.0, cfg=cfg)
    flags["valid_stop_rr"] = bool(plan is not None and plan.rr_ratio >= cfg.min_rr)

    # optional, walk-forward-gated signal filters (no-ops at default config)
    if cfg.adx_min > 0:
        flags["trend_strength"] = bool(float(row.get("adx", float("nan"))) >= cfg.adx_min)
    if cfg.require_obv_accum:
        flags["accumulation"] = bool(row.get("obv_slope_up", False))
    if cfg.bb_max_pct_b < 1.5:
        flags["not_band_extended"] = bool(float(row.get("bb_pct_b", float("inf"))) <= cfg.bb_max_pct_b)

    # any NaN in a flag means insufficient history -> fail
    failing = [name for name, ok in flags.items() if not ok]
    passed = len(failing) == 0
    return FilterResult(passed=passed, flags=flags, reason=("" if passed else failing[0]))
