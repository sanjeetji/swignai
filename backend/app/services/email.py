"""Transactional email (blueprint/19).

Sends via SMTP when configured (SMTP_HOST/USER/PASSWORD) — works with any provider
(Gmail, SendGrid, SES, Resend). Falls back to logging the message in dev so the flow
works with zero setup. Callers (password reset, etc.) don't change. Uses stdlib smtplib
in a worker thread so the async loop isn't blocked.
"""
from __future__ import annotations

import asyncio
import logging

from ..core.config import settings

logger = logging.getLogger("email")


def configured() -> bool:
    return bool(settings.SMTP_HOST)


async def send_email(to: str, subject: str, body: str) -> bool:
    if not configured():
        logger.info("EMAIL (no SMTP configured) → %s | %s\n%s", to, subject, body)
        return False

    def _send() -> None:
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
            s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
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
