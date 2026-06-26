"""Analytics & honest track record (blueprint/20). Win% = wins/(wins+losses+scratches).

Computed from real closed paper trades — no vanity numbers. With no trades yet it
returns an honest "insufficient data" rather than a fabricated figure.
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user, require_permissions
from ..models.trading import AIPick, PaperTrade
from ..models.user import User
from ..services.analytics import summarize_trades as _summarize
from ..services.tiers import require_tier

router = APIRouter(tags=["metrics"])


def _summarize_screener(picks: list[AIPick]) -> dict:
    """Honest record of the SCREENER's own resolved picks (R-multiples)."""
    closed = [p for p in picks if p.actual_result in ("hit_target", "hit_stoploss", "scratch", "time_exit")]
    if not closed:
        return {"resolved": 0, "open": len(picks), "note": "no resolved picks yet"}
    rs = [float(p.actual_r_multiple or 0) for p in closed]
    wins = [p for p in closed if (p.actual_r_multiple or 0) > 0.05]
    losses = [p for p in closed if (p.actual_r_multiple or 0) < -0.05]
    scratches = [p for p in closed if -0.05 <= (p.actual_r_multiple or 0) <= 0.05]
    decided = len(wins) + len(losses) + len(scratches)
    return {
        "resolved": len(closed), "open": len(picks) - len(closed),
        "expectancy_r": round(mean(rs), 3),
        "win_rate_pct": round(len(wins) / decided * 100, 1) if decided else 0,
        "wins": len(wins), "losses": len(losses), "scratches": len(scratches),
        "hit_target": sum(1 for p in closed if p.actual_result == "hit_target"),
        "hit_stoploss": sum(1 for p in closed if p.actual_result == "hit_stoploss"),
    }


@router.get("/api/track-record")
async def track_record(db: AsyncSession = Depends(get_db)):
    """Public honest scorecard — the SCREENER's resolved picks AND user paper trades."""
    picks = (await db.execute(select(AIPick))).scalars().all()
    trades = (await db.execute(select(PaperTrade))).scalars().all()
    return {
        "screener": _summarize_screener(list(picks)),   # did our picks work? (the moat)
        "paper_trades": _summarize(list(trades)),        # what users actually did
        "disclaimer": "Educational record of screened setups — not advice. "
                      "Win% counts wins/(wins+losses+scratches), in R-multiples, net. "
                      "Past results do not guarantee future returns.",
    }


@router.get("/api/analytics")
async def my_analytics(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(PaperTrade).where(PaperTrade.user_id == user.id))).scalars().all()
    return _summarize(list(rows))


@router.get("/api/analytics/equity")
async def my_equity_curve(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                          _tier=Depends(require_tier("pro"))):
    """Cumulative P&L (₹) and cumulative R over the user's closed trades, ordered by exit —
    the equity curve + R-multiple distribution (Pro+; trial grants full access)."""
    rows = (await db.execute(
        select(PaperTrade).where(PaperTrade.user_id == user.id, PaperTrade.status != "open")
        .order_by(PaperTrade.exit_date)
    )).scalars().all()

    curve, cum_pnl, cum_r = [], 0.0, 0.0
    dist = {"≤-1R": 0, "-1..0R": 0, "0..1R": 0, "1..2R": 0, "≥2R": 0}
    for i, t in enumerate(rows, start=1):
        cum_pnl += float(t.pnl_inr or 0)
        r = float(t.r_multiple or 0)
        cum_r += r
        curve.append({"i": i, "date": str(t.exit_date)[:10] if t.exit_date else None,
                      "symbol": t.stock_symbol, "pnl": round(cum_pnl, 2), "r": round(cum_r, 2),
                      "trade_r": round(r, 2)})
        bucket = ("≤-1R" if r <= -1 else "-1..0R" if r < 0 else "0..1R" if r < 1 else "1..2R" if r < 2 else "≥2R")
        dist[bucket] += 1
    return {"closed": len(rows), "curve": curve,
            "distribution": [{"bucket": k, "count": v} for k, v in dist.items()]}


@router.get("/api/trades")
async def my_trades(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """The user's trade journal — open + closed, with entry/exit reasons (Layer 2)."""
    rows = (await db.execute(
        select(PaperTrade).where(PaperTrade.user_id == user.id).order_by(desc(PaperTrade.entry_date))
    )).scalars().all()
    return {"trades": [{
        "id": str(t.id), "symbol": t.stock_symbol, "status": t.status,
        "entry": float(t.entry_price), "stop": float(t.stop_loss_set or 0), "target": float(t.target_set or 0),
        "qty": t.quantity, "exit": float(t.exit_price) if t.exit_price is not None else None,
        "pnl_inr": float(t.pnl_inr) if t.pnl_inr is not None else None,
        "r_multiple": float(t.r_multiple) if t.r_multiple is not None else None,
        "entry_date": str(t.entry_date)[:10], "exit_date": str(t.exit_date)[:10] if t.exit_date else None,
        "entry_reason": t.entry_reason, "exit_reason": t.exit_reason,
    } for t in rows]}


@router.get("/api/journal/review")
async def journal_review(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Post-trade review — discipline score + honest behavioural insights (Layer 2, blueprint/00)."""
    rows = (await db.execute(select(PaperTrade).where(PaperTrade.user_id == user.id))).scalars().all()
    closed = [t for t in rows if t.status in ("closed_profit", "closed_loss", "scratch")]
    if not closed:
        return {"closed": 0, "note": "Close some paper trades to see your review."}

    winners = [t for t in closed if t.status == "closed_profit"]
    losers = [t for t in closed if t.status == "closed_loss"]
    # winner exited BELOW its planned target = cut a winner early
    winners_early = [t for t in winners if t.target_set and t.exit_price and float(t.exit_price) < float(t.target_set)]
    # loss exited materially BELOW the planned stop = let a loser run past the stop
    stop_breaks = [t for t in losers if t.stop_loss_set and t.exit_price and float(t.exit_price) < float(t.stop_loss_set) * 0.995]

    n = len(closed)
    discipline = round(100 * (1 - (len(winners_early) + len(stop_breaks)) / n))
    insights = []
    if winners:
        insights.append({"key": "winners_early",
                         "text": f"You exited {len(winners_early)} of {len(winners)} winners before their target.",
                         "good": len(winners_early) == 0})
    if losers:
        insights.append({"key": "stop_breaks",
                         "text": f"You let {len(stop_breaks)} of {len(losers)} losers run past the stop.",
                         "good": len(stop_breaks) == 0})
    avg_hold = round(sum((t.exit_date - t.entry_date).days for t in closed if t.exit_date) / n, 1)
    insights.append({"key": "avg_hold", "text": f"Average hold: {avg_hold} days.", "good": True})

    return {"closed": n, "discipline_score": discipline,
            "winners_exited_early": len(winners_early), "stop_breaks": len(stop_breaks),
            "insights": insights,
            "note": "Discipline = trades where you followed the plan (held winners to target, respected stops)."}


@router.get("/api/admin/metrics")
async def admin_metrics(_=Depends(require_permissions("analytics.view")), db: AsyncSession = Depends(get_db)):
    """Platform business overview — real MRR/ARR/revenue/trials/conversion from live data."""
    from ..models.billing import Payment, Plan, Subscription

    now = datetime.now(timezone.utc)
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    trades = (await db.execute(select(func.count()).select_from(PaperTrade))).scalar_one()
    plans = {p.slug: p for p in (await db.execute(select(Plan))).scalars().all()}

    def live(sub: Subscription) -> bool:
        end = sub.current_period_end
        if end is not None and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return end is None or end >= now

    mrr = 0.0
    paying = 0
    active = (await db.execute(select(Subscription).where(Subscription.status == "active"))).scalars().all()
    for s in active:
        if not live(s):
            continue
        p = plans.get(s.plan)
        if p and float(p.price_inr) > 0:
            mrr += float(p.price_inr) / (12 if p.interval == "year" else 1)
            paying += 1

    trialing = (await db.execute(select(Subscription).where(Subscription.status == "trialing"))).scalars().all()
    trials = sum(1 for s in trialing if live(s))

    revenue = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount_inr), 0)).where(Payment.status == "captured")
    )).scalar_one()

    return {
        "users": users, "paper_trades": trades,
        "paying_customers": paying, "trial_users": trials,
        "mrr": round(mrr, 2), "arr": round(mrr * 12, 2),
        "total_revenue": float(revenue or 0),
        "conversion_pct": round(paying / users * 100, 1) if users else 0,
        "note": "Live from subscriptions + payments.",
    }
