"""Secret/config resolution (blueprint/17).

The Integrations vault (admin-managed, encrypted) takes precedence; otherwise fall back
to .env (settings). One place so every provider — LLM + payments — reads creds the same
way: vault → .env. Secrets are decrypted backend-side only, never returned to clients.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.platform import Integration
from . import secret_box


async def vault(db: AsyncSession | None, provider: str) -> tuple[str | None, dict]:
    """(secret, config) from the vault for `provider` if it exists + is enabled, else (None, config|{})."""
    if db is None:
        return None, {}
    row = (await db.execute(select(Integration).where(Integration.provider == provider))).scalar_one_or_none()
    if not row:
        return None, {}
    secret = None
    if row.enabled and row.secret_ciphertext is not None:
        try:
            secret = secret_box.decrypt(row.secret_ciphertext)
        except Exception:
            secret = None
    return secret, (row.config or {})


async def secret_for(db: AsyncSession | None, provider: str, env_fallback: str | None) -> str | None:
    """Vault secret for `provider` if set+enabled, else the .env value."""
    s, _ = await vault(db, provider)
    return s or env_fallback
