# Tasks: Raw shell history test failure (issue 3767)

**Input**: Numeric record `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/`. Read `spec.md` and `plan.md` first.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/quickstart.md`.

**Status values**: `open`, `verified-present`, `partial`, or `absent`. A status of `absent` means the code or the evidence does not exist yet.

## Task Summary

| ID | Status | Requirements | Depends on |
| - | - | - | - |
| T001 | verified-present | FR-001 | none |
| T002 | verified-present | FR-002 | none |
| T003 | verified-present | FR-003 | none |
| T004 | verified-present | FR-005 | none |
| T005 | verified-present | FR-006 | none |
| T006 | open | FR-004 | T001, T004 |
| T007 | open | FR-004 | T006 |
| T008 | absent | FR-007, FR-008 | T007 and owner authorization |
| T009 | absent | FR-008 | T008 |
| T-LOCAL-GATES | open | FR-009, FR-010 | T007, and T009 when T008 applies |
| T-PR | open | FR-010 | T-LOCAL-GATES |
| T-REMOTE-CI | open | FR-010 | T-PR |
| T-MERGE | open | FR-010 | T-REMOTE-CI and orchestrator authorization |

## Phase 1: Evidence (independent, parallel)

### T001 [P] Confirm the failing test identity

- **Requirements**: FR-001, SC-001
- **Files**: `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` (accepted main blob `0fc79d8b799f2ce0704580eb62ade41f9fb25869`)
- **Acceptance**: Research rows R-01 to R-03 name lines 454, 108, and 464 of accepted main.
- **Verification**: `python -m pytest tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`
- **Status**: verified-present

### T002 [P] Record the CI scan result

- **Requirements**: FR-002, SC-001
- **Files**: `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Acceptance**: The CI scan table lists the run count, the root-units failure count, the PASSED count, and the FAILED count.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Status**: verified-present

### T003 [P] Record the branch lines at both commits

- **Requirements**: FR-003
- **Files**: Accepted main source files under `src/websocket_streams/live/`: `runners/shell/lifecycle/outcomes.py`, `runners/shell/lifecycle/reading.py`, `transport/runtime/reader/keepalive.py`, and `transport/runtime/reader/frame_reader.py`. Current main holds the moved files under `src/mist/realtime/websocket_streams/`.
- **Acceptance**: Research rows R-08 to R-22, R-31 to R-34, and R-67 to R-74 name each line and each blob SHA.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Status**: verified-present

### T004 [P] Record the environment confounders

- **Requirements**: FR-005
- **Files**: `pyproject.toml` (line 23), `.github/workflows/ci.yml` (line 77), `documentation/development-setup.md` (line 13)
- **Acceptance**: Research rows R-36, R-37, and R-53 cite these lines. Research row R-29 records that `coverage.ini` is absent on current main.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Status**: verified-present

### T005 [P] Record the candidate delta

- **Requirements**: FR-006
- **Files**: `tests/unit/websocket_streams/live/transport/fake_mist_cloud/server.py` (candidate lines 198 and 199, and current main line 206), `tests/unit/websocket_streams/live/transport/test_fake_cloud_on_connect_3760.py` (candidate only)
- **Acceptance**: Research rows R-24 to R-28 record the blob SHAs. Row R-28 records the absence of the new test file on current main.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Status**: verified-present

## Phase 2: Controlled diagnosis (one run, no repository edit)

### T006 Run the controlled reproduction

- **Requirements**: FR-004, SC-002
- **Files**: No repository file changes. The run writes to `test-artifacts/3767/`.
- **Depends on**: T001 and T004.
- **Acceptance**: The run uses Python 3.15.2. The log file `test-artifacts/3767/controlled-run.log` exists. The run count is exactly one.
- **Verification**: `python -m pytest tests/unit/websocket_streams tests/contract/websocket_streams -x --log-cli-level=DEBUG`. Use the full command with its options in `design/quickstart.md`, section 5.

- **Requirements**: FR-004, SC-002
- **Files**: `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Depends on**: T006.
- **Acceptance**: Research section "Controlled run result" names the signature, the matched hypothesis, and the reason. If the run passes, the section states "not reproduced".
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/design/research.md`
- **Status**: open

## Phase 3: Authorized fix (conditional)

### T008 Change the close timing of the raw-output device

- **Requirements**: FR-007, FR-008
- **Files**: `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` (current main lines 179-192, class `RawOutputDevice`, method `on_connect`)
- **Depends on**: T007 confirms hypothesis H1, and the owner authorizes the change.
- **Acceptance**: The device sends the close frame without the 0.2-second delay. The assertion lines do not change. Each changed line has an inline comment.
- **Verification**: `python -m pytest tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`
- **Status**: absent

### T009 Check the test quality and the assertions

- **Requirements**: FR-008, SC-003
- **Files**: `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`, `.github/test-quality-config.toml`, `.github/test-quality-baseline.json`
- **Depends on**: T008.
- **Acceptance**: The analyzer prints `gate: 0 new findings vs baseline`. The diff keeps the `FINISHED` assertion and the exact history assertion.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- **Status**: absent

## Phase 4: Delivery gates

### T-LOCAL-GATES Run the local gates for the changed files

- **Requirements**: FR-009, FR-010
- **Files**: Each Markdown file in the record folder. The test file only when T008 applies.
- **Depends on**: T007. T009 also applies when T008 applies.
- **Acceptance**: Each Markdown file scores 80 or above. When T008 applies, the Lint, Format, Types, Tests, and Test quality gates pass.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/spec.md` (run the same command for each Markdown file)
- **Status**: open

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-010
- **Files**: The eight record files, copied from the draft folder to `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/`. The test file only when T008 applies.
- **Depends on**: T-LOCAL-GATES.
- **Acceptance**: Add the label `in-progress` to issue 3767 before creating the branch. The commit message uses `docs(specs): record raw shell history failure diagnosis`. The branch is `docs/3767-raw-shell-history-failed`. The pull request body contains `Closes #3767`.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/spec.md`
- **Status**: open

### T-REMOTE-CI Watch the remote CI run

- **Requirements**: FR-010
- **Files**: None.
- **Depends on**: T-PR.
- **Acceptance**: Each required check passes on the latest commit of the pull request. The `pytest coverage shard (root-units)` job passes.
- **Verification**: `python -m pytest tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` when T008 applies. For a record-only change, the STE command of T-LOCAL-GATES applies.
- **Status**: open

### T-MERGE Merge after authorization

- **Requirements**: FR-010
- **Files**: None.
- **Depends on**: T-REMOTE-CI and the orchestrator authorization.
- **Acceptance**: Auto-merge is enabled only after the remote CI passes and the orchestrator authorizes the merge. The branch is deleted after the squash merge.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/spec.md`
- **Status**: open

Caution: The squash merge closes issue 3767 when the pull request body keeps `Closes #3767`. The orchestrator reviews this point before merge.

## Dependencies and Execution Order

- Tasks T001 to T005 run in parallel. They need only GET requests and read access.
- Task T006 starts after T001 and T004 finish. It runs once.
- Task T008 starts only after T007 confirms H1 and the owner authorizes the change.
- Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in that order.
