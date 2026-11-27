# Feature Specification: Top-Five Complexity Target Map

**Feature Branch**: `fix/4837-check-top5-stale-target`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4837, "Bug: stale function target in check_top5_complexity.py". The top-five check utility stops with a missing-target error.

## Clarifications

### Session 2026-11-26

- Q: Should the utility search every source file for each target name? A: No. Each target maps to one file. A search reads more files and can match a duplicate name.
- Q: Should the target names change to qualified names, such as `PacketCaptureManager._execute_site_capture_loop`? A: No. The bare names appear in tests and in the spec-195 record. Only the file mapping changes.
- Q: Should a CI job run the utility? A: No. The utility runs by hand. A new job spends runner minutes and can fail on debt that exists before this change.
- Q: Should the utility move into a class in this change? A: No. This change edits the target map only. The debt goes to a follow-up issue.
- Q: What result must the utility print after the fix? A: PASS is expected, because the CI radon job passed on main. The actual result is recorded in task T004.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the top-five check to a result (Priority: P1)

A maintainer runs the top-five check from the repository root. The check prints the five target results and a PASS or FAIL line. It does not stop with a missing-target error.

**Why this priority**: The defect stops the only work that the utility performs.

**Independent Test**: Run `.venv\Scripts\python.exe scripts\check_top5_complexity.py` from the repository root. Expect five result lines and one PASS or FAIL line.

**Acceptance Scenarios**:

1. **Given** the current source layout, **When** the maintainer runs the utility, **Then** the utility prints five result lines in target order.
2. **Given** every target has CC 10 or below, **When** the utility ends, **Then** it prints PASS and exits with code 0.
3. **Given** one target has CC above 10, **When** the utility ends, **Then** it prints FAIL and exits with code 1.

---

### User Story 2 - Catch a moved target in the test suite (Priority: P2)

A maintainer moves a target to another file. The guard test fails and names the target and the expected file.

**Why this priority**: The defect reached main because no test checked the file of each target.

**Independent Test**: Run `.venv\Scripts\python.exe -m pytest tests\integration\test_top5_compatibility_paths.py -q`. Expect all five tests in the module to pass.

**Acceptance Scenarios**:

1. **Given** a target absent from its mapped file, **When** the guard test runs, **Then** it fails and names the target and the file.

---

### User Story 3 - Leave the other gates unchanged (Priority: P3)

A reviewer reads the change. The change touches no workflow file, no radon pin, and no runtime module.

**Why this priority**: A small change keeps review fast and limits risk to gates that already pass.

**Independent Test**: Read the changed file list in plan.md. Expect four paths. None lies under `.github\workflows\`, and none is `MistHelper.py`.

**Acceptance Scenarios**:

1. **Given** the completed change, **When** the reviewer reads the changed file list, **Then** the list holds only the four paths of the file change map.

---

### Edge Cases

- What happens when the utility runs from another folder? It raises `FileNotFoundError: Missing path`, as before. The first missing file stops the run.
- What happens when a target moves to another file? The guard test fails. Without that test, the utility raises a missing-target error.
- What happens when radon stalls? The 300-second bound raises a named `RuntimeError`, as before.
- What happens when a target exceeds CC 10? The utility prints FAIL and exits with code 1.
- What happens on Windows path separators? The map keys come from `pathlib.Path`. Radon and the lookup use the same separator.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The utility MUST map each target to the source file that defines it on main.
- **FR-002**: The utility MUST complete with a PASS or FAIL result when each target exists in its mapped file.
- **FR-003**: The utility MUST exit with code 0 for PASS and with code 1 for FAIL.
- **FR-004**: The guard test MUST fail and name the target and the file when a target is absent from its mapped file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The utility run from the repository root prints five result lines and no missing-target error. Task T004 measures this.
- **SC-002**: The guard test fails on the current target map and passes after the map change. Tasks T002 and T003 record both outputs.
- **SC-003**: All five tests in `tests/integration/test_top5_compatibility_paths.py` pass. Two tests exist already, and three tests are new.
- **SC-004**: `symbol-diff` reports no module-level name changed for `scripts/check_top5_complexity.py`.

Explained: The criteria name a command because the utility is a command-line tool.

## Assumptions

- The five targets stay in the files that remote checks R04 to R13 name.
- The radon version is 6.0.1 locally and in CI.
- A developer runs the utility from the repository root.
- The feature calls no Mist API, so no Mist contract applies.
- The change adds no dependency.

## Out of Scope (Non-Goals)

- Converting the utility into a class. This debt goes to a follow-up issue.
- Reducing the complexity of `main()`. This debt goes to a follow-up issue.
- Adding a CI job, a documentation page, or a `RADON_PATHS` entry for the utility.
- Changing the CC limit, the radon timeout, or the target names.
- Changing the spec-196 complexity parser test.
- Adding action logging to the utility.
