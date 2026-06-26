"""Daily pipeline (3:30 PM IST) — regime gate → picker → plans → explain → persist.

blueprint/07,10. Idempotent: upserts `ai_picks` on (symbol, date) and writes the day's
`regime_log`. Caches the served payload in Redis. Same picker code path as the backtest.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import select

from ..config import DEFAULT
from ..core.config import settings
from ..core.db import SessionLocal
from ..core.redis import cache_set
from ..data.factory import get_provider
from ..llm import generate_explanation
from ..data.sectors import sector_for
from ..models.trading import AIPick, RegimeLog
from ..services.revalidate import picks_paths, revalidate
from ..quant import picker as picker_mod
from ..quant import regime as regime_mod
from ..quant.features import analysis_dict, build_features
from ..services import event_log as ev

logger = logging.getLogger("daily_pipeline")


async def run(universe: str | None = None) -> dict:
    """`universe` (e.g. 'nifty50') scopes the scan to a tier for a fast first paint; default =
    the full configured universe (NIFTY 500)."""
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    if universe:
        from ..data.nifty500 import tier_symbols
        try:
            provider.universe = tier_symbols(universe)   # scope to the tier (angelone/dhan)
        except Exception:
            pass

    # The provider's market-data calls are blocking (Angel One HTTP). Run the whole fetch in a
    # worker thread so we don't freeze the event loop (which would make the API unresponsive —
    # e.g. the dashboard polling /api/daily-picks during the scan).
    import asyncio

    def _fetch_features():
        idx = provider.get_index()
        f = {}
        for sym in provider.get_universe():
            df = provider.get_ohlcv(sym)
            if df is not None and not df.empty and len(df) >= DEFAULT.warmup_bars + 5:
                f[sym] = build_features(df, idx, DEFAULT)
        return f, idx

    feats, index_close = await asyncio.to_thread(_fetch_features)

    date = index_close.index[-1]
    reg = regime_mod.regime_for_date(index_close, date, DEFAULT)
    picks = picker_mod.get_top_picks(date, feats, index_close, settings.DEFAULT_CAPITAL, DEFAULT)

    async with SessionLocal() as db:
        # regime_log (idempotent on date PK)
        existing_reg = await db.get(RegimeLog, date.date())
        nifty_close = float(index_close.loc[date])
        if existing_reg is None:
            db.add(RegimeLog(date=date.date(), nifty_close=nifty_close, regime=reg,
                             picks_generated=len(picks)))
        else:
            existing_reg.regime, existing_reg.picks_generated = reg, len(picks)
            existing_reg.nifty_close = nifty_close

        payload_picks = []
        for p in picks:
            plan = {"entry": p.plan.entry, "stop": p.plan.stop, "target_1": p.plan.target_1,
                    "target_2": p.plan.target_2, "rr_ratio": p.plan.rr_ratio,
                    "quantity": p.plan.quantity, "position_size": p.plan.position_size}
            expl = await generate_explanation({"symbol": p.symbol, "plan": plan, "rsi": p.rsi,
                                               "rel_strength": p.rel_strength, "regime": p.regime,
                                               "date": str(date.date())}, db=db)
            # upsert ai_picks on (symbol, date)
            row = (await db.execute(select(AIPick).where(
                AIPick.stock_symbol == p.symbol, AIPick.date_generated == date.date()))).scalar_one_or_none()
            if row is None:
                row = AIPick(stock_symbol=p.symbol, date_generated=date.date())
                db.add(row)
            row.sector = sector_for(p.symbol)
            row.score, row.score_breakdown, row.regime = p.score, p.breakdown, p.regime
            row.entry_price, row.stop_loss = p.plan.entry, p.plan.stop
            row.target_1, row.target_2, row.rr_ratio = p.plan.target_1, p.plan.target_2, p.plan.rr_ratio
            row.position_size_suggested = p.plan.position_size
            # full deterministic math snapshot for this pick (educational depth)
            feat_row = feats[p.symbol].iloc[-1]
            row.indicators = analysis_dict(feat_row)
            row.explanation_hinglish = expl
            row.actual_result = "still_open"
            payload_picks.append({"symbol": p.symbol, "score": p.score, "plan": plan,
                                  "regime": p.regime, "explanation_hinglish": expl})

        await ev.system(db, "pipeline.daily.completed", resource="ai_picks",
                        payload={"regime": reg, "count": len(picks), "date": str(date.date())})
        await db.commit()

    # Populate the scanner's full-scan cache (scan:latest) from the SAME features — but ONLY on a
    # full run. A tier (fast-paint) run must not overwrite scan:latest with a partial universe,
    # or the scanner's tier derivation would be wrong until the full run lands.
    if universe is None:
        try:
            from ..quant.scanner import scan_universe
            scan_data = scan_universe(date, feats, index_close, DEFAULT, settings.DEFAULT_CAPITAL)
            scan_data["date"] = str(date.date())
            for r in scan_data["results"]:
                r["sector"] = sector_for(r["symbol"])
            await cache_set("scan:latest", json.dumps(scan_data), ttl=60 * 60 * 24)
        except Exception:
            logger.exception("daily_pipeline: scan cache population failed")

    result = {"date": str(date.date()), "regime": reg, "cash_mode": len(picks) == 0,
              "picks": payload_picks}
    await cache_set(f"picks:{date.date()}", str(len(picks)), ttl=60 * 60 * 24)
    # refresh the public ISR pages on-demand (best-effort; never fails the job)
    await revalidate(picks_paths([p["symbol"] for p in payload_picks]))
    logger.info("daily_pipeline: %s picks for %s (regime=%s)", len(picks), date.date(), reg)
    return result
