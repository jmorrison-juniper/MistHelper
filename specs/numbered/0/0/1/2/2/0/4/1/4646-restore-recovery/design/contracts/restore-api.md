# Contract: Restore Portal Route

## Route

- Path: `/cisco-config-converter/admin/restore`
- Methods: `GET` returns the status of one operation. `POST` runs one command.
- Function: `restore_route` in `src/interfaces/portals/cisco_config_converter/routes.py`. It delegates to `RestoreCommandDispatcher`.
- Gate: the administrative gate that issue 4645 defines (decision D-22). A closed gate returns `404`. An open gate with a refused caller returns `403`.
- Every response uses `Cache-Control: no-store`.
- Every `POST` requires the converter CSRF token. The converter prefix is not an `/api/` path, so the middleware does not select JSON for it. Tests prove the CSRF failure shape.
- The request and response bodies use `application/json`.

## GET status

Query parameter: `operation_id`, which holds 32 lowercase hexadecimal characters.

Response `200`:

```json
{"operation_id": "<32 hex>", "phase": "<phase>", "proposal_digest": "<64 hex>", "scope_digest": "<64 hex>", "approval": null, "decisions": [], "outcomes": [], "recovery_actions": [], "write_count": 0}
```

Each entry in `decisions` holds `family`, `backup_object_id`, `current_object_id`, `decision`, `reason`, `override`, `before_digest`, `target_digest`, and `result_object_id`. No entry holds a body.

Response `404` for an unknown `operation_id`.

## POST command

The request body names one command in the field `command`. The allowed values are `propose`, `approve`, `execute`, `reconcile`, and `recovery-propose`.

| Command | Request fields | Success | Refusals |
| --- | --- | --- | --- |
| `propose` | `backup_id`, `organization_id`, `overrides` (a list of natural IDs) | `201` with the status shape | `400` for invalid input. `409` for a manifest that fails validation. |
| `approve` | `operation_id`, `proposal_digest`, `scope_digest`, `scope_confirmed` set to `true` | `201` with `approval_id` and `expires_at` | `403` while the operator identity is unverified (decision D-14). `409` when a digest differs or the phase is not reviewable. |
| `execute` | `operation_id`, `approval_id`, `confirm` set to `CONFIRM` | `200` with the outcomes | `400` for a wrong `confirm` word. `409` for an expired, consumed, or mismatched approval. `409` with code `lock_busy` when the scope lock times out. No write runs on any refusal. |
| `reconcile` | `operation_id` | `200` with the outcomes | `409` when the phase is not `partial` or `indeterminate`. Read-only. |
| `recovery-propose` | `operation_id`, `delete_created` (boolean) | `201` with the recovery actions | `403` for `delete_created` set to `true` without recorded owner permission (decision D-20). `409` when the phase is not `reconciled`. |

## Error shape

```json
{"error": "<code>", "message": "<text>", "correlation_id": "<32 hex>"}
```

The codes are `invalid_request`, `not_found`, `forbidden`, `conflict`, `lock_busy`, and `persistence_unavailable`.

Message rules:

- A message names the refused rule in plain words.
- A message never holds a backup body, a credential, or a secret value.
- A message uses ASCII characters only.

## Caution about partial results

Caution: A `200` response from `execute` can list a `partial` or `indeterminate` outcome. The client must show each outcome. The client must not show the whole operation as successful.

## Field stability

- The field names above are final when contract tests exist.
- A new field is additive. A removed field needs a new contract version.
- Issue 4647 renders these fields. It does not add a field to the response.
