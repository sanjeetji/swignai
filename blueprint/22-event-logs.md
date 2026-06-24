# 22 — Event Logs (Super Admin)

> 🧭 **Status:** 📝 Spec (OmniMark + extensions) · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The Super Admin needs a **unified, queryable event log** — a single stream of everything that happens on the platform (security, admin actions, system/pipeline events, integrations, data/compliance, billing), DB-backed and API-driven. This mirrors the OmniMark event-log pattern (`audit_logs` enriched with `level`/`category`/`location` + a `security_events` stream + a fire-and-forget `emit()` helper) and **extends it** with correlation IDs, before/after diffs, live tail, alert rules, and retention. It is a superset of the privileged-action **audit log** (doc 18): the audit log is just the `category in (admin, security)` view of this stream.

---

## 1. What it is (and how it relates to the audit log)

- **Event log = the unified stream** of all noteworthy events, actor-driven *and* system-generated (no-actor). One table, one viewer, filterable by category/level/actor/time.
- **Audit log (doc 18) = a filtered view** of the event log — the privileged/admin + security categories. Same storage; the "Audit Log" page is just a pre-filtered Event Log.
- This matches OmniMark, whose `audit_logs` table comment notes it records *"SYSTEM events (no tenant/no user) alongside actor-driven audit entries,"* with `level` + `category` + `location` dimensions.

---

## 2. Event taxonomy

**Dotted `event_type` namespaces** (OmniMark-style, extended for a trading platform):

| Category | Example event_types |
|---|---|
| **security** | `auth.login.success`, `auth.login.failure`, `auth.logout`, `auth.2fa.enabled`, `auth.password_change`, `session.force_logout`, `user.blocked`, `user.unblocked`, `ratelimit.tripped`, `anomaly.impossible_travel` |
| **admin** | `role.assigned`, `role.revoked`, `settings.appearance.updated`, `feature_flag.toggled`, `maintenance.enabled`, `pick.override`, `cms.page.published`, `cms.rollback`, `user.impersonate.start/stop` |
| **integration** | `integration.secret_read`, `integration.upserted`, `integration.rotated`, `integration.test.success/failure`, `integration.health.degraded`, `llm.fallback_used`, `data.provider.failover` |
| **system / pipeline** | `pipeline.daily.started/completed/failed`, `picks.generated` (count, regime), `exit_checker.triggered` (SL/target/breakeven), `job.metrics.recomputed`, `cache.redis.unavailable`, `data.fetch.failed` |
| **product** | `paper_trade.opened/closed`, `risk_guard.blocked` (over-heat/concentration), `subscription.created/upgraded/cancelled`, `alert.sent` |
| **data / compliance** | `data.export.requested/completed`, `data.deletion.requested/completed`, `consent.granted/withdrawn`, `retention.purged` |
| **billing** (P3) | `payment.succeeded/failed`, `refund.issued`, `subscription.renewed` |

**Severity `level`:** `debug | info | warning | error | critical` (indexed; drives filtering + alerting).

---

## 3. Data model (doc 06)

A single append-only `event_logs` table — OmniMark's fields **plus** advanced detail:

```
event_logs   (APPEND-ONLY: no UPDATE/DELETE from app; retention via TTL purge)
  id              uuid pk
  event_type      text         -- dotted namespace (security.* / system.* / …)
  category        text         -- security|admin|integration|system|product|data|billing  (indexed)
  level           text         -- debug|info|warning|error|critical                       (indexed)
  -- actor (nullable → SYSTEM events have no actor)
  actor_user_id   uuid null
  actor_role      text         -- snapshot of role at event time
  source          text         -- api|job|system|webhook|cli                              (indexed)
  -- target / subject of the event
  resource        text         -- e.g. "user", "integration", "cms_page", "paper_trade"
  resource_id     text
  -- change detail (advanced)
  before          jsonb null   -- prior state for mutations (secrets' VALUES never stored)
  after           jsonb null   -- new state
  payload         jsonb null   -- arbitrary structured context
  -- request / tracing context (advanced)
  request_id      text         -- correlation id to group all events of one request/job    (indexed)
  session_id      uuid null
  -- network / device
  ip              text
  location        text         -- resolved city/region/country (IP geo, doc 18)
  user_agent      text
  device          text
  -- integrity & time
  created_at      timestamptz  (indexed)
  hash_prev       text null    -- optional tamper-evident hash chain (advanced)
```

Plus (reused from OmniMark for compliance — doc 09):
```
data_subject_requests  -- DPDP/GDPR: requested_email, request_type(export/delete/rectify…),
                       --   status, regulation(dpdp/gdpr…), requester_ip, verified_at, due_at
                       --   (due_at = statutory deadline so the dashboard flags overdue)
```

---

## 4. Emitting events — the `emit()` helper (reuse OmniMark pattern)

A **fire-and-forget** helper every module calls after a noteworthy action:

```python
from app.services import event_log as ev
await ev.emit(db, "integration.secret_read", category="integration", level="warning",
              user=current_user, source="api", resource="integration", resource_id=provider,
              request_id=ctx.request_id, ip=req.client.host, payload={"provider": provider})
```

Rules (from OmniMark's `security_event_service.emit`, hardened):
- **Caller controls commit.** `emit()` just appends a row; if the caller's transaction rolls back, the event rolls back too — *correct*: no log entry for an action that didn't happen.
- **Never breaks the request path.** Wrapped in try/except + logged-and-swallowed; logging failures must not fail the user action.
- **Async + cheap.** For high-volume system events, batch/queue (Celery/Redis) so the hot path isn't slowed.
- **Secrets never logged** — store provider/key-id metadata, never the secret value (doc 17).
- **`request_id`** is set by middleware (doc 07) and threaded through, so all events of one request/job correlate.

Convenience wrappers: `ev.security(...)`, `ev.admin(...)`, `ev.system(...)` set the category.

---

## 5. Super Admin UI (`/admin/event-logs` — full page, doc 16)

OmniMark-style viewer, more advanced:
- **Unified table** (TanStack Table): time, level (colored), category, event_type, actor, resource, IP+location, source. Severity color-coded.
- **Filters (server-side):** category, level, event_type, actor, resource, date range, IP, source, `request_id`. **Saved filters** (e.g. "critical security last 24h").
- **Full-text search** over event_type/resource/payload.
- **Detail → full page** (not a dialog, doc 16): full payload, **before/after diff** for mutations, device/geo, and **"related events"** grouped by `request_id` (trace one request/job end-to-end).
- **Live tail:** optional real-time stream (SSE/WebSocket) to watch events as they happen.
- **Export:** CSV/JSON of the filtered set (DPDP-aware).
- **Alert rules:** define patterns (e.g. `level=critical`, or N `auth.login.failure` from one IP in 5 min) → notify admin (email/in-app, doc 18) and/or raise in Sentry.
- **Audit Log page** = this viewer pre-filtered to `category in (admin, security)`.
- **Pipeline/ops view** = pre-filtered to `category=system` (watch the 3:30 PM pipeline, data failures, integration health).

All RBAC-gated (`events.read`, doc 19); viewing is itself low-noise-logged.

---

## 6. API (doc 07)

```
GET /api/admin/event-logs            → filtered/paginated/searchable (server-side)
GET /api/admin/event-logs/{id}       → detail + before/after + related (by request_id)
GET /api/admin/event-logs/stream     → SSE/WebSocket live tail
GET /api/admin/event-logs/export     → CSV/JSON of filtered set
GET/POST/DELETE /api/admin/event-logs/alert-rules
GET /api/admin/event-logs/saved-filters
# audit log + pipeline views are the same endpoint with category filters
```

---

## 7. Integrity, retention & performance

- **Append-only:** no UPDATE/DELETE from the app; the "Audit Log" must be trustworthy (doc 18). Optional **hash chain** (`hash_prev`) for tamper-evidence.
- **Retention TTL:** purge by category/level after a configured window (security/compliance kept longer than debug/system) via the `retention_cleanup` job (doc 07); honors DPDP minimization (doc 09). Optional cold-archive (object storage) before purge.
- **Performance:** indexed on `created_at`, `category`, `level`, `event_type`, `request_id`; partition by month at scale; high-volume system events batched via a queue so the request path stays fast. Hot recent events cached for the live view.

---

## 8. Reuse from OmniMark (see [OMNIMARK-REUSE.md](./OMNIMARK-REUSE.md))

- **Reuse/adapt:** `audit_logs` (with `level`/`category`/`location`), `security_events`, `audit_log_service.py`, `security_event_service.py` (`emit()` pattern), `data_subject_requests`.
- **Build fresh for SwingAI:** the trading-domain event types (`pipeline.*`, `picks.generated`, `exit_checker.*`, `risk_guard.blocked`), correlation-by-`request_id`, live tail, alert rules, and before/after diffs (the "more advanced" parts you asked for).

---

## 9. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | `event_logs` table + `emit()` helper wired into auth/admin/integration/pipeline; full-page viewer with filters + detail + export; Audit Log view; DPDP `data_subject_requests` |
| 2 | Live tail, saved filters, alert rules → notifications, `request_id` tracing across request/job, before/after diffs |
| 3 | Hash-chain tamper-evidence, partitioning + cold archive, anomaly-pattern alerting, SIEM/export integrations |
| Future | ML anomaly detection on the event stream, forensics tooling, compliance report generation |

---

*Back to the [README index](./README.md). Related: audit log [18-user-management-sessions.md](./18-user-management-sessions.md), security [19-rbac-security.md](./19-rbac-security.md).*
