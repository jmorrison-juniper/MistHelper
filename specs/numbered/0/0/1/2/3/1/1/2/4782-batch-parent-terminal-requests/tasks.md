# Tasks: Batch Parent Terminal Requests

**Input**: Records in `specs/numbered/0/0/1/2/3/1/1/2/4782-batch-parent-terminal-requests/`. Read `spec.md`, `plan.md`, and `design/research.md` first.

**Prerequisites**: plan.md (required), spec.md (required), research.md (required), design/contracts/session-terminal-routes.md (required).

**Format**: `[ID] [P?] Description`. `[P]` marks a task that is safe in parallel. Each task names its requirements, files, acceptance statement, verification command, and status. Status values are `open`, `verified-present`, `partial`, and `absent`.

**Code task rule**: A code task uses the Tests row of the local gates table in `plan.md`. Precondition and pull request tasks use the commands named in the implementation brief.

## Phase 1: Preconditions and verification

### T001 [P] Confirm the ownership hold release

- **Requirements**: FR-007.
- **Files**: `tests/e2e/websockets_tab/test_websockets_page.py` (held by the retained #4773 work).
- **Acceptance**: The owner posts a release on issue #4782 or issue #4773 that names this file. No edit starts before the release is recorded.
- **Verification**: `gh issue view 4782 -R jmorrison-juniper/MistHelper --json comments --jq ".comments[].body"`. This is a read-only precondition check. The local gates table has no command for it.
- **Status**: open.

### T002 [P] Re-check the guard on main

- **Requirements**: FR-001, FR-002, FR-003.
- **Files**: `src/mist/realtime/websocket_streams/web/static/websockets.js` (read only).
- **Acceptance**: The contents API returns blob `c0b4f439743280511cf82c00e9ca23a2e1c2a9d4`, and line 1894 holds the `multi_site` guard. If the blob differs, stop and repeat research rows R-17 and R-64.
- **Verification**: `gh api "repos/jmorrison-juniper/MistHelper/contents/src/mist/realtime/websocket_streams/web/static/websockets.js?ref=main" --jq ".sha"`. This is a read-only precondition check.
- **Status**: verified-present (research rows R-17 and R-64, checked 2026-11-26).

## Phase 2: Regression tests

### T003 Add the request helper and extend the batch parent test

- **Requirements**: FR-001, FR-002, FR-005. Success criterion SC-001.
- **Files**: `tests/e2e/websockets_tab/test_websockets_page.py`. Add `session_route_requests` after `open_page` (line 753). Modify `test_a_batch_parent_of_a_shell_action_is_not_opened_as_a_terminal` (lines 1562 to 1573).
- **Acceptance**: The test fails when any request URL with the session route prefix contains `/resize` or `/terminal`. The existing `terminal_reads` assertion stays.
- **Verification**: With `UPGRADE_PORTAL_E2E_STRICT` set to `1`, run `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k batch_parent_of_a_shell_action -v`.
- **Status**: open. Depends on T001.

### T004 Add the reload test

- **Requirements**: FR-003, FR-005. Success criterion SC-002.
- **Files**: `tests/e2e/websockets_tab/test_websockets_page.py`. Add `test_a_batch_parent_restored_after_reload_sends_no_terminal_or_resize_request` after the batch parent test.
- **Acceptance**: After a reload, the restored batch parent sends no terminal read and no matching request. The test waits for the batch progress panel before it asserts.
- **Verification**: With `UPGRADE_PORTAL_E2E_STRICT` set to `1`, run `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k restored_after_reload -v`.
- **Status**: open. Depends on T003.

### T005 Prove that the tests can fail

- **Requirements**: FR-005. Success criterion SC-004.
- **Files**: `src/mist/realtime/websocket_streams/web/static/websockets.js` in a throwaway worktree only, with the guard at line 1894 removed. Tests: `tests/e2e/websockets_tab/test_websockets_page.py`.
- **Acceptance**: With the guard removed, both tests fail. With the guard restored, both tests pass. Remove the throwaway worktree after the run.
- **Verification**: `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k batch_parent -v`, run once without the guard and once with it.
- **Status**: open. Depends on T003 and T004.

### T006 Confirm the existing terminal journeys still pass

- **Requirements**: FR-004, FR-006. Success criterion SC-003.
- **Files**: `tests/e2e/websockets_tab/test_websockets_terminal.py`. Read and run only. It holds the `test_j5_resize` function at line 226 and the `not_terminal` case at line 749.
- **Acceptance**: `test_j5_resize` and the `not_terminal` case pass.
- **Verification**: With `UPGRADE_PORTAL_E2E_STRICT` set to `1`, run `python -m pytest tests/e2e/websockets_tab/test_websockets_terminal.py -k "j5_resize or not_terminal" -v`.
- **Status**: open. Depends on T003.

## Phase 3: Final tasks

### T-LOCAL-GATES Run every applicable local gate

- **Requirements**: FR-001 through FR-007. Success criteria SC-001 through SC-005.
- **Files**: `tests/e2e/websockets_tab/test_websockets_page.py` and each changed Markdown file under this record.
- **Acceptance**: Each applicable gate passes with its expected result. Each gate that does not apply has a reason in `plan.md`.
- **Verification**: Run in this order.
  1. `python -m ruff check .` prints `All checks passed`.
  2. `python -m black --check .` reports no file that needs a change.
  3. `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py` with `UPGRADE_PORTAL_E2E_STRICT=1` passes.
  4. `python -m pytest tests/guardrails` passes.
  5. `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` prints `gate: 0 new findings vs baseline`.
  6. `symbol-diff --base origin/main tests/e2e/websockets_tab/test_websockets_page.py` exits with code 0.
  7. `check-citations src tests` resolves each citation.
  8. `ste-linter --config .ste-linter.toml --min-score 80` scores each changed Markdown file at 80 or above.
- A failed local gate blocks the pull request. Repair the cause and run the gate again.
- **Status**: open. Depends on T003, T004, T005, and T006.

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-007. Success criterion SC-005.
- **Files**: `tests/e2e/websockets_tab/test_websockets_page.py` and the record folder `specs/numbered/0/0/1/2/3/1/1/2/4782-batch-parent-terminal-requests/`. Add files by explicit path only.
- **Acceptance**: Add the `in-progress` label before you create the branch. Branch `fix/4782-batch-parent-terminal-requests` starts from `origin/main`. The commit subject is `test(web-portal): guard batch parent terminal requests`. The body contains `Closes #4782`. The body states the README rule 4 exemption (D-6). The pull request lists only the two paths. The commit message ends with `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json files,title,body --jq ".files[].path"` shows only the two paths.
- **Warning**: Do not force-push to `main`. A force push removes commits that other agents rely on.
- **Status**: open. Depends on T-LOCAL-GATES.

### T-REMOTE-CI Watch the remote checks

- **Requirements**: FR-004. Success criterion SC-003.
- **Files**: None changed. Read the checks of the pull request.
- **Acceptance**: Every required check passes. This includes the `websockets-tab` shard (`ci.yml` line 797) and CodeQL.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`.
- **Status**: open. Depends on T-PR.

### T-MERGE Enable auto-merge after authorization

- **Requirements**: FR-007. Success criterion SC-005.
- **Files**: None changed.
- **Acceptance**: The `auto-merge` label is added only after every check is green and the orchestrator authorizes the merge. The pull request merges by squash. Issue #4782 closes.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state --jq ".state"` returns `MERGED`. `gh issue view 4782 -R jmorrison-juniper/MistHelper --json state --jq ".state"` returns `CLOSED`.
- **Caution**: Auto-merge merges the pull request without another review. A later revert undoes the change. Add the label only after authorization.
- **Status**: open. Depends on T-REMOTE-CI.

## Dependencies

- T001 gates T003 and every later edit task.
- T002 runs before T003 and has no other prerequisite.
- T003 gates T004, T005, and T006.
- T003, T004, T005, and T006 gate T-LOCAL-GATES.
- T-LOCAL-GATES gates T-PR, T-PR gates T-REMOTE-CI, and T-REMOTE-CI gates T-MERGE.

## Count

Ten tasks: T001 through T006, then T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
