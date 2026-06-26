"""SMS / WhatsApp (blueprint/19) via Twilio's REST API (no SDK — basic-auth HTTP).

Gated on TWILIO_* creds; a no-op (logs) until configured. `TWILIO_FROM` may be a normal
number (SMS) or `whatsapp:+…` (WhatsApp). Runs in a worker thread; never breaks the caller.
"""
from __future__ import annotations

import asyncio
import logging

from ..core.config import settings

logger = logging.getLogger("sms")


def configured() -> bool:
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM)


async def send_sms(to: str, body: str) -> bool:
    if not to:
        return False
    if not configured():
        logger.info("SMS (no Twilio configured) → %s: %s", to, body)
        return False

    # WhatsApp 'from' implies a 'whatsapp:' prefix on 'to' as well.
    dest = to if not settings.TWILIO_FROM.startswith("whatsapp:") else f"whatsapp:{to}"

    def _send() -> int:
        import requests
        sid = settings.TWILIO_ACCOUNT_SID
        r = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            auth=(sid, settings.TWILIO_AUTH_TOKEN),
            data={"From": settings.TWILIO_FROM, "To": dest, "Body": body},
            timeout=15,
        )
        return r.status_code

    try:
        code = await asyncio.to_thread(_send)
        logger.info("sms → %s (HTTP %s)", to, code)
        return 200 <= code < 300
    except Exception as e:
        logger.warning("sms send failed → %s: %s", to, e)
        return False
