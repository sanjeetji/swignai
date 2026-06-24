"""Daily picks — serves the deterministic quant engine output (blueprint/04,07).

In Phase 1 this runs the picker live against the configured data provider. In
production the daily cron pre-computes and caches in Redis; here we compute on
demand (cached) so the endpoint is real, not mocked.
"""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Query

from ..config import DEFAULT
from ..core.config import settings
from ..data.factory import get_provider
from ..quant import picker as picker_mod
from ..quant.features import build_features

router = APIRouter(tags=["picks"])

_cache: dict = {}


def _load_features(provider):
    index_close = provider.get_index()
    feats = {}
    for sym in provider.get_universe():
        df = provider.get_ohlcv(sym)
        if df is not None and not df.empty and len(df) >= DEFAULT.warmup_bars + 5:
            feats[sym] = build_features(df, index_close, DEFAULT)
    return feats, index_close


@router.get("/api/daily-picks")
async def daily_picks(limit: int = Query(5, ge=1, le=10)):
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    feats, index_close = _load_features(provider)
    date = index_close.index[-1]
    picks = picker_mod.get_top_picks(date, feats, index_close, settings.DEFAULT_CAPITAL, DEFAULT)[:limit]
    return {
        "date": str(date.date()),
        "regime": picks[0].regime if picks else "bear/none",
        "cash_mode": len(picks) == 0,
        "picks": [
            {
                "symbol": p.symbol, "score": p.score, "breakdown": p.breakdown,
                "regime": p.regime, "rsi": p.rsi, "rel_strength": p.rel_strength,
                "plan": {
                    "entry": p.plan.entry, "stop": p.plan.stop,
                    "target_1": p.plan.target_1, "target_2": p.plan.target_2,
                    "rr_ratio": p.plan.rr_ratio, "quantity": p.plan.quantity,
                    "position_size": p.plan.position_size,
                },
                "disclaimer": "Educational technical analysis only — not investment advice.",
            }
            for p in picks
        ],
    }
