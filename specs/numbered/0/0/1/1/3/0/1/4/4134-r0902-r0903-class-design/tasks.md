# Tasks: R0902 and R0903 class design

**Input**: `specs\numbered\0\0\1\1\3\0\1\4\4134-r0902-r0903-class-design\plan.md` and `spec.md`.

**Test IDs**: TS-01 to TS-18 are the tests of this record. Each task names the test IDs that it covers.

**Verification rule**: Each implementation task names one command from the Local gates table. The final tasks verify with GitHub checks and the scope check, because no local gate covers pull request creation and merge.

**Status values**: open, verified-present, partial, or absent. Every task starts as open.

## Format

- **[P]** marks a task that edits a different file from the other [P] tasks of its phase.
- Requirement IDs follow the task title.

## Phase 1: Tests First and Implementation by Module

### T001 [P] Write the settings tests for `missing_names` (FR-006, FR-003)

- **Files**: `tests/unit/juniper_rma/api/test_settings.py`
- **Acceptance**: TS-01 to TS-03 exist. TS-01 checks that all names give an empty list. TS-02 checks that a missing contact name is returned. TS-03 checks that the contact name is omitted when the contact is not required. All three fail before T002, with an attribute error.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_settings.py`
- **Status**: open

### T002 Add `missing_names` and use it in `load` (FR-002, FR-003)

- **Files**: `src/operations/exporting/juniper_rma/settings.py`
- **Acceptance**: `JuniperSettingsLoader.missing_names(needs_contact_email)` returns the same names that `load` computed before. `load` calls it and keeps its log lines and its error text. TS-01 to TS-03 pass. Every new line has an inline comment.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_settings.py`
- **Status**: open

### T003 Write the tests for `is_automated_run` (FR-006, FR-003)

- **Files**: `tests/unit/juniper_rma/api/test_settings.py`
- **Acceptance**: TS-04 checks that a `--test` flag in argv returns True. TS-05 checks that an argv without a flag returns False when runtime test mode is off. TS-06 checks that runtime test mode returns True. TS-05 and TS-06 set `runtime_settings.IS_TEST_MODE` with pytest monkeypatch. All three fail before T004.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_settings.py`
- **Status**: open

### T004 Add `is_automated_run` and use it in `refusal_message` (FR-002, FR-003)

- **Files**: `src/operations/exporting/juniper_rma/settings.py`
- **Acceptance**: `JuniperLiveCallGuard.is_automated_run(argv)` returns the same answer as the automated check inside `refusal_message`. `refusal_message` calls it and keeps the `JUNIPER_LIVE_TESTS` opt-in check. TS-04 to TS-06 pass.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_settings.py`
- **Status**: open

### T005 [P] Write the rate limiter tests for `refill` (FR-006, FR-003)

- **Files**: `tests/unit/juniper_rma/api/test_gateway.py`
- **Acceptance**: TS-07 checks that 0.25 seconds of refill at 2.0 tokens each second returns 0.5 after one token is spent. TS-08 checks that a 10-second idle period caps the level at 1.0. Both tests use the existing `FakeClock` fixture. Both fail before T007.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_gateway.py`
- **Status**: open

### T006 Write the token tests for `is_fresh` (FR-006, FR-003)

- **Files**: `tests/unit/juniper_rma/api/test_gateway.py`
- **Acceptance**: TS-09 checks that no cached token gives False. TS-10 checks that a cached token before its expiry gives True. TS-11 checks that the clock at the expiry time gives False. The token reply helper already in this module creates the cached token. All three fail before T008.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_gateway.py`
- **Status**: open

### T007 Add `refill` and use it in `acquire` (FR-002, FR-003)

- **Files**: `src/operations/exporting/juniper_rma/api/gateway.py`
- **Acceptance**: `RequestRateLimiter.refill()` adds the earned tokens, caps the level at 1.0, stores the refill time, and returns the level. `acquire` calls it and keeps its wait logic. TS-05 to TS-08 pass, and the existing rate limit tests still pass.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_gateway.py`
- **Status**: open

### T008 Add `is_fresh` and use it in `authorization_header` (FR-002, FR-003)

- **Files**: `src/operations/exporting/juniper_rma/api/gateway.py`
- **Acceptance**: `JuniperTokenProvider.is_fresh()` returns True only when a token is cached and the clock is before the expiry time. `authorization_header` uses `force_refresh or not self.is_fresh()`. TS-09 to TS-11 pass, and the existing token tests still pass.
- **Verification**: `python -m pytest tests/unit/juniper_rma/api/test_gateway.py`
- **Status**: open

### T009 [P] Write the retention tests for `cutoff` (FR-006, FR-003)

- **Files**: `tests/unit/juniper_rma/model/test_export_rows.py`
- **Acceptance**: TS-12 checks that `cutoff(now=1000000.0)` with a two-day window returns 827200.0. TS-13 checks that `cutoff(now=86400.0)` with a one-day window returns 0.0. Both fail before T010.
- **Verification**: `python -m pytest tests/unit/juniper_rma/model/test_export_rows.py`
- **Status**: open

### T010 [P] Add `cutoff` and use it in `purge` (FR-002, FR-003, FR-005)

- **Files**: `src/operations/exporting/juniper_rma/model/export_rows.py`
- **Acceptance**: `PersonalDataRetention.cutoff(now)` returns the same value that `purge` computed before. `purge` calls it and keeps its file loop and its log lines. The file names and the output folder do not change. TS-12 and TS-13 pass, and the existing purge test still passes.
- **Verification**: `python -m pytest tests/unit/juniper_rma/model/test_export_rows.py`
- **Status**: open

### T011 [P] Write the conversion tests for `to_tickets` (FR-006, FR-003)

- **Files**: `tests/unit/juniper_rma/workflows/test_correlation.py`
- **Acceptance**: TS-14 checks that two object rows convert in input order with their identifiers. TS-15 checks that a string item and a null item are dropped, and that the object rows keep their order. Both fail before T012.
- **Verification**: `python -m pytest tests/unit/juniper_rma/workflows/test_correlation.py`
- **Status**: open

### T012 [P] Add `to_tickets` and use it in `read` (FR-002, FR-003, FR-005)

- **Files**: `src/operations/exporting/juniper_rma/workflows/correlation.py`
- **Acceptance**: `MistTicketReader.to_tickets(rows)` converts object rows and drops other items, in order. It logs an info line before the work and a debug line after it, with counts only. `read` keeps its SDK call and its existing debug line, and returns `self.to_tickets(rows)`. TS-14 and TS-15 pass.
- **Verification**: `python -m pytest tests/unit/juniper_rma/workflows/test_correlation.py`
- **Status**: open

### T013 Add the release-note fragment (FR-007)

- **Files**: `changelog.d/issue-4134-r0902-r0903-class-design.md`
- **Acceptance**: The fragment has one `###` heading and one `Changed` bullet that names issue 4134. The file name follows the Name the file table of `changelog.d/README.md`. The changelog guard test TS-18 passes.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

### T014 Check the register against the scan (FR-001, FR-004)

- **Files**: `design\research.md` (read only), `design\quickstart.md` (read only)
- **Acceptance**: TS-16 passes. The scan reports exactly 19 findings. Each finding matches one register row by file, class, code, and count. No pylint pragma appears in any changed file.
- **Verification**: `pylint src/ --fail-under=9.5`, then the register scan in `design\quickstart.md`
- **Status**: open

## Phase 2: Final Tasks

### T-LOCAL-GATES (FR-003, FR-005, FR-009, SC-002, SC-003, SC-004)

- **Files**: The changed files in the change map of `plan.md`.
- **Acceptance**: Each applicable gate of the Local gates table exits with the expected result. Gates that do not apply carry a stated reason in the pull request body.
- **Verification**: Run the gates in the order of `design\quickstart.md`, section "Local gates".
- **Status**: open

### T-PR (FR-007, FR-008, FR-009, SC-005)

- **Files**: The change map of `plan.md`.
- **Acceptance**: The branch is `chore/4134-r0902-r0903-class-design` from `main`. One commit has the subject `refactor(juniper-rma): resolve six pylint R0903 findings`. The pull request title matches that subject. The body has `Closes #4134`, the gate results, the register summary, and the fragment decision with the conflict note. The changed-file list equals the change map (TS-17).
- **Verification**: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only origin/main`
- **Status**: open

### T-REMOTE-CI (FR-005)

- **Files**: The pull request.
- **Acceptance**: Each required check passes on the latest commit. The check list includes the Conventional Commits PR title check.
- **Verification**: `gh pr checks <number> --watch`
- **Status**: open

### T-MERGE (FR-008)

- **Files**: The pull request.
- **Acceptance**: The orchestrator authorizes the merge. The `auto-merge` label is added only after every check passes. The pull request is squash merged, and the branch is deleted.
- **Verification**: `gh pr view <number> --json state,mergedAt`
- **Status**: open

## Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T014 | TS-16 |
| FR-002 | T002, T004, T007, T008, T010, T012 | TS-01 to TS-15 |
| FR-003 | T002, T004, T007, T008, T010, T012 | TS-01 to TS-15 |
| FR-004 | T014 | TS-16 |
| FR-005 | T-LOCAL-GATES, T010, T012 | TS-01 to TS-15 |
| FR-006 | T001, T003, T005, T006, T009, T011 | TS-01 to TS-15 |
| FR-007 | T013 | TS-18 |
| FR-008 | T-PR | TS-17 |
| FR-009 | T-LOCAL-GATES | TS-17 |

## Test Count

- Pytest cases: 15 (TS-01 to TS-15).
- Register scan check: 1 (TS-16).
- Scope check: 1 (TS-17).
- Changelog guard test: 1 (TS-18).
- Total tests planned: 18.
