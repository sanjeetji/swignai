"""Pluggable LLM provider (OpenAI-compatible chat) — blueprint/03 §6.

All supported providers (OpenRouter / Groq / Together / OpenAI / Gemini) speak the
OpenAI chat format, so one adapter covers them — only the base URL + key + model differ.
Keys resolve vault → .env (blueprint/17). LLM_PROVIDER="auto" picks the first one with a
key; "template" disables LLM (free template fallback). Credentials never hardcoded.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("llm")

# provider → (OpenAI-compatible base URL, settings key attr, settings model attr)
PROVIDERS = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "OPENROUTER_MODEL"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL"),
    "together": ("https://api.together.xyz/v1", "TOGETHER_API_KEY", "TOGETHER_MODEL"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "OPENAI_MODEL"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "GEMINI_MODEL"),
}
# Groq first: fastest + most reliable free tier. Order is the auto fail-through preference.
_AUTO_ORDER = ["groq", "openrouter", "together", "openai", "gemini"]


class NullProvider:
    """No-op provider — signals 'use the template fallback'."""
    name = "template"

    def complete(self, system: str, user: str, max_tokens: int = 200) -> str:
        raise RuntimeError("no LLM provider configured")


class OpenAICompatProvider:
    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 200) -> str:
        import requests
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "max_tokens": max_tokens, "temperature": 0.7,
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


async def resolve_provider(db=None):
    """Pick the active LLM provider (vault → .env), or NullProvider when none/template."""
    from ..core.config import settings
    from ..services.integrations import secret_for, vault

    choice = (settings.LLM_PROVIDER or "template").lower()
    if choice in ("template", "none"):
        return NullProvider()
    order = _AUTO_ORDER if choice == "auto" else ([choice] if choice in PROVIDERS else [])
    for name in order:
        base_url, key_attr, model_attr = PROVIDERS[name]
        key = await secret_for(db, name, getattr(settings, key_attr, None))
        if not key:
            continue
        _, cfg = await vault(db, name)
        model = cfg.get("model") or getattr(settings, model_attr)
        logger.info("LLM provider: %s (%s)", name, model)
        return OpenAICompatProvider(name, base_url, key, model)
    return NullProvider()
