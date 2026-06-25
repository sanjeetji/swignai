"""LLM layer — Brain 2 (the Translator). Turns finished numbers into Hinglish.

GOLDEN RULE (blueprint/03): the LLM only TRANSLATES already-computed numbers. It
NEVER picks a stock or originates a number. Phase 1 ships the zero-cost template
fallback; a real provider (Gemini/OpenRouter/Claude) plugs in behind the same
`generate_explanation()` without touching callers.
"""
from .explain import generate_explanation  # noqa: F401
