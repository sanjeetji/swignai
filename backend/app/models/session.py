"""Sessions, login history, blocks — blueprint/18."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class UserSession(Base, TimestampMixin):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ip: Mapped[str | None] = mapped_column(String(64))
    geo: Mapped[dict] = mapped_column(JSON, default=dict)        # {city,region,country,isp}
    device: Mapped[str | None] = mapped_column(String(120))
    browser: Mapped[str | None] = mapped_column(String(80))
    os: Mapped[str | None] = mapped_column(String(80))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LoginHistory(Base, TimestampMixin):
    __tablename__ = "login_history"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    ip: Mapped[str | None] = mapped_column(String(64))
    geo: Mapped[dict] = mapped_column(JSON, default=dict)
    device: Mapped[str | None] = mapped_column(String(120))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str | None] = mapped_column(String(120))


class UserBlock(Base, TimestampMixin):
    __tablename__ = "user_blocks"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
