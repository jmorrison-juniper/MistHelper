# Feature Specification: WLAN fixture host teardown

**Feature Branch**: `fix/4492-wlan-fixture-host-teardown`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4492, "Test failure: WLAN fixture retains a mock resolver host after teardown".

## Clarifications

### Session 2026-11-26

- Q: Which file holds the WLAN fixture? A: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`. The issue path is absent on `main` (R-02). The same blob exists at the CI commit (R-03).
- Q: Does CI on `main` fail? A: No. Run 45774119357 passed the root-units shard on `main` (R-40). The failures occur on the PR branch run 40692675966 (R-41).
- Q: Does production code need a change? A: No. The fixture leaks the resolver host (R-01). Production code reads the host as designed (R-04 to R-07).
- Q: Does a legacy record exist? A: No. No folder under `specs\` starts with `4492-` (R-47). Nothing is reused.
- Q: Which labels change? A: `bug`, `tests`, and `needs-human-review` stay. `in-progress` is added when the implementation claims the issue (D-9).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore the resolver host after each WLAN fixture test (Priority: P1)

A maintainer runs the WLAN RADIUS tests before the initializer and TUI tests. The later tests then read the real MistHelper host.

**Why this priority**: The leak changes results for every later test in the same process. It causes the 21-test failure on the PR branch (R-41).

**Independent Test**: Run the three-node sequence in `design\quickstart.md`, Scenario 2. Expect no failed tests after the fix.

**Acceptance Scenarios**:

1. **Given** the `fake_mh` fixture ends, **When** a later test reads the resolver host, **Then** the host equals the value from before the fixture.
2. **Given** the WLAN module runs first, **When** the two named tests run next, **Then** both tests pass.

### User Story 2 - Keep the root-units shard passing (Priority: P2)

The CI root-units shard runs the unit tests in sorted order. The shard must pass after the fix.

**Why this priority**: A failed shard blocks the pull request. The coverage gate also fails when the shard fails (R-42).

**Independent Test**: Run both pytest-chunks commands in `design\quickstart.md`, Scenario 7. Each summary line reports no failed tests.

**Acceptance Scenarios**:

1. **Given** the fix is applied, **When** the root-units shard runs, **Then** its summary line reports no failed tests.

### User Story 3 - Keep the test-quality gate at zero new findings (Priority: P2)

A maintainer edits the fixture and moves seven baseline line numbers. The gate must still report zero new findings.

**Why this priority**: The gate blocks the pull request. Its baseline keys include line numbers (R-24).

**Independent Test**: Run the test-quality commands in `design\quickstart.md`, Scenario 6. Expect `gate: 0 new findings vs baseline`.

**Acceptance Scenarios**:

1. **Given** the fixture gains four lines, **When** the seven WLAN baseline entries move by four, **Then** the gate reports zero new findings.

### Edge Cases

- The explicit-order sequence runs before the fix. It reports two named failures (R-09, R-11).
- The issue reproduction command names the absent path. It fails before any test runs. Use the main path (D-6).
- Black changes the new `with` block. Re-measure the line delta and update the baseline to the measured delta (U-8).
- A future fixture binds the host without a restore. This change does not guard that case. A follow-up issue owns the guard (D-1).
- The restored value is `None`. This cannot happen in a test session, because `MistHelper.py` binds the host at import (R-12).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `fake_mh` fixture MUST restore the resolver host to its value from before the test.
- **FR-002**: The `fake_mh` fixture MUST keep its existing `sys.modules` patch and restore.
- **FR-003**: The change MUST NOT modify any file under `src\`.
- **FR-004**: The fixture MUST log one `info` line before the bind and one `debug` line after the restore.
- **FR-005**: Each changed line MUST carry an inline comment that gives its cause or purpose.
- **FR-006**: The change MUST shift each WLAN baseline `line_number` by the net line delta. No other baseline key may change.
- **FR-007**: Every verification command MUST use the main path `tests\unit\refactors\test_wlanradius_timer_manager_paths.py`.
- **FR-008**: All 21 named test IDs in `design\research.md` MUST pass after the change.
- **FR-009**: Each applicable local gate MUST pass before the pull request opens. Each skipped gate MUST name its reason.
- **FR-010**: The pull request body MUST contain `Closes #4492`, so the merge closes the issue.
- **FR-011**: The record and the pull request MUST NOT claim a gate result that no run produced.

### Mist Cloud Transport Requirements

Not applicable: the change alters test setup only and calls no Mist REST endpoint.

### Key Entities

- **Resolver host**: The `_root_module` value of `SourceDependencyResolver`. The method `root_module()` returns it.
- **Fake host**: The `MagicMock` that `fake_mh` binds and places in `sys.modules`.
- **Baseline entry**: One object in `.github\test-quality-baseline.json`. Its canonical key includes `line_number`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The three-node sequence reports no failed tests after the fix. Without the restore line, it reports two failed tests.
- **SC-002**: Both pytest-chunks shard commands report no failed tests after the fix.
- **SC-003**: The test-quality gate reports `gate: 0 new findings vs baseline` after the baseline edit.
- **SC-004**: The mutation proof fails the two named tests when the restore line is removed.
- **SC-005**: Ruff and Black pass for the changed file. `symbol-diff` reports no removed module-level name.

## Assumptions

- Local runs use the `.venv` that the repository bootstrap creates (R-39).
- `MistHelper.py` binds the resolver host at import during each test session (R-12).
- Black keeps the new fixture block at the measured line count (U-8).

## Out of Scope

- Any change under `src\`.
- A conftest guard that restores the resolver host for every test. A follow-up issue owns it (D-1).
- Repair of failing tests outside the named regression set (D-7).
- A changelog fragment (D-11).
- Any change to CI workflows, branch protection, or required checks.
