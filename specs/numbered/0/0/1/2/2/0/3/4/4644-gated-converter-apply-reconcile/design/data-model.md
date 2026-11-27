# Data Model: Gated Converter Apply and Reconciliation

This model adds the apply entities on top of the issue 4636 records. It adds no new storage file. The operation and approval records use the issue 4636 store, and the seal uses `PORTAL_SECRET_KEY`.

## Conventions

- Timestamps use UTC with an explicit offset. A naive timestamp is refused.
- Local identifiers are 32 lowercase hexadecimal characters from `uuid4`. A client never chooses an identifier.
- Mist objects use natural Mist IDs. Names are display hints only.
- `digest` means a SHA-256 hex value. The digest covers canonical JSON.
- No record holds a payload value, a token, or a secret.

## Entities

### ChangeItem

Natural key: `family_id` with `object_id`, or `family_id` with `request_key` for a create.

| Field | Type | Rule |
| --- | --- | --- |
| `family_id` | string | One of `F-01` to `F-08`. |
| `action` | string | `create`, `update`, or `assign`. |
| `object_id` | string or null | Natural Mist ID. Null for a create until the create returns an ID. |
| `request_key` | string | Local identifier for a create. Used to match a read-back. |
| `before_digest` | string or null | Digest of the current object. Null for a create. |
| `payload_digest` | string | Digest of the approved fields only. |
| `outcome` | string or null | One value from the outcome table. Null before execution. |

### ChangeSet

A `ChangeSet` is an ordered list of `ChangeItem` values. It has one organization ID, the site IDs, and the gateway IDs. Its digest is part of the scope digest (amendment X-4 in issue 4636).

### ApprovalRecord (issue 4636)

The approval holds `approval_id`, `operator_id`, `proposal_digest`, `scope_digest`, `created_at`, `expires_at` (15 minutes after creation, inclusive), `state` (`unused` or `consumed`), and `consumed_at`. This record adds a cancel reason. A cancel sets `state` to `consumed` and `consumed_reason` to `canceled`.

### OperationRecord (issue 4636)

The operation holds `operation_id`, `approval_id`, `proposal_digest`, `scope_digest`, `phase`, `items` (a list of `ChangeItem`), `backup_ids`, and `updated_at`. Amendment X-2 adds the outcome `not-applied`.

### ReconciliationResult

Natural key: `operation_id` with `object_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `approved_fields_match` | boolean | True when each approved field equals the read-back value. |
| `unrelated_digest_match` | boolean | True when the unrelated fields equal the before-state digest. |
| `read_count` | integer | Count of read calls for the object. Zero write calls are allowed. |
| `outcome` | string | `verified`, `failed`, `partial`, or `indeterminate`. |

## State Transitions

The transitions use the table from issue 4636, with amendments X-2 and X-3.

| From | To | Guard |
| --- | --- | --- |
| `reviewed` | `approved` | A usable approval exists. The typed word equals `APPLY`. |
| `approved` | `backup-verified` | `BackupGate` passes for each family. |
| `approved` | `reviewed` | Cancel voids the approval (amendment X-3). |
| `backup-verified` | `executing` | The approval is consumed under the scope lock. Preflight digests match. |
| `executing` | `verified` | Each item outcome is `verified` and the store verified the record. |
| `executing` | `partial` | At least one item is `verified` and at least one is `failed`, `indeterminate`, or `not-applied`. |
| `executing` | `failed` | No item is written, and each refusal is `failed`. |
| `executing` | `indeterminate` | At least one item is `indeterminate` and no item is `partial`. |
| `partial` | `reconciled` | Read-only reconciliation finished for each item. |
| `indeterminate` | `reconciled` | Read-only reconciliation finished for each item. |

No edge leads from `indeterminate` to `executing`. The table refuses that edge.

## Outcome Mapping

The mapping applies to each item after its write call and its read-back.

| Condition | Outcome |
| --- | --- |
| A 2xx status, a valid body, and a read-back that matches the approved fields | `verified` |
| A 2xx status, and a read-back that differs | `partial` |
| HTTP 400, 401, 403, or 404 | `failed` |
| A final HTTP 429 after the SDK retries | `indeterminate` |
| HTTP 5xx, a timeout, a connection loss, a proxy error, or a malformed body | `indeterminate` |
| A create with no natural ID in the response or the read-back | `indeterminate` |
| An item after a stop | `not-applied` |

## Relationships

- One `ChangeSet` holds many `ChangeItem` values.
- One `ApprovalRecord` binds one proposal digest and one scope digest.
- One `OperationRecord` refers to at most one `ApprovalRecord` and many backup records.
- One `OperationRecord` holds one `ReconciliationResult` for each item after reconciliation.

## Persistence

The store writes each record under its kind directory, as issue 4636 defines. This record adds the kind `operation` for the operation record and the kind `approval` for the approval record. It adds no file layout.
