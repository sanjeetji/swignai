# 18 — User Management & Session Control

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The Super Admin needs full visibility and control over users — see who they are, their active sessions, the device/IP/approximate location/time of each, and be able to **force-logout, block, unblock/re-enable** any user at any time. This doc defines user tracking, the session model, the admin controls, impersonation, and the audit log. All screens are **full pages with a back button** (doc 16), all data is **live from the backend**, and tracking **IP + location triggers DPDP obligations** (doc 09) — consent + privacy policy are mandatory.
>
> **Confirmed:** location is **IP-based city/region + ISP** (no GPS).

---

## 1. Users list — `/admin/users`

A full-page, server-driven table (the `DataTable` component, doc 14) with:
- **Columns:** name, email, phone, role, subscription tier, status (active/blocked), created, last active, last-seen IP city/region.
- **Search** (name/email/phone), **filters** (role, tier, status, date joined, country/region), **sort**, **pagination** — all server-side (no client-only filtering of partial data).
- **Bulk actions:** block/unblock, change tier, export (DPDP-compliant), send notification.
- **Row → full-page user detail** (`/admin/users/[id]`), not a dialog.

Everything reads from real user/session APIs (doc 07) — no static rows.

---

## 2. User detail — `/admin/users/[id]` (full page)

Tabs/sections (all on routed full pages or in-page sections, with back button):
- **Profile:** identity, role (doc 19), tier/subscription, capital/risk settings, created/updated.
- **Sessions & devices** (§3): every active and recent session with device, browser/OS, **IP + city/region + ISP**, login time, last activity. Per-session **Force logout**.
- **Activity / audit:** this user's recent actions (logins, trades, settings changes) — from the audit log.
- **Trading:** their paper trades, analytics, discipline score (doc 06) — read-only admin view.
- **Billing** (P3): subscription status, payments, refunds.
- **Controls:** **Block / Unblock**, **Force-logout all sessions**, **Reset password / send reset**, **Impersonate (view as)** (§5), change role/tier (permission-gated, doc 19).

---

## 3. Session & device tracking

**On login / session activity, capture (server-side):**
- Session id (linked to Supabase Auth session), user id.
- **IP address** → resolved to **city / region / country + ISP** via a geo-IP provider (key in the vault, doc 17).
- **Device / browser / OS** parsed from User-Agent.
- **Login time, last-activity time**, expiry.
- Login outcome history (success/failure) in `login_history` (doc 06) — supports anomaly detection (§7).

**Stored in** `user_sessions` + `login_history` (doc 06). A **session-tracking middleware** (doc 07) records/updates these on authenticated requests (throttled, async — must not slow requests). Geo lookups are cached (Redis) to avoid per-request cost/latency.

**Honest accuracy note:** IP geolocation is **approximate** — city/region level, sometimes the ISP's hub city, not the user's exact "local area." VPNs/mobile networks reduce accuracy. The UI labels it as approximate. Precise location would require GPS consent (declined per design decision).

---

## 4. Admin controls — force-logout, block, unblock

- **Force-logout (single session or all):** revoke the session(s) — invalidate the Supabase session / bump a token version so the user's tokens stop working immediately. Next request → re-auth required.
- **Block user:** set `status = blocked` (+ reason, by whom, when in `user_blocks`, doc 06). A blocked user is **denied at the API gate** (middleware checks block status on every authed request) and force-logged-out. They see a clear "account suspended — contact support" full-page screen (localized, doc 15).
- **Unblock / re-enable:** clear the block; user can log in again. All transitions audit-logged.
- **Scope:** blocking is **account-level** (not IP-level by default) — cleaner and avoids collateral damage on shared/mobile IPs. Optional IP/abuse blocking can be added later for security (doc 19), kept separate from account suspension.
- Controls are **permission-gated** (doc 19): e.g. `support` can force-logout but only `super_admin`/`admin` can block; destructive actions may require re-auth.

---

## 5. Impersonation — "view as user" (support)

- Admins (permitted roles) can **impersonate** a user to debug issues — enter a read-mostly "view as" mode seeing the user's dashboard/state.
- **Strict guardrails:** clearly banner-flagged ("Viewing as <user> — admin session"), **heavily audit-logged** (who impersonated whom, when, duration), time-boxed, and **never used to perform financial-affecting actions as the user** without explicit logging. Sensitive data access respects least privilege.

---

## 6. Audit log — `/admin/audit-log`

> The audit log is the **`category in (admin, security)` view of the unified Event Log (doc 22)** — same storage, pre-filtered. See doc 22 for the full event stream, `emit()` helper, correlation IDs, live tail, and alert rules.

- **Every privileged/sensitive action** is recorded as an event (doc 06 `event_logs`): actor, action, target (user/setting/secret), before/after (where applicable, secrets' *values* never stored), IP, location, timestamp.
- Covered actions: logins (admin), role/permission changes, block/unblock, force-logout, impersonation start/stop, secret create/rotate/delete (doc 17), platform-setting/theme/flag changes (doc 16), pick overrides (doc 07).
- Full-page, searchable/filterable; **immutable/append-only** (no edits/deletes from the UI) so it's trustworthy.

---

## 7. Security & abuse (ties to doc 19)

- **Anomaly signals** from `login_history`: impossible travel, many failed logins, new-device/new-geo login → optional email alert / step-up auth.
- **Rate limiting** on auth + sensitive endpoints (doc 19).
- Sessions have sensible **expiry + refresh**; "log out all devices" available to users too (self-service security).
- Suspicious-session flags surfaced to admin.

---

## 8. DPDP / privacy (mandatory — see doc 09)

- Tracking IP + approximate location is **personal data** under India's DPDP Act → requires **consent** (at signup), a clear **privacy policy** explaining what's collected and why (security, fraud prevention, support), **purpose limitation**, and **retention limits** (don't keep session/geo logs forever — define a TTL).
- Users get **data export** and **account deletion** (right to erasure) — admin tooling + self-service.
- Geo/session data access is least-privilege and audit-logged. This is honest, lawful tracking — not covert surveillance.

---

## 9. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | User list + detail (full pages), session/device + IP-city tracking, force-logout, block/unblock, audit log, DPDP consent + privacy policy, data export/deletion |
| 2 | Impersonation, anomaly alerts, bulk actions, richer filters, notifications to users |
| 3 | Advanced abuse/fraud tooling, step-up auth, retention automation, support workflows |
| Future | Risk scoring, device fingerprinting, SSO/enterprise, granular consent management |

---

*Next: [`19-rbac-security.md`](./19-rbac-security.md) — the roles, permissions, and security hardening that make all of this safe.*
