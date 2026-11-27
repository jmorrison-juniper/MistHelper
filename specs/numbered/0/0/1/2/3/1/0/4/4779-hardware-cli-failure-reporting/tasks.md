# Tasks: Hardware CLI failure reporting

**Input**: `plan.md`, `spec.md`, `design/research.md`, `design/contracts/cli-failure-contract.md`, `design/data-model.md`, and `design/quickstart.md`.

**Status legend**: `open` means not started. `verified-present` means a remote check confirms the change on GitHub. `partial` means the local commit holds part of the change. `absent` means neither the local commit nor GitHub holds the change.

**Format**: `[ID] [P?] Description`. `[P]` marks a task that touches a different file from every other open task.

**Line references** point to the branch copy at commit `8140bb37c`, unless a row names `main`.

## Phase 1: Verify the Starting Point

- [ ] **T001** Reproduce the three regression cases on the publication branch.
  - Requirements: FR-001, FR-002, FR-004. Tests: SC-001.
  - Files: `tests/unit/websocket_streams/web/hardware/test_cli.py` (read) and `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py` (read).
  - Acceptance: Run quickstart step 3. Record the exit code and counts. The expected result is three passed. A failure stops the work until its cause is known.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: open.

- [ ] **T002** Rebase the publication branch onto `origin/main`.
  - Requirements: FR-009.
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py`, `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py` (main changes), and the ten overlap files listed in `analysis.md` item A-13.
  - Acceptance: Keep `csv`, `master-xml`, and `csv-master-xml` from `main`. Keep `xml`, `json`, and `both` from the branch. No conflict marker remains.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: open.

## Phase 2: Harden the Failure Boundary

- [ ] **T003** Add the admission state to the workflow.
  - Requirements: FR-005, FR-007.
  - Files: `cli.py` (modify), `HardwareCliWorkflow.__init__` (lines 109 to 119).
  - Acceptance: Add attribute `admission` with the values `not_started`, `uncertain`, and `admitted`. Set `uncertain` before the start request. Set `admitted` after a verified reply.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: absent. No attribute exists in lines 109 to 119.

- [ ] **T004** Validate the start reply.
  - Requirements: FR-008.
  - Files: `cli.py` (modify), `HardwareCollectionCli._collect` (lines 101 to 102).
  - Acceptance: Raise `StreamRequestError` with code `admission_unverified` when the reply is not a mapping. Raise it when `session_id` is not a non-empty string. Keep the state `uncertain`.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: absent. Line 102 assigns `session_id` with no check.

- [ ] **T005** Re-raise programming errors at both boundaries.
  - Requirements: FR-001, FR-003.
  - Files: `cli.py` (modify), `run` (lines 68 to 71) and `Completion.cancel` (line 243).
  - Acceptance: Add `except (NotImplementedError, RecursionError): raise` before each operational clause. No clause catches `TypeError`.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: absent. The operational clauses at lines 70 and 243 catch both classes.

- [ ] **T006** Print cautions and log the admission state.
  - Requirements: FR-002, FR-005, FR-006, FR-007.
  - Files: `cli.py` (modify), `_failure` and `_incomplete` (lines 76 to 86).
  - Acceptance: Replace `Admitted: %s` with `Admission state: %s` in the error log. Print the caution from the contract for `uncertain` and `admitted`. Print no caution for `not_started`.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: partial. The stable-cause line exists at line 80. The caution and the new log text are absent.

- [ ] **T007** Add action logs around the preview and start requests.
  - Requirements: FR-006.
  - Files: `cli.py` (modify), `_collect` (lines 89 to 103).
  - Acceptance: Write one info line before the preview request and one before the start request. Write one debug line after each. Log counts and states only.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: absent. No log call exists in lines 89 to 103.

## Phase 3: Tests

- [ ] **T008** Extend the never-retry test.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006. Tests: SC-001 and SC-002.
  - Files: `tests/unit/websocket_streams/web/hardware/test_cli.py` (modify). The parametrize decorator is at line 129, and the function is at line 130.
  - Acceptance: Parametrize over `OSError`, `RuntimeError`, `TypeError`, `NotImplementedError`, `RecursionError`, and `KeyboardInterrupt`. Keep the IDs of `OSError`, `RuntimeError`, and `TypeError`. Check the status, cause, caution, one start request, and log text. Adds 3 new cases and changes 3.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: partial. Three of the six cases exist at lines 129 to 142.

- [ ] **T009** Refuse a pre-admission operational failure without a caution.
  - Requirements: FR-007. Tests: SC-002.
  - Files: `test_cli.py` (modify). The parametrize decorator is at line 110, and the function is at line 121.
  - Acceptance: Add one case where the first prompt raises `OSError`. Check that no start request runs, no directory prints, and no caution prints. Adds 1 new case.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: absent.

- [ ] **T010** Add one function for admission and polling failures.
  - Requirements: FR-003, FR-005, FR-008. Tests: SC-002.
  - Files: `test_cli.py` (modify). Add one new function with three parametrized cases.
  - Acceptance: Case `reply_without_session` expects cause `admission_unverified` and the uncertain caution. Case `poll_failure` expects the admitted caution after an `OSError` and no directory. Case `cancel_programming_error` expects `NotImplementedError` to propagate. Adds 3 new cases.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: absent.

## Phase 4: Documentation

- [ ] **T011** [P] Update the operator guide and the changelog fragment.
  - Requirements: FR-010. Checks: C-3.
  - Files: `documentation/operator-guide.md` (section `#### Reusable CLI class`, line 423) and `changelog.d/issue-4773-transceiver-master-report.md`.
  - Acceptance: Describe the two cautions, the cause `admission_unverified`, and the class-name causes. In the fragment, name issue 4773 in each bullet and keep the file name. Do not edit `CHANGELOG.md`.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md changelog.d/issue-4773-transceiver-master-report.md`
  - Status: partial. The CLI section exists at line 423 and has no caution text. The fragment uses two change-type headings, and its bullets name no issue.

## Phase 5: Gates and Publication

- [ ] **T-LOCAL-GATES** Run every applicable local gate.
  - Requirements: SC-001, SC-002, SC-003. Checks: C-4.
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py`, `src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py`, `tests/unit/websocket_streams/web/hardware/test_cli.py`, `documentation/operator-guide.md`, and `changelog.d/issue-4773-transceiver-master-report.md`, plus the record folder `specs/numbered/0/0/1/2/3/1/0/4/4779-hardware-cli-failure-reporting/`.
  - Acceptance: Run each gate that plan.md marks `Yes`. Record each command, exit code, and count. Record each gate that plan.md marks `No` with its reason. A gate that cannot run stops this task.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: open. Depends on T008, T009, T010, and T011.

- [ ] **T-PR** Commit, push, and open the publication pull request.
  - Requirements: FR-009. Checks: C-1.
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py`, `src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py`, `tests/unit/websocket_streams/web/hardware/test_cli.py`, `documentation/operator-guide.md`, and `changelog.d/issue-4773-transceiver-master-report.md`, plus the record folder `specs/numbered/0/0/1/2/3/1/0/4/4779-hardware-cli-failure-reporting/`.
  - Acceptance: Add label `in-progress` to issue 4779. Issue 4773 already carries it. Commit the repair as `fix(web-portal): report uncertain hardware CLI admission`. Push `feat/4773-transceiver-master-report`. Open the pull request with title `feat(web-portal): add EX transceiver master report and CLI collection`. The body contains `Closes #4779`, `Refs #4773`, and the gate results. Keep the fragment name.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] **T-REMOTE-CI** Watch CI and verify the remote tree.
  - Requirements: FR-011, SC-004. Checks: C-2.
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py`, `src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py`, `tests/unit/websocket_streams/web/hardware/test_cli.py`, `documentation/operator-guide.md`, and `changelog.d/issue-4773-transceiver-master-report.md`.
  - Acceptance: Run `gh pr checks --watch` from the publication worktree. The command reads the pull request that T-PR opened. Each required check shows success. Read the remote tree of the pushed commit and record each changed path with its blob SHA.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: open. Depends on T-PR.

- [ ] **T-MERGE** Enable auto-merge and merge.
  - Requirements: FR-009. Checks: C-1.
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py`, `src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py`, `tests/unit/websocket_streams/web/hardware/test_cli.py`, `documentation/operator-guide.md`, and `changelog.d/issue-4773-transceiver-master-report.md`. The worktree `MistHelper-feat-4773` is removed after the merge.
  - Acceptance: Enable auto-merge only after each required check passes and the orchestrator authorizes the merge. Squash-merge the pull request. Confirm that issue 4779 closes. Remove the worktree after the status check reports a clean state.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`
  - Status: open. Depends on T-REMOTE-CI.

Warning: removing a worktree deletes its uncommitted files. Confirm a clean status before removal.

Caution: a commit pushed after a squash merge becomes an orphan. Open a new issue for any later fix.

## Dependencies

- T001, then T002, then T003, then T004, then T005, then T006, then T007. These tasks change `cli.py` in order.
- T006 before T008, T009, T010, and T011.
- T008, then T009, then T010. These tasks change `test_cli.py` in order.
- T011 runs in parallel with the `cli.py` and `test_cli.py` work after T006 supplies the final text.
- T-LOCAL-GATES after T008, T009, T010, and T011. Then T-PR, T-REMOTE-CI, and T-MERGE in order.

## Counts

- Numbered tasks: 11 (T001 to T011). Final tasks: 4.
- New pytest cases: 7. Changed pytest cases: 3. Planned pytest cases: 10.
