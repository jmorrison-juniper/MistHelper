# Feature Specification: Lint repair for W0212 and W0201 findings

**Feature Branch**: `chore/4133-lint-w0212-w0201`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4133, "Lint: W0212 protected-access and W0201 attribute-defined-outside-init -- 11 findings in 2 files". The issue names `MistHelper.py` and `tests/unit/test_menu_entry_metadata.py`.

## Clarifications

### Session 2026-11-26

- Q: Which findings remain open on `main`? → A: Two W0212 findings remain. Both sit in `tests/unit/test_menu_entry_metadata.py`, at lines 84 and 93. `MistHelper.py` has no W0212 finding and no W0201 finding. Evidence: research.md rows RC-03 to RC-06.
- Q: Does PR #4607 still own `MistHelper.py`? → A: No. PR #4607 merged on 2026-11-13. The publication hold in the issue comments still applies. See research.md decision D-5.
- Q: Which commit removed the protected accesses from `MistHelper.py`? → A: Commit aa8d12e90 (#4853), dated 2026-11-19. Evidence: research.md row RC-07.
- Q: Does the commit that the issue cites exist? → A: No. GitHub returns HTTP 422 for commit 61505c611. The issue line numbers apply to no commit on GitHub. Evidence: rows RC-09 and RC-10.
- Q: Does the change need a changelog fragment? → A: Yes. Constitution line 409 requires one fragment for each change. See decision D-4.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm zero lint findings in the two files (Priority: P1)

A maintainer runs pylint with the W0212 and W0201 checks on the two named files. The run reports no finding.

**Why this priority**: The issue exists to clear these findings. A clean pylint run proves the result.

**Independent Test**: Run the pylint command in `design/quickstart.md`. The JSON output is an empty list.

**Acceptance Scenarios**:

1. **Given** the change is merged, **When** the maintainer runs the pylint command on both files, **Then** the output is `[]`.
2. **Given** `MistHelper.py` is unchanged, **When** pylint checks it for W0212 and W0201, **Then** pylint reports no finding.

### User Story 2 - Keep the menu refusal tests and their behavior (Priority: P1)

A maintainer runs the menu metadata test module. The two interactive tests still check the refusal text and the empty-input notice. The tests reach that behavior through the public menu dispatch function.

**Why this priority**: The fix must not weaken the tests that guard invalid input and the destructive-selection rules.

**Independent Test**: Run `python -m pytest tests/unit/test_menu_entry_metadata.py`. All 35 collected cases pass.

**Acceptance Scenarios**:

1. **Given** the operator enters an unknown number, **When** direct mode dispatches it, **Then** the process exits with code 1 and prints the refusal text.
2. **Given** an empty selection followed by end of input, **When** the public dispatch runs, **Then** the empty-input notice prints once and no exit occurs.
3. **Given** a test replaces shared values, **When** that test ends, **Then** pytest restores the original values.

### User Story 3 - Pass every applicable repository gate (Priority: P2)

A reviewer sees each applicable local gate pass for the changed files. The test-quality gate reports no new finding.

**Why this priority**: The repository rules require each applicable gate before a commit. A clean pylint run alone does not satisfy those rules.

**Independent Test**: Run the local gates in `design/quickstart.md` and read each result.

**Acceptance Scenarios**:

1. **Given** the changed test file and the changelog fragment, **When** each applicable gate runs, **Then** each gate prints its expected result from the local gates table.
2. **Given** the test-quality gate runs, **When** it finishes, **Then** it prints `gate: 0 new findings vs baseline`.

### Edge Cases

- What happens when `main` changes before the pull request opens? The branch rebases on `origin/main`. The pylint command runs again after the rebase.
- What happens when pylint reports a new finding in `MistHelper.py`? The change stops. A new issue tracks that finding. The change adds no suppression.
- What happens when the public dispatch function changes its fallback path? The invalid-selection test fails. The assertions show the changed outcome.
- What happens when the test runs on a host inside a container? The container check is replaced with a direct-mode answer, so the result does not depend on the host.
- What happens when the test-quality analyzer reports a new finding for the test file? The change stops. The baseline file stays unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST leave zero W0212 findings in `tests/unit/test_menu_entry_metadata.py`.
- **FR-002**: The change MUST leave zero W0212 and zero W0201 findings in `MistHelper.py`. The change MUST NOT edit `MistHelper.py`.
- **FR-003**: The invalid-selection test MUST check exit code 1 and the refusal text through `MistHelper.dispatch_main_mode`.
- **FR-004**: The empty-input test MUST check the notice count and the absence of an exit through `MistHelper.dispatch_main_mode`.
- **FR-005**: The two tests MUST restore every value that they replace, through the pytest monkeypatch fixture.
- **FR-006**: The change MUST NOT add a suppression comment, a baseline entry, or an alias that hides a finding.
- **FR-007**: The two tests MUST run in direct mode by replacing the container check with a false answer.
- **FR-008**: The change MUST add one changelog fragment under `changelog.d/`.
- **FR-009**: The change MUST pass each applicable local gate and the test-quality gate for the changed files.
- **FR-010**: The change MUST keep the 35 collected cases and their test names. The change MUST add no top-level name to the test module.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The pylint command in `design/quickstart.md` prints `[]` for both files.
- **SC-002**: `python -m pytest tests/unit/test_menu_entry_metadata.py` reports 35 passed cases.
- **SC-003**: The test-quality gate prints `gate: 0 new findings vs baseline`.
- **SC-004**: The symbol check reports no module-level name changed for the test file.
- **SC-005**: Each requirement maps to at least one task and one check in `analysis.md`.

## Assumptions

- The pinned pylint 4.1.4 in `pyproject.toml` line 117 applies the same W0201 and W0212 rules as the pylint 4.1.3 run in the issue comments. The installed source confirms the rules. Evidence: rows RC-33 and RC-34.
- The publication hold in the issue comments stays in force until the orchestrator authorizes the pull request.
- No open pull request touches `MistHelper.py` or the test file. The check ran with seven open pull requests in total.
- The analyzer installed in `.venv` matches the pinned analyzer version.

## Out of Scope

- Any edit to `MistHelper.py` or to a `src/` module.
- Moving the three attribute declarations into `__init__` as the issue text describes. Pylint 4.1.4 accepts the current helper design.
- The HTTP finding rule of the test-quality analyzer. Issue #2746 tracks that rule. Issues #2711 and #4702 track other analyzer findings.
- A change to the pylint gate scope. The CI gate checks `src/` only.
- The held analyzer detector and its release. The repository owner owns that work.
