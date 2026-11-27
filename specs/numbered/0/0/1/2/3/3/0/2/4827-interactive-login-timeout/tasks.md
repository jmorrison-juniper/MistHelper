# Tasks: Interactive login request timeout

**Input**: Numeric record `specs/numbered/0/0/1/2/3/3/0/2/4827-interactive-login-timeout/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/contracts/login-request-timeout.md`, `design/quickstart.md`.

**Count**: 16 tasks. Status counts: verified-present 3, absent 9, open 4.

**Status values**: `verified-present` means the file or test exists on `main` at the blob SHA that the research file names. `absent` means the change is not on `main`. `open` means the gate or delivery step has not run.

## Format

`- [ ] ID [P?] [Requirement IDs] Title`. The `[P]` marker means the task can run in parallel with other `[P]` tasks. Each task names its files, its acceptance statement, one verification command from the local gates table, and its status.

## Phase 1: Verified state on main

- [x] T001 [FR-001] Confirm the removed import on `main`.
  - Files: `src/mist/access/auth/interactive/login_orchestrator.py` (delivered: blob `fd475be9467068e6c34a819697c3c46235801047`, merge commit `0c89de53d39caeae359b981b371d70b794a9b312`).
  - Acceptance: The file has no import of `src.mist.access.auth.session_timeout`. The path `src/mist/access/auth/session_timeout.py` is absent from the tree (RC-07, RC-08).
  - Verification: Tests gate `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py::TestImportResolution -q`.
  - Status: verified-present.

- [x] T002 [FR-002] Keep the import-resolution regression test.
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` lines 570 to 576 (delivered: blob `55133013405d582ce05fac7a36d6d11ed8112b64`).
  - Acceptance: Class `TestImportResolution` and method `test_every_imported_module_resolves` exist (RC-09, RC-10).
  - Verification: Tests gate `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py::TestImportResolution -q`.
  - Status: verified-present.

- [x] T003 [FR-010] Keep the token path unchanged.
  - Files: `src/foundation/support/refactors/initialize_mist_session.py` lines 35 and 179 (delivered: blob `b5e3c1ec102cbe08b1e68b0909f2da94318280ca`).
  - Acceptance: `MistSessionConfigurator.configure_once` remains called at line 179 (RC-11, RC-12). This change edits the file in no way.
  - Verification: Tests gate `python -m pytest tests/unit/refactors/test_initialize_mist_session.py -q`.
  - Status: verified-present.

## Phase 2: Tests first

- [ ] T004 [P] [FR-004, FR-005, FR-006, FR-007, FR-008, FR-009] Add class `TestRequestTimeout` and update the fake sessions.
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py`.
  - Work: (a) Add `request_timeout_seconds: int = 120` to `_make_orchestrator` at line 44, and pass it to the constructor at line 50. (b) Replace the fake sessions created with `MagicMock(spec=object)` at lines 295, 309, and 325 with `MagicMock(spec=["_new_session", "_session", "login_with_return"])`. (c) Add these nine test functions: `test_adapter_fills_missing_timeout`, `test_adapter_keeps_caller_timeout`, `test_adapter_never_retries`, `test_apply_wraps_each_transport_and_keeps_headers`, `test_loopback_stall_raises_read_timeout_within_bound`, `test_pipeline_bounds_transports_before_first_login`, `test_non_positive_timeout_is_rejected`, `test_authenticate_reports_invalid_timeout_as_value_error`, and `test_missing_transport_hook_fails_closed`.
  - Acceptance: Every new function fails before T008. The function `test_non_positive_timeout_is_rejected` has two parameter cases, 0 and -5. The test `test_apply_wraps_each_transport_and_keeps_headers` checks that the `Authorization` header and the prepared request URL do not change.
  - Verification: Tests gate `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q`.
  - Status: absent.
  - Depends on: none.

- [ ] T005 [P] [FR-003] Add the wiring test to the wave-9 initializer test.
  - Files: `tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py`.
  - Work: Add `test_orchestrator_receives_configured_request_timeout`. The test sets `MistHelper.API_REQUEST_TIMEOUT` to 75 with `monkeypatch.setattr`, runs `MistSessionInteractiveInitializer.initialize()`, and asserts `call_kwargs["request_timeout_seconds"] == 75`.
  - Acceptance: The test fails before T009 with a `KeyError` for `request_timeout_seconds`.
  - Verification: Tests gate `python -m pytest tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py -q`.
  - Status: absent.
  - Depends on: none.

- [ ] T006 [P] [FR-008] Add the SDK transport hook pin tests.
  - Files: `tests/integration/test_mistapi_sdk_compatibility.py`.
  - Work: Add class `TestInteractiveTransportHook` with two tests. The test `test_sdk_exposes_transport_hook_and_no_timeout_parameter` checks that `mistapi.APISession` has `_new_session` and that `timeout` is not a parameter of `APISession.__init__`. The test `test_login_paths_call_the_transport_hook` checks that the source of `APISession._process_login` and of `APISession.login_with_return` contains `self._new_session()`. Each failure message names the missing hook.
  - Acceptance: Both tests pass on mistapi 0.64.1 (RC-54, RC-55, RC-56, RC-60, RC-65).
  - Verification: Tests gate `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -q`.
  - Status: absent.
  - Depends on: none.

- [ ] T007 [P] [FR-003] Update the constructor calls in the interactive session test.
  - Files: `tests/unit/marvis/mist/access/auth/test_interactive_session.py` (constructors at lines 27 and 51).
  - Work: Add `request_timeout_seconds=120,` to each `LoginOrchestrator(` call (RC-50).
  - Acceptance: The two tests in the file pass after T008 and T009.
  - Verification: Tests gate `python -m pytest tests/unit/marvis/mist/access/auth/test_interactive_session.py -q`.
  - Status: absent.
  - Depends on: none.

## Phase 3: Implementation

- [ ] T008 [FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009] Implement the timeout seam in the orchestrator.
  - Files: `src/mist/access/auth/interactive/login_orchestrator.py`.
  - Work: Add `from requests.adapters import HTTPAdapter`. Add the constructor argument `request_timeout_seconds: int` and store it in `self.request_timeout_seconds`. Call `self._apply_request_timeout(apisession)` after the `apisession is None` guard, after line 107. Add the method `_apply_request_timeout`, the static methods `_timed_transport_factory`, `_mount_timeout_adapters`, and `_build_timeout_adapter`, and the nested class `RequestTimeoutAdapter`. Use the shapes in `plan.md`, section "Design of the Changed Methods". Add an inline comment to each new line, and a docstring to each new function.
  - Acceptance: Every test in T004 passes. Each new function has at most 25 lines and five logical blocks. The `send` override takes `**kwargs` and no more than five parameters in total.
  - Verification: Tests gate `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q`.
  - Status: absent.
  - Depends on: T004.

- [ ] T009 [FR-003] Pass the configured request timeout from the interactive initializer.
  - Files: `src/foundation/support/refactors/initialize_mist_session_interactive.py` (constructor call at line 48, keyword arguments at lines 49 to 51).
  - Work: Add `request_timeout_seconds=_MH.API_REQUEST_TIMEOUT,  # Pass the configured request timeout to each login transport.` after the `detect_msp_privileges` keyword at line 51.
  - Acceptance: The tests T005 and T007 pass. The symbol gate reports no removed module-level name for this file.
  - Verification: Tests gate `python -m pytest tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py tests/unit/marvis/mist/access/auth/test_interactive_session.py -q`.
  - Status: absent.
  - Depends on: T008.

## Phase 4: Documentation and changelog

- [ ] T010 [P] [FR-011] Correct the CONTRIBUTING row for `configure_session_timeout`.
  - Files: `documentation/CONTRIBUTING-MistHelper.md` (row at line 46).
  - Work: Replace the description with: "Compatibility entry point that changes no session. Token sessions use `MistSessionConfigurator`. Interactive login uses `LoginOrchestrator`."
  - Acceptance: The row describes both paths correctly. The row keeps the symbol name unchanged (RC-17, RC-22).
  - Verification: STE gate `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation/CONTRIBUTING-MistHelper.md`.
  - Status: absent.
  - Depends on: none.

- [ ] T011 [P] [FR-011] Document the request timeout in the README and the operator guide.
  - Files: `README.md` (one sentence after line 26), `documentation/operator-guide.md` (one new paragraph after line 589).
  - Work: In the README, add: "A login request that gets no answer within `API_REQUEST_TIMEOUT` seconds fails with a message. The default is 120 seconds." In the operator guide, add one paragraph with two sentences about the variable and its default, and one caution: "Caution: a value of 0 or less fails each login at once. Use a positive whole number."
  - Acceptance: Each sentence has at most 25 words, and no sentence has a semicolon. The README and the guide name the same variable and the same default (RC-25, RC-27).
  - Verification: STE gate `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 README.md documentation/operator-guide.md`.
  - Status: absent.
  - Depends on: none.

- [ ] T012 [P] [FR-012] Add the changelog fragment.
  - Files: `changelog.d/issue-4827-interactive-login-timeout.md` (new file).
  - Work: Add one `###` heading "Interactive login request timeout" and one bullet: "- **Fixed**: Each interactive login request stops after `API_REQUEST_TIMEOUT` seconds, which defaults to 120. Issue #4827."
  - Acceptance: The changelog guard reads the file and passes (RC-28, RC-29, RC-45).
  - Verification: Tests gate `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`.
  - Status: absent.
  - Depends on: none.

## Phase 5: Gates and delivery

- [ ] T-LOCAL-GATES [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, SC-002, SC-003] Run each local gate that applies to the changed files.
  - Files: `src/mist/access/auth/interactive/login_orchestrator.py`, `src/foundation/support/refactors/initialize_mist_session_interactive.py`, the changed test files, `tests/integration/test_mistapi_sdk_compatibility.py`, the changed documents, and the changelog fragment.
  - Work: Run each command in `design/quickstart.md`, section 5, in order. Run the test-quality analyzer after the local commit. Record each command and its result in the pull request body. The menu reference gate and the ops gates do not apply. FR-013 is checked by `tests/guardrails/test_src_domain_structure.py`, which the tests gate includes.
  - Acceptance: Each gate reports its expected result. The pylint score is 9.5 or above. The symbol gate lists any added import in the pull request body (analysis item U-6).
  - Verification: Code quality gate `pylint src/ --fail-under=9.5`.
  - Status: open.
  - Depends on: T004, T005, T006, T007, T008, T009, T010, T011, T012.

- [ ] T-PR [FR-012] Commit, rebase, push, and open the pull request.
  - Files: each file in the change map of `plan.md`, staged by explicit path.
  - Work: (a) Add the `in-progress` label to issue #4827. (b) Create branch `fix/4827-interactive-login-timeout` from `main` in a worktree. (c) Stage each changed file by its explicit path. (d) Commit with the subject `fix(auth): apply the request timeout to interactive login`, a body with `Closes #4827`, and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`. (e) Rebase onto `origin/main`, rerun the affected gates, and push. (f) Open the pull request with the commit subject as its title. The body holds `Closes #4827`, the gate results, the file list, and the rollback note from `plan.md`.
  - Acceptance: The pull request targets `main`. Its title passes the Conventional Commits title check. The pull request changes no file that open PR #4208 changes.
  - Warning: Do not push to this branch after the squash merge. A later commit becomes an orphan that no merge picks up.
  - Verification: Tests gate `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q` before the push.
  - Status: open.
  - Depends on: T-LOCAL-GATES.

- [ ] T-REMOTE-CI [SC-005] Watch the remote checks of the pull request.
  - Files: none. The remote checks read the pull request on GitHub.
  - Work: Run `gh pr checks <number> --watch`. Read each failing job. Repair the cause, and push a new commit only when the cause needs a code change.
  - Acceptance: Every required check passes on the latest commit, and CodeQL passes too.
  - Verification: Coverage gate `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` predicts the coverage shards. The remote check result is the acceptance source.
  - Status: open.
  - Depends on: T-PR.

- [ ] T-MERGE [SC-005, SC-006] Enable auto-merge after the orchestrator authorizes the merge.
  - Files: none.
  - Work: Confirm that the remote checks pass on the latest commit. Wait for the orchestrator authorization. Add the `auto-merge` label. Squash-merge the pull request. Remove the branch and the worktree. Wait for the `container-build.yml` run on the merged commit. Confirm that the image revision label equals the merge commit SHA (constitution Principle IV, steps 10 and 11).
  - Acceptance: The merge commit exists on `main`. The `container-build.yml` run on that commit passes. The image revision label equals the merge commit SHA.
  - Warning: A squash merge closes the pull request. A commit pushed after the merge becomes an orphan. File a new issue for any later fix.
  - Verification: Test quality gate `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` must print `gate: 0 new findings vs baseline`.
  - Status: open.
  - Depends on: T-REMOTE-CI.

## Dependency summary

- T004, T005, T006, and T007 run first. They touch different files, so they run in parallel.
- T008 follows T004. T009 follows T008.
- T010, T011, and T012 run in parallel with the tests.
- T-LOCAL-GATES follows every implementation and documentation task.
- T-PR, T-REMOTE-CI, and T-MERGE run in that order.
