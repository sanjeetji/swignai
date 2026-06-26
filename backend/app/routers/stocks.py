"""Per-stock technical analysis (educational) — blueprint/08,12.

Returns the FULLY MATHEMATICAL indicator snapshot for a symbol on real data, plus
which swing-screening conditions it currently meets and (if valid) the deterministic
trade plan. Framed as educational analysis — NOT a recommendation (blueprint/09).
Cached so on-demand yfinance calls don't repeat per request.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, status

from ..config import DEFAULT
from ..core.config import settings
from ..core.redis import cache_get, cache_set
from ..data.factory import get_provider
from ..quant import filters as filters_mod
from ..quant import scorer as scorer_mod
from ..quant.features import analysis_dict, build_features
from ..quant.risk import build_trade_plan

router = APIRouter(tags=["stocks"])


def _norm(symbol: str) -> str:
    s = symbol.upper().strip()
    if settings.DATA_PROVIDER in ("yfinance", "yahoo") and "." not in s:
        s += ".NS"
    return s


@router.get("/api/stocks/{symbol}")
async def stock_analysis(symbol: str):
    sym = _norm(symbol)
    cache_key = f"analysis:{sym}"
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)

    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    df = provider.get_ohlcv(sym)
    if df is None or df.empty or len(df) < DEFAULT.warmup_bars + 5:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Not enough price data for {sym}")

    feats = build_features(df, provider.get_index(), DEFAULT)
    row = feats.iloc[-1]

    fr = filters_mod.passes_knockouts(row, DEFAULT)
    plan = build_trade_plan(row, settings.DEFAULT_CAPITAL, DEFAULT)
    score, breakdown = scorer_mod.score_row(row, DEFAULT)

    out = {
        "symbol": sym,
        "as_of": str(row.name.date()),
        "analysis": analysis_dict(row),               # the deterministic math
        "swing_screen": {
            "meets_all_conditions": fr.passed,
            "conditions": fr.flags,                    # each knockout, true/false
            "score": score, "score_breakdown": breakdown,
        },
        "trade_plan": None if plan is None else {
            "entry": plan.entry, "stop": plan.stop, "target_1": plan.target_1,
            "target_2": plan.target_2, "rr_ratio": plan.rr_ratio,
            "quantity": plan.quantity, "position_size": plan.position_size,
        },
        "disclaimer": "Educational technical analysis computed from real prices — not investment advice. "
                      "Conditions met do not imply future returns.",
    }
    await cache_set(cache_key, json.dumps(out), ttl=60 * 60 * 6)
    return out
