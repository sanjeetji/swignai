"""Watchlist + custom price alerts + digest preference (retention — blueprint/13)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import get_current_user
from ..data.nifty500 import NIFTY_500
from ..models.platform import UserPreference
from ..models.user import User
from ..models.watchlist import PriceAlert, Watchlist
from ..services.tiers import require_access

router = APIRouter(prefix="/api", tags=["watchlist"])

_UNIVERSE = set(NIFTY_500)


# ---- Watchlist --------------------------------------------------------------
class WatchIn(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def _up(cls, v: str) -> str:
        return v.strip().upper()


@router.get("/watchlist")
async def get_watchlist(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                        _gate=Depends(require_access())):
    """The user's watched symbols, enriched with the latest cached price + screener score."""
    from .paper import _live_prices
    rows = (await db.execute(select(Watchlist).where(Watchlist.user_id == user.id)
            .order_by(Watchlist.created_at.desc()))).scalars().all()
    prices = await _live_prices()
    scores = await _latest_scores()
    items = [{"symbol": w.symbol, "price": prices.get(w.symbol),
              "score": scores.get(w.symbol, {}).get("score"),
              "regime_ok": scores.get(w.symbol, {}).get("passes")} for w in rows]
    return {"items": items, "disclaimer": "Educational technical screening, not investment advice."}


@router.post("/watchlist")
async def add_watch(body: WatchIn, user: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db), _gate=Depends(require_access())):
    if body.symbol not in _UNIVERSE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown symbol")
    exists = (await db.execute(select(Watchlist).where(
        Watchlist.user_id == user.id, Watchlist.symbol == body.symbol))).scalar_one_or_none()
    if not exists:
        db.add(Watchlist(user_id=user.id, symbol=body.symbol))
        await db.commit()
    return {"ok": True, "symbol": body.symbol}


@router.delete("/watchlist/{symbol}")
async def remove_watch(symbol: str, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db), _gate=Depends(require_access())):
    await db.execute(delete(Watchlist).where(
        Watchlist.user_id == user.id, Watchlist.symbol == symbol.strip().upper()))
    await db.commit()
    return {"ok": True}


# ---- Price alerts -----------------------------------------------------------
class AlertIn(BaseModel):
    symbol: str
    direction: str            # "above" | "below"
    target_price: float

    @field_validator("symbol")
    @classmethod
    def _up(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("direction")
    @classmethod
    def _dir(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("above", "below"):
            raise ValueError("direction must be 'above' or 'below'")
        return v


@router.get("/alerts")
async def list_alerts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                      _gate=Depends(require_access())):
    rows = (await db.execute(select(PriceAlert).where(PriceAlert.user_id == user.id)
            .order_by(PriceAlert.created_at.desc()))).scalars().all()
    return {"alerts": [{"id": str(a.id), "symbol": a.symbol, "direction": a.direction,
                        "target_price": a.target_price, "is_active": a.is_active,
                        "triggered_at": str(a.triggered_at) if a.triggered_at else None} for a in rows]}


@router.post("/alerts")
async def create_alert(body: AlertIn, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db), _gate=Depends(require_access())):
    if body.symbol not in _UNIVERSE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown symbol")
    if body.target_price <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Target price must be positive")
    a = PriceAlert(user_id=user.id, symbol=body.symbol, direction=body.direction,
                   target_price=body.target_price, is_active=True)
    db.add(a)
    await db.commit()
    return {"ok": True, "id": str(a.id)}


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db), _gate=Depends(require_access())):
    await db.execute(delete(PriceAlert).where(
        PriceAlert.id == alert_id, PriceAlert.user_id == user.id))
    await db.commit()
    return {"ok": True}


# ---- Digest preference ------------------------------------------------------
class DigestIn(BaseModel):
    email_digest: bool


@router.put("/me/digest")
async def set_digest(body: DigestIn, user: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    pref = (await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))).scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=user.id)
        db.add(pref)
    pref.email_digest = body.email_digest
    await db.commit()
    return {"ok": True, "email_digest": body.email_digest}


async def _latest_scores() -> dict:
    """symbol → {score, passes} from the scanner cache (best-effort)."""
    import json
    from ..core.redis import cache_get
    cached = await cache_get("scan:latest")
    if not cached:
        return {}
    try:
        data = json.loads(cached)
        return {r["symbol"]: {"score": r.get("score"), "passes": r.get("passes")}
                for r in data.get("results", [])}
    except (ValueError, KeyError, TypeError):
        return {}
