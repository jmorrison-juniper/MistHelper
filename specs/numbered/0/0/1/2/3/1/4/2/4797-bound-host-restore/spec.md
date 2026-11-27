# Feature Specification: Bound host restore for the WLAN RADIUS fixture

**Feature Branch**: `fix/4797-bound-host-restore`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Test failure: resolver host persists after WLAN RADIUS fixture" (GitHub issue #4797)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the admission test independent of earlier modules (Priority: P1)

A maintainer runs the WLAN RADIUS fixture module before the WAN admission test. The admission test reads its patched organization context and passes.

**Why this priority**: A leaked fake host fails an unrelated admission test. The failure hides the true state of the suite.

**Independent Test**: Run the reproduction pair on the candidate commit and on the PR head. The candidate fails, and the PR head passes.

**Acceptance Scenarios**:

1. **Given** the candidate commit, **When** the reproduction pair runs, **Then** the admission test fails with the site organization error.
2. **Given** the PR head, **When** the reproduction pair runs, **Then** both test targets pass.

---

### User Story 2 - Keep later tests on the real bound host (Priority: P1)

A maintainer runs shard 1 after the fix merges. Each fixture restores the bound host before the next test starts.

**Why this priority**: Later tests read the shared resolver. A fake host left bound changes their results.

**Independent Test**: Run shard 1 on the PR head. The summary reports zero failed tests.

**Acceptance Scenarios**:

1. **Given** the PR head, **When** shard 1 runs, **Then** the summary reports zero failed tests.
2. **Given** the follow-up branch, **When** the restore tests run, **Then** every case passes with the restore in place.

---

### User Story 3 - Detect a future leak in the restore tests (Priority: P2)

A maintainer removes the restore from the fake_mh fixture in a later edit. The restore tests report an error.

**Why this priority**: A leak passes every test that runs alone. Only an ordered run exposes it.

**Independent Test**: Remove the restore in a scratch worktree. The restore tests report an error at teardown.

**Acceptance Scenarios**:

1. **Given** a fake_mh fixture without the restore, **When** the restore tests run, **Then** the teardown check reports an error for each case.
2. **Given** a fake_mh fixture with the restore, **When** the restore tests run, **Then** each case passes.

---

### Edge Cases

- What happens when no bound host exists before the test? The fixture restores None. The restore tests cover this case.
- What happens when the test body binds another host? The fixture restores the previous host captured at setup, not the inner host.
- What happens when a test runs alone? A leak cannot reach a later test. Only an ordered run exposes the defect.
- What happens when PR #4208 changes the fixture path before it merges? The reproduction node IDs change. The verification repeats with the new IDs.
- What happens when MistHelper.py stops during its import? No real host exists, so the restore returns None. Research item U-4 records this condition.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fake_mh fixture MUST restore the previous bound host at teardown.
- **FR-002**: The change MUST NOT alter production code, including the shared resolver and the request admission module.
- **FR-003**: The reproduction pair MUST fail on the candidate commit with the site organization error.
- **FR-004**: The reproduction pair MUST pass on the PR head.
- **FR-005**: Shard 1 MUST report zero failed tests on the PR head.
- **FR-006**: Shard 2 MUST report zero failed tests on the follow-up branch, including the process folder guard.
- **FR-007**: The restore tests MUST fail when the fixture does not restore the previous bound host.
- **FR-008**: Each changed Python file MUST pass the Lint and Format gates.
- **FR-009**: The test quality ratchet MUST report zero new findings for the changed test file.

### Key Entities

- **Shared resolver**: The instance `SourceDependencyResolver`. Source packages read their dependencies through this instance.
- **Bound host**: The value that the shared resolver stores in its `_root_module` attribute. It can be None, the real MistHelper module, or a fake host.
- **Fake host**: A MagicMock that the fake_mh fixture binds for one test.
- **Previous host**: The bound host that exists before a fixture binds its fake host.
- **PR head**: Commit 843be63bc837513b4442dae69da9f0db922e0ed1 on pull request #4208.
- **Candidate commit**: Commit 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473. The issue names it as the reconstruction candidate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The reproduction pair reports one failed test on the candidate commit and zero failed tests on the PR head.
- **SC-002**: Shard 1 reports zero failed tests on the PR head. The passed and skipped counts appear in the evidence.
- **SC-003**: The restore tests pass with the restore in place. Without the restore, they report an error.
- **SC-004**: All 15 required checks on PR #4208 report SUCCESS for the PR head.
- **SC-005**: Before the follow-up merges, main holds fixture blob 75b4bdc1abe393be8eadf50b0cbe299f23cfa458.

## Assumptions

- The reporter failure matches the candidate commit. Candidate lines 195, 212, and 230 match the issue traceback.
- The repository virtual environment uses Python 3.15.2 and pytest 9.2.0.
- Shard 1 takes about 1179 seconds on the measured host.
- No other open pull request changes the fixture file before the follow-up starts.

## Clarifications

### Session 2026-11-26

- Q: Should the fix change production code? A: No. The issue body says to restore the fixture-owned host rather than change production admission.
- Q: Which test paths apply? A: The candidate and PR head use `tests/unit/wan_performance/`. Main uses `tests/unit/wan_dashboard/wan_performance/collection/`. Pre-merge checks use PR head paths. Post-merge checks use main paths.
- Q: Is the fix on main? A: No. Commit 1f4843c on PR #4208 contains the fix. Main still holds the defect.
- Q: Does shared resolver mean the DNS resolver? A: No. The shared resolver is SourceDependencyResolver. `host_resolver.py` performs DNS lookups and is out of scope.

## Out of Scope

- Production admission changes. The issue excludes them.
- A suite-wide autouse fixture that restores the bound host after every test.
- Issue #4798, a test that has no assertion.
- Moving tests from `tests/unit/wan_dashboard/` to `tests/unit/wan_performance/`. PR #4208 owns that move.
- Editing the issue body or the PR #4208 body. The owner or the orchestrator makes those edits.
- Any Mist Cloud request. The change adds none.
- Warning: a push to the PR #4208 branch changes work that another owner controls.
