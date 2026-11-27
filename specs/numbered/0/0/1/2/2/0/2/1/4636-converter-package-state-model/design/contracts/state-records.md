# Contract: State Records

This contract defines the public shape and refusal rules of each record in `state/`. Tests in `test_state_records.py` and `test_state_transitions.py` prove each rule.

## Module Ownership

| Module | Public names | Owned rule |
| --- | --- | --- |
| `state/intake.py` | `REVIEW_LIFETIME`, `SourceConfiguration`, `ReviewState`, `SourceRecord`, `ReviewRecord` | Source validation and review binding |
| `state/proposal.py` | `GatewayTemplate`, `UnsupportedItem`, `ConversionProposal`, `ProposalRecord` | Proposal shape and digests |
| `state/lifecycle/approval.py` | `ApprovalRecord` | Operator, digest, scope, expiry, and one use |
| `state/lifecycle/operation.py` | `OperationPhase`, `OperationRecord` | Operation phase and outcomes |
| `state/lifecycle/backup.py` | `BackupManifest` | Backup completeness and scope |
| `state/lifecycle/transitions.py` | `StateRefused`, `TransitionTable` | Allowed phase changes |
| `state/storage/integrity.py` | `CanonicalDigest`, `RecordSeal` | Digest and seal calculation |
| `state/storage/redaction.py` | `SecretRedaction` | Public view and log redaction |

## Digest Rules

- `CanonicalDigest.of(payload)` encodes the payload with `json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)`.
- It hashes the UTF-8 bytes with SHA-256 and returns lowercase hexadecimal.
- The same encoding must match `ReviewState.digest` for every proposal. A test proves equality.
- `ProposalRecord.scope_digest` hashes `version`, `source_id`, `target_refs`, `contract_versions`, and `proposal_digest`.

## Record Refusals

| Record | Refusal | Error | Message rule |
| --- | --- | --- | --- |
| `SourceRecord` | Byte count is zero or above 16,777,216 | `ValueError` | Names the limit. Shows no source text. |
| `ReviewRecord` | `created_at` or `expires_at` is naive | `StateRefused` | Names the field. |
| `ReviewRecord` | `expires_at` differs from `created_at` plus `REVIEW_LIFETIME` | `StateRefused` | Names the rule. |
| `ApprovalRecord` | `operator_id` is `unverified` or empty | `StateRefused` | Says that no verified operator exists. |
| `ApprovalRecord` | Proposal or scope digest differs | `StateRefused` | Says that the approval does not match. |
| `ApprovalRecord` | `expires_at` is at or before the read time | `StateRefused` | Says that the approval expired. |
| `ApprovalRecord` | State is `consumed` | `StateRefused` | Says that the approval is used. |
| `BackupManifest` | `pagination_complete` is false | `StateRefused` | Says that pagination is incomplete. |
| `BackupManifest` | `object_count` differs from `object_digests` | `StateRefused` | Says that the count differs. |
| `BackupManifest` | A recomputed digest differs | `StateRefused` | Names the object identifier. |
| `BackupManifest` | Organization or family differs | `StateRefused` | Names the expected value. |

## Public View

`SecretRedaction.public_view(record)` returns a copy of the record with these rules applied.

- Keys named `password`, `secret`, `community`, `token`, `key`, `hash`, or `credential` have the value `[redacted]`.
- The key `content` is removed entirely.
- Nested objects follow the same rules.
- The function returns a new object. It never changes the stored record.

## Logging Rules

- A log line names the record kind and the local identifier.
- A log line never names a source text, a secret, or a derived key.
- A refusal logs the exception class name and the rule that failed.

## Compatibility

- `SourceConfiguration.read` keeps its current signature and its current validation.
- `ReviewState.digest`, `publish`, `verify`, and `approve` keep their current behavior.
- The role values `standalone` and `spoke` stay unchanged.
