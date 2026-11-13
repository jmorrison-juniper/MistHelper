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

**Decision**: Treat HTTP 400, 401, 403, and 404 as refusal candidates because the local OpenAPI lists them for the upgrade endpoints. Treat HTTP 429 and every undocumented status as uncertain.

**Rationale**: The OpenAPI lists HTTP 400, 401, 403, 404, and 429 for the upgrade endpoints. It does not list the other statuses in the earlier candidate allowlist. A refusal candidate still cannot prove that no job exists when the response retains a job identity or an accepted target.

**Alternatives considered**:

- Treat every 4xx response as a refusal. Rejected because 408 and 429 can occur after an uncertain request and 499 does not provide a reliable cloud refusal.
- Treat the earlier candidate list as proven refusal evidence. Rejected because the local OpenAPI does not list 405, 409, 410, 413, 415, or 422.
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
- The previous candidate allowed undocumented 4xx statuses to prove refusal, and it did not check for a retained job identity or accepted target.
- The current route uses `_operation_is_settled` for both lock release and retry eligibility.
- The previous summary path counted every `rejected` child as fully failed, even when stored evidence conflicted.
- Organization upgrade response data can retain an `id` or accepted target list even when the response status is a refusal candidate. Device submissions can retain both accepted targets and an upgrade identity.
- The issue's prior assessment identified `src/operations/execution/firmware/aggregate_upgrade_service.py`, `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`, and `src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py` as the current source paths.
- The exact open-PR path check found no open pull request that changes these three production files.
- The issue contains no attached artifacts or images.

## Unresolved Questions

None. The documented refusal candidates and the conflict rule are now explicit. The human reviewer must review the lock-retention behavior before merge.
