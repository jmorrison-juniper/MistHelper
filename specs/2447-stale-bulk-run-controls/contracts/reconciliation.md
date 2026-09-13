# Reconciliation Contract: Stale Runs

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Version**: 2

Reconciliation is an explicit read and decision. It sends no new firmware,
stop, or cancel request to the cloud.

## 1. Entry Conditions

The operator must meet all conditions:

1. The actor has a valid signed session.
2. The actor has current write permission.
3. The actor owns the exact current site lock token.
4. The run is stale under the 24-hour policy.
5. The actor types `RECONCILE <run_id>`.
6. The request carries a valid idempotency key.
7. ArangoDB can create the action record.

The action accepts only a pre-cloud state or `stopping`.

Reconciliation creates a `single_reconciliation` action. It does not request
or accept a bulk preview. Its preview fields are null, and its run and site
counts are one.

## 2. Pre-Cloud Reconciliation

The accepted states are:

- `created`
- `pre_capture_running`
- `pre_capture_done`
- `awaiting_confirmation`

Immediately before mutation, the service rechecks permission and the lock
token.

One ArangoDB transaction re-reads the run, changes it to `cancelled`, and
replaces the action placeholder. The service sends no cloud request.

The success reason is `precloud_run_cancelled`.

## 3. Stopping Evidence

The service reads:

1. The stored stop request and time.
2. The stored stop outcome for every target.
3. The stored cloud task identifiers.
4. The current cloud task states.
5. The current firmware write state for every target.
6. Any stored final driver evidence.

The service records the source and observation time for each target.

Each target record follows `TargetEvidence` in
[data-model.md](../data-model.md). The record uses digests for target and task
identifiers. It stores no raw cloud payload, credential, token, actor identity,
or exception text.

The complete evidence value follows `ReconciliationEvidence`. Its serialized
form follows `ReconciliationEvidenceSummary`.

## 4. Meaning of Evidence

| Evidence | Meaning |
| - | - |
| Recorded cancel accepted | The cloud accepted a request. It does not prove the current state. |
| Recorded already writing | A target wrote at that time. It does not prove a later stop. |
| Current task final | The named cloud task does not run. |
| Current task active | Firmware work can continue. |
| Current device writing | The target writes firmware now. |
| Current device not writing | The target is not in a write phase now. |
| Missing target | The evidence is incomplete. |
| Conflicting sources | The evidence is unsafe for a final claim. |

## 5. Decision Table

| Condition | Classification | State change | Reason |
| - | - | - | - |
| Permission is absent. | `refused` | None | `site_write_forbidden` |
| The lock token changed. | `refused` | None | `site_lock_token_changed` |
| The run changed after evidence. | `refused` | None | `run_changed` |
| The run is no longer stale. | `refused` | None | `run_not_stale` |
| The state is not accepted. | `refused` | None | `run_not_reconcilable` |
| Any target writes firmware. | `refused` | None | `firmware_write_active` |
| A cloud task remains active. | `refused` | None | `cloud_task_active` |
| Any target lacks evidence. | `unknown` | None | `cloud_evidence_incomplete` |
| Evidence sources conflict. | `unknown` | None | `cloud_evidence_conflict` |
| A cloud read fails. | `unknown` | None | `cloud_evidence_unavailable` |
| Complete proof shows no write and no live task. | `succeeded` | `stopping` to `stopped` | `stopping_run_reconciled` |
| The transaction fails. | `failed` | None | `run_write_failed` |
| Verification is uncertain. | `unknown` | None | `run_write_unverified` |

## 6. Meaning of `stopped`

The portal uses `stopped` only when complete evidence proves:

1. No selected target writes firmware.
2. No live cloud task remains.
3. The run still matches the evidence read.

The portal does not use `complete`, `failed`, or `cancelled` for a
`stopping` reconciliation.

The success message is:

> The portal confirmed that no selected firmware task remains. Some devices
> can have finished before this check.

The portal does not state that a device stopped unless evidence proves that
specific result.

## 7. Atomic Outcome

The final ArangoDB transaction:

1. Rechecks the run state and version.
2. Changes the run to `stopped`.
3. Stores the safe evidence summary on the outcome.
4. Stores the matching summary digest on the action.
5. Replaces the action placeholder with success.

No partial commit is valid. If ArangoDB is unavailable, the portal returns 503
before it changes the run.

A refusal, failure, or unknown result changes no run. One outcome-only
compare-and-swap write stores that final result. If evidence collection
started, the same write stores the summary and its matching action digest.

A pre-cloud reconciliation stores null in both evidence fields. A refusal
before evidence collection also stores null in both fields.

The repository rejects an unsafe field, a missing required summary, a target
count mismatch, or a digest mismatch.

After the item becomes final, one compare-and-swap write changes the action
from `processing` to `complete`. The response reads the verified stored record.

## 8. Idempotency and Recovery

A same-key replay returns the stored actor-scoped action while its lease is
current. It performs no new cloud read and no new run write.

After lease expiry, one worker takes ownership with compare-and-swap. An old
claimed reconciliation item becomes final `unknown` with reason
`processing_interrupted`.

Recovery does not repeat that reconciliation read or mutation. It finalizes
the action as `complete`.

## 9. Prohibited Behavior

Reconciliation must not:

- Submit firmware.
- Send a new stop or cancel call.
- Change a cloud-active state other than proven `stopping`.
- Use age alone as proof.
- Treat a network fault as proof.
- Treat a partial target list as proof.
- Store success outside the run mutation transaction.
- Use a file, memory, SQLite, or Redis action fallback.
