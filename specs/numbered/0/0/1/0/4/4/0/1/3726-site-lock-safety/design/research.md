# Research: Site Lock Safety for Uncertain Submissions

**Date**: 2026-11-09
**Feature**: [spec.md](../spec.md)

## Decision: Keep one shared refusal contract

**Decision**: Put the explicit refusal status set and predicate in `src/foundation/support/submission_certainty.py`. Use that predicate from submission classification, lock settlement, retry eligibility through the existing settlement gate, and cancellation reporting.

**Rationale**: The affected behavior currently disagrees across three existing modules. One predicate prevents the cancellation and lock paths from assigning different meanings to the same status evidence. The firmware package already has 12 direct children, so the shared module belongs in the existing foundation support package, which has three direct children.

**Alternatives considered**:

- Keep separate status rules in the three modules. Rejected because one rule can drift and reintroduce the defect.
- Put the rule on `AggregateUpgradeService`. Rejected because that class already has 82 direct members, and the constitution limits each hierarchy level to five children.
- Put the rule in the portal cancellation module. Rejected because the firmware service should not depend on a portal module.

## Decision: Use a narrow client-refusal allowlist

**Decision**: Treat HTTP 400, 401, 403, 404, 405, 409, 410, 413, 415, and 422 as explicit refusal evidence. Treat 408, 429, 499, 5xx, and every unlisted value as uncertain.

**Rationale**: A refused destructive write can release a site only when the response clearly rejects the request. Timeouts, rate limits, server failures, and unlisted statuses do not prove that the cloud created no job. A narrow allowlist fails closed when the response is new or malformed.

**Alternatives considered**:

- Treat every 4xx response as a refusal. Rejected because 408 and 429 can occur after an uncertain request and 499 does not provide a reliable cloud refusal.
- Treat only HTTP 400 as a refusal. Rejected because authorization, missing-resource, conflict, and validation responses are explicit refusal cases in the current bounded design.
- Treat every returned response as final. Rejected because HTTP 200 can contain malformed data or lack an identity needed to reconcile the job.

## Decision: Preserve existing recovery and lease behavior

**Decision**: Keep the current lock lease, operator recovery controls, retry behavior, and post-upgrade watch behavior. Block a retry through the existing settled-operation gate while any child remains uncertain.

**Rationale**: The issue evidence supports correcting the lock-release decision. It does not show that changing lease duration, adding retries, or introducing a new recovery workflow is safe.

**Alternatives considered**:

- Extend or remove the lock lease. Rejected because this changes unrelated timeout and recovery behavior without evidence.
- Retry a request with an unknown outcome. Rejected because a retry can create a duplicate firmware job.
- Add a manual lock-clear workflow. Rejected because existing operator recovery controls already exist.

## Evidence

- The issue's source-export proof showed that HTTP 503 and malformed HTTP 200 replies become `rejected`, while the lock predicate treats every `rejected` child as settled.
- The current cancellation path already requires refusal evidence, but its range includes all 4xx values.
- The current route uses `_operation_is_settled` for both lock release and retry eligibility.
- The issue's prior assessment identified `src/operations/execution/firmware/aggregate_upgrade_service.py`, `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`, and `src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py` as the current source paths.
- The exact open-PR path check found no open pull request that changes these three production files.
- The issue contains no attached artifacts or images.

## Unresolved Questions

None. The explicit allowlist is a conservative implementation assumption. The human reviewer must review the allowlist and lock-retention behavior before merge.
