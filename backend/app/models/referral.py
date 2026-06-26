"""Referrals (blueprint/14 growth) — a shareable code per user + who-referred-whom."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)


class Referral(Base, TimestampMixin):
    """One row per referred user (a user can be referred at most once)."""
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = uuid_pk()
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    referred_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    code: Mapped[str | None] = mapped_column(String(16))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
