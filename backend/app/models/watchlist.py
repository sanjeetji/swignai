"""Watchlists & custom price alerts — retention layer (blueprint/13 future-vision §retention)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class Watchlist(Base, TimestampMixin):
    """A symbol a user wants to keep an eye on (one row per user+symbol)."""
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_watch_user_symbol"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)


class PriceAlert(Base, TimestampMixin):
    """'Alert me when SYMBOL goes above/below ₹X' — fires an in-app + email/SMS notification once."""
    __tablename__ = "price_alerts"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    direction: Mapped[str] = mapped_column(String(6))        # "above" | "below"
    target_price: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
