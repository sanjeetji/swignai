"""Daily picks — serves the deterministic quant engine output (blueprint/04,07).

Primary path: read today's pre-computed picks from the DB (`ai_picks`), populated by
the daily pipeline on REAL data (fast, no per-request market calls). Fallback: compute
live from the configured provider (used in dev/synthetic before the pipeline has run).
Framed as educational screening — not advice (blueprint/09).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import DEFAULT
from ..core.config import settings
from ..core.db import get_db
from ..core.redis import cache_get, cache_set
from ..core.security import get_current_user
from ..data.factory import get_provider
from ..data.sectors import sector_for
from ..llm import generate_explanation
from ..models.trading import AIPick, RegimeLog
from ..quant import picker as picker_mod
from ..quant.features import analysis_dict, build_features

router = APIRouter(tags=["picks"])

DISCLAIMER = "Educational technical screening from real prices — not investment advice."

# NSE regular session in IST (Mon–Fri 09:15–15:30; 09:00–09:15 pre-open). Holidays aren't
# modelled here — a holiday simply shows "closed" with the last available close, which is honest.
from datetime import datetime, time as _time, timedelta, timezone as _tz  # noqa: E402

_IST = _tz(timedelta(hours=5, minutes=30))


def _nse_session(now_ist: datetime) -> str:
    if now_ist.weekday() >= 5:
        return "closed"
    t = now_ist.time()
    if _time(9, 0) <= t < _time(9, 15):
        return "pre-open"
    if _time(9, 15) <= t <= _time(15, 30):
        return "open"
    return "closed"


async def _live_nifty() -> float | None:
    """Best-effort latest NIFTY value from the live provider, cached 60s. None on any error."""
    cached = await cache_get("market:nifty_live")
    if cached is not None:
        try:
            return float(cached)
        except (TypeError, ValueError):
            return None
    try:
        import asyncio
        provider = get_provider(settings.DATA_PROVIDER,
                                **({"days": 30} if settings.DATA_PROVIDER == "synthetic" else {}))
        series = await asyncio.to_thread(provider.get_index)
        if series is None or len(series) == 0:
            return None
        val = float(series.iloc[-1])
        await cache_set("market:nifty_live", val, ttl=60)
        return val
    except Exception:
        return None


@router.get("/api/market-status")
async def market_status(db: AsyncSession = Depends(get_db)):
    """Live-ish market state for the dashboard banner: NSE session (open/pre-open/closed),
    regime, NIFTY level + trend. When the market is open we try a fresh index value (cached
    60s); otherwise we show the last available close from the daily pipeline."""
    now_ist = datetime.now(_IST)
    session = _nse_session(now_ist)
    reg = (await db.execute(select(RegimeLog).order_by(desc(RegimeLog.date)).limit(1))).scalar_one_or_none()
    last_close = float(reg.nifty_close) if reg and reg.nifty_close is not None else None
    ema20 = float(reg.nifty_ema20) if reg and reg.nifty_ema20 is not None else None
    regime = (reg.regime if reg else None) or "unknown"
    as_of = str(reg.date) if reg else None

    live = await _live_nifty() if session in ("open", "pre-open") else None
    level = live if live is not None else last_close
    # Trend from the regime gate (the actual signal); fall back to level-vs-EMA20 if regime unknown.
    if regime == "bull":
        trend = "up"
    elif regime == "bear":
        trend = "down"
    elif level is not None and ema20 is not None:
        trend = "up" if level >= ema20 else "down"
    else:
        trend = "flat"
    change_pct = round((level - last_close) / last_close * 100, 2) if (live is not None and last_close) else None

    return {
        "session": session,                      # open | pre-open | closed
        "is_open": session == "open",
        "regime": regime,                        # bull | neutral | bear | unknown
        "trend": trend,                          # up | down
        "index": {
            "symbol": "NIFTY 50",
            "level": round(level, 2) if level is not None else None,
            "ema20": round(ema20, 2) if ema20 is not None else None,
            "last_close": round(last_close, 2) if last_close is not None else None,
            "change_pct": change_pct,            # vs last close, only when a live value is fresh
            "live": live is not None,            # true = freshly fetched; false = last close
            "as_of": as_of,
        },
        "server_time_ist": now_ist.strftime("%d %b %Y, %H:%M IST"),
        "disclaimer": DISCLAIMER,
    }


# Simple in-process guard so concurrent dashboard opens don't run the pipeline twice.
_refresh_in_progress = False


@router.post("/api/daily-picks/refresh")
async def refresh_daily_picks(force: bool = Query(False),
                              user=Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    """Populate today's picks by running the screener pipeline. Idempotent + freshness-gated:
    a no-op when the DB already holds today's picks (so it's safe for the dashboard to call on
    first open after a fresh install). `force=true` re-runs regardless. Auth-required."""
    global _refresh_in_progress
    # `date_generated` is the latest TRADING day (may be < today on weekends/holidays), so we
    # gate on "any picks exist" rather than "== today" — this endpoint exists to populate an
    # EMPTY db (first run / after `fresh`). Daily freshness is the scheduler's / `force`'s job.
    latest = (await db.execute(select(func.max(AIPick.date_generated)))).scalar()
    if latest is not None and not force:
        return {"ran": False, "reason": "up_to_date", "date": str(latest)}
    if _refresh_in_progress:
        return {"ran": False, "reason": "in_progress"}
    _refresh_in_progress = True
    try:
        from ..jobs.daily_pipeline import run
        r = await run()
        return {"ran": True, "regime": r.get("regime"), "count": len(r.get("picks", [])),
                "date": str(datetime.now(_IST).date())}
    except Exception as e:
        return {"ran": False, "reason": "error", "detail": str(e)[:200]}
    finally:
        _refresh_in_progress = False


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
                                           "date": str(date.date())}, db=db)
        out.append({"symbol": p.symbol, "score": p.score, "breakdown": p.breakdown,
                    "regime": p.regime, "analysis": analysis_dict(feats[p.symbol].iloc[-1]),
                    "plan": plan, "explanation_hinglish": expl})
    return {"date": str(date.date()), "regime": picks[0].regime if picks else "bear/none",
            "cash_mode": len(picks) == 0, "source": "live", "disclaimer": DISCLAIMER, "picks": out}
