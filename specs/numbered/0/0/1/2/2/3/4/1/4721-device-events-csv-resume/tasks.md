# Tasks: Resumed 52-week device-event CSV export

**Input**: Numeric record `specs\numbered\0\0\1\2\2\3\4\1\4721-device-events-csv-resume\`. The plan is in `plan.md`. The requirements are in `spec.md`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design\research.md`, `design\data-model.md`, `design\quickstart.md`, `design\contracts\`.

**Status values**: `open` means not started. `absent` means the required behavior is not on main. `partial` means some of the behavior is on main. `verified-present` means the behavior is on main, and the authoring agent read the code and test.

## Format

- `[P]` marks a task that can run in parallel. The files differ, and no task depends on it.
- Each task lists requirement IDs, exact repository paths, an acceptance statement, one verification command, and a status.
- Commands use the local gates table in `plan.md`. The final four tasks name the CI or pull request step when the local table has no entry.

## Phase 1: Tests first

- [ ] **T001** Add six new tests and update one existing test. Requirements: FR-006, FR-007, FR-008, FR-009, FR-012. Paths: `tests\unit\test_device_events_52w_exporter_extended.py`. Acceptance: Tests N1, N4, N5, and N6 fail on main. Tests N2, N3, and U1 pass on main. Verification: `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider`. Status: absent. Depends on: none.

## Phase 2: Exporter behavior

- [ ] **T002** Refuse a resumed run on an empty checkpoint when the CSV file exists. Requirements: FR-006, FR-009. Paths: `src\operations\exporting\export\device_events_52w_exporter.py` (method `_read_checkpoint`, lines 141-155). Acceptance: Test N1 passes. Both files keep their bytes. Verification: `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider`. Status: absent. Depends on: T001.

- [ ] **T003** Write each checkpoint token through the temporary checkpoint file, then replace. Requirements: FR-007, FR-012. Paths: `src\operations\exporting\export\device_events_52w_exporter.py` (method `_write_checkpoint`, lines 342-353). Acceptance: Tests N4 and N5 pass. The live checkpoint file is never opened for writing. Verification: `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider`. Status: absent. Depends on: T001.

- [ ] **T004** Keep both files unchanged for a resumed run with no new rows. Requirements: FR-008, FR-012. Paths: `src\operations\exporting\export\device_events_52w_exporter.py` (method `export`, line 91, and method `_handle_empty_result`, lines 120-125). Acceptance: Test N6 passes. The CSV and checkpoint keep their bytes. The log names no new rows and no completion. Verification: `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider`. Status: absent. Depends on: T001.

- [ ] **T009** Confirm the regression tests pass without edits. Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-010, FR-011. Paths: `tests\unit\test_device_events_52w_exporter_extended.py` (tests at lines 91, 104, 543, 574, 597, 625, 649, 679, 703, 725). Acceptance: Each named test passes after T002 to T004. No assertion changes. Verification: `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py -q -p no:cacheprovider`. Status: verified-present. Depends on: T002, T003, T004.

## Phase 3: Documentation and changelog

- [ ] **T005** [P] Describe the resume rules and the duplicate-row risk in the operator guide. Requirements: FR-013. Paths: `documentation\operator-guide.md` (insert a section before line 744, `### Find your output`). Acceptance: The section names menu 97, each refusal, the `.tmp` file, and the duplicate risk. Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`. Status: absent. Depends on: none.

- [ ] **T006** [P] Link the operator guide section from the README. Requirements: FR-013. Paths: `README.md` (table under `## Documentation`, lines 115-133). Acceptance: One table row links the new section by anchor. Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md`. Status: absent. Depends on: T005.

- [ ] **T007** [P] Add the changelog fragment. Requirements: FR-014. Paths: `changelog.d\issue-4721-device-events-csv-resume.md` (add). Acceptance: One `###` heading and one `Fixed` bullet name issue 4721. Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4721-device-events-csv-resume.md`. Status: absent. Depends on: none.

- [ ] **T008** [P] Correct the menu list in the device-events endpoint note. Requirements: FR-013. Paths: `documentation\api\orgs\GET_orgs_org_id_devices_events_search.md` (line 269). Acceptance: The note names menu 97 and drops menus 2 and 63. Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/api/orgs/GET_orgs_org_id_devices_events_search.md`. Status: absent. Depends on: none.

## Phase 4: Gates and delivery

- [ ] **T-LOCAL-GATES** Run each applicable gate in the local gate plan. Requirements: FR-010, FR-011, FR-012, FR-015. Paths: `src\operations\exporting\export\device_events_52w_exporter.py`, `tests\unit\test_device_events_52w_exporter_extended.py`, `documentation\operator-guide.md`, `README.md`, `documentation\api\orgs\GET_orgs_org_id_devices_events_search.md`, `changelog.d\issue-4721-device-events-csv-resume.md`. Acceptance: Each applicable gate reports its expected result. Record each command and its output. Verification: `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider`. Status: open. Depends on: T002, T003, T004, T005, T006, T007, T008, T009.

- [ ] **T-PR** Commit, push, and open the pull request. Requirements: FR-014, FR-015. Paths: the six changed paths listed for T-LOCAL-GATES. Acceptance: The commit subject starts with `fix(export):`. The body contains `Closes #4721`. The branch is `fix/4721-device-events-csv-resume`. Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body,headRefName`. The local gate table has no entry for this step. Status: open. Depends on: T-LOCAL-GATES.

- [ ] **T-REMOTE-CI** Watch the CI run for the pull request. Requirements: FR-012. Paths: none. Acceptance: Each required check passes on the latest commit. Verification: `gh pr checks <number> --watch`. The local gate table has no entry for this step. Status: open. Depends on: T-PR.

- [ ] **T-MERGE** Enable auto-merge only after CI passes and the orchestrator authorizes the merge. Requirements: FR-015. Paths: none. Acceptance: `main` receives one squash commit. The branch and worktree are removed. Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt`. The local gate table has no entry for this step. Status: open. Depends on: T-REMOTE-CI.

## Dependencies and Execution Order

- T001 comes first. It writes the failing tests.
- T002, T003, and T004 depend on T001. They change the same file, so run them in this order: T002, T003, T004.
- T009 depends on T002, T003, and T004. It confirms the regression tests.
- T005 and T007 and T008 have no prerequisite. They can run in parallel with the code tasks.
- T006 depends on T005. It links the section that T005 creates.
- T-LOCAL-GATES depends on every task above it.
- T-PR, T-REMOTE-CI, and T-MERGE run in order.

## Notes

- Do not change `tests\unit\export\` or `src\operations\exporting\export\` in a new file. FR-015 forbids it.
- Do not change the SQLite or Redis code path. FR-011 forbids it.
- Each new line of Python needs an inline comment. Each touched block needs logs before and after the action.
- The full unit tree runs in CI. Local runs cover the changed module only.
