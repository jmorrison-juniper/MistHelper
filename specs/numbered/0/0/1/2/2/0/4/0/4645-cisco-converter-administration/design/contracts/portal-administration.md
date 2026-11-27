# Contract: Portal Administration Routes

This contract defines the four administrative routes that `AdministrationRoutes` registers on the converter blueprint. The blueprint URL prefix is `/cisco-config-converter`. The routes stay unregistered on the shared portal until issue 4648 completes (FR-023).

## Gate Order

Each request passes these gates in order. The first failed gate returns its status. No later gate runs. No gate after a failure reads or writes Mist.

| Order | Gate | Failure status | Write allowed |
| --- | --- | --- | --- |
| 1 | Existing CSRF guard on each POST (FR-004) | 400 | No |
| 2 | Administrative mode equals `enabled` (FR-001) | 404 | No |
| 3 | Family appears in `CISCO_CONVERTER_ADMIN_FAMILIES` (FR-002). Not checked on the page route. | 403 | No |
| 4 | Verified operator identity (FR-003) | 403 | No |
| 5 | Request body is a JSON object with valid fields (FR-005) | 400 | No |
| 6 | Scope review is current (FR-007, FR-008). Checked on approve and execute. | 409 | No |
| 7 | Scope confirmation equals the scope digest (FR-009). Checked on approve. | 400 | No |
| 8 | Typed word equals `CONFIRM` (FR-009). Checked on execute. | 400 | No |
| 9 | Approval exists, is unexpired, and is unused (FR-010). Checked on execute. | 409 | No |
| 10 | Operation record persists (FR-012) | 503 | No |
| 11 | Before-state digest matches for each object (FR-011) | 409 | No |
| 12 | Writes, read-back, and outcomes for each object (FR-014, FR-016, FR-017) | 200 with outcomes | Yes, one object at a time |

Warning: Gate 12 writes to Mist. A failure in gate 12 cannot undo a write that already succeeded. The response lists each completed object outcome.

## Route 1: Administration Page

- Method and path: `GET /cisco-config-converter/admin`
- Response when the mode is enabled: HTML from `presentation/administration.html`, with the header `Cache-Control: no-store`.
- Response when the mode is disabled: 404 with no body.
- The page does not call Mist. It holds the controls and the static text only.

## Route 2: Scope Review

- Method and path: `POST /cisco-config-converter/admin/scope`
- Request body (JSON):

```json
{"organization_id": "6f1f2c4e-0d7a-4c2b-9a51-3e8b2d7c1a10", "family": "gateway_templates", "object_ids": ["4b7d1c2e-9f3a-4e8b-8d2a-1c5e7f9a3b20"]}
```

- Response body (JSON), status 200 for a valid request:

```json
{"review_status": "current", "scope_digest": "3b7e1f0c9a2d4e6f8b1c3d5e7f9a0b2c4d6e8f1a3b5c7d9e0f2a4b6c8d0e1f2a", "blocked_reasons": [], "objects": [{"object_id": "4b7d1c2e-9f3a-4e8b-8d2a-1c5e7f9a3b20", "display_name": "Example gateway template", "before_state_digest": "3b7e1f0c9a2d4e6f8b1c3d5e7f9a0b2c4d6e8f1a3b5c7d9e0f2a4b6c8d0e1f2a", "reference_status": "none_found"}], "backup_status": [{"family": "gateway_templates", "manifest_id": "bk-2026-11-26-0001", "status": "verified"}]}
```

- When any reference is blocked or unverified, `review_status` is `blocked`. `scope_digest` is `null`. `blocked_reasons` names each reason in plain text.
- A malformed request returns 400 with `{"error": "Submit a valid JSON scope."}`.
- The route reads Mist objects. It writes nothing.

## Route 3: Scope Confirmation and Approval

- Method and path: `POST /cisco-config-converter/admin/approve`
- Request body (JSON):

```json
{"organization_id": "6f1f2c4e-0d7a-4c2b-9a51-3e8b2d7c1a10", "family": "gateway_templates", "object_ids": ["4b7d1c2e-9f3a-4e8b-8d2a-1c5e7f9a3b20"], "scope_digest": "3b7e1f0c9a2d4e6f8b1c3d5e7f9a0b2c4d6e8f1a3b5c7d9e0f2a4b6c8d0e1f2a", "scope_confirmation": "3b7e1f0c9a2d4e6f8b1c3d5e7f9a0b2c4d6e8f1a3b5c7d9e0f2a4b6c8d0e1f2a"}
```

- `scope_confirmation` must equal `scope_digest`. The approval step recomputes the digest from the request. It refuses a stale or changed scope (gates 6 and 7).
- Response body (JSON), status 200:

```json
{"approval_id": "6f1f2c4e-0d7a-4c2b-9a51-3e8b2d7c1a10", "expires_at_utc": "2026-11-26T16:15:00Z"}
```

- The approval expires 15 minutes after `created_at_utc`. The boundary is inclusive (FR-010).

## Route 4: Run

- Method and path: `POST /cisco-config-converter/admin/execute`
- Request body (JSON):

```json
{"approval_id": "6f1f2c4e-0d7a-4c2b-9a51-3e8b2d7c1a10", "typed_word": "CONFIRM"}
```

- `typed_word` must equal `CONFIRM` exactly. The server compares the value. The client check is a convenience only.
- Response body (JSON), status 200 when the run reaches a final phase:

```json
{"operation_id": "9d4e2b1a-7c3f-4a5e-8b6d-2f1e0c9a8b7d", "run_status": "completed", "objects": [{"family": "gateway_templates", "object_id": "4b7d1c2e-9f3a-4e8b-8d2a-1c5e7f9a3b20", "action": "delete", "outcome": "verified", "detail": "Deleted and read back as absent"}]}
```

- `run_status` is `completed`, `stopped`, or `reconcile_required`. A stopped run lists `not_attempted` for each later object.
- A refusal before the first write returns the status in the gate table. No operation record reaches the `executing` phase.

## Headers and Errors

- Each JSON response uses `Cache-Control: no-store`.
- Each JSON POST sends the `X-CSRFToken` header (FR-004).
- Each error body has one field: `{"error": "Submit a valid JSON scope."}`. The text names the refusal in plain words.

## Redaction

- A response never returns a token, a password, or a raw Mist response body (FR-018).
- A response never echoes `typed_word`.
- A log line never holds the typed word, a token, or a request body (FR-020).
- MAC addresses and object IDs appear in responses. They identify objects and hold no secret.
