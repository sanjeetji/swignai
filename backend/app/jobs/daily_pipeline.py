"""Daily pipeline (3:30 PM IST) — regime gate → picker → plans → explain → persist.

blueprint/07,10. Idempotent: upserts `ai_picks` on (symbol, date) and writes the day's
`regime_log`. Caches the served payload in Redis. Same picker code path as the backtest.
"""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import select

from ..config import DEFAULT
from ..core.config import settings
from ..core.db import SessionLocal
from ..core.redis import cache_set
from ..data.factory import get_provider
from ..llm import generate_explanation
from ..models.trading import AIPick, RegimeLog
from ..quant import picker as picker_mod
from ..quant import regime as regime_mod
from ..quant.features import build_features
from ..services import event_log as ev

logger = logging.getLogger("daily_pipeline")


async def run() -> dict:
    provider = get_provider(settings.DATA_PROVIDER,
                            **({"days": 600} if settings.DATA_PROVIDER == "synthetic" else {}))
    index_close = provider.get_index()
    feats = {}
    for sym in provider.get_universe():
        df = provider.get_ohlcv(sym)
        if df is not None and not df.empty and len(df) >= DEFAULT.warmup_bars + 5:
            feats[sym] = build_features(df, index_close, DEFAULT)

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
                                               "date": str(date.date())})
            # upsert ai_picks on (symbol, date)
            row = (await db.execute(select(AIPick).where(
                AIPick.stock_symbol == p.symbol, AIPick.date_generated == date.date()))).scalar_one_or_none()
            if row is None:
                row = AIPick(stock_symbol=p.symbol, date_generated=date.date())
                db.add(row)
            row.score, row.score_breakdown, row.regime = p.score, p.breakdown, p.regime
            row.entry_price, row.stop_loss = p.plan.entry, p.plan.stop
            row.target_1, row.target_2, row.rr_ratio = p.plan.target_1, p.plan.target_2, p.plan.rr_ratio
            row.position_size_suggested = p.plan.position_size
            row.indicators = {"rsi": p.rsi, "rel_strength": p.rel_strength}
            row.explanation_hinglish = expl
            row.actual_result = "still_open"
            payload_picks.append({"symbol": p.symbol, "score": p.score, "plan": plan,
                                  "regime": p.regime, "explanation_hinglish": expl})

        await ev.system(db, "pipeline.daily.completed", resource="ai_picks",
                        payload={"regime": reg, "count": len(picks), "date": str(date.date())})
        await db.commit()

    result = {"date": str(date.date()), "regime": reg, "cash_mode": len(picks) == 0,
              "picks": payload_picks}
    await cache_set(f"picks:{date.date()}", str(len(picks)), ttl=60 * 60 * 24)
    logger.info("daily_pipeline: %s picks for %s (regime=%s)", len(picks), date.date(), reg)
    return result
