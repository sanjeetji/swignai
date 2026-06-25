"""Pluggable LLM provider interface (OpenAI-compatible chat) — blueprint/03 §6.

Phase 1 uses NullProvider (no external call → callers fall back to templates).
Add GeminiProvider / OpenRouterProvider / AnthropicProvider later behind this same
interface; selection is one config line (LLM_PROVIDER). Credentials come from the
encrypted vault (blueprint/17), never hardcoded.
"""
from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, system: str, user: str, max_tokens: int = 200) -> str: ...


class NullProvider:
    """No-op provider — signals 'use the template fallback'."""

    def complete(self, system: str, user: str, max_tokens: int = 200) -> str:
        raise RuntimeError("no LLM provider configured")


def get_provider():
    """Resolve the configured provider. Phase 1 → NullProvider (templates).

    Later: read LLM_PROVIDER + credentials from the vault and return a real client.
    Kept import-light so the backend boots without any LLM SDK installed.
    """
    from ..core.config import settings

    provider = getattr(settings, "LLM_PROVIDER", None)
    if not provider or provider in ("none", "template"):
        return NullProvider()
    # Future: gemini / openrouter / anthropic / openai adapters
    return NullProvider()
