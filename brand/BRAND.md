# Brand & Platform Name

> **Single source of truth for the platform's name and identity**, plus the honest naming/domain decision and the **one-command rename** procedure. The product is built so the name can be changed across the entire platform with minimal effort.

---

## 1. Current name

| Field | Value |
|---|---|
| **Name** | **SwingAI** *(working name — not final)* |
| Short name | SwingAI |
| Domain (intended) | `swingai.in` |
| Tagline | "Disciplined swing trading, proven honestly." |

Defined once in [`brand.config.json`](./brand.config.json) and `.env` (`APP_NAME` etc.). **Nothing in the product hardcodes the name** — backend reads `app/brand.py`, frontend reads `NEXT_PUBLIC_APP_NAME` + the i18n `brand.name` token.

---

## 2. Honest naming & domain decision

- **Do NOT buy `swingai.com` at ~₹1 crore/year.** Catastrophic misallocation for a pre-revenue product whose edge is still unproven. The name contributes ~0% to whether the business works. Premium domains are a post-product-market-fit purchase.
- **Preferred: `swingai.in`** (~₹500–1,000/yr) — cheap, India-appropriate (NSE/BSE, Hindi audience, SEBI), and SEO-perfect for India-targeted search (your entire market). Buy on **Cloudflare Registrar** (wholesale, no markup) or Namecheap — not GoDaddy.
- `theswingai.com` (₹1,500) is an acceptable fallback, but the `the-` prefix leaks traffic to whoever owns `swingai.com`.
- Exact-match keyword domains no longer help SEO (Google deprioritized them years ago) — a brandable name + content is what ranks.

### Alternative names considered (if rebranding)
Avoid SEBI-risky words (*tips, profit, sure, multibagger, advisor, guru*).

| Name | Why | Note |
|---|---|---|
| **SwingProof** | Points at the moat — the transparent, *proven* track record. Compliance-safe ("proof" = record, not advice). | Top rebrand pick |
| **SwingLab** | Experimentation / paper-trading / validation — matches the "prove the edge first" ethos. | Honest, research-y |
| **SwingWise** | Education + discipline angle. | Trustworthy |
| **SwingSathi / SwingMitra** | "Companion/friend" (Hindi) — not an *advisor*. Warm, Hinglish. | India-first |
| **SwingIQ** | Short, smart, brandable. | Neutral |

> Caveat: "AI" in the name leans on the *translator* (which adds zero accuracy) rather than the math (which is the edge). Names like **SwingProof** market the real differentiator and are more compliance-safe. Minor, but worth knowing.

### Decision log
- **2026-06-24:** Working name `SwingAI`, intended domain `swingai.in`. Rejected `swingai.com` (₹1cr/yr). Rebrand candidate of record: **SwingWise / SwingProof**. _(Update when finalized.)_

---

## 3. How to rename the entire platform (minimal changes)

The product is built for cheap renames. To change `SwingAI` → e.g. `SwingWise`:

1. **Edit the source of truth:** [`brand.config.json`](./brand.config.json) (and `.env` `APP_NAME`, `NEXT_PUBLIC_APP_NAME`, domain). This alone re-brands all **runtime** UI/emails/API that read the brand config + i18n token — no code edits.
2. **Sweep source text** (comments, docs, any stray literals):
   ```bash
   scripts/rename-brand.sh SwingAI SwingWise        # dry-run preview
   scripts/rename-brand.sh SwingAI SwingWise --apply # apply
   ```
3. **Domain/env:** update `APP_DOMAIN`, DNS, and any absolute URLs (also env-driven).
4. Done. Because the name lives in config + i18n + one script, a full rename is minutes, not a hunt.

**Rule for all contributors:** never hardcode the platform name. Use `app/brand.py` (backend), `NEXT_PUBLIC_APP_NAME` / the `brand.name` i18n token (frontend). This is what keeps renames cheap.

---

## 4. Pre-launch checklist (when finalizing the name)
- [ ] Domain available on Cloudflare/Namecheap (`.in` first, grab matching `.com` if cheap)
- [ ] Social handles free (X / Instagram / YouTube / Telegram)
- [ ] Quick trademark search (India)
- [ ] Not SEBI-risky (no implied advice/guaranteed returns)
- [ ] Easy to say/spell in Hinglish
