# Tasks: mistapi signature mismatch repair

**Input**: Design documents from `specs/2741-signature-mismatch/`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: The issue requires tests that fail on the old call shape.

## Phase 1: Setup

- [x] T001 Read issue #2741, issue #2726, and issue #2717. (delivered: GitHub issue context)
- [x] T002 Create `fix/2741-signature-mismatch` from current `origin/main`. (delivered: worktree)
- [x] T003 Verify `mistapi` 0.64.0 and pytest collection. (delivered: local command output)

## Phase 2: API Contract Evidence

- [x] T004 Inspect `createSiteDeviceShellSession` with `help()`. (delivered: SDK output)
- [x] T005 Read the shell session OpenAPI body schema. (delivered: `documentation/api/utilities/POST_sites_site_id_devices_device_id_shell.md`)
- [x] T006 Inspect `listSiteDevicesStats` with `inspect.signature`. (delivered: SDK output)
- [x] T007 Audit every `listSiteDevicesStats` call under `src/`. (delivered: `specs/2741-signature-mismatch/plan.md`)

## Phase 3: User Story 1 - CLI shell session

**Goal**: Pass the required shell body and expose signature programming errors.

**Independent Test**: Run `python -m pytest tests\unit\ssh\test_cli_shell_manager.py::TestCreateSession -v`.

- [x] T008 [US1] Update the shell session success test to require `body={}`. (delivered: `tests/unit/ssh/test_cli_shell_manager.py`)
- [x] T009 [US1] Add a test that proves `TypeError` is not hidden. (delivered: `tests/unit/ssh/test_cli_shell_manager.py`)
- [x] T010 [US1] Pass `body={}` to `createSiteDeviceShellSession`. (delivered: `src/ssh/cli_shell_manager.py`)
- [x] T011 [US1] Narrow the shell handler so runtime failures return `None` and `TypeError` raises. (delivered: `src/ssh/cli_shell_manager.py`)

## Phase 4: User Story 2 - Reconciliation evidence read

**Goal**: Remove the unsupported `fields` keyword and preserve running-version evidence.

**Independent Test**: Run `python -m pytest tests\unit\upgrade_portal\test_site_stats_evidence_reader.py -v`.

- [x] T012 [US2] Add a strict SDK-signature test for reconciliation. (delivered: `tests/unit/upgrade_portal/test_site_stats_evidence_reader.py`)
- [x] T013 [US2] Remove `fields` from `listSiteDevicesStats`. (delivered: `src/upgrade_portal/api/run_controls/routes.py`)
- [x] T014 [US2] Apply `gate.STATISTICS_FIELDS` as a local projection. (delivered: `src/upgrade_portal/api/run_controls/routes.py`)
- [x] T015 [US2] Keep `running_version` and `fwupdate_status` in the evidence row. (delivered: `tests/unit/upgrade_portal/test_site_stats_evidence_reader.py`)

## Phase 5: Validation and Delivery

- [ ] T016 Run the required local gates from issue #2741.
- [ ] T017 Create `changelog.d/issue-2741-signature-mismatch.md`.
- [ ] T018 Commit, push, open the pull request, and wait for checks.
- [ ] T019 Merge after every required check, including CodeQL, reports green.
- [ ] T020 Verify issue #2741 closes or close it with evidence.

## Dependencies

- T004 and T005 must complete before T010.
- T006 and T007 must complete before T013.
- T008 and T009 must complete before T010 and T011.
- T012 must complete before T013 through T015.
- T016 must complete before T018.
- T019 must complete before T020.
