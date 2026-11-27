# Tasks: Site export write results

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/`.

## Format

Each task names its requirements, its exact repository paths, its acceptance statement, one verification command, and its status. The status is `open`, `verified-present`, `partial`, or `absent`. Status `verified-present` requires remote evidence in `design/research.md`.

## Phase 1: Verify the merged repair

**Purpose**: Confirm that `main` holds the repair. These tasks change no file.

### T001 [P] Verify application list failed-write handling

- **Requirements**: FR-001, FR-002, FR-003
- **Files**: `src/operations/exporting/export/site_application_list_exporter.py` (lines 63-68)
- **Acceptance**: The persistence method logs one error and returns when the writer returns `False`.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k test_failed_write_reports_error_without_success`
- **Status**: verified-present. Remote blob `01cba0e52d5a3a6ced43d3e4b8c2d949cd76a31b`, lines 63-68.

### T002 [P] Verify system event failed-write handling

- **Requirements**: FR-001, FR-002, FR-003
- **Files**: `src/operations/exporting/export/site_system_events_exporter.py` (lines 63-68)
- **Acceptance**: The persistence method logs one error and returns when the writer returns `False`.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k test_failed_write_reports_error_without_success`
- **Status**: verified-present. Remote blob `12dcaccad3a704231f66127e6ed1f60e2414d27d`, lines 63-68.

### T003 [P] Verify success, empty, and exception contracts

- **Requirements**: FR-004, FR-005, FR-006, FR-007
- **Files**: `tests/unit/export/test_site_asset_and_events_exporters.py` (lines 376-435)
- **Acceptance**: All 12 non-failure cases in `TestSiteWriteOutcomes` pass without change.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k TestSiteWriteOutcomes`
- **Status**: verified-present. Remote blob `a2aa37e006a3265a70422c2bbca32faecacf030c`, lines 376-435.

### T004 [P] Verify operator guide and menu reference

- **Requirements**: FR-011
- **Files**: `documentation/operator-guide.md` (line 120), `documentation/menu_reference.md` (lines 249-250)
- **Acceptance**: The operator guide names the failed-write behavior. The generated menu reference lists menus 213 and 214 with no stale page.
- **Verification**: `python -m scripts.menu_api_map`
- **Status**: verified-present. Remote blobs `60d28f9ea461fc8798973d1d1b7e40491c27c248` and `2bd972183c64302e76442d30669bb9e7362856f1`.

### T005 [P] Verify the release note fragment

- **Requirements**: FR-012
- **Files**: `changelog.d/issue-4717-site-export-writer-results.md`
- **Acceptance**: The fragment has one heading, one bullet, and the issue number.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: verified-present. Remote blob `daee06e8a274a98f7b06a70f34143e0e3f7a3441`, lines 1-3.

### T006 [P] Verify module-level names against main

- **Requirements**: FR-008
- **Files**: `src/operations/exporting/export/site_application_list_exporter.py`
- **Acceptance**: No module-level name is lost compared with `origin/main`. T-LOCAL-GATES checks the other two owned paths.
- **Verification**: `symbol-diff --base origin/main src/operations/exporting/export/site_application_list_exporter.py`
- **Status**: verified-present. Remote blob `01cba0e52d5a3a6ced43d3e4b8c2d949cd76a31b`. No later commit changed the file after `db06604d18`.

## Phase 2: Repair the gaps

**Purpose**: Add the comments and the offline proof that `main` does not yet hold.

### T007 [P] Comment application list persistence statements

- **Requirements**: FR-010
- **Files**: `src/operations/exporting/export/site_application_list_exporter.py` (lines 58, 67, 68)
- **Acceptance**: Each listed statement line carries an inline comment that gives its purpose. No code changes.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k TestApplicationList`
- **Status**: absent. Lines 58, 67, and 68 lack a comment on `main`.

### T008 [P] Comment system event persistence statements

- **Requirements**: FR-010
- **Files**: `src/operations/exporting/export/site_system_events_exporter.py` (lines 58, 67, 68)
- **Acceptance**: Each listed statement line carries an inline comment that gives its purpose. No code changes.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k TestSystemEvents`
- **Status**: absent. Lines 58, 67, and 68 lack a comment on `main`.

### T009 [P] Comment the TestSiteWriteOutcomes statements

- **Requirements**: FR-010
- **Files**: `tests/unit/export/test_site_asset_and_events_exporters.py` (lines 337, 340, 344, 347-355, 366, 369, 389-391, 394-397, 410, 414, 426, 431, 434, 435)
- **Acceptance**: Each of the 27 listed statement lines carries an inline comment. No test code changes.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k TestSiteWriteOutcomes`
- **Status**: absent. The 27 lines lack a comment on `main`.

### T010 Build and run the offline harness

- **Requirements**: FR-009
- **Files**: `test-artifacts/offline-guard/offline_guard.py` (create, not committed), `tests/unit/export/test_site_asset_and_events_exporters.py` (read only)
- **Acceptance**: The harness blocks `socket.socket.connect`, `socket.socket.connect_ex`, `socket.getaddrinfo`, `socket.create_connection`, and `sqlite3.connect`. Its self-test proves each block fails. The module run reports zero attempts.
- **Verification**: `python -m pytest -p offline_guard tests/unit/export/test_site_asset_and_events_exporters.py` (with `PYTHONPATH` set to `test-artifacts/offline-guard`)
- **Status**: absent. No offline harness exists in the repository, and `pyproject.toml` sets no socket guard.

## Phase 3: Route and record evidence

**Purpose**: Prove the route and replace the draft record.

### T011 [P] Run the route check under pwsh

- **Requirements**: FR-013
- **Files**: `.specify/scripts/powershell/spec-route.ps1` (read and run under `pwsh`), `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/` (path result only)
- **Acceptance**: `Resolve-SpecFeaturePath -SpecsDir specs -BranchName 4717-site-export-writer-results -Number 4717` returns `specs\numbered\0\0\1\2\2\3\3\2\4717-site-export-writer-results`.
- **Verification**: `python -m pytest tests/guardrails/test_spec_route_contract.py`
- **Status**: partial. The route is computed by hand from `spec-route.ps1` lines 17-31. The script did not run during authoring.

### T012 Replace the draft record

- **Requirements**: FR-014, FR-001 to FR-015 (record content)
- **Files**: the record folder `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/`. Replace `spec.md`, `plan.md`, `tasks.md`, and `design/checklists/requirements.md`. Add `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/` (three files), and `design/checklists/` (two added files).
- **Acceptance**: The record folder holds this record. Each directory holds five children or fewer.
- **Verification**: `python -m pytest tests/guardrails/test_process_folder_structure.py`
- **Status**: partial. The draft exists on `main`, and it holds stale claims listed in `design/research.md`.

## Phase 4: Final delivery

**Purpose**: Run the gates, open the pull request, watch CI, and merge after authorization.

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-001 to FR-012
- **Files**: the three owned source and test paths, and the record folder
- **Acceptance**: Each applicable row of the local gates table passes. Record each command and its exact output in the pull request body. Mark each row not applicable with its reason.
- **Verification**: `python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py`
- **Status**: open.

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-015
- **Files**: the owned paths and the record folder
- **Acceptance**: A worktree branch named `docs/4717-site-export-verification` holds one Conventional Commit. The pull request body contains `Closes #4717`. The change adds no changelog fragment, because it is internal.
- **Verification**: `gh pr view <number> --json title,body,headRefName` (remote command, not a local gate. See decision R-14.)
- **Status**: open.

### T-REMOTE-CI Watch remote CI

- **Requirements**: FR-015
- **Files**: the pull request head commit
- **Acceptance**: Each required check reports SUCCESS on the latest commit.
- **Verification**: `gh pr checks <number> --watch` (remote command, not a local gate. See decision R-14.)
- **Status**: open.

### T-MERGE Enable auto-merge after authorization

- **Requirements**: FR-015
- **Files**: the pull request
- **Acceptance**: The orchestrator authorizes the merge. Auto-merge completes. Issue #4717 closes. The orchestrator removes the `in-progress` label.
- **Verification**: `gh pr view <number> --json mergedAt,closingIssuesReferences` (remote command, not a local gate. See decision R-14.)
- **Status**: open.

## Dependencies and Execution Order

- T001 to T006 run in parallel. They change no file.
- T007, T008, and T009 run in parallel. Each edits one file.
- T010 runs after T009. Both affect the shared test module.
- T011 and T012 run in parallel with Phase 2.
- T-LOCAL-GATES runs after T007 to T010, T011, and T012.
- T-PR runs after T-LOCAL-GATES.
- T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI and the authorization.

## Requirement Coverage

| Requirement | Tasks |
| - | - |
| FR-001 | T001, T002, T-LOCAL-GATES |
| FR-002 | T001, T002, T003 |
| FR-003 | T001, T002 |
| FR-004 | T003 |
| FR-005 | T003 |
| FR-006 | T003 |
| FR-007 | T003 |
| FR-008 | T006, T-LOCAL-GATES |
| FR-009 | T010 |
| FR-010 | T007, T008, T009 |
| FR-011 | T004 |
| FR-012 | T005 |
| FR-013 | T011 |
| FR-014 | T012 |
| FR-015 | T-PR, T-REMOTE-CI, T-MERGE |

## Notes

- The local gates table in `.github/copilot-instructions.md` lines 57-74 defines every local command.
- `pytest` runs against the `.venv` created by `scripts/bootstrap_worktree.py`.
- Each comment-only edit keeps the line count. A line count change moves the line numbers in this file.
