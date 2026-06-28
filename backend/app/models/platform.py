"""Platform settings, theming, feature flags, integrations vault — blueprint/16,17."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class PlatformSetting(Base, TimestampMixin):
    """Singleton-ish (one active row) — global defaults (blueprint/16 §3,5)."""
    __tablename__ = "platform_settings"

    id: Mapped[uuid.UUID] = uuid_pk()
    default_theme_mode: Mapped[str] = mapped_column(String(10), default="system")  # light/dark/system
    default_preset: Mapped[str] = mapped_column(String(40), default="default")
    default_font: Mapped[str] = mapped_column(String(40), default="inter")
    default_locale: Mapped[str] = mapped_column(String(8), default="en")
    locked_axes: Mapped[dict] = mapped_column(JSON, default=dict)         # {mode,preset,font,locale: bool}
    enabled_presets: Mapped[list] = mapped_column(JSON, default=list)
    enabled_fonts: Mapped[list] = mapped_column(JSON, default=list)
    enabled_locales: Mapped[list] = mapped_column(JSON, default=lambda: ["en", "hi"])
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_message: Mapped[str | None] = mapped_column(String(500))
    new_user_defaults: Mapped[dict] = mapped_column(JSON, default=dict)


class ThemePreset(Base, TimestampMixin):
    __tablename__ = "theme_presets"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(40), unique=True)
    label: Mapped[str] = mapped_column(String(60))
    tokens_light: Mapped[dict] = mapped_column(JSON)   # CSS-variable token map
    tokens_dark: Mapped[dict] = mapped_column(JSON)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class UserPreference(Base, TimestampMixin):
    """Per-user overrides (NULL = inherit platform default) — blueprint/14."""
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme_mode: Mapped[str | None] = mapped_column(String(10))
    theme_preset: Mapped[str | None] = mapped_column(String(40))
    font: Mapped[str | None] = mapped_column(String(40))
    locale: Mapped[str | None] = mapped_column(String(8))
    email_digest: Mapped[bool] = mapped_column(Boolean, default=True)   # daily picks + weekly perf email


class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    targeting: Mapped[dict] = mapped_column(JSON, default=dict)  # {tier/role/cohort}
    description: Mapped[str | None] = mapped_column(String(255))


class Integration(Base, TimestampMixin):
    """API-key/secret vault entry — ciphertext only (blueprint/17,19)."""
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = uuid_pk()
    category: Mapped[str] = mapped_column(String(20), index=True)   # llm/data/payments/alerts/infra
    provider: Mapped[str] = mapped_column(String(40), index=True)   # gemini/angelone/razorpay...
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(12), default="primary")  # primary/fallback
    config: Mapped[dict] = mapped_column(JSON, default=dict)        # non-secret (e.g. default model)
    secret_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)  # ENCRYPTED
    secret_meta: Mapped[dict] = mapped_column(JSON, default=dict)   # masked hint, key id (no values)
    last_status: Mapped[str | None] = mapped_column(String(20))
