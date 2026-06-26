"""Notifications (blueprint/20) — create an in-app notification (always) and, when a
provider is configured, fan out to email/WhatsApp/SMS. The external channels are a seam
(gated on creds) like the email service; in-app works with zero external dependencies.
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.billing import Notification

logger = logging.getLogger("notify")


async def push(db: AsyncSession, user_id, type_: str, payload: dict, channel: str = "inapp") -> Notification:
    """Create an in-app notification row (caller commits). Returns the row."""
    n = Notification(user_id=user_id, type=type_, channel=channel, payload=payload, status="sent")
    db.add(n)
    # external channels (email/whatsapp/sms) would dispatch here once a provider is wired.
    if channel != "inapp":
        logger.info("notify[%s] → user %s: %s", channel, user_id, type_)
    return n
