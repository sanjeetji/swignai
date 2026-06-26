"""Nightly DPDP data-retention purge (blueprint/09,19).

Deletes personal/operational rows past their TTL so we don't hold data longer than
needed: stale sessions, old login history, and aged events. Audit events
(category in admin/security) are kept on a longer clock than ordinary events.
TTLs are configurable in settings. Idempotent — re-running deletes nothing new.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from ..core.config import settings
from ..core.db import SessionLocal
from ..models.event import EventLog
from ..models.session import LoginHistory, UserSession

logger = logging.getLogger("retention")

_AUDIT_CATEGORIES = ("admin", "security")


async def run() -> dict:
    now = datetime.now(timezone.utc)

    def cutoff(days: int) -> datetime:
        return now - timedelta(days=days)

    deleted: dict[str, int] = {}
    async with SessionLocal() as db:
        r = await db.execute(
            delete(UserSession).where(UserSession.created_at < cutoff(settings.SESSION_RETENTION_DAYS))
        )
        deleted["user_sessions"] = r.rowcount or 0

        r = await db.execute(
            delete(LoginHistory).where(LoginHistory.created_at < cutoff(settings.LOGIN_HISTORY_RETENTION_DAYS))
        )
        deleted["login_history"] = r.rowcount or 0

        r = await db.execute(
            delete(EventLog).where(
                EventLog.category.notin_(_AUDIT_CATEGORIES),
                EventLog.created_at < cutoff(settings.EVENT_LOG_RETENTION_DAYS),
            )
        )
        deleted["event_logs"] = r.rowcount or 0

        r = await db.execute(
            delete(EventLog).where(
                EventLog.category.in_(_AUDIT_CATEGORIES),
                EventLog.created_at < cutoff(settings.AUDIT_LOG_RETENTION_DAYS),
            )
        )
        deleted["audit_logs"] = r.rowcount or 0

        await db.commit()
    logger.info("retention purge: %s", deleted)
    return {"deleted": deleted}
