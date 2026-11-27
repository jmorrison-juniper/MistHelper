# Tasks: Unattended token skip for menu 247

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/4/3/4/4744-unattended-token-skip/`. Available documents: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/`, and `design/checklists/`.

**Status legend**: `open` means work has not started. `verified-present` means main already holds the artifact. `partial` means some parts exist. `absent` means main lacks the artifact. This change creates or edits that artifact.

**Format**: `T### [P] [US#] Description`. `[P]` marks a task that is safe to run in parallel. Each task names its requirements, its exact paths, its acceptance statement, its verification command, and its status.

## Phase 1: Red Tests (write first)

### T001 [US1] Write the menu 247 regression

- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-008, FR-009, FR-014.
- Files: `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py`.
- Acceptance: The test `test_menu_247_unattended_run_records_one_skip_without_verification` uses the real `SelfAccountExporter.verify_email`. It fails on the current code with one pass event and zero skip events.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "menu_247" -q`
- Status: absent (no regression exists on main).
- Depends on: none.

### T002 [P] [US2] Write the provider tests

- Requirements: FR-010 and FR-011.
- Files: `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py`.
- Acceptance: `test_provider_raises_for_operator_only_prompt_without_default` expects `OperatorPromptRequired`. `test_provider_returns_empty_answer_for_optional_prompt` expects an empty string. The existing test `test_unattended_input_provider_fails_unresolved_required_prompt` covers FR-011 without edit.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "provider" -q`
- Status: absent.
- Depends on: none.

### T003 [P] [US3] Write the loop and summary tests

- Requirements: FR-004, FR-006, and FR-013.
- Files: `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py`.
- Acceptance: `test_run_option_loop_counts_operator_prompt_skip_apart_from_pass` expects `(1, 0, 1)` for one pass and one skip. `test_run_and_finalize_reports_skip_in_summary_and_fails_zero_exercised` expects `skipped == 1`, `passed == 0`, `failed == 0`, and a false verdict.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "operator_prompt or skip_in_summary" -q`
- Status: absent.
- Depends on: none.

### T004 [P] [US3] Unpack three loop tally values

- Requirements: FR-015.
- Files: `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py` at lines 418, 512, 582, 752, 780, and 813.
- Acceptance: Each site unpacks `success, failure, _skipped` from `_run_option_loop`. Each assertion keeps its meaning.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -q` (passes after T008).
- Status: verified-present (the two-value form exists on main at RC-26).
- Depends on: none. Commit with T008.

## Phase 2: Implementation

### T005 [US1] Create the operator-only prompt module

- Requirements: FR-001, FR-003, and FR-014.
- Files: `src/foundation/support/menu_testing/operator_prompt.py` (new).
- Acceptance: The module declares `OperatorPromptRequired`, `OperatorPromptPolicy`, and `OperatorPromptSkipRecorder`. Each class has a docstring. The module does not import the runner. The skip log lines are ASCII.
- Verification: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
- Status: absent.
- Depends on: T001, T002, and T003 (the tests exist and fail first).

### T006 [US1] Stop operator-only prompts in the input provider

- Requirements: FR-001, FR-010, FR-011, and FR-014.
- Files: `src/foundation/support/menu_testing/interactive_test_runner.py` (method `UnattendedInteractiveInputProvider.answer`).
- Acceptance: The check runs before the rule table. A non-empty default answer wins. Optional prompts keep the empty answer. The info line precedes the raise.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "provider" -q`
- Status: absent.
- Depends on: T005.

### T007 [US1] Catch the stop in the option runner

- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, and FR-009.
- Files: `src/foundation/support/menu_testing/interactive_test_runner.py` (method `_run_single_option`, return type `bool | None`).
- Acceptance: The except clause for `OperatorPromptRequired` precedes `except Exception`. The clause detaches the error observer, calls the recorder with the registry skip reason, and returns None. `prompt_error_count` does not change.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "menu_247" -q`
- Status: absent.
- Depends on: T005 and T006.

### T008 [US3] Count the skip in the loop and the summary

- Requirements: FR-006, FR-013, and FR-015.
- Files: `src/foundation/support/menu_testing/interactive_test_runner.py` (methods `_run_option_loop` and `_run_and_finalize`).
- Acceptance: `_run_option_loop` returns `(success, error, skip)`. A None outcome counts as a skip. `_run_and_finalize` passes `ctx.skip_count + runtime skips` to `SuiteTallies`. The verdict code stays unchanged.
- Verification: `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -q`
- Status: absent.
- Depends on: T007 and T004.

### T009 [P] [US2] Confirm the exporter stays unchanged

- Requirements: FR-007, FR-008, and FR-012.
- Files: `src/operations/exporting/export/self_account_exporter.py` (no edit).
- Acceptance: The exporter tests pass without edit. The empty-token cancel test (RC-28) and the SDK call tests pass.
- Verification: `python -m pytest tests/unit/export/test_self_account_exporter.py -q`
- Status: verified-present (RC-13 to RC-15 and RC-28 on main).
- Depends on: none.

## Phase 3: Documentation and Release Note

### T010 [P] [US3] Update the `--testinteractive` row

- Requirements: FR-016.
- Files: `documentation/cli-reference.md` (row 60, RC-36).
- Acceptance: The row names the operator-only skip and the menu 247 token. The row keeps the existing `safe` and `interactive_safe` text. The STE gate passes.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/cli-reference.md`
- Status: absent (row 60 on main has no skip text).
- Depends on: none.

### T011 [P] [US3] Add the changelog fragment

- Requirements: FR-017.
- Files: `changelog.d/issue-4744-unattended-token-skip.md` (new).
- Acceptance: The file holds one `###` heading, one `- **Fixed**:` bullet, and the issue number at the end of the bullet. The file name passes the issue-form rule.
- Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- Status: absent.
- Depends on: none.

## Phase 4: Final Tasks

### T-LOCAL-GATES

- Requirements: all, including SC-005 and SC-006.
- Acceptance: Run each gate in `design/quickstart.md` section "Local gates" that applies to the changed files. Each gate reports its expected result. Record each result in the pull request body.
- Verification: The commands in `design/quickstart.md`.
- Status: open.
- Depends on: T008, T009, T010, and T011.

### T-PR

- Requirements: all.
- Acceptance: Commit with a Conventional Commits message, push `fix/4744-unattended-token-skip`, and open a pull request. The title is `fix(tests): skip unattended menu 247 at the token prompt`. The body holds `Closes #4744`, the changed-file summary, the gate results, and the test quality result.
- Verification: `gh pr view --json title,body,headRefName` (run in the implementation worktree on branch `fix/4744-unattended-token-skip`)
- Status: open.
- Depends on: T-LOCAL-GATES.

### T-REMOTE-CI

- Requirements: all.
- Acceptance: Each required check and CodeQL pass on the latest commit.
- Verification: `gh pr checks --watch` (run in the implementation worktree on branch `fix/4744-unattended-token-skip`)
- Status: open.
- Depends on: T-PR.

### T-MERGE

- Requirements: all.
- Acceptance: Add the `auto-merge` label only after every check is green and the orchestrator authorizes the merge. The pull request must not change a destructive operation, and this one does not.
- Verification: `gh pr view --json labels,mergeStateStatus` (run in the implementation worktree on branch `fix/4744-unattended-token-skip`)
- Status: open.
- Depends on: T-REMOTE-CI.

## Requirement Traceability

| Requirement | Tasks | Tests and checks |
| - | - | - |
| FR-001 | T001, T005, T006, T007 | `test_menu_247_unattended_run_records_one_skip_without_verification` |
| FR-002 | T001, T007 | Regression asserts the registry reason text |
| FR-003 | T001, T005 | Regression asserts category `operator_prompt` and test mode `interactive-operator-prompt` |
| FR-004 | T001, T003, T007 | Regression asserts zero pass and zero fail events. Loop test asserts `(1, 0, 1)` |
| FR-005 | T001, T007 | Regression asserts `prompt_error_count == 0` |
| FR-006 | T003, T008 | `test_run_and_finalize_reports_skip_in_summary_and_fails_zero_exercised` asserts `skipped == 1` |
| FR-007 | T001, T009 | Regression asserts the SDK function mock records no call |
| FR-008 | T001, T009 | Regression asserts the writer mock records no call |
| FR-009 | T001, T007 | Regression asserts the input seam is the original function |
| FR-010 | T002, T006 | `test_provider_returns_empty_answer_for_optional_prompt` |
| FR-011 | T002, T006 | Existing `test_unattended_input_provider_fails_unresolved_required_prompt` |
| FR-012 | T009 | Existing `test_an_empty_token_cancels` and `test_an_empty_answer_cancels` |
| FR-013 | T003, T008 | Summary test asserts a false verdict |
| FR-014 | T001, T005 | Regression asserts the captured log text is ASCII |
| FR-015 | T004, T008 | Test module runs with three unpacked values |
| FR-016 | T010 | STE gate on `documentation/cli-reference.md` |
| FR-017 | T011 | `tests/guardrails/test_changelog_fragment_policy.py` |

Planned new tests: five. Changed call sites: six. Existing tests re-run: the runner test module, the standalone star import, the exporter tests, and the two action test modules.
