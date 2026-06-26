"""Daily picks — serves the deterministic quant engine output (blueprint/04,07).

Primary path: read today's pre-computed picks from the DB (`ai_picks`), populated by
the daily pipeline on REAL data (fast, no per-request market calls). Fallback: compute
live from the configured provider (used in dev/synthetic before the pipeline has run).
Framed as educational screening — not advice (blueprint/09).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import DEFAULT
from ..core.config import settings
from ..core.db import get_db
from ..core.redis import cache_get, cache_set
from ..data.factory import get_provider
from ..data.sectors import sector_for
from ..llm import generate_explanation
from ..models.trading import AIPick, RegimeLog
from ..quant import picker as picker_mod
from ..quant.features import analysis_dict, build_features

router = APIRouter(tags=["picks"])

DISCLAIMER = "Educational technical screening from real prices — not investment advice."


@router.get("/api/universe")
async def universe():
    """The tradeable NSE symbols we cover — drives the SEO sitemap + stock pages (blueprint/12).
    Cheap: returns the configured provider's static watchlist, no market calls."""
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    syms = [s[:-3] if s.upper().endswith(".NS") else s for s in provider.get_universe()]
    return {"symbols": syms, "count": len(syms)}


@router.get("/api/sectors")
async def sectors():
    """NSE sector → symbols map — drives the /sectors SEO pages (blueprint/12)."""
    from ..data.sectors import sectors_map
    m = sectors_map()
    return {"sectors": m, "count": len(m)}


@router.get("/api/scan")
async def scan(min_score: float = 0, sector: str | None = None, regime_bias: str | None = None):
    """Scan the whole tradeable universe and rank by score (blueprint/04) — the screener.
    Cached per day in Redis; filters (min score / sector / regime bias) applied server-side."""
    cache_key = "scan:latest"
    cached = await cache_get(cache_key)
    if cached:
        data = json.loads(cached)
    else:
        from ..quant.scanner import scan_universe
        provider = get_provider(settings.DATA_PROVIDER,
                                **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
        feats, index_close = _load_features(provider)
        if index_close is None or len(index_close) == 0:
            return {"date": None, "regime": "unknown", "count": 0, "results": []}
        date = index_close.index[-1]
        data = scan_universe(date, feats, index_close, DEFAULT, settings.DEFAULT_CAPITAL)
        data["date"] = str(date.date())
        for r in data["results"]:
            r["sector"] = sector_for(r["symbol"])
        await cache_set(cache_key, json.dumps(data), ttl=60 * 60 * 6)

    results = data["results"]
    if min_score:
        results = [r for r in results if r["score"] >= min_score]
    if sector:
        results = [r for r in results if (r.get("sector") or "").lower() == sector.lower()]
    if regime_bias == "bullish":
        results = [r for r in results if r["trend"] in ("Strong Up", "Up")]
    elif regime_bias == "valid":
        results = [r for r in results if r.get("valid_setup")]
    return {"date": data.get("date"), "regime": data.get("regime"), "count": len(results), "results": results}


def _load_features(provider):
    index_close = provider.get_index()
    feats = {}
    for sym in provider.get_universe():
        df = provider.get_ohlcv(sym)
        if df is not None and not df.empty and len(df) >= DEFAULT.warmup_bars + 5:
            feats[sym] = build_features(df, index_close, DEFAULT)
    return feats, index_close


async def _from_db(db: AsyncSession, limit: int):
    """Return today's pre-computed picks (latest date_generated) from the DB."""
    latest = (await db.execute(select(AIPick.date_generated).order_by(desc(AIPick.date_generated)).limit(1))).scalar_one_or_none()
    if latest is None:
        return None
    rows = (await db.execute(
        select(AIPick).where(AIPick.date_generated == latest).order_by(desc(AIPick.score)).limit(limit)
    )).scalars().all()
    reg = (await db.get(RegimeLog, latest))
    regime = reg.regime if reg else (rows[0].regime if rows else "unknown")
    return {
        "date": str(latest), "regime": regime, "cash_mode": len(rows) == 0, "source": "pipeline",
        "disclaimer": DISCLAIMER,
        "picks": [{
            "symbol": r.stock_symbol, "score": float(r.score) if r.score is not None else None,
            "breakdown": r.score_breakdown, "regime": r.regime, "analysis": r.indicators,
            "plan": {"entry": float(r.entry_price), "stop": float(r.stop_loss),
                     "target_1": float(r.target_1), "target_2": float(r.target_2),
                     "rr_ratio": float(r.rr_ratio), "position_size": float(r.position_size_suggested or 0),
                     "quantity": int(float(r.position_size_suggested or 0) / float(r.entry_price)) if r.entry_price else 0},
            "explanation_hinglish": r.explanation_hinglish,
        } for r in rows],
    }


@router.get("/api/daily-picks")
async def daily_picks(limit: int = Query(5, ge=1, le=10), db: AsyncSession = Depends(get_db)):
    # 1) prefer the pipeline's stored picks (real data, fast)
    from_db = await _from_db(db, limit)
    if from_db is not None:
        return from_db

    # 2) fallback: compute live from the configured provider (dev/synthetic)
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    feats, index_close = _load_features(provider)
    date = index_close.index[-1]
    picks = picker_mod.get_top_picks(date, feats, index_close, settings.DEFAULT_CAPITAL, DEFAULT)[:limit]
    out = []
    for p in picks:
        plan = {"entry": p.plan.entry, "stop": p.plan.stop, "target_1": p.plan.target_1,
                "target_2": p.plan.target_2, "rr_ratio": p.plan.rr_ratio,
                "quantity": p.plan.quantity, "position_size": p.plan.position_size}
        expl = await generate_explanation({"symbol": p.symbol, "plan": plan, "rsi": p.rsi,
                                           "rel_strength": p.rel_strength, "regime": p.regime,
                                           "date": str(date.date())})
        out.append({"symbol": p.symbol, "score": p.score, "breakdown": p.breakdown,
                    "regime": p.regime, "analysis": analysis_dict(feats[p.symbol].iloc[-1]),
                    "plan": plan, "explanation_hinglish": expl})
    return {"date": str(date.date()), "regime": picks[0].regime if picks else "bear/none",
            "cash_mode": len(picks) == 0, "source": "live", "disclaimer": DISCLAIMER, "picks": out}
