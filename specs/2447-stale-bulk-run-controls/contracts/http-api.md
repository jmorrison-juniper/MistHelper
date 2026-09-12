# HTTP API Contract: Stale and Bulk Run Controls

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Version**: 2

The interfaces use the existing signed actor, cross-site request token, write
authorization, and site lock rules.

## 1. Common Rules

Every write request carries:

```http
Content-Type: application/json
X-CSRFToken: <session token>
Idempotency-Key: <request key>
```

The request key has 16 through 128 visible ASCII characters. The server stores
only a digest.

The server derives `actor_scope` from the existing identity kind and normalized
actor identity. A browser identifier or renewed session does not change this
scope.

The server rejects a list with a duplicate run identifier. It does not
de-duplicate the list.

## 2. Preview a Bulk Action

`POST /api/runs/bulk-actions/preview`

### Request

```json
{
  "action": "cancel",
  "organization_id": "org-a",
  "history_scope": "all-sites",
  "run_ids": ["run-111", "run-222"]
}
```

The endpoint is read-only. It needs the current signed actor and cross-site
request token. It does not need an idempotency key.

The server applies the current organization, history filter, and actor access.
It removes identifiers that are not visible in that scope.

### Response

```json
{
  "preview_id": "preview-opaque",
  "action": "cancel",
  "run_ids": ["run-111"],
  "removed_run_ids": ["run-222"],
  "run_count": 1,
  "site_count": 1,
  "site_counts": {"site-a": 1},
  "confirmation": "CANCEL 1 RUNS",
  "preview_token": "<signed-token>",
  "expires_at": "2026-09-11T09:00:00Z"
}
```

The browser replaces its stored selection with `run_ids` before it shows the
phrase input.

### Preview Errors

| Status | Code | Condition |
| - | - | - |
| 400 | `invalid_request` | A field has the wrong type or value. |
| 400 | `duplicate_run_id` | A run identifier occurs more than once. |
| 403 | `organization_forbidden` | The actor cannot read the organization. |
| 422 | `batch_size_invalid` | The list holds zero or more than 50 items. |
| 422 | `preview_empty` | No requested identifier remains visible. |

## 3. Submit a Bulk Action

`POST /api/runs/bulk-actions`

### Request

```json
{
  "action": "cancel",
  "run_ids": ["run-111"],
  "confirmation": "CANCEL 1 RUNS",
  "preview_token": "<signed-token>"
}
```

The signed preview token binds:

- The durable actor scope.
- The organization and history scope.
- The action.
- The ordered run identifiers.
- The exact counts.
- The expiry time.

The action request fails before processing when any bound value differs.

### Action Initialization

The first ArangoDB transaction creates:

1. One action record for the composite domain key.
2. `source_kind: bulk_preview` and the required preview fields.
3. One ordered outcome placeholder for each requested run.
4. `processing_state: pending`, `classification: unknown`, and
   `reason: not_processed` for each placeholder.

If this transaction fails, the endpoint returns 503 and mutates no run.

Before item work, a compare-and-swap write changes the item from `pending` to
`claimed`.

A refusal, failure, or unknown result that changes no run uses an outcome-only
compare-and-swap write. A successful mutation finalizes the item in the same
transaction as the run change.

After every item becomes final, one compare-and-swap write changes the action
from `processing` to `complete`. The endpoint reads the stored complete record
before it reports success.

### Complete Response

The endpoint returns 200 after every item has a durable outcome.

```json
{
  "action_id": "action-opaque",
  "action": "cancel",
  "status": "complete",
  "run_count": 1,
  "site_count": 1,
  "evidence_summary_digest": null,
  "counts": {
    "succeeded": 1,
    "refused": 0,
    "failed": 0,
    "unknown": 0
  },
  "items": [
    {
      "source_run_id": "run-111",
      "site_id": "site-a",
      "action": "cancel",
      "processing_state": "final",
      "classification": "succeeded",
      "reason": "precloud_run_cancelled",
      "message": "The portal cancelled the pre-cloud run.",
      "result_run_id": "run-111",
      "prior_state": "awaiting_confirmation",
      "final_state": "cancelled",
      "evidence_summary": null
    }
  ]
}
```

### Request-Level Errors

| Status | Code | Condition |
| - | - | - |
| 400 | `invalid_request` | A field has the wrong type or value. |
| 400 | `duplicate_run_id` | A run identifier occurs more than once. |
| 400 | `confirmation_mismatch` | The typed phrase does not match. |
| 409 | `idempotency_key_reused` | The same key has different content. |
| 409 | `preview_mismatch` | The request does not match the signed preview. |
| 410 | `preview_expired` | The signed preview expired. |
| 422 | `batch_size_invalid` | The list holds zero or more than 50 items. |
| 503 | `action_store_unavailable` | ArangoDB cannot start the action. |

The endpoint does not use Redis, SQLite, memory, or file fallback for a 503.

## 4. Per-Item Guard Order

Before each item mutation, the service:

1. Reads the current run.
2. Reads current write permission.
3. Reads and compares the current site lock token.
4. Starts the ArangoDB mutation transaction.

If permission or the lock fails, the current item receives a refusal. The
service stops later writes for that site.

Later items for that site keep `unknown` and receive
`not_processed_after_site_guard_loss`. Other sites continue.

## 5. Cancel Reasons

| Classification | Reason |
| - | - |
| `succeeded` | `precloud_run_cancelled` |
| `refused` | `run_not_found` |
| `refused` | `run_not_precloud` |
| `refused` | `run_already_final` |
| `refused` | `run_state_unknown` |
| `refused` | `site_write_forbidden` |
| `refused` | `site_lock_not_owned` |
| `refused` | `site_lock_token_changed` |
| `refused` | `run_changed` |
| `failed` | `run_write_failed` |
| `unknown` | `run_write_unverified` |
| `unknown` | `processing_interrupted` |
| `unknown` | `not_processed` |
| `unknown` | `not_processed_after_site_guard_loss` |

The cancel transaction changes the run and replaces its outcome together.
Cancel sends no cloud request.

## 6. Retry Rules

Retry accepts only `failed`, `stopped`, or `cancelled`.

The source must have a valid `updated_at`. The newest source for one site uses
UTC `updated_at`, then `run_id` as a stable tie breaker.

The exact top-level option allowlist is:

```text
reboot
junos_file_action
strategy
force
stable_version
canary
rrm
peer_to_peer
ssr
schedule
```

Nested fields must match the fields accepted by
`upgrade.options.build_options`. The service rejects any unknown field. It
then validates the copied value through that existing validator.

The service copies targets and approved options only. It does not copy a
pre-check, confirmation, cloud task identifier, or unsupported absolute time.

### Retry Reasons

| Classification | Reason |
| - | - |
| `succeeded` | `retry_created` |
| `refused` | `run_not_found` |
| `refused` | `run_not_retryable` |
| `refused` | `retry_source_time_unknown` |
| `refused` | `retry_options_unsupported` |
| `refused` | `retry_options_invalid` |
| `refused` | `site_duplicate_retry_source` |
| `refused` | `site_write_forbidden` |
| `refused` | `site_lock_not_owned` |
| `refused` | `site_lock_token_changed` |
| `refused` | `upgrade_already_running` |
| `refused` | `run_changed` |
| `failed` | `retry_create_failed` |
| `unknown` | `retry_create_unverified` |
| `unknown` | `processing_interrupted` |
| `unknown` | `not_processed` |
| `unknown` | `not_processed_after_site_guard_loss` |

A live-run refusal includes `live_run_id`. A success includes `result_run_id`
and the fresh pre-check URL.

The live-run check, retry insert, and success outcome use one transaction.

## 7. Reconcile One Run

`POST /api/runs/<run_id>/reconcile`

### Request

```json
{
  "confirmation": "RECONCILE run-111"
}
```

The request uses the common idempotency rules. Reconciliation follows
[reconciliation.md](reconciliation.md).

The endpoint does not request or accept a bulk preview token.

The initialization transaction stores:

```json
{
  "source_kind": "single_reconciliation",
  "preview_id": null,
  "preview_digest": null,
  "history_scope": null,
  "action": "reconcile",
  "run_count": 1,
  "site_count": 1
}
```

It creates one pending durable outcome for `run_id`. The confirmation digest,
actor scope, organization, and request digest bind the action.

For a pre-cloud reconciliation, `evidence_summary` and
`evidence_summary_digest` remain null.

For a final `stopping` reconciliation item, the item contains the safe
`ReconciliationEvidenceSummary` from
[data-model.md](../data-model.md). The action contains its matching digest.

The same outcome-only write stores these fields for a refused, failed, or
unknown result after evidence collection. The response contains no raw target
identifier, task identifier, cloud payload, credential, token, actor identity,
or exception text.

## 8. Read an Action Result

`GET /api/run-actions/<action_id>`

The endpoint performs no write and needs no idempotency key.

The server queries by the current durable `actor_scope` and `action_id`. It
returns 404 for an absent action or an action of another actor.

| Status | Code | Condition |
| - | - | - |
| 404 | `action_not_found` | The actor-scoped action does not exist. |
| 503 | `action_store_unavailable` | ArangoDB cannot answer the read. |

This response does not reveal whether another actor owns the identifier.

## 9. Replay and Recovery

1. A same-key same-request replay returns the stored action.
2. A same-key different-request replay returns 409.
3. A replay never repeats a mutation.
4. A current processing lease returns `processing`.
5. After lease expiry, one worker takes ownership with compare-and-swap.
6. Recovery finalizes each old claimed item as `processing_interrupted`.
7. Recovery processes only pending items.
8. Recovery never repeats a claimed or final item.
9. A stored site block prevents later writes for that site.
10. Recovery finalizes all items and then changes the action to `complete`.

## 10. Stable Response Rules

- Response order matches request order.
- Each requested run has exactly one item.
- An `unknown` item claims no final state.
- A `succeeded` item has a verified final or new run identifier.
- A complete action contains only final items.
- A final `stopping` reconciliation item contains one valid evidence summary.
- Its parent action contains the matching evidence summary digest.
- Responses contain no credential, token, raw actor identity, or cloud secret.
