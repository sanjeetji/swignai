# 03 — AI / LLM Layer

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The LLM in SwingAI is "Brain 2 — The Guru": a *translator* that turns finished, math-derived numbers into a beginner-friendly Hinglish story. It builds trust and retention but adds **zero** mathematical accuracy. Because it's decoration on top of final math, model quality barely matters — which is exactly why we can run entirely on **free** AI now and upgrade later with a two-line config change. This doc covers the golden rule, the free→paid options with reasons, the pluggable design, the template fallback, and the future multi-agent direction.

---

## 1. The golden rule (unbreakable)

> **The LLM only translates finished numbers into Hinglish. It NEVER picks stocks and NEVER originates a number.** It is the PR department, not the Research department.

Why this is absolute:
- LLMs hallucinate numbers — an LLM "entry price" or "target" is a liability.
- More importantly, **your moat is a backtestable, deterministic track record** (see [`00-overview-philosophy.md`](./00-overview-philosophy.md) and [`04-picker-strategy.md`](./04-picker-strategy.md)). An LLM in the selection path makes the track record unprovable.

The LLM receives the already-final Stage 0–3 output (symbol, score breakdown, entry, stop, targets, R:R, indicators, regime) and writes ~60 words of Hinglish + a risk warning + the "educational analysis, not advice" line. That's its entire job.

---

## 2. Why free AI is the correct choice now

Because the LLM is decoration on final math, **a free model is ~95% as good as Claude for this task.** Nobody loses money because the *explanation* came from a free model — the numbers are identical either way. So: **spend nothing on AI until there is revenue.** This is correctly prioritized, not a compromise.

---

## 3. Options compared (ranked for Hinglish quality)

The one thing that actually varies between models is **Hinglish quality** — natural Hindi+English code-switching. Most small open models do this poorly.

| Provider | Cost | Hinglish quality | Verdict |
|---|---|---|---|
| **Google Gemini Flash** | Free tier (generous) | **Best among free** — natural code-switching | **PICK — primary (now)** |
| **OpenRouter** (free models: Llama 3.3 70B, DeepSeek, Qwen, etc.) | Free tier | Good; one API key → many models | **PICK — secondary / experimentation / fallback** |
| **Groq** | Free tier | Good, *extremely* fast | Optional — great for low latency |
| **Together AI** | Free credits | Good open models | Optional fallback |
| **Cloudflare Workers AI** | Free tier | Weaker (smaller models) | Only if already hosting on Cloudflare |
| **Claude (Anthropic)** | Paid (cheap: ~₹2.5/day cached) | Excellent | **UPGRADE — post-revenue, preferred** |
| **OpenAI / ChatGPT API** | Paid | Excellent | Alternative UPGRADE; also strong Hinglish |

---

## 4. Decision (free now, paid later)

- **PICK both free, by role:**
  - **Gemini Flash** = primary daily explanation generator (best free Hinglish + generous limits).
  - **OpenRouter** = secondary/fallback + A/B testing harness (one OpenAI-compatible key → many models, provider redundancy).
- **UPGRADE:** **Claude** (preferred) or **OpenAI** once revenue exists. Because of the pluggable design (§6), this is **two config strings**, no rewrite.
- **Zero-cost fallback / launch option:** **template-based Hinglish** (§5) — may even ship Phase 1 without any LLM at all.

---

## 5. The zero-cost option you might not need an LLM for at all

Since the numbers are already computed by the math, you can ship **template-based Hinglish explanations** — fill-in-the-blank from the final values:

```
"{stock} abhi 20-EMA ke upar trade kar raha hai, RSI {rsi} (healthy zone).
Volume average se {volume_x}x zyada — buyers active hain.
Entry ₹{entry}, stop-loss ₹{sl} (risk {risk}%), target ₹{t1}.
⚠️ Yeh educational analysis hai, investment advice nahi."
```

Advantages: **zero cost, zero rate limits, zero hallucination risk, 100% accurate, and SEBI-safe wording you control exactly.** The LLM only adds *natural variation* — a nice-to-have, not a requirement. Many founders would launch on templates and add the LLM later as polish. **Recommended: build templates first as the guaranteed fallback, layer the LLM on top.** The pipeline always falls back to a template if the LLM call fails (see doc 07 error handling).

---

## 6. Pluggable design (mandatory)

Write against the **OpenAI-compatible chat format** — Gemini (via its OpenAI-compat endpoint), OpenRouter, Groq, and Together all speak it, and Anthropic/OpenAI are trivial adapters.

```python
# llm/base.py
class LLMProvider(Protocol):
    def complete(self, system: str, user: str, max_tokens: int) -> str: ...

# config
LLM_PROVIDER = "gemini"        # → "openrouter" → "anthropic" → "openai"
LLM_MODEL    = "gemini-1.5-flash"
```

One public function, cached:
```python
# llm/explain.py
def generate_explanation(pick) -> str:
    # 1. check Redis cache (key = pick.id) → return if hit
    # 2. build prompt from FINAL numbers (never ask the model to compute)
    # 3. call configured LLMProvider
    # 4. on failure → fall back to template
    # 5. validate output (length, disclaimer, no imperative buy/sell) → cache 24h → return
```

- **Cached in Redis 24h keyed by pick id.** ~5 explanations generated per day total, read by all users from cache → **free-tier limits are irrelevant** at any user count.
- **Output validation before caching:** <60 words, disclaimer present, ≈60% Hindi / 40% English, **no imperative "buy/sell"** language (SEBI — see doc 09). Reject + regenerate or fall back to template if it fails.

---

## 7. The system prompt (enforced constraints)

The Guru system prompt must enforce:
- **Language:** Hinglish, ~60% Hindi / 40% English, simple beginner words.
- **Length:** under 60 words.
- **Content:** explain *why* the math flagged this stock, in plain language, from the numbers provided. Never invent or alter a number.
- **Risk:** always include an explicit risk line.
- **Compliance:** always include "educational analysis, not investment advice"; **never** use directive "buy/sell" phrasing — describe conditions, not commands (doc 09).

Keep the prompt in `llm/prompts.py`, versioned. Snapshot-test outputs (doc 11).

---

## 8. On "multiple AI agents"

For Phase 1, **multi-agent is over-engineering.** Translating 5 picks into Hinglish is one cached call. Adding an agent framework adds failure points and rate-limit exposure for zero accuracy gain (accuracy lives entirely in the math).

Multi-agent becomes reasonable **later (Phase 3+ / future)** only when there are genuinely different jobs — and even then it's just *different prompts to the same pluggable layer*, not a framework:
- **Explanation agent** — Hinglish pick narration (now).
- **SEO content agent** — weekly "Top swing setups" blog from real data (Phase 2).
- **Risk-coach agent** — personalized post-trade review copy ("you exited winners early") (Phase 2/3).
- **Market-summary agent** — daily regime narration (Phase 2).
- **Chat assistant** — "ask about any stock," strictly RAG-grounded on *our computed numbers*, never free-forming picks (future — see doc 13).

Build cleverness into the math, not the plumbing. See [`13-future-vision.md`](./13-future-vision.md) for the full multi-agent vision.

---

## 9. Cost summary

| Phase | Provider | Approx cost |
|---|---|---|
| 1 | Gemini Flash / OpenRouter (free) or templates | ~₹0 (~5 cached calls/day) |
| 2 | Same + SEO/coach prompts (free tiers) | ~₹0–minimal |
| 3 | Claude / OpenAI (config swap) | ~₹2.5/day cached → trivial vs revenue |
| Future | Multi-agent + chat (Claude/OpenAI) | scales with usage; still cached aggressively |

---

*Next: [`04-picker-strategy.md`](./04-picker-strategy.md) — Brain 1, the deterministic math that actually determines the edge.*
