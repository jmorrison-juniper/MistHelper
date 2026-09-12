# Frontend Contracts: API Client Layer

**Portal**: Ops Frontend Portal
**Consumes**: Mist Ops Platform REST API (`/api/v1/`)
**Contract Source**: `specs/001-mist-ops-platform/contracts/`

---

## Overview

The portal does not expose its own API. This document defines the frontend's API client contracts — how the portal organizes, calls, and handles responses from the backend API.

---

## API Client Architecture

### Query Factory Pattern

Each backend route group maps to a query factory that produces TanStack Query keys and fetch functions:

| Factory | Backend Route Group | File |
|---------|-------------------|------|
| `configQueries` | `/api/v1/config/*` | `src/api/config.ts` |
| `auditQueries` | `/api/v1/audit/*` | `src/api/audit.ts` |
| `deployQueries` | `/api/v1/deploy/*` | `src/api/deploy.ts` |
| `syncQueries` | `/api/v1/sync/*` | `src/api/sync.ts` |
| `systemQueries` | `/api/v1/system/*` | `src/api/system.ts` |

### Example: Config Query Factory

```typescript
export const configQueries = {
  revisions: (params: RevisionParams) => ({
    queryKey: ['config', 'revisions', params],
    queryFn: () => apiClient.get<ConfigRevision[]>('/config/revisions', { params }),
  }),
  diff: (leftId: string, rightId: string) => ({
    queryKey: ['config', 'diff', leftId, rightId],
    queryFn: () => apiClient.post<ConfigDiff>('/config/diff', { left_id: leftId, right_id: rightId }),
  }),
  timeTravel: (deviceId: string, timestamp: string) => ({
    queryKey: ['config', 'time-travel', deviceId, timestamp],
    queryFn: () => apiClient.get<TimeTravelSnapshot>('/config/time-travel', { params: { device_id: deviceId, timestamp } }),
  }),
};
```

### Base API Client

```typescript
class ApiClient {
  private baseUrl = '/api/v1';

  async get<T>(path: string, options?: RequestOptions): Promise<ApiResponse<T>>;
  async post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>>;
  async put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>>;
  async delete<T>(path: string, options?: RequestOptions): Promise<ApiResponse<T>>;
}
```

**Key behaviors**:
- Relative URLs only (`/api/v1/...`) — Nginx proxies to backend
- `Authorization: Bearer <token>` header on all requests (or session cookie)
- 401 responses trigger session expiry flow (FR-007)
- Response envelope unwrapping: extracts `data` from `{data, meta, errors}`
- All errors mapped to `ApiError` type (FR-040)

---

## Polling Contracts

### Active Polling (5-second interval)

Used when the operator is watching a live operation:

| View | Endpoint | Condition |
|------|----------|-----------|
| Deployment progress | `GET /deploy/jobs/{id}` | Job status is `running` |
| Rollout progress | `GET /deploy/rollouts/{id}` | Rollout status is `active` |
| Export progress | `GET /audit/export/{id}` | Export status is `generating` |
| Compliance pack | `GET /audit/compliance-packs/{id}` | Pack status is `generating` |
| Install-from-revision | `GET /deploy/jobs/{id}` | Restore job is `running` |

### Passive Polling (30-second interval)

Used for background monitoring on the dashboard:

| View | Endpoint |
|------|----------|
| Dashboard org cards | `GET /sync/status` |
| Dashboard alert counts | `GET /sync/drift/alerts?acknowledged=false` |
| Notification badge | `GET /notifications/channels` |

### Polling Configuration

```typescript
interface PollingConfig {
  activeIntervalMs: number;   // Default: 5000
  passiveIntervalMs: number;  // Default: 30000
  maxRetries: number;         // Default: 3
  backoffMultiplier: number;  // Default: 2
}
```

Stored in Zustand settings store, configurable via Settings view.

---

## Mutation Contracts

### Destructive Operations (FR-039)

All destructive mutations send `{ confirm: true, reason: "..." }` in the request body. The portal MUST show a confirmation dialog before setting `confirm: true`.

| Operation | Endpoint | Confirmation Keyword |
|-----------|----------|---------------------|
| Install from revision | `POST /config/install-from-revision` | `RESTORE` |
| Remediate drift | `POST /sync/drift/alerts/{id}/remediate` | `REMEDIATE` |
| Rollback wave | `POST /deploy/rollouts/{id}/waves/{n}/rollback` | `ROLLBACK` |
| Cancel job | `DELETE /deploy/jobs/{id}` | (click confirm only) |
| Delete baseline | `DELETE /config/baselines/{id}` | (click confirm only) |

### Non-destructive Mutations

| Operation | Endpoint | Cache Invalidation |
|-----------|----------|--------------------|
| Login | `POST /auth/login` | Clears all queries |
| Create job | `POST /deploy/jobs` | `['deploy', 'jobs']` |
| Approve job | `POST /deploy/jobs/{id}/approve` | `['deploy', 'jobs', id]` |
| Run dry-run | `POST /deploy/dry-run` | None (read-only) |
| Create rollout | `POST /deploy/rollouts` | `['deploy', 'rollouts']` |
| Activate rollout | `POST /deploy/rollouts/{id}/activate` | `['deploy', 'rollouts', id]` |
| Acknowledge drift | `POST /sync/drift/alerts/{id}/acknowledge` | `['sync', 'drift']` |
| Accept baseline | `POST /sync/drift/alerts/{id}/accept` | `['sync', 'drift']`, `['config', 'baselines']` |
| Create baseline | `POST /config/baselines` | `['config', 'baselines']` |
| Export audit | `POST /audit/export` | `['audit', 'exports']` |
| Generate pack | `POST /audit/compliance-packs` | `['audit', 'packs']` |

---

## Error Handling Contract

### Error Code to Message Mapping

```typescript
const ERROR_MESSAGES: Record<string, string> = {
  ENTITY_NOT_FOUND: 'The requested resource was not found.',
  UNAUTHORIZED: 'Your session has expired. Please log in again.',
  FORBIDDEN: 'You do not have permission for this action.',
  VALIDATION_ERROR: 'Please check the highlighted fields and try again.',
  CONFLICT: 'This resource was modified by another user. Please refresh.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  SERVICE_UNAVAILABLE: 'The service is temporarily unavailable. Please try again shortly.',
};
```

### Global Error Handler

- **401**: Redirect to login page with `returnUrl` preserved (FR-007)
- **403**: Show inline error message (not redirect)
- **404**: Show "Not Found" state with last known entity details
- **409**: Show "Conflict" banner with refresh option (optimistic concurrency)
- **429**: Show "Rate Limited" toast with retry countdown
- **5xx**: Show "Service Unavailable" banner with retry option

---

## Security Contract

### CSP Headers (served by Nginx)

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; form-action 'self'
```

### Data Sanitization

All API-sourced string data rendered in the DOM MUST be sanitized:
- React's JSX escapes by default (covers most cases)
- `dangerouslySetInnerHTML` is PROHIBITED
- User-controlled strings in `title`, `alt`, `placeholder` are safe (attribute context)
- Configuration values displayed in diff views use text nodes only (no HTML rendering)

### Token Storage

- Session token stored in `httpOnly` cookie (set by backend)
- API token (if used) stored in memory only — never localStorage
- On logout: clear all cookies, clear Zustand store, clear TanStack Query cache
