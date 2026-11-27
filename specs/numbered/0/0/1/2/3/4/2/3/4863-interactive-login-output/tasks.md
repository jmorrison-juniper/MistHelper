# Tasks: Interactive Login Output

**Input**: Design documents in `specs/numbered/0/0/1/2/3/4/2/3/4863-interactive-login-output/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: Write each test task before its implementation task, and see the new test fail first. Use fake SDK sessions and patched HTTP for every automated check. The live login check is manual and read-only.

**Ownership**: Do not modify `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. The fragment under `changelog.d/` is the only release note.

**Environment**: Run Python from the `.venv` of the worktree. Run commands from the worktree root.

## Format

- **[P]**: The task can run in parallel with other [P] tasks of its phase, because it edits a different file.
- **[US]**: The user story that the task serves.
- **Requirements**: The `FR` and `SC` identifiers from `spec.md`.
- **Status**: `open` until the verification command passes. Then the status changes to `verified-present`.

## Phase 1: Setup

- [ ] T001 Create the branch `fix/4863-interactive-login-output` from `origin/main` in a new worktree.
  - Requirements: FR-020
  - Files: none
  - Acceptance: The worktree starts at the current `origin/main` commit. Each cited line in `plan.md` matches its remote line.
  - Verification: `git -C <worktree> rev-parse --abbrev-ref HEAD` prints `fix/4863-interactive-login-output`.
  - Status: open

- [ ] T002 [P] Record the baseline result of the interactive login test folder on the untouched worktree.
  - Requirements: FR-011
  - Files: `tests/unit/marvis/mist/access/auth/interactive/`
  - Acceptance: The baseline lists each test that passes before the change. The output stays in the session draft folder, not in the repository.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive -q`
  - Status: open

## Phase 2: User Story 1 - Cloud menu and banners as direct output

- [ ] T003 [P] [US1] Add three tests in the new module `tests/unit/marvis/mist/access/auth/interactive/test_clouds.py`.
  - Requirements: FR-001, FR-002
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_clouds.py` (new)
  - Acceptance: The tests are `test_render_menu_prints_direct_output_without_warning`, `test_default_cloud_choice_echoes_selection`, and `test_eof_at_cloud_prompt_returns_none`. They fail on the untouched code.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_clouds.py -q`
  - Status: open

- [ ] T004 [US1] Change the menu lines of `clouds.py` to `echo`, and write the inline comments for each new line.
  - Requirements: FR-001, FR-002, FR-017
  - Files: `src/mist/access/auth/interactive/clouds.py`
  - Depends on: T003
  - Acceptance: Lines 59 and 66 to 81 use `echo`. No `logger.warning` call remains in `_render_menu`. The three tests pass.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_clouds.py -q`
  - Status: open

## Phase 3: User Story 2 - Login success and 2FA success without warning labels

- [ ] T005 [P] [US2] Update five existing tests in `test_login_orchestrator.py`.
  - Requirements: FR-004, FR-009, FR-014
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py`
  - Acceptance: These tests change: `test_happy_path_delegates_to_pipeline` (line 183), `test_returns_session_and_clears_token` (line 368), `test_none_when_user_aborts` (line 446), `test_with_grants_populates_state_and_echoes_each` (line 583), and `test_no_grants_prints_org_level_message` (line 598). The constructor assertion expects `console_log_level=30`.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q -k "happy_path or clears_token or user_aborts or echoes_each or org_level"`
  - Status: open

- [ ] T006 [P] [US2] Add five tests in `test_login_orchestrator.py`.
  - Requirements: FR-006, FR-007, FR-008, FR-009, FR-010, FR-016
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py`
  - Acceptance: The tests are `test_accepted_2fa_code_prints_success_line`, `test_refused_2fa_code_prints_no_success_line`, `test_sentinel_password_and_2fa_code_stay_out_of_output`, `test_finalize_session_prints_success_without_warning`, and `test_sdk_success_line_stays_off_console`. The real-SDK test also confirms that a refused password prints the SDK error line. It restores the SDK console level in teardown. The five tests fail on the untouched code.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q -k "2fa or sentinel or finalize_session or sdk_success"`
  - Status: open

- [ ] T007 [US2] Change `login_orchestrator.py` as the file change map in `plan.md` states.
  - Requirements: FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-014, FR-017
  - Files: `src/mist/access/auth/interactive/login_orchestrator.py`
  - Depends on: T005, T006
  - Acceptance: Five progress lines are deleted. The console level is 30. The banner, success, and MSP summary lines use `echo`. The 2FA success line follows the debug record. `_handle_two_factor` keeps 25 lines or fewer.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q`
  - Status: open

- [ ] T008 [US2] Review each remaining warning call in `login_orchestrator.py`.
  - Requirements: FR-011
  - Files: `src/mist/access/auth/interactive/login_orchestrator.py`
  - Depends on: T007
  - Acceptance: Each remaining `logger.warning` or `logging.warning` call prints an `X` failure line. No success, banner, or progress line remains at WARNING.
  - Verification: `rg -n "logger.warning|logging.warning" src/mist/access/auth/interactive/login_orchestrator.py`
  - Status: open

## Phase 4: User Story 4 - MSP picker as direct output

- [ ] T009 [P] [US4] Update five existing tests and add one test in `test_msp_org_selector.py`.
  - Requirements: FR-012, FR-013
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py`
  - Acceptance: These tests change: `test_select_single_msp_autopicks_and_selects_org` (line 49), `test_fetch_msp_orgs_empty_data_returns_empty` (line 226), `test_paginated_pick_quit_shortcut` (line 277), `test_render_msp_menu_prints_all_msps` (line 328), and `test_render_page_shows_multi_page_hint` (line 343). The autopick test also asserts the organization progress info record. The new test is `test_banner_and_selection_print_direct_output`.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py -q`
  - Status: open

- [ ] T010 [US4] Change `msp_org_selector.py` as the file change map in `plan.md` states.
  - Requirements: FR-012, FR-013, FR-017
  - Files: `src/mist/access/auth/interactive/msp_org_selector.py`
  - Depends on: T009
  - Acceptance: The banner, menus, skip lines, and selection lines use `echo`. Line 101 writes an info record. The invalid input and invalid number lines keep their warning records.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py -q`
  - Status: open

## Phase 5: User Story 3 and User Story 5 - Cancel record and documentation

- [ ] T011 [P] [US3] Add `test_cancel_logs_info_record` to the switch flow test module.
  - Requirements: FR-015
  - Files: `tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py`
  - Acceptance: The test calls the real `MistHelper.prompt_switch_login_confirmation` with the fake answer `n`. It asserts one INFO record and no warning record. The test fails on the untouched code.
  - Verification: `python -m pytest tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py -q -k cancel_logs_info`
  - Status: open

- [ ] T012 [US3] Change line 2702 of `MistHelper.py` from `logger.warning` to `logger.info`.
  - Requirements: FR-015, FR-017
  - Files: `MistHelper.py`
  - Depends on: T011
  - Acceptance: The cancel record is an info record. The `echo("  Cancelled.")` line at 2701 does not change. The inline comment names the channel.
  - Verification: `python -m py_compile MistHelper.py`, then `python -m pytest tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py -q`
  - Status: open

- [ ] T013 [P] [US5] Add the 2FA success sentence to `documentation/operator-guide.md`.
  - Requirements: FR-019
  - Files: `documentation/operator-guide.md`
  - Acceptance: The paragraph before the text that begins with "After the login" says that MistHelper prints `+ 2FA verification successful` after Mist accepts the code.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - Status: open

- [ ] T014 [P] [US5] Add the changelog fragment `changelog.d/issue-4863-interactive-login-output.md`.
  - Requirements: FR-019
  - Files: `changelog.d/issue-4863-interactive-login-output.md` (new)
  - Acceptance: The file follows the format of `changelog.d/issue-4755-2fa-login.md`. It holds one heading and one `Fixed` bullet that names issue 4863.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4863-interactive-login-output.md`
  - Status: open

## Phase 6: Verification

- [ ] T015 [US5] Run the redaction and SDK tests as one group.
  - Requirements: FR-016, SC-004
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py`
  - Depends on: T007, T010
  - Acceptance: The sentinel test and the real-SDK test pass. Neither sentinel value appears in captured output or in log records.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q -k "sentinel or sdk_success"`
  - Status: open

- [ ] T016 [US2] Run the credential prompter tests without changing that file.
  - Requirements: FR-003, FR-011
  - Files: `tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py`
  - Acceptance: All tests pass. The failure assertions at line 134 still find the validation warning record.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py -q`
  - Status: open

- [ ] T017 [US1] Check each changed line for an inline comment and for ASCII text.
  - Requirements: FR-017, FR-018
  - Files: `MistHelper.py`, `src/mist/access/auth/interactive/clouds.py`, `src/mist/access/auth/interactive/login_orchestrator.py`, `src/mist/access/auth/interactive/msp_org_selector.py`, `tests/unit/marvis/mist/access/auth/interactive/test_clouds.py`
  - Depends on: T004, T007, T010, T012
  - Acceptance: The search finds no non-ASCII character. Each changed line holds an inline comment that states its channel and reason.
  - Verification: `rg -n "[^\x00-\x7F]" MistHelper.py src/mist/access/auth/interactive tests/unit/marvis/mist/access/auth/interactive`
  - Status: open

## Phase 7: Final tasks

- [ ] T-LOCAL-GATES Run each gate of the local gates table that applies to the changed files.
  - Requirements: SC-005
  - Files: each file in the change map of `plan.md`
  - Depends on: T013, T014, T015, T016, T017
  - Acceptance: Each command prints its expected result. The gate list and the results go into the pull request body. A failing gate is reported as it failed.
  - Verification: Run each command below and compare its output with the expected result.
  - Applicable gates:
    - Compile: `python -m py_compile MistHelper.py`. Expected: no output.
    - Lint: `python -m ruff check .`. Expected: `All checks passed`.
    - Format: `python -m black --check .`. Expected: no file needs a change.
    - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Expected: `Success`. The paths come from `MYPY_PATHS`.
    - Tests: `python -m pytest` on each changed test module. Expected: every test passes.
    - Full tests: the two `pytest-chunks` commands of the local gates table. Expected: one summary line for each shard.
    - Safe sweep: `python MistHelper.py --test`. Expected: each safe operation completes.
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected: 80 percent or above.
    - Test quality: the test quality ratchet of the local gates table. Expected: `gate: 0 new findings vs baseline`.
    - Complexity: `radon cc src/mist/access/auth/interactive -j | complexity-gate --max 10`. Expected: no block above complexity 10.
    - Security lint: `bandit -c pyproject.toml -r src/mist/access/auth/interactive -q`. Expected: no finding.
    - Code quality: `pylint src/ --fail-under=9.5`. Expected: a score of 9.5 or above.
    - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`. Expected: no finding. The paths come from `VULTURE_PATHS`.
    - Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`. Expected: no violation and coverage of 90 percent or above.
    - Symbols: `symbol-diff --base origin/main <file>` for each changed Python file. Expected: `no module-level name changed`. Report the exact result if the gate names an added import.
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` for the operator guide and the changelog fragment. Expected: each file scores 80 or above.
    - Not applicable: dependency audit, because no dependency file changes. Menu reference, because no menu row changes. Ops portal and ops platform, because those trees do not change.
  - Status: open

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-019, SC-005
  - Files: the changed files of the change map, added by explicit path
  - Depends on: T-LOCAL-GATES
  - Acceptance: The commit subject and the pull request title read `fix(login): route interactive login messages to direct output`. The body holds `Closes #4863`, the changed-file summary, the local gate results, and remediation items R-1 and R-2.
  - Verification: `gh pr view <number> --json title,body,headRefName` shows the title and the text `Closes #4863`.
  - Status: open

- [ ] T-REMOTE-CI Watch the required checks of the pull request.
  - Requirements: SC-005
  - Files: none
  - Depends on: T-PR
  - Acceptance: Each required check reports success. A skipped job is read as unknown and is investigated before the merge.
  - Verification: `gh pr checks <number> --watch`
  - Status: open

- [ ] T-MERGE Enable auto-merge only after remote checks pass and the orchestrator authorizes the merge.
  - Requirements: SC-005
  - Files: none
  - Depends on: T-REMOTE-CI
  - Acceptance: The `auto-merge` label is added only after authorization. The squash commit lands on `main`. The branch and the worktree are removed after the merge.
  - Verification: `gh pr view <number> --json mergedAt,state` reports `MERGED` after the merge.
  - Status: open
