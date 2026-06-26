"""Universe scanner (blueprint/04) — scores EVERY stock in the universe (not only valid
setups) so the UI can present a full ranked watchlist with trend / relative-strength /
volume, like a professional scanner. Deterministic + read-only over precomputed features.
"""
from __future__ import annotations

import pandas as pd

from ..config import StrategyConfig
from . import filters as filters_mod
from . import regime as regime_mod
from . import scorer as scorer_mod
from .picker import _row_for_date


def _trend_label(row: pd.Series) -> str:
    c = float(row.get("close", 0) or 0)
    e20 = float(row.get("ema20", 0) or 0)
    e50 = float(row.get("ema50", 0) or 0)
    e200 = float(row.get("ema200", 0) or 0)
    if c > e20 > e50 > e200:
        return "Strong Up"
    if c > e50 and c > e20:
        return "Up"
    if c < e50 and c < e20:
        return "Down"
    return "Consolidating"


def scan_universe(date: pd.Timestamp, features: dict[str, pd.DataFrame],
                  index_close: pd.Series, cfg: StrategyConfig) -> dict:
    reg = regime_mod.regime_for_date(index_close, date, cfg)
    rows: list[dict] = []
    for symbol, feat in features.items():
        row = _row_for_date(feat, date)
        if row is None or bool(row.isna().get("ema200", True)):
            continue
        score, _ = scorer_mod.score_row(row, cfg)
        fr = filters_mod.passes_knockouts(row, cfg)
        rows.append({
            "symbol": symbol[:-3] if symbol.upper().endswith(".NS") else symbol,
            "score": round(float(score), 1),
            "rel_strength": round(float(row.get("rel_strength", 0.0) or 0), 2),
            "trend": _trend_label(row),
            "vol_ratio": round(float(row.get("vol_ratio", 0.0) or 0), 2),
            "rsi": round(float(row.get("rsi", 0.0) or 0), 1),
            "valid_setup": bool(fr.passed),
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return {"regime": reg, "results": rows}
