# 19 — RBAC & Security

> 🧭 **Status:** 📝 Spec (OmniMark reuse) · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** With a Super Admin control plane (doc 16), a secrets vault (doc 17), and user/session governance (doc 18), the platform handles privileged actions and sensitive data — so security is foundational, not an afterthought. This doc defines the role-based access control (RBAC) model, permissions, admin 2FA, secret/data protection, rate limiting/abuse defense, session security, and the DPDP posture. Goal: **most-advanced, clean, secure platform — secure by default, everything enforced server-side.**

---

## 1. Roles (hierarchy)

| Role | Who | Capability |
|---|---|---|
| **super_admin** | Platform owner (you) | Everything: appearance, integrations/secrets, users, roles, analytics, settings, audit |
| **admin** | Trusted operators | Most admin functions per granted permissions; cannot manage secrets or roles unless granted |
| **support** | Support staff | Read users, force-logout, assist; **no** secrets, **no** blocking/roles (configurable) |
| **user** | Normal trader | Own dashboard, paper trades, analytics, settings only |

Roles are data (`roles`, `permissions`, `user_roles` — doc 06), not hardcoded — so new roles/permissions can be defined without code changes (a custom role editor lands Phase 3, doc 16).

---

## 2. Permissions model

- **Granular, permission-based** (not just role-name checks): roles are bundles of permissions like `users.read`, `users.block`, `users.impersonate`, `integrations.manage`, `settings.appearance`, `analytics.view`, `roles.manage`, `picks.override`.
- **Enforced server-side** on every endpoint (FastAPI dependency that checks the caller's permissions, doc 07) — the frontend hiding a button is convenience only; the API is the gate.
- **Least privilege** by default; sensitive permissions (`integrations.manage`, `roles.manage`, `users.block`) granted sparingly.
- Frontend mirrors permissions to show/hide UI, but never relies on it for security.

---

## 3. Authentication & admin 2FA

- **Supabase Auth** for primary auth (JWT/sessions, doc 01).
- **2FA mandatory for all admin roles** (super_admin/admin/support) — TOTP (authenticator app); enforced at login and re-checked for sensitive actions. **Reuse from OmniMark:** `pyotp` + `qrcode` 2FA flow, `roles`/`audit_logs` tables, and `audit_log_service.py` (see [`OMNIMARK-REUSE.md`](./OMNIMARK-REUSE.md)).
- **Step-up / re-auth** for high-risk actions: revealing/rotating secrets (doc 17), blocking users, changing roles, editing strategy params (doc 16).
- Strong password policy; account-lockout/backoff on repeated failures (§5).
- Optional 2FA for normal users (offered, recommended for a finance product).

---

## 4. Secret & sensitive-data protection

- **Secrets encrypted at rest** (vault, doc 17); master key in env/KMS, never in DB/code.
- Secrets decrypted **only in backend at call time**, **never** sent to frontend, **never** logged (scrub from logs/Sentry/error payloads).
- **PII** (email, phone, IP, geo) access is least-privilege + audit-logged (doc 18); encrypt sensitive columns where warranted.
- **TLS everywhere**; HSTS; secure, httpOnly, sameSite cookies for sessions.
- DB access via least-privilege credentials; **Supabase Row Level Security** so users can only touch their own rows (doc 06); admin access via service role on the backend only (never expose service keys to the client).

---

## 5. Rate limiting & abuse defense

- **Rate limits** on auth (login/signup/reset), public APIs (anti-scraping of picks/SEO), and sensitive admin actions. Implemented at the edge and/or backend (Redis-backed counters).
- **Brute-force protection:** progressive backoff + lockout on failed logins; CAPTCHA on suspicious signup/login.
- **Bot/abuse:** Cloudflare (doc 01) for WAF/DDoS/CDN; basic anomaly detection from `login_history` (doc 18).
- **Idempotency** on state-changing endpoints (e.g. paper-trade buy, doc 07) to prevent duplicate/abuse.
- Optional **IP/abuse blocking** (separate from account suspension, doc 18) for security incidents.

---

## 6. Session security

- Short-lived access tokens + refresh; **server-side session revocation** (force-logout, doc 18) via token versioning / session invalidation.
- Block-status checked at the API gate on every authed request (blocked → immediate denial).
- "Log out all devices" (self-service + admin).
- Session/geo anomaly signals → optional step-up auth or alert.

---

## 7. Auditing & observability

- **Append-only audit log** of all privileged actions (doc 18 §6) — tamper-evident, searchable.
- **Sentry** for errors (secrets scrubbed); structured logs with correlation ids.
- Admin health/overview surfaces auth anomalies, failed jobs, integration failures (docs 07, 16, 17).
- Alerting on security-relevant events (mass failed logins, secret access spikes, new-admin-login).

---

## 8. DPDP & data governance (India)

- **Consent** at signup for data collection incl. IP/approximate location (doc 18); clear, localized **privacy policy** (doc 15) stating what/why/retention.
- **Purpose limitation** (security, fraud prevention, support) + **retention limits** (TTL on session/geo/login logs).
- **Right to access/export** and **right to erasure** (account deletion) — self-service + admin tooling.
- Data-processing records; breach-response readiness. (Pair with SEBI framing, doc 09 — both are launch-gating compliance items; confirm with a lawyer.)

---

## 9. Backups & resilience

- **Automated DB backups** (Supabase) + tested restore; point-in-time recovery where available.
- Secrets recoverable via the KMS/secret store (not lost with the DB).
- Disaster-recovery note: documented restore procedure; critical config (settings, roles, integrations metadata) backed up.
- Graceful degradation (doc 07): Redis/LLM/data failures fall back, never hard-crash the user experience.

---

## 10. Secure-by-default checklist (carried into build)

- [ ] All admin/sensitive endpoints permission-checked server-side
- [ ] 2FA enforced for admin roles; step-up for high-risk actions
- [ ] Secrets encrypted at rest; never to client; never logged
- [ ] RLS on user data; service keys backend-only
- [ ] Rate limiting + lockout + WAF
- [ ] Audit log append-only, covering all privileged actions
- [ ] DPDP: consent, privacy policy, retention, export/delete
- [ ] TLS/HSTS, secure cookies, input validation everywhere
- [ ] Backups + tested restore
- [ ] No hardcoded secrets/data anywhere (doc 11 audit)

---

## 11. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | RBAC (roles + permissions, server-enforced), admin 2FA, secret encryption, RLS, rate limiting, audit log, DPDP basics (consent/policy/export/delete), backups |
| 2 | Step-up auth, anomaly detection/alerts, abuse tooling, retention automation |
| 3 | Custom role editor (doc 16), advanced fraud defense, pen-test/security review, SOC-style logging |
| Future | SSO/enterprise, device fingerprinting, KMS/HSM, formal compliance certifications |

---

*Next: [`20-business-analytics.md`](./20-business-analytics.md) — role-based dashboards: revenue, MRR, ARR, and advanced metrics.*
