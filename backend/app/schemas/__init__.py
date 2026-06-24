"""Pydantic request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# --- auth ---
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    name: str | None
    capital_amount: float
    risk_pct: float
    subscription_tier: str
    roles: list[str] = []
    permissions: list[str] = []


# --- paper trading ---
class PaperBuyIn(BaseModel):
    stock_symbol: str
    entry_price: float
    stop_loss: float
    target: float
    quantity: int
    ai_pick_id: str | None = None
    entry_reason: str | None = None


class PaperCloseIn(BaseModel):
    exit_price: float
    exit_reason: str | None = None


# --- admin ---
class AppearanceIn(BaseModel):
    default_theme_mode: str | None = None
    default_preset: str | None = None
    default_font: str | None = None
    default_locale: str | None = None
    locked_axes: dict | None = None
    maintenance_mode: bool | None = None
    maintenance_message: str | None = None


class IntegrationIn(BaseModel):
    category: str
    provider: str
    enabled: bool = False
    role: str = "primary"
    config: dict = {}
    secret: str | None = None      # plaintext in -> encrypted at rest, never returned
