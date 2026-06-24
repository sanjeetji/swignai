# 17 — Integrations & Secrets Vault

> 🧭 **Status:** 📝 Spec (OmniMark reuse) · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The platform integrates many third-party services — LLM providers, market-data providers, payments, alerts. The Super Admin needs **one place to add, test, rotate, and manage the API keys/secrets for every integration**, without editing code or redeploying. This doc defines that integrations tab: an encrypted secrets vault, per-provider config, connection testing, and the security model. **No keys are hardcoded; nothing is dummy — every integration reads its credentials from the vault and is exercised against the real provider.**

---

## 1. Goal

A full-page admin section (`/admin/integrations`, doc 16) where the owner manages credentials for **all** integrations:

| Category | Providers (pluggable — docs 02, 03) |
|---|---|
| **LLM** | Gemini, OpenRouter, Groq, Together, **Claude (Anthropic)**, OpenAI |
| **Market data** | yfinance (no key), **Angel One SmartAPI**, Dhan, Upstox, TrueData |
| **Payments** (P3) | Razorpay |
| **Alerts** (P2) | Gupshup / MSG91 (WhatsApp), MSG91 / Twilio (SMS), SMTP/email provider |
| **Infra/Observability** | Sentry DSN, analytics keys, geo-IP provider (doc 18) |

Each provider has its own **full-page config screen** (`/admin/integrations/[provider]`) — not a dialog (doc 16).

---

## 2. Per-integration config screen

Each provider page exposes:
- **Credential fields** specific to that provider (e.g. Angel One: API key, client code, password/TOTP secret; OpenRouter: API key + default model; Razorpay: key id + secret).
- **Enable/disable** toggle (turn an integration on/off platform-wide — ties into feature flags, doc 16).
- **Primary / fallback designation** (e.g. set Gemini primary, OpenRouter fallback — doc 03; Angel One primary, Dhan fallback — doc 02).
- **Default model / params** where relevant (LLM model id).
- **Test Connection** button — calls the provider with the saved credentials and reports success/failure live (§4).
- **Status & last-checked** indicator; **last-used / quota info** where the provider exposes it.
- **Rotate / replace** key flow; **delete** with confirmation.
- Masked display: secrets shown as `••••••••1234`, revealed only on explicit action + re-auth.

The set of available providers comes from the backend provider registry (docs 02, 03) — adding a provider in code makes it appear here; the **admin supplies the key, code stays untouched.**

---

## 3. Storage & encryption (security model)

- **Secrets are encrypted at rest** — never stored in plaintext, never in the repo, never in client-side code.
- Store in an `integrations` table (doc 06) with **application-level encryption** (e.g. envelope encryption: a master key in the platform secret store / KMS encrypts per-record data keys), **or** delegate to a managed secret store (Supabase Vault / cloud KMS). The DB only holds ciphertext.
- **Reuse from OmniMark:** `backend/app/core/secrets.py` + `backend/app/services/secret_box.py` implement exactly this envelope-encryption pattern (DEK / `data_encryption_keys`). Adapt it rather than rebuilding (see [`OMNIMARK-REUSE.md`](./OMNIMARK-REUSE.md)).
- The **master/encryption key lives in the environment/secret store** (Railway/Render/Vercel secrets), **not** in the DB or code. Compromising the DB alone does not reveal secrets.
- Secrets are **decrypted only in the backend at call time**, held in memory transiently, and **never sent to the frontend** — the admin UI shows masked values + status, not raw secrets (except a deliberate, re-authenticated reveal).
- All secret reads/writes/rotations are **audit-logged** (doc 18) with actor + timestamp + IP (value never logged).

---

## 4. Connection testing & health

- **Test Connection** runs a minimal real call (e.g. LLM: a tiny completion; data: fetch one quote; payments: a sandbox ping) using the saved credentials and returns pass/fail + latency + error detail. This proves the integration actually works — **no assuming, no dummy success.**
- A background **health check** (cron, doc 07) periodically validates critical integrations and surfaces status on `/admin` overview + `/admin/integrations`; failures alert the admin (and can auto-failover to the fallback provider — docs 02, 03).
- If a provider's key is missing/invalid, the system uses the configured fallback (LLM → fallback model or template; data → fallback provider) and flags it, rather than breaking the pipeline (doc 07 error handling).

---

## 5. How the backend consumes vault credentials

```
request/job needs LLM ─► provider factory (doc 03) ─► reads enabled+primary integration
                                                      ─► decrypts key from vault (backend only)
                                                      ─► calls provider ─► on fail, fallback
```
- The pluggable provider factories (docs 02, 03) resolve **which** provider + **its credentials** from the vault at runtime — so switching primary provider or rotating a key is an **admin action**, not a deploy.
- Local dev can use `.env` for convenience, but production credentials live in the vault; precedence is documented so there's no ambiguity.

---

## 6. Guardrails

- **Least privilege:** only `super_admin` (and explicitly permitted roles) can view/edit integrations (doc 19).
- **Re-auth** for revealing or rotating a secret (sensitive action, doc 19).
- **No secret ever in logs, error messages, Sentry payloads, or client bundles** — scrub on the way out.
- **Validation** of key format before saving; **Test Connection** strongly encouraged before enabling.
- Rotating a key takes effect immediately (next call uses the new value); old value is overwritten, not retained.

---

## 7. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | Vault + encryption, integration pages for LLM (Gemini/OpenRouter) + data (Angel One/Dhan) + Sentry/geo, Test Connection, masking, audit logging |
| 2 | Alerts providers (WhatsApp/SMS/email), health-check cron + dashboard status, fallback wiring |
| 3 | Payments (Razorpay), paid LLM (Claude/OpenAI) + paid data (TrueData), quota/usage display, key rotation policies |
| Future | Per-environment vaults, automated rotation, KMS/HSM, scoped sub-keys |

---

*Next: [`18-user-management-sessions.md`](./18-user-management-sessions.md) — tracking users, sessions, devices, and admin control over access.*
