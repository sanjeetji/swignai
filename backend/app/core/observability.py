"""Error tracking / observability (blueprint/19).

Sentry is wired but OFF until SENTRY_DSN is set — so dev/CI run with zero external
calls, and production gets full error + performance capture the moment the DSN lands
in the environment. No-op and import-safe when the SDK or DSN is absent.
"""
from __future__ import annotations

import logging

from .config import settings

logger = logging.getLogger("observability")


def init_sentry() -> bool:
    """Initialise Sentry if a DSN is configured. Returns True when active."""
    if not settings.SENTRY_DSN:
        logger.info("Sentry disabled (no SENTRY_DSN)")
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning("sentry-sdk not installed; error tracking disabled")
        return False

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV,
        release=f"swingai@{settings.RELEASE}" if settings.RELEASE else None,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,           # never ship user PII to Sentry (DPDP)
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    logger.info("Sentry initialised (env=%s)", settings.ENV)
    return True
