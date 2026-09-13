# Data Model: Stale and Bulk Run Controls

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Date**: 2026-09-11

This document defines the view records, preview records, action records, and
transaction rules.

## 1. StaleAssessment

**Owner**: `RunStalePolicy`

| Field | Type | Rule |
| - | - | - |
| `updated_at` | `str` | Normalized UTC time, or empty when invalid. |
| `age_seconds` | `int \| None` | Whole seconds from update to server clock. |
| `age_text` | `str` | Short age text, or `unknown`. |
| `is_stale` | `bool` | True only for a nonfinal run at 24 hours. |
| `reason` | `str` | Stable age reason. |

The canonical final set is `complete`, `failed`, `stopped`, and `cancelled`.

## 2. RunSelection

**Owner**: One browser tab.

| Field | Type | Rule |
| - | - | - |
| `organization_id` | `str` | Current organization scope. |
| `history_scope` | `str` | Current server-defined history filter. |
| `run_ids` | `list[str]` | Ordered browser candidates. |
| `saved_at` | `str` | Display and cleanup time only. |

The browser stores this record in `sessionStorage`. The record is not an
authority for visibility, counts, eligibility, or action scope.

## 3. DurableActorScope

**Owner**: The existing identity service.

| Field | Type | Rule |
| - | - | - |
| `identity_kind` | `str` | Existing identity kind. |
| `normalized_actor` | `str` | Existing normalized actor identity. |
| `actor_scope` | `str` | Stable digest of kind and normalized identity. |

The service does not use `browser_id`, the signed session key, or a tab value.
The raw normalized identity never appears in a response, URL, or log.

The result endpoint queries by `actor_scope` and `action_id`. It returns 404
when either value does not match.

## 4. BulkActionPreview

**Purpose**: Replace hidden browser state with an authoritative server view.

| Field | Type | Rule |
| - | - | - |
| `preview_id` | `str` | Random identifier for audit correlation. |
| `actor_scope` | `str` | Owner of this preview. |
| `organization_id` | `str` | Current organization. |
| `history_scope` | `str` | Current history filter. |
| `action` | `str` | `cancel` or `retry`. |
| `run_ids` | `list[str]` | Ordered visible and distinct identifiers. |
| `run_count` | `int` | Exact retained count. |
| `site_counts` | `dict[str, int]` | Exact retained count for each site. |
| `selection_digest` | `str` | Digest of action, scope, and ordered IDs. |
| `expires_at` | `str` | Short server expiry. |
| `preview_token` | `str` | Signed token for the action request. |

The preview rejects duplicate identifiers. It removes identifiers outside the
current visible result scope. The browser replaces its selection with the
returned ordered list before it shows phrase input.

## 5. UpgradeRunAction

**Collection**: `upgrade_run_actions`

**Authority**: ArangoDB only.

**Composite domain key**:

```text
(actor_scope, idempotency_key_digest)
```

The Arango `_key` is a stable digest of the composite domain key. The primary
key strategy entry names both domain fields.

```python
"upgradeRunActions": {
    "type": "composite_pk",
    "primary_key": ["actor_scope", "idempotency_key_digest"],
    "indexes": ["action_id", "actor_scope", "created_at"],
    "unique_constraints": ["action_id"],
    "description": "Durable actor-scoped upgrade portal action outcomes",
}
```

| Field | Type | Rule |
| - | - | - |
| `_key` | `str` | Digest of the composite domain key. |
| `action_id` | `str` | Public opaque identifier. |
| `schema_version` | `int` | Starts at 1. |
| `actor_scope` | `str` | Durable actor owner. |
| `idempotency_key_digest` | `str` | Digest of the raw request key. |
| `request_digest` | `str` | Digest of the source-specific request fields. |
| `source_kind` | `str` | `bulk_preview` or `single_reconciliation`. |
| `preview_id` | `str \| None` | Required for a bulk action and null for reconciliation. |
| `preview_digest` | `str \| None` | Required for a bulk action and null for reconciliation. |
| `organization_id` | `str` | Current organization for both source kinds. |
| `history_scope` | `str \| None` | Required for a bulk action and null for reconciliation. |
| `confirmation_digest` | `str` | Digest of the exact typed confirmation. |
| `action` | `str` | `cancel`, `retry`, or `reconcile`. |
| `status` | `str` | `processing` or `complete`. |
| `run_count` | `int` | One through 50. |
| `site_count` | `int` | Preview count, or one for reconciliation. |
| `items` | `list[RunActionOutcome]` | One ordered item for every request ID. |
| `site_blocks` | `dict[str, str]` | Durable reason that stops later site writes. |
| `created_at` | `str` | UTC creation time. |
| `processing_expires_at` | `str` | UTC end of the active processing lease. |
| `processing_owner` | `str` | Opaque worker lease owner. |
| `completed_at` | `str \| None` | UTC completion time. |
| `evidence_summary_digest` | `str \| None` | Digest of the stored reconciliation summary. |

**Indexes**:

1. A unique composite index covers `actor_scope` and
   `idempotency_key_digest`.
2. A unique index covers `action_id`.
3. An index covers `actor_scope` and `created_at`.

The implementation adds the strategy to
`src/refactors/endpoint_primary_key_strategies.py` before collection code.
The action repository uses the key definition directly.

It does not call `DatabaseRouter.write`. That path would fan out a composite
record and could report a fallback result outside the run transaction.

### Source-Specific Rules

For `bulk_preview`, `preview_id`, `preview_digest`, and `history_scope` are
required. The preview supplies the ordered run list and counts.

For `single_reconciliation`, those three fields are null. The request stores
one run identifier, one site, one confirmation digest, `run_count: 1`, and
`site_count: 1`.

Reconciliation does not create or consume a bulk preview.

`evidence_summary_digest` is null for a bulk action. It is also null for a
reconciliation placeholder and for a pre-cloud reconciliation.

For a final `stopping` reconciliation item, the field is required. It equals
`decision_basis_digest` in the canonical `evidence_summary` value on that
item.

## 6. RunActionOutcome

| Field | Type | Rule |
| - | - | - |
| `source_run_id` | `str` | One requested run. |
| `site_id` | `str` | Known site, or empty before processing. |
| `action` | `str` | Parent action. |
| `processing_state` | `str` | `pending`, `claimed`, or `final`. |
| `claim_owner` | `str \| None` | Worker that claimed the item. |
| `claim_expires_at` | `str \| None` | End of the item claim lease. |
| `classification` | `str` | `succeeded`, `refused`, `failed`, or `unknown`. |
| `reason` | `str` | Stable reason. |
| `message` | `str` | Safe operator text. |
| `result_run_id` | `str` | Changed or created run, or empty. |
| `prior_state` | `str` | State at the final eligibility read. |
| `final_state` | `str` | Verified final state, or empty. |
| `checked_at` | `str` | Final check time, or empty. |
| `completed_at` | `str` | Outcome time, or empty. |
| `evidence_summary` | `ReconciliationEvidenceSummary \| None` | Safe stored reconciliation proof. |

The action record starts with one placeholder for each requested run. Each
placeholder has `processing_state: pending`, `classification: unknown`, and
`reason: not_processed`.

One compare-and-swap write changes a pending item to claimed before work. A
final write changes only that item to final. The list order never changes.

A refusal, failure, or unknown result that changes no run uses an outcome-only
compare-and-swap write. It does not require a run mutation.

`evidence_summary` is null for cancel and retry items. It is null for a
pre-cloud reconciliation and for a refusal that occurs before evidence
collection.

The field is required for every final `stopping` reconciliation item after
evidence collection starts. This rule includes succeeded, refused, failed, and
unknown outcomes.

## 7. Atomic Write Units

### Cancel

One ArangoDB transaction:

1. Reads the current run and checks the expected version.
2. Changes the pre-cloud run to `cancelled`.
3. Replaces the action item placeholder with the verified success.

If the transaction fails, neither the mutation nor the outcome commits.

### Retry

One ArangoDB transaction:

1. Reads the source and all nonfinal runs for the site.
2. Refuses when a nonfinal run exists.
3. Inserts one new `created` run.
4. Replaces the source item placeholder with the verified success.

### Reconciliation

One ArangoDB transaction:

1. Rechecks the run state and version from the evidence read.
2. Changes pre-cloud to `cancelled`, or proven `stopping` to `stopped`.
3. Stores the evidence summary on the outcome.
4. Stores the matching evidence summary digest on the action.
5. Replaces the action item placeholder.

Permission and lock checks occur immediately before each transaction. A guard
failure stops later writes for that site.

### Outcome-Only Write

One compare-and-swap write:

1. Verifies that the item is claimed by the current worker.
2. Stores the final `refused`, `failed`, or `unknown` outcome.
3. Changes `processing_state` to `final`.
4. Changes no run record.

### Action Finalization

After every item is final, one compare-and-swap write changes the action from
`processing` to `complete` and stores `completed_at`.

The response reads the stored complete record. The portal reports no success
before this verification.

## 8. Replay and Recovery

A same-key same-request replay returns the current durable action record. It
does not process an item again.

If the processing lease is current, replay returns `processing`.

If the lease expired, one worker takes ownership with compare-and-swap. The
worker changes each old claimed item to a final `unknown` outcome with reason
`processing_interrupted`.

The worker resumes only pending items. It never repeats a claimed or final
item. A stored site block prevents later writes for that site after recovery.

Recovery finalizes every item and then changes the action to `complete`. This
rule prevents an unknown mutation from receiving a second write.

## 9. RetryCopyPolicy

The top-level option allowlist is exact:

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

The nested allowlists use only fields that
`src/upgrade_portal/upgrade/options.py::build_options` accepts.

| Group | Allowed fields |
| - | - |
| `canary` | `canary_phases`, `max_failures`, `max_failure_percentage` |
| `rrm` | `rrm_first_batch_percentage`, `rrm_max_batch_percentage`, `rrm_mesh_upgrade`, `rrm_node_order`, `rrm_slow_ramp` |
| `peer_to_peer` | `enable_p2p`, `p2p_cluster_size`, `p2p_parallelism` |
| `ssr` | `channel` |
| `schedule` | `start_time_after`, `reboot_at_after` |

The policy refuses an unknown top-level or nested field. It rebuilds absolute
times from valid durations. It then calls the existing options validator.

A retry source needs a valid `updated_at`. The policy refuses a missing,
invalid, or future source time with `retry_source_time_unknown`.

## 10. Reconciliation Evidence

### TargetEvidence

`TargetEvidence` is an immutable value for one run target.

| Field | Type | Required and null rule |
| - | - | - |
| `target_digest` | `str` | Required. It is an HMAC-SHA-256 digest of the normalized target identifier. |
| `stored_stop_result` | `str` | Required. Use `cancel_accepted`, `already_writing`, `not_requested`, or `unknown`. |
| `task_digest` | `str \| None` | Required HMAC-SHA-256 digest when a stored task identifier exists. Otherwise, use null. |
| `task_state` | `str` | Required. Use `active`, `final`, `absent`, `unknown`, or `unavailable`. |
| `write_state` | `str` | Required. Use `writing`, `not_writing`, `unknown`, or `unavailable`. |
| `driver_state` | `str \| None` | Use `stopped`, `completed`, `failed`, or `cancelled` for stored final evidence. Otherwise, use null. |
| `sources` | `list[str]` | Required nonempty ordered list from `stored`, `cloud_task`, `device`, and `driver`. |
| `observed_at` | `str \| None` | Required UTC time for a current read. Use null only when no current read completed. |
| `is_complete` | `bool` | Required. True only when the target has enough current proof. |
| `has_conflict` | `bool` | Required. True when two sources disagree. |
| `conflict_reason` | `str \| None` | Use `task_state_conflict`, `write_state_conflict`, `driver_state_conflict`, or `target_missing` when a conflict exists. Otherwise, use null. |

The record stores no raw target identifier, cloud task identifier, cloud
payload, credential, token, actor identity, or exception text.

### ReconciliationEvidence

`ReconciliationEvidence` is the complete immutable decision input for one
stale `stopping` run.

| Field | Type | Required and null rule |
| - | - | - |
| `schema_version` | `int` | Required. The first version is 1. |
| `run_id` | `str` | Required source run identifier. |
| `run_revision` | `str` | Required ArangoDB revision from the evidence read. |
| `collected_at` | `str` | Required UTC collection time. |
| `targets` | `list[TargetEvidence]` | Required. It has one item for every run target. |
| `target_count` | `int` | Required. It equals the number of run targets. |
| `complete_target_count` | `int` | Required. It equals the number of complete target items. |
| `active_write_count` | `int` | Required. It counts target items with `writing`. |
| `active_task_count` | `int` | Required. It counts distinct active task digests. |
| `unknown_target_count` | `int` | Required. It counts incomplete target items without a conflict. |
| `has_conflict` | `bool` | Required. True when any target or task source conflicts. |
| `is_complete` | `bool` | Required. True only when all targets and tasks have current proof. |
| `decision_basis_digest` | `str` | Required SHA-256 digest of all other canonical evidence fields. |

`targets` can be empty only when the run record has no targets. That condition
produces `is_complete: false` and an unknown outcome.

### ReconciliationEvidenceSummary

`ReconciliationEvidenceSummary` is the canonical JSON serialization of
`ReconciliationEvidence`. It uses the same fields. It contains only JSON
strings, integers, booleans, null values, and target lists.

The serializer sorts each `sources` list and each target by `target_digest`.
It uses UTF-8, sorted object keys, and no insignificant whitespace.

It calculates `decision_basis_digest` from the canonical object without that
field. It then adds the digest to the serialized summary.

The action stores the summary digest. The final outcome stores the serialized
summary. The API can return this summary because every field is safe.

### Storage Transactions

For a successful `stopping` reconciliation, one ArangoDB transaction:

1. Rechecks `run_revision`.
2. Changes the run to `stopped`.
3. Stores `evidence_summary` on the final outcome.
4. Stores `evidence_summary_digest` on the action.
5. Finalizes the claimed item.

For a refused, failed, or unknown result after evidence collection, one
outcome-only compare-and-swap write stores both evidence fields and finalizes
the item. It changes no run.

The repository must reject a missing summary, a digest mismatch, an unsafe
field, or a summary with a target count mismatch. It must not report success
when either evidence field fails to persist.

`ReconciliationDecision.next_state` can be:

- `cancelled` for a stale pre-cloud run.
- `stopped` for a stale `stopping` run with complete proof.
- Empty for every other result.

The decision never changes `stopping` to `complete`, `failed`, or `cancelled`.

## 11. Storage Policy

The action journal is portal-internal transactional state. It is not an API
data export.

The current CSV, SQLite, Redis, and memory paths cannot join one transaction
with the authoritative `upgrade_runs` record. A fallback would permit a run
mutation without its idempotency outcome, or the reverse.

The portal therefore refuses the action when ArangoDB is unavailable. It does
not report a fallback success.

This design follows the multi-backend rule for exported API data. It follows
the safety rule for transactional portal state and avoids split-brain writes.

Before schema work or deployment, the operator creates an ArangoDB backup and
verifies that the backup contains the run and action collections.

The recovery drill restores the backup to an isolated target. It verifies
collection counts, key indexes, actor indexes, and sample linked records.

The first release retains an action record for the lifetime of its referenced
run records. It installs no automatic action cleanup.

## 12. Test Records

Each E2E server owns runs, captures, actions, locks, authorization, cloud
evidence, and audit rows in memory.

Each record carries one `test_run_id`. A store rejects a record from another
test run. No test record uses the production file fallback.
