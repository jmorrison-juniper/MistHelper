# Data Model: Reviewed Restore and Partial-Operation Recovery

This model extends the private state records of issue 4636. It adds the restore and recovery fields and one transition edge. Records live under the private store. The store writes one sealed JSON file for each record.

## Conventions

- All timestamps use UTC with an explicit offset. A naive timestamp is refused. Issue 4636 uses the same rule.
- Local identifiers are 32 lowercase hexadecimal characters from `uuid4`. A client never chooses an identifier.
- Mist objects use their natural IDs. Names are display and matching hints only.
- `digest` means a SHA-256 hex value. `seal` means an HMAC-SHA256 hex value.
- A normalized body is the object without the readOnly fields `id`, `org_id`, `created_time`, and `modified_time`. Task T002 may add a readOnly field from the OpenAPI schema.
- Canonical JSON uses `json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)` and then UTF-8 bytes. This is the encoding that issue 4636 uses.
- No record holds a credential. Only the `objects` mapping of a backup manifest holds object bodies, and only in the private store.

## BackupManifest (extended)

Natural key: `backup_id` with `object_family`.

| Field | Type | Rule |
| --- | --- | --- |
| `backup_id` | string | Local identifier. |
| `schema_version` | integer | `1` in this change. |
| `object_family` | string | One of `network`, `service`, or `service-policy`. |
| `organization_id` | string | Natural Mist organization ID. |
| `captured_at` | timestamp | UTC. |
| `pagination_complete` | boolean | Must be `true`. |
| `object_count` | integer | Must equal the number of entries in `object_digests` and `objects`. |
| `object_digests` | object | Natural Mist ID to normalized digest. |
| `objects` | object | Natural Mist ID to normalized body. Private. Decision D-27. |
| `relationships` | list | Each item holds `from_id`, `to_id`, and `relation`. |
| `seal` | string | HMAC-SHA256 over the canonical payload. |

Validation runs before any cloud call. It refuses the manifest when the seal fails, the count differs, a recomputed digest differs, the organization differs, the family differs, or pagination is incomplete. The refusal raises `StateRefused` and names the rule. The public view removes `objects`.

## ObjectDecision

Natural key: `operation_id`, `family`, and `backup_object_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `family` | string | One of `network`, `service`, or `service-policy`. |
| `backup_object_id` | string | Natural ID from the manifest. |
| `current_object_id` | string or null | Natural ID of the current object with the same ID, when one exists. |
| `decision` | string | One of `create`, `update`, `conflict`, `unchanged`, or `preserve`. |
| `reason` | string | One reason code from the table below. |
| `override` | boolean | `true` only for an update that an operator recorded. |
| `before_digest` | string or null | Normalized digest of the current object. |
| `target_digest` | string or null | Normalized digest of the backup body that a write sends. |
| `result_object_id` | string or null | New natural ID after a confirmed create. |

| Decision | Reason code | Rule |
| --- | --- | --- |
| `create` | `absent-free-name` | The ID is absent. A read returns not found. No current object has the same name. |
| `update` | `override-recorded` | The ID is present. The normalized digests differ. An operator recorded an override. |
| `conflict` | `changed-after-backup` | The ID is present. The normalized digests differ. No override exists. |
| `conflict` | `duplicate-name` | The ID is absent, and another current object has the same name. |
| `conflict` | `unresolved-reference` | A referenced name does not resolve. |
| `conflict` | `lookup-unavailable` | A read failed for a reason other than not found. |
| `conflict` | `wrong-organization` | The current object belongs to another organization. |
| `unchanged` | `identical` | The ID is present. The normalized digests are equal. |
| `preserve` | `absent-from-backup` | A current object has no backup entry. It is listed and never written or deleted. |

## OperationRecord (restore and recovery)

Natural key: `operation_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `operation_id` | string | Local identifier. |
| `organization_id` | string | Natural Mist organization ID. |
| `source_backup_id` | string | The verified backup that the proposal uses. |
| `recovery_backup_id` | string or null | The verified backup of target objects taken before the first write. |
| `approval_id` | string or null | Set when the record reaches `approved`. |
| `phase` | string | One `OperationPhase` value. |
| `proposal_digest` | string | Digest of the ordered `object_decisions`. |
| `scope_digest` | string | Digest of the organization, the source backup, the ordered write list, and the overrides. |
| `object_decisions` | list | One `ObjectDecision` for each backup object. Issue 4636 field extension. |
| `outcomes` | list | Each item holds `object_id`, `family`, `outcome`, `read_back_digest`, and `attempts`. |
| `recovery_actions` | list | One `RecoveryAction` for each proven write. Issue 4636 field extension. |
| `write_count` | integer | At most 100 (decision D-15). |
| `updated_at` | timestamp | UTC. |

`outcome` is one of `verified`, `failed`, `partial`, `indeterminate`, or `not-applied`. `attempts` is `0` or `1` for each write. The executor never sends a second attempt for one object. The SDK may repeat an HTTP 429 request internally, and the record counts that as one attempt.

## RecoveryAction

Natural key: `operation_id` and `object_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `object_id` | string | Natural ID of the object the action changes. |
| `action` | string | One of `restore-before-state`, `keep`, `delete`, or `none`. |
| `expected_digest` | string | Normalized digest that this operation recorded after a verified write. |
| `current_digest` | string | Normalized digest read during the proposal. |
| `status` | string | One of `proposed`, `conflict`, `approved`, `verified`, `failed`, `partial`, `indeterminate`, or `kept`. |
| `owner_permission` | boolean | Must be `true` before a `delete` action. Decision D-20. |

Rules:

- `restore-before-state` needs `current_digest` equal to `expected_digest`. Otherwise the status is `conflict` (decision D-18).
- `delete` needs `owner_permission` set to `true` and the deletion path of issue 4645 (decision D-20).
- `keep` is the default for each created object (decision D-19).
- `none` applies to a preserved object, an unchanged object, or an object whose write did not apply.

## ApprovalRecord (issue 4636, unchanged)

Natural key: `approval_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `approval_id` | string | Local identifier. |
| `operator_id` | string | Verified identity. The value `unverified` is refused (decision D-14). |
| `proposal_digest` | string | Must equal the proposal digest when checked. |
| `scope_digest` | string | Must equal the scope digest when checked. |
| `created_at` | timestamp | UTC. |
| `expires_at` | timestamp | `created_at` plus 15 minutes. Expiry is inclusive (decision D-21). |
| `state` | string | `unused` or `consumed`. |
| `consumed_at` | timestamp or null | Set once, under the approval lock. |

A usable approval has state `unused`, an unexpired `expires_at`, a verified operator, and matching digests. Any other case refuses execution.

## OperationPhase and transitions

The phase values come from issue 4636: `selected`, `validated`, `parsed`, `proposed`, `reviewed`, `approved`, `backup-verified`, `executing`, `verified`, `failed`, `partial`, `indeterminate`, `reconciled`, `recovery-proposed`, `recovering`, and `recovery-verified`.

The restore path uses these edges in order:

```text
selected -> validated -> parsed -> proposed -> reviewed -> approved
approved -> backup-verified -> executing
executing -> verified | failed | partial | indeterminate
partial | indeterminate -> reconciled
reconciled -> verified | recovery-proposed
recovery-proposed -> reviewed -> approved -> recovering
recovering -> recovery-verified | failed | partial | indeterminate
```

This record adds one edge to the table of issue 4636: `reconciled` to `verified` (decision D-25). The other edges come from issue 4636.

| Phase | Meaning in a restore |
| --- | --- |
| `selected` | The operator chose one source backup. |
| `validated` | The manifest passed every check. |
| `parsed` | The bodies are normalized and digested. |
| `proposed` | Each object has one decision. |
| `reviewed` | The operator confirmed the scope. |
| `approved` | One approval exists and is unused. |
| `backup-verified` | The recovery backup passed verification. |
| `executing` | Writes are running. The phase blocks a second execution. |
| `verified` | Every write has a verified outcome. |
| `failed` | The first write failed, and no earlier write applied. |
| `partial` | Some writes applied, and a later write failed. |
| `indeterminate` | A write outcome is unknown. |
| `reconciled` | Read-only lookups have resolved each uncertain outcome. |
| `recovery-proposed` | Recovery actions exist for proven changes. |
| `recovering` | Recovery writes are running. |
| `recovery-verified` | Every recovery action has a verified outcome. |

Guard rules:

- `approved` to `backup-verified` needs a verified recovery backup.
- `backup-verified` to `executing` needs a usable approval. A refused approval stops the transition.
- No edge leads from `indeterminate` to `executing`.
- `verified`, `failed`, and `recovery-verified` are terminal for their operation record. A new proposal starts a new record.

## ScopeLock

A scope lock is a lock file, not a record. Its key is the first 32 hexadecimal characters of the SHA-256 digest of the organization ID (decision D-26). The lock path is `<root>/operation/<key>.lock`. A lock timeout refuses execution and raises `PersistenceUnavailable`.

## Relationships

- One source `BackupManifest` serves many `OperationRecord` values.
- One `OperationRecord` refers to at most one recovery `BackupManifest`.
- One `OperationRecord` refers to one `ApprovalRecord` for each approved phase. A recovery has its own approval.
- One `OperationRecord` holds one `ObjectDecision` for each backup object.
- One `OperationRecord` holds zero or more `RecoveryAction` values.

## Persistence keys

| Kind | Record path | Lock path |
| --- | --- | --- |
| `operation` | `<root>/operation/<operation_id>.json` | `<root>/operation/<operation_id>.lock` |
| `approval` | `<root>/approval/<approval_id>.json` | `<root>/approval/<approval_id>.lock` |
| `backup` | `<root>/backup/<backup_id>.json` | `<root>/backup/<backup_id>.lock` |

Each identifier matches `^[0-9a-f]{32}$` before any path is built. The scope lock uses the key in the ScopeLock section.

## Exceptions

| Name | Raised by | Meaning |
| --- | --- | --- |
| `StateRefused` | `TransitionTable`, the manifest validator, and the approval check | A requested change or value is not allowed. The message names the rule and holds no secret. |
| `PersistenceUnavailable` | `PrivateStateStore` and the scope lock | A write, a read-back, or a lock failed. No success is reported. |
