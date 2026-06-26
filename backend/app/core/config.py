"""Settings — 12-factor config via pydantic-settings (blueprint/01).

Local dev defaults to async SQLite (zero infra). Production sets DATABASE_URL to
Postgres (Supabase). Secrets are read from env / the encrypted vault, never hardcoded.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- environment ---
    ENV: str = "dev"                     # dev | staging | prod
    DEBUG: bool = True

    # --- database (async) ---
    # dev default = local sqlite (no infra). prod = postgresql+asyncpg://...
    DATABASE_URL: str = "sqlite+aiosqlite:///./swingai_dev.db"

    # --- cache ---
    REDIS_URL: str | None = None         # optional in dev; required at scale

    # --- auth / security ---
    JWT_SECRET: str = "dev-insecure-change-me"   # MUST be overridden in prod
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_TTL_MIN: int = 60
    REFRESH_TOKEN_TTL_DAYS: int = 30
    # master key for the secrets vault (envelope encryption). Set in prod env/KMS.
    SECRET_VAULT_KEY: str = "dev-vault-key-change-me-0123456789"

    # --- data / quant ---
    DATA_PROVIDER: str = "synthetic"     # synthetic | yfinance | angelone | dhan
    DEFAULT_CAPITAL: float = 100000.0

    # --- Angel One SmartAPI (official NSE data) — set in backend/.env ---
    ANGELONE_API_KEY: str | None = None
    ANGELONE_CLIENT_CODE: str | None = None      # your Angel One login id
    ANGELONE_MPIN: str | None = None             # MPIN / password
    ANGELONE_TOTP_SECRET: str | None = None      # base32 secret from enable-totp

    # --- jobs / LLM ---
    ENABLE_SCHEDULER: bool = False       # off in dev/tests; true in prod to run cron jobs
    LLM_PROVIDER: str = "template"       # template | gemini | openrouter | anthropic | openai

    # --- rate limiting ---
    RATE_LIMIT_PER_MIN: int = 120        # per-IP default for sensitive/public endpoints

    # --- geo / sessions ---
    GEOIP_ENABLED: bool = False          # IP->city lookup (blueprint/18); off in dev

    # --- CORS (web origins) ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:9001",         # dashboard (9000 series; clear of OmniMark)
        "http://localhost:9002",         # marketing
    ]

    @property
    def is_prod(self) -> bool:
        return self.ENV == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
