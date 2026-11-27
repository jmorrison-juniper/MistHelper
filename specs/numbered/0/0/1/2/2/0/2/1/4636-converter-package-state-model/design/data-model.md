# Data Model: Compliant Converter Package and State Model

This model defines the private records of the converter state package. Each record lives under `state/` and needs no database. The store writes each record as one sealed JSON file. Section Persistence Keys names the file layout.

## Conventions

- All timestamps use UTC with an explicit offset. A naive timestamp is refused.
- Local identifiers are 32 lowercase hexadecimal characters from `uuid4`. A client never chooses an identifier.
- Mist objects use their natural IDs as references. Names are display hints only.
- `digest` means a SHA-256 hex value. `seal` means an HMAC-SHA256 hex value.
- Each record keeps no source text and no secret value.

## Source and Review

### SourceRecord

Natural key: `source_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `source_id` | string | Local identifier. |
| `content_digest` | string | SHA-256 of the raw UTF-8 bytes. |
| `byte_count` | integer | From 1 through 16,777,216. |
| `suffix` | string | One of `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, or `.log`. |
| `display_name` | string | From 1 through 120 visible characters. |
| `kind` | string | `standalone` or `spoke`. Unchanged until T011 and T012. |
| `owner` | string | Operator identity, or the value `unverified` for read-only records. |
| `created_at` | timestamp | UTC. |

Source text does not enter this record. The record shows only the digest and size.

### ReviewRecord

Natural key: `review_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `review_id` | string | Local identifier. |
| `source_id` | string | References one `SourceRecord`. |
| `proposal_digest` | string | Legacy digest of the three proposal keys. |
| `owner` | string | Operator identity. |
| `created_at` | timestamp | UTC. |
| `expires_at` | timestamp | `created_at` plus `REVIEW_LIFETIME`, which is 15 minutes. |
| `state` | string | `current` or `invalidated`. A review is `expired` when the read time is at or after `expires_at`. |
| `invalidated_reason` | string | `none`, `input-changed`, `proposal-changed`, `target-changed`, `new-preview`, or `failed-preview`. |

The existing `ReviewState` class keeps its session behavior. It is not a stored record. This model adds `ReviewRecord` beside it.

## Proposal

### ProposalRecord

Natural key: `proposal_digest` together with `version`.

| Field | Type | Rule |
| --- | --- | --- |
| `proposal_digest` | string | Canonical digest of `gateway_template`, `unsupported_items`, and `known_gaps`. It equals `ReviewState.digest` for the same object. |
| `scope_digest` | string | Canonical digest of `version`, `source_id`, `target_refs`, `contract_versions`, and `proposal_digest`. |
| `version` | integer | At least 1. |
| `source_id` | string | References one `SourceRecord`. |
| `gateway_template` | object | The `GatewayTemplate` shape. |
| `unsupported_items` | list | Each item holds `line`, `command`, and `reason`. |
| `known_gaps` | list of strings | Limits of the conversion subset. |
| `target_refs` | list of strings | Natural Mist IDs. Empty in this change. |
| `contract_versions` | object | Empty in this change. Filled after gate G2. |
| `created_at` | timestamp | UTC. |

Decision D-4 explains the two digests. The legacy digest keeps existing review values. The scope digest covers targets and versions, so an approval changes when a target changes.

## Approval and Operation

### ApprovalRecord

Natural key: `approval_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `approval_id` | string | Local identifier. |
| `operator_id` | string | A verified identity. The issue refuses the value `unverified`. |
| `proposal_digest` | string | Must equal the current proposal digest when checked. |
| `scope_digest` | string | Must equal the current scope digest when checked. |
| `created_at` | timestamp | UTC. |
| `expires_at` | timestamp | `created_at` plus `REVIEW_LIFETIME`. Expiry is inclusive. |
| `state` | string | `unused` or `consumed`. |
| `consumed_at` | timestamp or null | UTC. Set once, under the approval lock. |

A usable approval has state `unused`, an unexpired `expires_at`, a verified operator, and matching digests. Any other case refuses execution.

### OperationPhase

The enum values use the same kebab-case terms as the transition table.

`selected`, `validated`, `parsed`, `proposed`, `reviewed`, `approved`, `backup-verified`, `executing`, `verified`, `failed`, `partial`, `indeterminate`, `reconciled`, `recovery-proposed`, `recovering`, and `recovery-verified`.

### OperationRecord

Natural key: `operation_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `operation_id` | string | Local identifier. |
| `approval_id` | string or null | Set when the operation reaches `approved`. |
| `proposal_digest` | string | Copied from the approval. |
| `scope_digest` | string | Copied from the approval. |
| `phase` | string | One `OperationPhase` value. |
| `object_refs` | list of strings | Natural Mist IDs. |
| `before_state_digests` | object | Natural Mist ID to digest. |
| `backup_ids` | list of strings | References to `BackupManifest` records. |
| `outcomes` | list | Each item holds `object_ref` and `outcome`. `outcome` is `verified`, `failed`, `partial`, or `indeterminate`. |
| `updated_at` | timestamp | UTC. |

The phase `verified` needs every object outcome set to `verified` and a successful read-back.

## Backup

### BackupManifest

Natural key: `backup_id`.

| Field | Type | Rule |
| --- | --- | --- |
| `backup_id` | string | Local identifier. |
| `schema_version` | integer | `1` in this change. |
| `object_family` | string | One of `gateway-template`, `device-profile`, `network`, `service`, `service-policy`, or `site-setting`. |
| `organization_id` | string | Natural Mist organization ID. |
| `captured_at` | timestamp | UTC. |
| `pagination_complete` | boolean | Must be `true`. |
| `object_count` | integer | Must equal the number of `object_digests`. |
| `object_digests` | object | Natural Mist ID to digest. |
| `relationships` | list | Each item holds `from_id`, `to_id`, and `relation`. |
| `seal` | string | HMAC-SHA256 over the canonical payload. |

Validation refuses a manifest when pagination is incomplete, the count differs, a recomputed digest differs, the organization differs, or the family differs.

## Relationships

- One `SourceRecord` has many `ReviewRecord` values.
- One `ReviewRecord` refers to one `ProposalRecord` by digest.
- One `ApprovalRecord` binds one proposal digest and one scope digest.
- One `OperationRecord` refers to at most one `ApprovalRecord`.
- One `OperationRecord` refers to many `BackupManifest` records.

## Transition Table

The transition table is `TransitionTable` in `state/lifecycle/transitions.py`. A pair not listed here is refused with `StateRefused`.

### Documented edges

These edges come from the full-parity data model, section State Transitions, at lines 43 to 50.

| From | To |
| --- | --- |
| `selected` | `validated` |
| `validated` | `parsed` |
| `parsed` | `proposed` |
| `proposed` | `reviewed` |
| `reviewed` | `approved` |
| `approved` | `backup-verified` |
| `backup-verified` | `executing` |
| `executing` | `verified` |
| `executing` | `failed` |
| `executing` | `partial` |
| `executing` | `indeterminate` |
| `partial` | `reconciled` |
| `indeterminate` | `reconciled` |
| `reconciled` | `recovery-proposed` |
| `recovery-proposed` | `reviewed` |
| `approved` | `recovering` |
| `recovering` | `recovery-verified` |

### Added edges (decision D-12)

The documented edges omit four rules that the same data model states in prose. This change adds the edges that those rules need.

| From | To | Reason |
| --- | --- | --- |
| `validated`, `parsed`, `proposed`, `reviewed`, `approved`, `backup-verified` | `selected` | Rejected or changed input returns to selection. |
| `reviewed`, `approved`, `backup-verified` | `proposed` | A proposal or target change returns to `proposed`. |
| `recovering` | `failed` | A failed recovery stays visible as failed. |
| `recovering` | `partial` | A partial recovery stays visible as partial. |
| `recovering` | `indeterminate` | An unknown recovery outcome stays indeterminate. |

### Guard rules

- `backup-verified` to `executing` needs a usable approval. The table takes a boolean for this check. A false value refuses the transition.
- No edge leads from `indeterminate` to `executing`.
- `verified`, `failed`, and `recovery-verified` are terminal in this operation record.
- A new proposal starts a new operation record. It does not reuse a terminal record.

## Persistence Keys

The store writes each record below its kind directory. The kind names are `source`, `review`, `proposal`, `approval`, `operation`, and `backup`.

- Record path: `<root>/<kind>/<identifier>.json`
- Lock path: `<root>/<kind>/<identifier>.lock`
- Temporary path: `<root>/<kind>/<identifier>.json.tmp-<uuid4 hex>`

The identifier must match `^[0-9a-f]{32}$` before any path is built. Source: `design/contracts/state-store.md`.

## Exceptions

| Name | Raised by | Meaning |
| --- | --- | --- |
| `StateRefused` | `TransitionTable`, record validators | A requested state change or record value is not allowed. The message holds no secret. |
| `PersistenceUnavailable` | `PrivateStateStore` | A write, a read-back, or a lock failed. No success is reported. |
