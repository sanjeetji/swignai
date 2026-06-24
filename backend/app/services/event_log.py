"""Event log emit() — fire-and-forget, never breaks the request path (blueprint/22 §4).

Usage:
    from app.services import event_log as ev
    await ev.emit(db, "auth.login.success", category="security", user=user, ip=ip)

Caller controls commit: if the caller's transaction rolls back, the event does too
(correct — no log for an action that didn't happen). Secrets' VALUES are never logged.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.event import EventLog

logger = logging.getLogger("event_log")


async def emit(
    db: AsyncSession,
    event_type: str,
    *,
    category: str = "system",
    level: str = "info",
    user=None,
    source: str = "api",
    resource: str | None = None,
    resource_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    payload: dict | None = None,
    request_id: str | None = None,
    ip: str | None = None,
    location: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        db.add(
            EventLog(
                event_type=event_type[:80],
                category=category,
                level=level,
                actor_user_id=(user.id if user else None),
                actor_role=getattr(user, "_primary_role", None) if user else None,
                source=source,
                resource=resource,
                resource_id=(str(resource_id)[:64] if resource_id is not None else None),
                before=before,
                after=after,
                payload=payload,
                request_id=request_id,
                ip=(ip or None),
                location=location,
                user_agent=(user_agent[:400] if user_agent else None),
                created_at=datetime.now(timezone.utc),
            )
        )
    except Exception as e:  # logging must never break the request
        logger.warning("event_log.emit failed (%s): %s", event_type, e)


# convenience wrappers
async def security(db, event_type, **kw):
    await emit(db, event_type, category="security", **kw)


async def admin(db, event_type, **kw):
    await emit(db, event_type, category="admin", **kw)


async def system(db, event_type, **kw):
    await emit(db, event_type, category="system", **kw)
