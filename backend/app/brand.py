"""Brand — the single source of truth for the platform name, in code.

Renaming the whole platform must be cheap. EVERY backend reference to the product
name goes through here; nothing hardcodes "SwingAI". Values come from env (12-factor),
falling back to brand/brand.config.json, falling back to safe defaults.

To rename: edit brand/brand.config.json (or set APP_NAME env), and for source text
run scripts/rename-brand.sh. See brand/BRAND.md.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "brand" / "brand.config.json"

_DEFAULTS = {
    "name": "SwingAI",
    "shortName": "SwingAI",
    "legalName": "SwingAI",
    "tagline": "Disciplined swing trading, proven honestly.",
    "domain": "swingai.in",
    "supportEmail": "support@swingai.in",
}


@lru_cache(maxsize=1)
def _file_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text())
    except Exception:
        return {}


def _get(key: str, env: str) -> str:
    # precedence: env var > brand.config.json > default
    return os.getenv(env) or _file_config().get(key) or _DEFAULTS[key]


# Public accessors — import these, never a string literal.
def app_name() -> str:
    return _get("name", "APP_NAME")


def short_name() -> str:
    return _get("shortName", "APP_SHORT_NAME")


def legal_name() -> str:
    return _get("legalName", "APP_LEGAL_NAME")


def tagline() -> str:
    return _get("tagline", "APP_TAGLINE")


def domain() -> str:
    return _get("domain", "APP_DOMAIN")


def support_email() -> str:
    return _get("supportEmail", "APP_SUPPORT_EMAIL")


# Convenience snapshot (e.g. to expose at /api/platform/brand for the frontend)
def brand_dict() -> dict:
    return {
        "name": app_name(),
        "shortName": short_name(),
        "legalName": legal_name(),
        "tagline": tagline(),
        "domain": domain(),
        "supportEmail": support_email(),
    }
