# Tasks: Report a Mist transport fault as an unavailable Mist API

**Input**: Design documents in `specs/numbered/0/0/1/2/2/4/4/3/4748-mist-token-timeout-unavailable/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`.

**Tests**: The specification requires tests. Write each test task before its implementation task, and see it fail first. Use mocked HTTP only (FR-017).

**Working directory**: run `pytest` and `ruff` from `mist-ops-platform/`. Run `python -m py_compile`, `ste-linter`, and `symbol-diff` from the repository root with repository paths.

## Format: `[ID] [P?] [Requirements] Description`

- **[P]**: The task runs in parallel with other `[P]` tasks of its phase. It edits a different file.
- **Status**: `open` for process work. `absent` for code that does not exist on `main`. `partial` for a file that exists and needs a change. `verified-present` for code that exists and needs only a run.

## Phase 1: Baseline

- [ ] T001 Record the ops platform baseline on the untouched worktree. Files: `mist-ops-platform/pyproject.toml`. Requirements: SC-004. Acceptance: the run reports the collected count and the coverage before any change. Verification: `pytest --cov=src --cov-fail-under=56 --timeout=120`. Status: open.

## Phase 2: Registry and Result Shape (blocking for Phase 3)

- [ ] T002 [P] Write three failing tests in `mist-ops-platform/tests/unit/mist/test_list_status.py`. Cover tests N13, N14, and N15. Requirements: FR-014, FR-015. Acceptance: each test fails on `main`. Verification: `pytest tests/unit/mist/test_list_status.py -q`. Status: partial.
- [ ] T003 Add `single_object: bool = False` to `MistEndpoint` and set `single_object=True` on `self_identity` in `mist-ops-platform/src/shared/mist/types.py`. Requirements: FR-014. Acceptance: the field is the last field and has a default. Verification: `python -m py_compile mist-ops-platform/src/shared/mist/types.py`. Status: absent.
- [ ] T004 Return False from `ApiResult.success` when the status is None. Add the single-object branch and `_single_object_rows` in `mist-ops-platform/src/shared/mist/endpoints.py`. Requirements: FR-014, FR-015. Acceptance: tests N13 to N15 pass. Verification: `pytest tests/unit/mist/test_list_status.py -q`. Status: absent.

## Phase 3: Validation Session and Classification (User Stories 1 to 4)

- [ ] T005 [P] Write twelve failing tests in `mist-ops-platform/tests/unit/api/test_auth.py`. Cover tests N1 to N12, including the two SDK contract tests. Add an autouse guard that fails each unmocked network call. Requirements: FR-001 to FR-011, FR-013, FR-017. Acceptance: each new test fails on `main`. Verification: `pytest tests/unit/api/test_auth.py -q`. Status: partial.
- [ ] T006 Add class `TokenValidationSession` to `mist-ops-platform/src/shared/services/auth.py`. Override `_load_env` as a no-op. Set the host to `api.mist.com`. Mount the nested `_BoundedTimeoutAdapter` with `TIMEOUT_SECONDS = 30`. Call `set_api_token(token, validate=False)`. Requirements: FR-008, FR-009, FR-011, FR-013, SC-003. Acceptance: tests N6, N7, and N12 pass. Verification: `python -m py_compile mist-ops-platform/src/shared/services/auth.py`. Status: absent.
- [ ] T007 Add static method `_is_valid_token_shape` to `mist-ops-platform/src/shared/services/auth.py`. Accept only ASCII code points 33 to 126. Requirements: FR-010. Acceptance: test N8 passes, and no request runs for a rejected shape. Verification: `pytest tests/unit/api/test_auth.py -q -k malformed`. Status: absent.
- [ ] T008 Add methods `_request_identity` and `_identity_from_result` to `mist-ops-platform/src/shared/services/auth.py`. Change `_fetch_self` and `_handle_self_failure` so each outcome follows the table in `design/contracts/validation-service.md`. Keep each function within 25 lines. Requirements: FR-001 to FR-007, SC-002. Acceptance: tests N1 to N5 pass. Verification: `pytest tests/unit/api/test_auth.py -q`. Status: absent.
- [ ] T009 Add action logging to `mist-ops-platform/src/shared/services/auth.py`. Log before each privilege lookup and after each result. Log the exception class name and the HTTP status code only. Requirements: FR-012, FR-016. Acceptance: test N9 passes. Verification: `pytest tests/unit/api/test_auth.py -q -k log`. Status: absent.
- [ ] T010 [P] Update three existing tests in `mist-ops-platform/tests/unit/api/test_auth.py`. The tests are `test_fetch_self_returns_empty_privileges_on_401`, `test_fetch_self_raises_unavailable_on_503`, and `test_fetch_self_direct_service_reports_503`. Requirements: FR-004, FR-006. Acceptance: each test patches the new seam and asserts the new result. Verification: `pytest tests/unit/api/test_auth.py -q`. Status: partial.
- [ ] T011 [P] Update the patch targets of two tests in `mist-ops-platform/tests/unit/api/test_session_security.py` at L338 and L369. Requirements: FR-016. Acceptance: both tests pass without a network call. Verification: `pytest tests/unit/api/test_session_security.py -q`. Status: partial.

## Phase 4: Unchanged Behavior and Documents

- [ ] T012 Run the unchanged tests in `mist-ops-platform/tests/unit/mist/test_consumer_registry_usage.py` and `mist-ops-platform/tests/unit/api/test_health.py`. Requirements: FR-013, FR-016. Acceptance: both files pass without an edit. Verification: `pytest tests/unit/mist/test_consumer_registry_usage.py tests/unit/api/test_health.py -q`. Status: verified-present.
- [ ] T013 Read the section at `mist-ops-platform/docs/operations.md` L112. Change its text only when it attributes a timeout to an invalid token. Requirements: FR-016. Acceptance: the section names only the causes that the code produces. Verification: `ste-linter --config .ste-linter.toml --min-score 80 mist-ops-platform/docs/operations.md`. Status: partial.
- [ ] T014 Add the fragment `changelog.d/issue-4748-mist-token-timeout-unavailable.md` with one `Fixed` bullet. The bullet names issue 4748. Requirements: FR-016. Acceptance: the fragment follows `changelog.d/README.md`. Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4748-mist-token-timeout-unavailable.md`. Status: absent.

## Phase 5: Final Gates and Delivery

- [ ] T-LOCAL-GATES Files: `mist-ops-platform/src/shared/services/auth.py`, `mist-ops-platform/src/shared/mist/endpoints.py`, `mist-ops-platform/src/shared/mist/types.py`, `mist-ops-platform/tests/unit/api/test_auth.py`, `mist-ops-platform/tests/unit/api/test_session_security.py`, `mist-ops-platform/tests/unit/mist/test_list_status.py`, `mist-ops-platform/docs/operations.md` (when changed), and `changelog.d/issue-4748-mist-token-timeout-unavailable.md`. Run each applicable gate on the changed files. Requirements: SC-001, SC-004, SC-005, SC-007. Acceptance: each gate reports the expected result in the table below. Verification: the table below. Status: open.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile` on each changed Python file | No output |
| Ops lint | `ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise` in `mist-ops-platform/` | No finding |
| Ops tests | `pytest --cov=src --cov-fail-under=56 --timeout=120` in `mist-ops-platform/` | At least 390 tests collected. Coverage at least 56 percent. |
| Format | `python -m black --check` on each changed Python file | No file needs a change. The root Black configuration is unverified (open item U-9). |
| Security lint | `bandit -c pyproject.toml -r mist-ops-platform/src -q` | No finding at any severity |
| Symbols | `symbol-diff --base origin/main` on each changed Python file | No module-level name removed. Each added name is explained in the pull request (open item U-7). |
| STE | `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file | Each file scores 80 or above |
| Test quality | `test-quality-analyzer --gate` with the repository configuration | Zero new findings, if the analyzer scans ops tests (open item U-8) |

- [ ] T-PR Files: the eight paths in T-LOCAL-GATES. Commit with the message `fix(ops-platform): report a Mist transport fault as an unavailable Mist API`. Push branch `fix/4748-mist-token-timeout-unavailable`. Open a pull request. Its body contains `Closes #4748` and `Closes #4749`. Requirements: none (process gate). Acceptance: the title passes the Conventional Commits title check. Verification: `pytest --cov=src --cov-fail-under=56 --timeout=120` in `mist-ops-platform/` before the push. Status: open.
- [ ] T-REMOTE-CI Files (read only): `.github/workflows/ci.yml`. Watch the pull request checks with `gh pr checks <number> --watch`. Requirements: SC-004, SC-005. Acceptance: the jobs `pytest (ops platform)` and `Ruff (ops platform)` pass. Verification: `ci.yml` jobs `ops_platform_pytest` (L1122) and `ops_platform_ruff` (L1198). Status: open.
- [ ] T-MERGE Files: none. Add the `auto-merge` label to the pull request only after remote CI passes and the orchestrator authorizes the merge. Requirements: none (process gate). Acceptance: the squash merge closes #4748 and #4749. Verification: the same two `ci.yml` jobs as T-REMOTE-CI. Status: open.
