"""Billing + notifications (Phase 3 active; models defined now) — blueprint/06,20."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(20), default="free")  # free/pro/premium
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    razorpay_subscription_id: Mapped[str | None] = mapped_column(String(80))


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount_inr: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20))
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(80))


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    channel: Mapped[str] = mapped_column(String(20), default="inapp")  # inapp/email/whatsapp/sms
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    locale: Mapped[str] = mapped_column(String(8), default="en")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")
