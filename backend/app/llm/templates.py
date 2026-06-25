"""Template Hinglish explanations — zero cost, zero hallucination, SEBI-safe (blueprint/03 §5).

Fills in the ALREADY-computed numbers. Describes conditions ("RSI healthy zone",
"buyers active") — never an imperative buy/sell command (blueprint/09). The output is
validated by `is_safe()` before use.
"""
from __future__ import annotations

DISCLAIMER = "Yeh educational analysis hai, investment advice nahi."

# Words that would make copy read as a directive recommendation (SEBI risk).
_BANNED = ("buy ", "sell ", "kharido", "becho", "buy now", "sell now")


def render(pick: dict) -> str:
    """`pick` keys: symbol, plan{entry,stop,target_1}, rsi, rel_strength, regime, breakdown."""
    plan = pick.get("plan", {})
    sym = pick.get("symbol", "Stock")
    entry = plan.get("entry", "-")
    stop = plan.get("stop", "-")
    t1 = plan.get("target_1", "-")
    rsi = pick.get("rsi", "-")
    rs = pick.get("rel_strength", 0)
    risk_pct = ""
    try:
        if entry and stop and float(entry) > 0:
            risk_pct = f" (risk ~{round((float(entry) - float(stop)) / float(entry) * 100, 1)}%)"
    except (TypeError, ValueError):
        pass
    strength = "NIFTY se strong" if (isinstance(rs, (int, float)) and rs > 0) else "market ke saath"

    return (
        f"{sym} apne short-term trend ke upar hai aur {strength} chal raha hai. "
        f"RSI {rsi} healthy zone mein hai, volume mein buyers active dikh rahe hain. "
        f"Setup: entry ₹{entry}, stop-loss ₹{stop}{risk_pct}, pehla target ₹{t1}. "
        f"⚠️ {DISCLAIMER}"
    )


def is_safe(text: str) -> bool:
    """Guard: must carry the disclaimer and avoid imperative buy/sell language."""
    low = text.lower()
    if "advice nahi" not in low and "not investment advice" not in low:
        return False
    return not any(b in low for b in _BANNED)
