"""The picker — orchestrates GATE 0 -> STAGE 1 -> STAGE 2 -> STAGE 3 (blueprint/04).

`get_top_picks` is the single entry point used by BOTH the live pipeline (later)
and the backtest engine — so what you backtest is exactly what you ship.
Deterministic: same inputs -> same output.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..config import StrategyConfig
from . import regime as regime_mod
from . import filters as filters_mod
from . import scorer as scorer_mod
from .risk import TradePlan, build_trade_plan


@dataclass
class Pick:
    symbol: str
    date: pd.Timestamp
    score: float
    breakdown: dict
    flags: dict
    plan: TradePlan
    regime: str
    rsi: float
    rel_strength: float


def _row_for_date(feat: pd.DataFrame, date: pd.Timestamp) -> pd.Series | None:
    sub = feat[feat.index <= date]
    if sub.empty:
        return None
    return sub.iloc[-1]


def get_top_picks(
    date: pd.Timestamp,
    features: dict[str, pd.DataFrame],
    index_close: pd.Series,
    capital: float,
    cfg: StrategyConfig,
) -> list[Pick]:
    """Return the ranked top-N picks for `date`, or [] in a bear regime (cash mode)."""
    reg = regime_mod.regime_for_date(index_close, date, cfg)
    if not regime_mod.is_tradeable(reg):
        return []

    candidates: list[Pick] = []
    for symbol, feat in features.items():
        row = _row_for_date(feat, date)
        if row is None:
            continue
        if row.isna().get("ema200", True):  # not enough warmup
            continue

        fr = filters_mod.passes_knockouts(row, cfg)
        if not fr.passed:
            continue

        plan = build_trade_plan(row, capital, cfg)
        if plan is None or plan.quantity <= 0:
            continue

        score, breakdown = scorer_mod.score_row(row, cfg)
        candidates.append(
            Pick(
                symbol=symbol,
                date=row.name,
                score=score,
                breakdown=breakdown,
                flags=fr.flags,
                plan=plan,
                regime=reg,
                rsi=round(float(row.get("rsi", 0.0)), 2),
                rel_strength=round(float(row.get("rel_strength", 0.0)), 2),
            )
        )

    # neutral regime -> trade fewer / smaller (halve the slate)
    top_n = cfg.top_n if reg == "bull" else max(1, cfg.top_n // 2)
    candidates.sort(key=lambda p: p.score, reverse=True)
    return candidates[:top_n]
