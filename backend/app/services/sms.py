"""SMS / WhatsApp (blueprint/17,19) via Twilio's REST API (no SDK — basic-auth HTTP).

Creds resolve **vault → .env**: admin pastes Twilio creds in the Integrations tab
(provider "twilio": auth_token = secret, account_sid/from = config), else TWILIO_* from
backend/.env. A no-op (logs) until configured. `from` may be a number (SMS) or
`whatsapp:+…` (WhatsApp). Runs in a worker thread; never breaks the caller.
"""
from __future__ import annotations

import asyncio
import logging

from ..core.config import settings
from . import integrations

logger = logging.getLogger("sms")


async def _creds(db=None) -> dict:
    secret, cfg = await integrations.vault(db, "twilio")
    return {
        "sid": cfg.get("account_sid") or settings.TWILIO_ACCOUNT_SID,
        "token": secret or settings.TWILIO_AUTH_TOKEN,
        "from": cfg.get("from") or settings.TWILIO_FROM,
    }


async def configured(db=None) -> bool:
    c = await _creds(db)
    return bool(c["sid"] and c["token"] and c["from"])


async def send_sms(to: str, body: str, *, db=None) -> bool:
    if not to:
        return False
    c = await _creds(db)
    if not (c["sid"] and c["token"] and c["from"]):
        logger.info("SMS (no Twilio configured) → %s: %s", to, body)
        return False

    sender = c["from"]
    dest = f"whatsapp:{to}" if sender.startswith("whatsapp:") else to

    def _send() -> int:
        import requests
        r = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{c['sid']}/Messages.json",
            auth=(c["sid"], c["token"]),
            data={"From": sender, "To": dest, "Body": body},
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
