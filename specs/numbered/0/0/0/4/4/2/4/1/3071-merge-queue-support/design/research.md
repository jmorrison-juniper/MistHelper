# Research: Protected merge queue validation

## Queue events

**Decision**: Add `merge_group` with `types: [checks_requested]` to CI and CodeQL.

**Rationale**: These two workflows supply all 15 required contexts.
Other workflows report no required context and do not need extra runs.

**Alternatives considered**: Disabling strict protection contradicts the selected repair.
Automatic branch updates do not remove the rebase race.

## Concurrency and checkout

**Decision**: Retain reference-based groups. Limit CodeQL cancellation to pull requests.

**Rationale**: Queue references separate candidates. CI already cancels only pull request runs.
Default checkout uses the queue candidate. The test-quality checkout falls back to `github.sha`.

**Alternatives considered**: A second SHA-based grouping mechanism adds no necessary isolation.

## Shared workflows

**Decision**: Retain the pinned shared workflows without edits.

**Rationale**: CodeQL checks out the caller commit and preserves the Python analysis category.
Issue synchronization explicitly excludes events that are neither pull requests nor main runs.
No queue event can create or close an issue through that path.

**Alternatives considered**: Changing shared workflow pins expands the repair without a compatibility need.

## Ownership and acceptance

**Decision**: Use only the released `ci.yml` trigger section.

**Rationale**: PR #4208 holds its browser evidence section.
Preserve the merged #4306 coverage historical-fetch step.

**Decision**: Document the rollout in `documentation/quality-gates.md`.

**Rationale**: The user approved this location and the historical instruction-path exception.
The preparation pull request must not close the operational issue.
