"""Unified event log + DPDP data-subject requests — blueprint/22, 09."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class EventLog(Base):
    """APPEND-ONLY unified event stream (blueprint/22). Audit log = category in (admin,security)."""
    __tablename__ = "event_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    event_type: Mapped[str] = mapped_column(String(80), index=True)     # dotted, e.g. auth.login.success
    category: Mapped[str] = mapped_column(String(20), index=True)       # security/admin/integration/system/product/data/billing
    level: Mapped[str] = mapped_column(String(12), default="info", index=True)  # debug/info/warning/error/critical
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    actor_role: Mapped[str | None] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(12), default="api", index=True)  # api/job/system/webhook/cli
    resource: Mapped[str | None] = mapped_column(String(60))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    payload: Mapped[dict | None] = mapped_column(JSON)
    request_id: Mapped[str | None] = mapped_column(String(40), index=True)
    ip: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(120))
    user_agent: Mapped[str | None] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DataSubjectRequest(Base, TimestampMixin):
    """DPDP/GDPR export/delete requests with statutory deadline (blueprint/09)."""
    __tablename__ = "data_subject_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    requested_email: Mapped[str] = mapped_column(String(255), index=True)
    request_type: Mapped[str] = mapped_column(String(20))     # export/delete/rectify
    status: Mapped[str] = mapped_column(String(20), default="pending")
    regulation: Mapped[str] = mapped_column(String(10), default="dpdp")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
