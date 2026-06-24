"""Analytics & honest track record (blueprint/20). Win% = wins/(wins+losses+scratches).

Computed from real closed paper trades — no vanity numbers. With no trades yet it
returns an honest "insufficient data" rather than a fabricated figure.
"""
from __future__ import annotations

from statistics import mean

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user, require_permissions
from ..models.trading import PaperTrade
from ..models.user import User

router = APIRouter(tags=["metrics"])


def _summarize(trades: list[PaperTrade]) -> dict:
    closed = [t for t in trades if t.status != "open"]
    if not closed:
        return {"trades": 0, "note": "insufficient data — no closed trades yet"}
    wins = [t for t in closed if t.status == "closed_profit"]
    losses = [t for t in closed if t.status == "closed_loss"]
    scratches = [t for t in closed if t.status == "scratch"]
    rs = [float(t.r_multiple or 0) for t in closed]
    gp = sum(float(t.pnl_inr or 0) for t in closed if (t.pnl_inr or 0) > 0)
    gl = -sum(float(t.pnl_inr or 0) for t in closed if (t.pnl_inr or 0) < 0)
    decided = len(wins) + len(losses) + len(scratches)
    return {
        "trades": len(closed),
        "expectancy_r": round(mean(rs), 3),                       # headline
        "win_rate_pct": round(len(wins) / decided * 100, 1),      # incl. scratches
        "wins": len(wins), "losses": len(losses), "scratches": len(scratches),
        "profit_factor": round(gp / gl, 2) if gl > 0 else None,
        "total_pnl_inr": round(sum(float(t.pnl_inr or 0) for t in closed), 2),
    }


@router.get("/api/track-record")
async def track_record(db: AsyncSession = Depends(get_db)):
    """Public honest scorecard across all paper trades (the trust weapon)."""
    rows = (await db.execute(select(PaperTrade))).scalars().all()
    out = _summarize(list(rows))
    out["disclaimer"] = "Educational record of screened setups — not advice. Past results do not guarantee future returns."
    return out


@router.get("/api/analytics")
async def my_analytics(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(PaperTrade).where(PaperTrade.user_id == user.id))).scalars().all()
    return _summarize(list(rows))


@router.get("/api/admin/metrics")
async def admin_metrics(_=Depends(require_permissions("analytics.view")), db: AsyncSession = Depends(get_db)):
    """Platform overview — real counts (MRR/ARR wire in at Phase 3 with subscriptions)."""
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    trades = (await db.execute(select(func.count()).select_from(PaperTrade))).scalar_one()
    return {"users": users, "paper_trades": trades, "mrr": 0, "arr": 0,
            "note": "MRR/ARR populate once subscriptions are live (Phase 3)."}
