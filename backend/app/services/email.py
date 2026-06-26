"""Transactional email (blueprint/17,19).

Creds resolve **vault → .env** (like LLM/Razorpay): the admin can paste SMTP creds in the
Integrations tab (provider "smtp": password = secret, host/port/user/from = config), else
the SMTP_* values in backend/.env are used. Sends via stdlib smtplib in a worker thread;
falls back to logging when nothing is configured so dev works with zero setup.
"""
from __future__ import annotations

import asyncio
import logging

from ..core.config import settings
from . import integrations

logger = logging.getLogger("email")


async def _creds(db=None) -> dict:
    secret, cfg = await integrations.vault(db, "smtp")
    return {
        "host": cfg.get("host") or settings.SMTP_HOST,
        "port": int(cfg.get("port") or settings.SMTP_PORT or 587),
        "user": cfg.get("user") or settings.SMTP_USER,
        "password": secret or settings.SMTP_PASSWORD,
        "from": cfg.get("from") or settings.EMAIL_FROM,
    }


async def configured(db=None) -> bool:
    return bool((await _creds(db))["host"])


async def send_email(to: str, subject: str, body: str, *, db=None) -> bool:
    c = await _creds(db)
    if not c["host"]:
        logger.info("EMAIL (no SMTP configured) → %s | %s\n%s", to, subject, body)
        return False

    def _send() -> None:
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = c["from"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(c["host"], c["port"], timeout=15) as s:
            s.starttls()
            if c["user"]:
                s.login(c["user"], c["password"] or "")
            s.send_message(msg)

    try:
        await asyncio.to_thread(_send)
        logger.info("email sent → %s (%s)", to, subject)
        return True
    except Exception as e:  # never break the calling flow on a send failure
        logger.warning("email send failed → %s: %s", to, e)
        return False


def dev_mode() -> bool:
    """Whether to expose reset tokens/links in API responses (never in prod)."""
    return settings.ENV != "prod"
