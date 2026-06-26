"""Notifications (blueprint/20) — create an in-app notification (always) and, when a
provider is configured, fan out to email / SMS. In-app works with zero external deps;
email (SMTP) and SMS (Twilio) are gated on creds, so fan-out is a safe no-op until set.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.billing import Notification
from ..models.user import User
from . import email as email_svc
from . import sms as sms_svc

logger = logging.getLogger("notify")


def _format(type_: str, payload: dict) -> tuple[str, str]:
    sym = payload.get("symbol", "")
    if type_.startswith("trade."):
        outcome = payload.get("outcome", type_.split(".")[-1])
        return (f"SwingAI: {sym} {outcome}",
                f"Your paper trade {sym} closed ({outcome}). "
                f"Exit ₹{payload.get('exit')}, P&L ₹{payload.get('pnl_inr')} "
                f"({payload.get('r_multiple')}R). Educational tracking — not advice.")
    return (f"SwingAI: {type_}", "; ".join(f"{k}={v}" for k, v in payload.items()))


async def _fanout(db: AsyncSession, user_id, type_: str, payload: dict) -> None:
    """Best-effort email/SMS dispatch — never breaks the calling job."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        return
    subject, body = _format(type_, payload)
    try:
        if email_svc.configured() and user.email:
            await email_svc.send_email(user.email, subject, body)
        if sms_svc.configured() and user.phone:
            await sms_svc.send_sms(user.phone, body)
    except Exception as e:
        logger.warning("notify fan-out failed for user %s: %s", user_id, e)


async def push(db: AsyncSession, user_id, type_: str, payload: dict,
               channel: str = "inapp", *, fanout: bool = True) -> Notification:
    """Create an in-app notification row (caller commits) and, when email/SMS providers
    are configured, fan the same alert out to those channels. Returns the in-app row."""
    n = Notification(user_id=user_id, type=type_, channel=channel, payload=payload, status="sent")
    db.add(n)
    if fanout and (email_svc.configured() or sms_svc.configured()):
        await _fanout(db, user_id, type_, payload)
    elif channel != "inapp":
        logger.info("notify[%s] → user %s: %s", channel, user_id, type_)
    return n
