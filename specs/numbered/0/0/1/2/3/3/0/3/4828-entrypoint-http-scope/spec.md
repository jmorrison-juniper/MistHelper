# Feature Specification: Entry-point test quality for HTTP status scope

**Issue**: #4828, "Test quality: MissingFailureModeDetector -- help requires HTTP status cases"
**Repository**: jmorrison-juniper/MistHelper
**Record path**: `specs\numbered\0\0\1\2\3\3\0\3\4828-entrypoint-http-scope`
**Current state**: Partly repaired on `main`. The rest depends on an analyzer fix in `misthelper-devtools`.

## Clarifications

### Session 2026-11-26

- Q: Does the reported gate failure remain on `main`? A: Code reading shows no remaining failure for the help test and the reject-flag test. The gate was not run (Unverified U-01). Evidence: RC-01, RC-05, RC-20.
- Q: Which modules still carry the bootstrap finding? A: Three modules do. They are `test_main_entrypoint.py`, `test_app_context_session_state.py`, and `test_fast_mode_small_seams.py`. Evidence: RC-11, RC-13, RC-14, RC-15, RC-16, RC-17.
- Q: May this repair change the baseline? A: No. Stale entries leave the baseline only after the analyzer pin. See D-4.
- Q: Does this repository own the analyzer fix? A: No. The analyzer belongs to `misthelper-devtools`. See D-2.
- Q: Does the final change close the issue? A: Yes, only after the analyzer pin and the baseline refresh merge. See D-5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Help and reject-flag tests stop before startup (Priority: P1)

A maintainer runs the help tests and the reject-flag tests. Each test proves that the parser exits before startup. The gate reports no HTTP status finding for these two files.

**Status**: Verified present on `main` (RC-01, RC-04, RC-05, RC-07).

**Independent test**: Run the help file and the reject-flag file. Expect 15 passing cases and 3 passing tests.

### User Story 2 - Argument tests use the public entry point (Priority: P1)

A maintainer reads an argument test. The test calls `MainEntrypoint.run`. The test does not build `ApplicationBootstrap` to parse arguments.

**Status**: Partial. One argument test in `test_main_entrypoint.py` builds `ApplicationBootstrap` (RC-12). Task T003 removes it.

**Independent test**: Search `test_main_entrypoint.py` for `ApplicationBootstrap(argv`. Expect no match.

### User Story 3 - Analyzer scopes HTTP risk to the code under test (Priority: P2)

A maintainer runs the test quality gate. The analyzer does not assign HTTP status risk from a logging import in an unrelated method.

**Status**: Absent in this repository. The defect is in `misthelper-devtools` (RC-32 to RC-34). Tasks T004 to T007 depend on the fix.

**Independent test**: The new good fixture in `misthelper-devtools` passes. The full-suite gate reports zero new findings after the pin.

### User Story 4 - Baseline lists only current findings (Priority: P2)

A maintainer reads the baseline. Each entry matches a current analyzer finding.

**Status**: Partial. Two stale entries for the reject-flag test remain (RC-18, RC-19). Task T007 removes them after the pin.

**Independent test**: The baseline diff after T007 shows removed lines only.

### User Story 5 - Logging and web bootstrap tests keep their import (Priority: P3)

A maintainer runs the logging and web bootstrap tests. These tests keep the `ApplicationBootstrap` import, because they exercise real startup behavior.

**Status**: Accepted until User Story 3 lands. The baseline keeps their entries (RC-15, RC-16, RC-17).

**Independent test**: Each module still imports the class, and each module's tests pass.

### Edge Cases

- The duplicate argument case exists in two files. Delete the duplicate only after the surviving case passes (T001, T003).
- The analyzer fix reports a new finding in another file. Stop the baseline refresh and report the new entry (T007).
- A baselined module gains a bootstrap-importing test. The gate reports no new finding, because the baseline key uses line 1 (analysis A-03). Review each test diff in those modules.
- Dependabot pull request 4888 changes `requirements-dev.txt` (RC-49). Rebase after it merges, or agree a handover first (T-PR).
- The pin change makes `uv lock --check` fail. Run `uv lock` again. Do not edit `uv.lock` by hand (T006).
- The fixed analyzer commit adds a runtime dependency. Review the `uv.lock` diff before the commit (T006).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The help tests MUST call `MainEntrypoint.run`. They MUST NOT import `ApplicationBootstrap`.
- **FR-002**: The reject-flag tests MUST call `MainEntrypoint.run` for each unsupported flag.
- **FR-003**: No argument test MUST build `ApplicationBootstrap` to parse arguments.
- **FR-004**: This repair MUST NOT disable a rule, add an HTTP status fixture, or add a baseline entry.
- **FR-005**: The analyzer MUST assign HTTP status risk only from code that a test reaches.
- **FR-006**: `pyproject.toml`, `uv.lock`, and `requirements-dev.txt` MUST name the same misthelper-devtools commit.
- **FR-007**: The baseline MUST drop each stale entry after the pin. It MUST add no entry.
- **FR-008**: The test quality gate MUST report zero new findings on push runs and pull request runs.
- **FR-009**: Issue #4828 MUST stay open until FR-005, FR-006, and FR-007 pass on `main`.

### Key Entities

- **Test module**: A test file with imports and test cases. Natural key: repository path.
- **Baseline entry**: One accepted analyzer finding. Natural key: category, rule ID, file path, line number, and explanation.
- **Analyzer pin**: One misthelper-devtools commit that three files name. Natural key: commit SHA.

The full model is in `design\data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After T007, the full-suite gate prints `gate: 0 new findings vs baseline`.
- **SC-002**: The help file passes 15 cases. The reject-flag file passes 3 tests.
- **SC-003**: After T003, a search of `test_main_entrypoint.py` for `ApplicationBootstrap(argv` finds no match.
- **SC-004**: After T007, the baseline diff adds zero lines.
- **SC-005**: After T006, `uv lock --check` exits with code 0.
- **SC-006**: GitHub closes issue #4828 only when the final pull request merges.

## Out of Scope

- Changes to production code under `src/`.
- Changes to rule settings or exclusions in `.github/test-quality-config.toml`.
- HTTP status fixtures for help tests or argument tests.
- Changes to the `mistapi` pin, which stays at version 0.64.1.
- Changes to menu, product, or container behavior.
- Any analyzer change inside this repository.

## Assumptions

- Commit `2239e7bd` of misthelper-devtools contains the code that RC-32 to RC-36 cite. The installed package matches that commit (RC-50).
- The orchestrator opens the misthelper-devtools issue and merges the analyzer fix.
- The local `.venv` stays in place for the local gates.
- The repository files keep the blob SHAs listed in the remote verification table until T003 starts.
