"""Transactional email (blueprint/19).

No email provider is wired yet, so in dev this logs the message (and password-reset
endpoints surface the link in the response when ENV != prod, for testing). Production
plugs SMTP / Resend / SES in here behind the same `send_email` signature — callers
don't change.
"""
from __future__ import annotations

import logging

from ..core.config import settings

logger = logging.getLogger("email")


async def send_email(to: str, subject: str, body: str) -> bool:
    # TODO: wire a provider (SMTP/Resend/SES) via settings.EMAIL_* in production.
    logger.info("EMAIL → %s | %s\n%s", to, subject, body)
    return True


def dev_mode() -> bool:
    """Whether to expose reset tokens/links in API responses (never in prod)."""
    return settings.ENV != "prod"
