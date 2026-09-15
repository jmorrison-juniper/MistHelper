# Feature Specification: Pytest Coverage Gate Headroom

**Feature Branch**: `chore/2650-coverage-gate`

**Created**: 2026-09-15

**Status**: Ready to implement

**Input**: GitHub issue #2650 reports that the `pytest (coverage gate)` job runs near its 15 minute limit and cancels.

## Background

The root coverage gate runs the root pytest suite in one job. Recent successful runs took 7.9 to 11.9 minutes. The job limit is 15 minutes.

Pull request #2636 showed the failure mode. One run cancelled at the job limit, and a second run of the same commit passed. That means normal runner speed can decide the result.

The local Windows worktree collected 16,554 tests for the CI-equivalent root suite. A plain `python -m pytest --durations=40 -q` collected 16,796 tests because it also included E2E tests. That run reached only 4 percent after about 25 minutes on Windows, so it was not a useful measure for the Linux coverage job.

## User Scenarios and Testing

### User Story 1 - Keep the coverage gate inside its limit (Priority: P1)

A pull request author needs the root coverage gate to finish without a job timeout during normal runner variation.

**Why this priority**: This is the issue defect. A cancelled required check blocks review without naming a failing test.

**Independent Test**: Read `.github/workflows/ci.yml` and verify that the root coverage suite runs in parallel shards.

**Acceptance Scenarios**:

1. **Given** the quality gate workflow, **When** a pull request starts CI, **Then** root pytest tests run in at least four coverage shards.
2. **Given** all shards pass, **When** the final coverage job runs, **Then** it combines all coverage data and applies `COVERAGE_THRESHOLD` once.
3. **Given** one shard fails, cancels, or skips, **When** the final coverage job runs, **Then** it fails before it reports a partial coverage result.

### User Story 2 - Preserve the required check contract (Priority: P1)

A maintainer needs branch protection to see the same required check name after the split.

**Why this priority**: A renamed required check can block every pull request.

**Independent Test**: Read the workflow and verify that the final job is still named `pytest (coverage gate)`.

**Acceptance Scenarios**:

1. **Given** branch protection expects `pytest (coverage gate)`, **When** the workflow runs, **Then** the final job reports that exact name.
2. **Given** extra shard jobs exist, **When** the workflow runs, **Then** they do not replace the required final check.

### User Story 3 - Keep future edits from undoing the split (Priority: P2)

A maintainer needs a local contract test that fails if a future edit restores the serial coverage suite.

**Why this priority**: The failure is easy to reintroduce during workflow cleanup.

**Independent Test**: Run the contract test that parses `.github/workflows/ci.yml`.

**Acceptance Scenarios**:

1. **Given** the workflow file changes, **When** the contract test runs, **Then** it verifies the shard matrix, artifact upload, final check name, and coverage combine command.

### Edge Cases

- If a shard uploads no `.coverage` file, the artifact upload step fails.
- If a shard fails, the final job fails before coverage reads partial data.
- If the artifact action hides dotfiles, the contract test fails because `include-hidden-files` must remain true.
- If a future edit changes the required check name, the contract test fails.

## Requirements

### Functional Requirements

- **FR-001**: The root pytest coverage suite MUST run in parallel shards.
- **FR-002**: The final coverage job MUST combine the shard coverage data before it applies the threshold.
- **FR-003**: The final coverage job MUST keep the name `pytest (coverage gate)`.
- **FR-004**: The workflow MUST keep the existing `COVERAGE_THRESHOLD` value and variable.
- **FR-005**: The workflow MUST fail if any shard fails, cancels, or skips.
- **FR-006**: A contract test MUST assert the workflow settings changed for issue #2650.
- **FR-007**: The workflow MUST NOT use `paths-ignore` on a required check.

### Key Entities

- **Coverage shard**: One matrix job that runs a test path group and writes one `.coverage.<shard>` file.
- **Final coverage gate**: The required job that downloads shard artifacts, combines coverage, and enforces the threshold.
- **Contract test**: A pytest test that reads the workflow file and asserts the coverage gate contract.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Recent pre-change CI evidence records coverage job durations between 7.9 and 11.9 minutes.
- **SC-002**: The workflow uses at least four coverage shards.
- **SC-003**: The final coverage job keeps the 80 percent default threshold through `COVERAGE_THRESHOLD`.
- **SC-004**: The contract test passes locally.
- **SC-005**: The pull request check list shows the final `pytest (coverage gate)` check passing.

## Assumptions

- The root coverage denominator remains `SRC_PATH`.
- The repository wants parallel shards before a timeout increase.
- The branch table does not allow a `ci/` branch. This work uses `chore/2650-coverage-gate`.
- The plain Windows full-suite timing is not comparable to the Linux coverage job because it includes E2E tests and runs much slower.
