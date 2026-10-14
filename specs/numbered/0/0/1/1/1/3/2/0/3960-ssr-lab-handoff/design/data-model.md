# Evidence Model: SSR lab runbook validation

This document defines a review record, not a database schema or software implementation.

## Lab Observation

| Field | Rule |
| --- | --- |
| Observation ID | One of OBS-01 through OBS-06. Keep the issue order. |
| Release | Record the measured SSR release. Never infer it from the intended target. |
| Port type | Required for interface observations. OBS-04 requires a fiber port. |
| Timestamp | Record UTC in ISO 8601 form. |
| Command or action | Use the matching observation contract. |
| Sanitized output | Preserve exact errors and field names. Remove customer identifiers and secrets. |
| Status | One of `Not run`, `Observed`, `Accepted`, or `Inconclusive`. |
| Cause or limitation | Required for `Not run` or `Inconclusive`. |
| Reviewer | Identify the reviewer when status becomes `Accepted`. |
| Destination | Identify the specific runbook section from the contract. |

No new observation file is created during artifact preparation.
All six observations currently have status `Not run`.
The cause is that the current assignment excludes lab execution and supplies no measured output.

## Lab Experiment Approval

OBS-06 additionally requires an authorized human, a lab-only target reference, approval scope,
an independent console recovery path, and stop conditions.
Its record must include the pre-test state, verified cloud-loss state, portal results, and verified recovery state.
Do not record credentials or raw network addresses in published approval evidence.

## Runbook Correction

Each correction references one accepted observation, its measured release, the prior claim, the revised claim, and the destination.
Contradictory or inconclusive evidence cannot silently become a confirmed runbook statement.
Review the difference and preserve any limitation.

## State Transitions

1. Start at `Not run`.
2. Change to `Observed` only after sanitized measured output exists.
3. Change to `Accepted` only after a reviewer checks the release, output, privacy, and destination.
4. Use `Inconclusive` when the conditions do not prove the claim.
5. Repeat an inconclusive observation only under renewed valid prerequisites.

OBS-06 cannot become `Accepted` without confirmed recovery.
Artifact checks and documentation source reviews cannot advance any observation status.
