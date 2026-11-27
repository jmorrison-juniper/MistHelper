# Tasks: Menu 243 Result File Not Found

**Input**: Numeric record `specs/numbered/0/0/1/1/2/1/2/1/4036-menu-243-result-file-not-found/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/result-preview-route.md`

**Format**: `[ID] [P?] [Story] [Requirements] Description`. `[P]` marks a task that is safe to run in parallel. Each task names its paths and one verification command from the local gates table. Status values are open, verified-present, partial, and absent.

## Phase 1: Verify the existing fixes on main

- [x] T001 [P] [US1] [FR-001, FR-002] Verify the single file route and the absent table route in `web_portal/routes/data.py`.
  - Acceptance: One preview route exists at line 45. No table route exists. The table branch runs only for database directories.
  - Verification: `python -m pytest tests/unit/web_portal/test_preview_row_order.py`
  - Status: verified-present (RC-14, RC-15, RC-18)

- [x] T002 [P] [US2] [FR-002, FR-006, FR-008] Verify table selection, path denials, and nondisclosing JSON errors in `web_portal/routes/data.py` and `web_portal/services/data_browser.py`.
  - Acceptance: A table selection needs a database suffix and a file. JSON read errors return fixed text and log details on the server.
  - Verification: `python -m pytest tests/unit/web_portal/test_preview_row_order.py`
  - Status: verified-present (RC-19, RC-24, RC-25, RC-47, RC-48)

- [x] T003 [P] [US3] [FR-005] Verify the output-list exclusion in `web_portal/services/operation.py` and its test module.
  - Acceptance: The discovery test names the MIB input exclusion. The output list keeps existing files only.
  - Verification: `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/quality/test_operation_output_file_discovery.py`
  - Status: verified-present (RC-26, RC-53)

- [x] T004 [P] [US2] [FR-004, FR-007] Verify the pending clear and the missing-file browser test in `web_portal/static/js/operation_results.js` and `tests/e2e/web_portal/test_operation_results_table.py`.
  - Acceptance: `load()` clears rows and page controls before each request. The missing-file test asserts the message text.
  - Verification: `python -m pytest tests/e2e/web_portal/test_operation_results_table.py`
  - Status: verified-present (RC-30, RC-52)

## Phase 2: Publish the regression test

- [ ] T005 [US1] [US2] [FR-001, FR-003, FR-004, FR-005, FR-009] Merge the test from commit `18ce4c8` into `tests/e2e/web_portal/test_operation_results_table.py`.
  - Work: Add the three helpers, the menu 243 fixture, and the test function. Add `from functools import partial`. Reuse `READY_TIMEOUT_MS`. Add `RUN_TIMEOUT_MS`. Add inline comments and action logs.
  - Acceptance: The test passes on the branch. It asserts the ledger-only output list. It asserts HTTP 200 for both downloads and for the preview. Each executable line has an inline comment.
  - Verification: `python -m pytest tests/e2e/web_portal/test_operation_results_table.py`
  - Status: open. The commit exists, but the file is absent on main [RC-68, RC-70].

- [ ] T006 [P] [FR-010] Add `changelog.d/issue-4036-menu-243-preview-test.md` with a `### Changed` heading and one bullet that names issue #4036.
  - Acceptance: The fragment has one heading and one bullet. It names the test as the only change. It uses plain words.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4036-menu-243-preview-test.md`
  - Status: open

- [ ] T007 [FR-009] [SC-002] Show the red result in a scratch copy outside the repository path.
  - Work: Create a worktree at `..\misthelper-red-4036`. Add the two-part table route from line 77 of commit `2a48cee`. Make it call the existing table helper. Copy the test module. Run it.
  - Acceptance: The nested preview assertion fails with HTTP 404. Remove the scratch worktree after the run.
  - Verification: `python -m pytest tests/e2e/web_portal/test_operation_results_table.py`
  - Status: open

- [ ] T-RECORD [FR-010] Place the record folder and its files at `specs/numbered/0/0/1/1/2/1/2/1/4036-menu-243-result-file-not-found/`. Stage the folder with the change.
  - Acceptance: The feature root holds five children or fewer. The process folder guard passes.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
  - Status: open

## Phase 3: Final gates and delivery

- [ ] T-LOCAL-GATES [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009] Run each applicable local gate on the changed files.
  - Paths: `MistHelper.py`, `tests/e2e/web_portal/test_operation_results_table.py`, `tests/unit/web_portal/test_preview_row_order.py`, `changelog.d/issue-4036-menu-243-preview-test.md`, and the record folder files.
  - Work: Run the compile, lint, format, module test, symbol, test-quality, and STE commands listed in `design/quickstart.md`.
  - Acceptance: Each command exits 0. The pull request body records each command and its result.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: open

- [ ] T-PR [FR-010] Commit, push, and open the pull request.
  - Paths: `tests/e2e/web_portal/test_operation_results_table.py`, `changelog.d/issue-4036-menu-243-preview-test.md`, and the record folder.
  - Work: Commit with `test(web-portal): cover menu 243 result preview end to end`. Push `fix/4036-menu-243-preview-test`. Set the body to `Relates to #4036` [D-04]. Rename the fragment to `pr-<number>.md` after GitHub returns the pull request number.
  - Acceptance: The title passes the Conventional Commits check. The body names the local gates and their results.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Status: open

- [ ] T-REMOTE-CI [FR-010] Watch the required checks on the pull request head.
  - Paths: No file changes. The checks cover the paths in T005, T006, and T-RECORD.
  - Work: Run `gh pr checks` with the pull request number and `--watch`. Read every check result.
  - Acceptance: Every required check reports success. A skipped job does not count as success.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Status: open

- [ ] T-MERGE [FR-010] [SC-004] Merge after authorization. Then run the live check on the deployed container.
  - Paths: No file changes in the repository. The live check reads `data/mib_generator/` and writes a backup outside the repository.
  - Work: The orchestrator authorizes the merge. A human reviews the pull request first, because the issue carries `needs-human-review`. After the squash merge, deploy the image. Run the live check in `design/quickstart.md` section 4.
  - Acceptance: The live check shows ledger rows and no error text. The orchestrator posts the revision label and the result on #4036. Only then does the orchestrator close #4036.
  - Verification: `python MistHelper.py --test`
  - Status: open

## Dependencies and execution order

- T001 to T004 are verification tasks. They run first and in parallel.
- T005 follows T001 and T003. It changes only the browser module.
- T006 runs in parallel with T005.
- T007 follows T005. It proves the test can fail.
- T-RECORD follows T006.
- T-LOCAL-GATES follows T005, T006, T007, and T-RECORD.
- T-PR follows T-LOCAL-GATES.
- T-REMOTE-CI follows T-PR.
- T-MERGE follows T-REMOTE-CI and the orchestrator authorization.
