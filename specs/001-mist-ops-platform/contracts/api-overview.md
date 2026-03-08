# API Contracts: Overview

**Platform**: Mist Ops Platform
**Protocol**: REST over HTTPS (JSON)
**Base URL**: `/api/v1`
**Auth**: Bearer token (Mist API token) or session cookie (interactive login)

---

## API Organization

The API is organized into 5 route groups, each documented in its own file:

| Group | Prefix | File | Purpose |
|-------|--------|------|---------|
| Config | `/api/v1/config` | [config.md](config.md) | Revisions, diffs, install-from-revision, baselines |
| Audit | `/api/v1/audit` | [audit.md](audit.md) | Change audit trail, export, compliance packs |
| Deploy | `/api/v1/deploy` | [deploy.md](deploy.md) | Scheduled jobs, rollouts, dry-run, firmware |
| Sync | `/api/v1/sync` | [sync.md](sync.md) | Sync status, drift alerts, inventory, webhooks |
| System | `/api/v1/system` | (inline below) | Health, auth, notifications |

---

## Common Patterns

### Authentication

All endpoints require authentication via one of:
- `Authorization: Bearer <mist_api_token>` header
- Session cookie (from interactive login flow)

The platform validates the token against the Mist API (`GET /api/v1/self`)
and caches the result for 5 minutes. Org-scoped tokens can only access
resources within their org. MSP-level sessions can access all orgs.

### Response Envelope

All responses follow a standard envelope:

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 1234,
    "total_pages": 25
  },
  "errors": []
}
```

- `data`: Response payload (object or array)
- `meta`: Pagination metadata (present on list endpoints)
- `errors`: Array of error objects (empty on success)

### Error Format

```json
{
  "data": null,
  "errors": [
    {
      "code": "ENTITY_NOT_FOUND",
      "message": "Config revision 42 not found",
      "field": null,
      "detail": "No revision with ID 42 exists for org abc-123"
    }
  ]
}
```

### Pagination

List endpoints accept query parameters:
- `page` (default: 1): Page number
- `per_page` (default: 50, max: 200): Items per page

### Filtering

List endpoints accept filter query parameters specific to each resource.
Timestamp filters use ISO 8601 format: `2026-03-05T14:00:00Z`.

### Confirmation for Destructive Operations

Destructive operations (install-from-revision, remediation push, rollback,
firmware upgrade) require an explicit `confirm` field in the request body:

```json
{
  "confirm": true,
  "reason": "Reverting WLAN change that caused client drops"
}
```

If `confirm` is false or missing, the endpoint returns a 400 error with
a description of what would happen (dry-run behavior).

---

## System Endpoints (inline)

### GET /api/v1/healthz

Health check for container orchestration liveness probe.

**Response** (200 OK):
```json
{"status": "healthy"}
```

### GET /api/v1/readyz

Readiness check for container orchestration readiness probe.

**Response** (200 OK):
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "mist_api": "ok"
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "not_ready",
  "checks": {
    "database": "ok",
    "redis": "error: connection refused",
    "mist_api": "ok"
  }
}
```

### GET /api/v1/metrics

Prometheus metrics endpoint. Returns metrics in Prometheus exposition format.

### POST /api/v1/auth/login

Interactive login flow (email/password + optional 2FA).

**Request**:
```json
{
  "email": "operator@example.com",
  "password": "...",
  "two_factor_code": "123456"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "session_id": "...",
    "privileges": { ... },
    "msp_id": "...",
    "orgs": [{"org_id": "...", "name": "..."}]
  }
}
```

### GET /api/v1/auth/self

Returns the authenticated user's identity and privileges (proxied from
Mist API `GET /api/v1/self`).

### GET /api/v1/notifications/channels

List notification channels for the authenticated org.

### POST /api/v1/notifications/channels

Create a notification channel.

**Request**:
```json
{
  "name": "Slack Ops Channel",
  "channel_type": "webhook",
  "destination": "https://hooks.slack.com/services/...",
  "alert_subscriptions": ["deployment_failed", "drift_detected"],
  "auth_config": {"type": "bearer", "vault_ref": "secret/slack/token"}
}
```

### PUT /api/v1/notifications/channels/{channel_id}

Update a notification channel.

### DELETE /api/v1/notifications/channels/{channel_id}

Delete a notification channel.
