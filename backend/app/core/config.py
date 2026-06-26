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
    DATA_PROVIDER_FALLBACK: str | None = None   # e.g. "dhan" — used if the primary errors (blueprint/02)
    DEFAULT_CAPITAL: float = 100000.0

    # --- Dhan (fallback NSE data) — set in backend/.env ---
    DHAN_CLIENT_ID: str | None = None
    DHAN_ACCESS_TOKEN: str | None = None

    # --- Angel One SmartAPI (official NSE data) — set in backend/.env ---
    ANGELONE_API_KEY: str | None = None
    ANGELONE_CLIENT_CODE: str | None = None      # your Angel One login id
    ANGELONE_MPIN: str | None = None             # MPIN / password
    ANGELONE_TOTP_SECRET: str | None = None      # base32 secret from enable-totp

    # --- jobs / LLM ---
    ENABLE_SCHEDULER: bool = False       # off in dev/tests; true in prod to run cron jobs
    # "auto" picks the first provider with a key; or pin to one. "template" = no LLM (free).
    LLM_PROVIDER: str = "auto"           # auto | template | openrouter | groq | together | openai | gemini
    # Per-provider keys + default models (vault overrides these via the Integrations tab).
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    TOGETHER_API_KEY: str | None = None
    TOGETHER_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- payments (Razorpay) — vault overrides these via the Integrations tab ---
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None
    RAZORPAY_WEBHOOK_SECRET: str | None = None

    # --- rate limiting ---
    RATE_LIMIT_PER_MIN: int = 120        # per-IP default for sensitive/public endpoints

    # --- geo / sessions ---
    GEOIP_ENABLED: bool = False          # IP->city lookup (blueprint/18); off in dev

    # --- ISR on-demand revalidation (backend -> Next marketing app, blueprint/08) ---
    REVALIDATE_URL: str = "http://localhost:9002/api/revalidate"
    REVALIDATE_TOKEN: str = "dev-revalidate-token-change-me"   # MUST match the marketing app's token

    # --- email (SMTP — works with Gmail/SendGrid/SES/Resend; OFF until SMTP_HOST set) ---
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM: str = "SwingAI <no-reply@swingai.in>"

    # --- SMS / WhatsApp (Twilio — OFF until creds set) ---
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM: str | None = None            # e.g. +1xxxx (SMS) or whatsapp:+1xxxx

    # --- observability / Sentry (blueprint/19) — OFF until SENTRY_DSN is set ---
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0    # 0=errors only; raise in prod for perf tracing
    RELEASE: str | None = None                # e.g. git sha, for Sentry release tagging

    # --- data retention / DPDP (blueprint/09,19) — nightly purge TTLs (days) ---
    SESSION_RETENTION_DAYS: int = 90          # stale user_sessions rows
    LOGIN_HISTORY_RETENTION_DAYS: int = 180   # login_history rows
    EVENT_LOG_RETENTION_DAYS: int = 365       # ops/product events (non-audit)
    AUDIT_LOG_RETENTION_DAYS: int = 730       # admin/security events kept longer (audit)

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
