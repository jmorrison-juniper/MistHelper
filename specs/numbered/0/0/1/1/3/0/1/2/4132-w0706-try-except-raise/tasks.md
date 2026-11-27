# Tasks: W0706 try-except-raise handlers in MistHelper.py

**Input**: Design documents in `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, and `design/quickstart.md`.

**Tests**: Required by the constitution and by `AGENTS.md`. Write tasks T003 to T007 before the edits in T008 and T009.

**Environment**: Create a new git worktree on branch `chore/4132-w0706-try-except-raise` from `origin/main`. Run Python from the worktree `.venv`.

**Edit rule**: Locate each handler by its unique text before you edit. Line numbers in this file refer to main at blob `98d7828479ded6bc4c83d15e0c1847171cfbfd49`.

## Format: `[ID] [P?] [Story] Requirement. Description`

- **[P]**: Safe to run in parallel, because the task changes a different file.
- **[USn]**: The user story that the task serves.
- **FR-###**: The requirements that the task satisfies.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. Each task starts as `open`.
- Tick a task only after you verify the delivered file. Add the note `(delivered: path)`.

## Phase 1: Setup

- [ ] T001 [US3] FR-012. Claim the issue and create the branch.
  - Paths: `MistHelper.py` (overlap check only)
  - Acceptance: Issue 4132 carries `in-progress`. A new worktree holds the branch from `origin/main`. No open pull request changes `MistHelper.py`.
  - Verification: Compile gate `python -m py_compile MistHelper.py`
  - Status: open

- [ ] T002 [US1] FR-006. Record the pylint baseline before any edit.
  - Paths: `MistHelper.py`
  - Acceptance: `python -m pylint MistHelper.py` reports seven W0706 messages at lines 1820, 6610, 6654, 6666, 7811, 8094, and 8343. Copy the count into the pull request body.
  - Verification: Compile gate `python -m py_compile MistHelper.py`
  - Status: open

## Phase 2: Tests first

- [ ] T003 [US1] FR-005, FR-007. Add the detector test and the repository guard test.
  - Paths: `tests/unit/test_issue_1709_narrow_except.py`
  - Acceptance: Test `test_reraise_detector_flags_synthetic_handler` passes. Test `test_misthelper_has_no_reraise_first_handler` fails before T008 and names seven offenders.
  - Verification: Tests gate `python -m pytest tests/unit/test_issue_1709_narrow_except.py`
  - Status: open

- [ ] T004 [US2] FR-003. Add the ten stop-signal propagation cases.
  - Paths: `tests/unit/test_issue_1709_narrow_except.py`
  - Acceptance: Test `test_operator_stop_propagates` passes ten cases before and after T008. Each case shows the same stop signal and exit code at the caller.
  - Verification: Tests gate `python -m pytest tests/unit/test_issue_1709_narrow_except.py`
  - Status: open

- [ ] T005 [US2] FR-002. Add the three ordinary-exception cases.
  - Paths: `tests/unit/test_issue_1709_narrow_except.py`
  - Acceptance: Test `test_ordinary_exception_is_still_handled` passes three cases before and after T008. Each `RuntimeError` returns the existing fallback value.
  - Verification: Tests gate `python -m pytest tests/unit/test_issue_1709_narrow_except.py`
  - Status: open

- [ ] T006 [US2] FR-004. Add the `__main__` structure test.
  - Paths: `tests/unit/test_issue_1709_narrow_except.py`
  - Acceptance: Test `test_main_block_keeps_keyboard_interrupt_and_finally` fails before T008. It passes after T008 with handler names `KeyboardInterrupt` and `Exception`.
  - Verification: Tests gate `python -m pytest tests/unit/test_issue_1709_narrow_except.py`
  - Status: open

- [ ] T007 [US2] FR-008. Add the logging cases for the two fast-mode readers.
  - Paths: `tests/unit/test_issue_1709_narrow_except.py`
  - Acceptance: Test `test_touched_fast_mode_readers_log_before_and_after` fails in two cases before T009. Each case shows an info record before a debug record.
  - Verification: Tests gate `python -m pytest tests/unit/test_issue_1709_narrow_except.py`
  - Status: open

## Phase 3: Implementation

- [ ] T008 [US1] FR-001, FR-002, FR-003, FR-004. Delete the seven re-raise-only handler pairs.
  - Paths: `MistHelper.py`
  - Acceptance: The seven pairs in `plan.md` changes M1 to M7 are gone. Each `except Exception` handler survives. Each surviving handler comment carries the stop-signal sentence from `plan.md`.
  - Verification: Compile gate `python -m py_compile MistHelper.py`
  - Status: open

- [ ] T009 [US2] FR-008. Add inline comments and action logging to each touched function.
  - Paths: `MistHelper.py`
  - Acceptance: Changes M1 to M6 in `plan.md` are present. Each new line carries an inline comment. Each new log line is ASCII and uses `%s` formatting. Touched functions keep the lengths that `plan.md` states.
  - Verification: Tests gate `python -m pytest tests/unit/test_issue_1709_narrow_except.py`
  - Status: open

- [ ] T010 [P] [US3] FR-009. Add the changelog fragment.
  - Paths: `changelog.d/issue-4132-w0706-try-except-raise.md`
  - Acceptance: The file holds one `###` heading and one bullet that starts with `- **Changed**:`. The bullet names issue 4132. The file holds no version heading.
  - Verification: Tests gate `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open

- [ ] T011 [P] [US3] FR-011. Add the specification record folder.
  - Paths: `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/` with `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`
  - Acceptance: The feature root holds five children. The `design/` folder holds four children. Each Markdown file passes the STE gate at 80 or above.
  - Verification: STE gate `ste-linter --config .ste-linter.toml --min-score 80` with each record file named
  - Status: open

- [ ] T-LOCAL-GATES. FR-006, FR-007, FR-010, FR-011. Run each applicable local gate.
  - Paths: `MistHelper.py`, `tests/unit/test_issue_1709_narrow_except.py`, `changelog.d/issue-4132-w0706-try-except-raise.md`, and the record folder
  - Acceptance: Each gate reports its expected result in the list below. Record each result in the pull request body.
  - Verification: Every command in the list below
  - Status: open
  - Gate list with expected results:
    1. Compile: `python -m py_compile MistHelper.py`. Expected: no output.
    2. Lint: `python -m ruff check .`. Expected: `All checks passed`.
    3. Format: `python -m black --check .`. Expected: no file needs a change.
    4. Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Expected: `Success`.
    5. Tests: `python -m pytest tests/unit/test_issue_1709_narrow_except.py`. Expected: 18 new cases pass.
    6. Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`. Expected: one summary line for each shard, with no failure.
    7. Safe sweep: `python MistHelper.py --test`. Expected: each safe operation completes. Credential checks skip with a reason.
    8. Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected: the CI shards reach 80 percent or above.
    9. Test quality: the `test-quality-analyzer --gate` command in `.github/copilot-instructions.md`. Expected: `gate: 0 new findings vs baseline`.
    10. Complexity: `radon cc MistHelper.py -j | complexity-gate --max 10`. Expected: no block above complexity 10.
    11. Security lint: `bandit -c pyproject.toml -r . -q`. Expected: no finding.
    12. Dependency audit: not applicable. The change edits no dependency file.
    13. Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`. Expected: no finding.
    14. Docstrings: `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`. Expected: coverage of 90 percent or above.
    15. Menu reference: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map --check`. Expected: no changed file after the run.
    16. Symbols: `symbol-diff --base origin/main MistHelper.py`. Expected: `no module-level name changed`, exit code 0.
    17. STE: `ste-linter --config .ste-linter.toml --min-score 80` with each new Markdown file named. Expected: each file scores 80 or above.
    18. Process folder guard: `python -m pytest tests/guardrails/test_process_folder_structure.py`. Expected: pass, with the examined count printed.
    19. Pylint acceptance: `python -m pylint MistHelper.py`. Expected: zero `W0706` lines.
    20. Suppression check: search the added lines of `git diff origin/main -- MistHelper.py` for `pylint: disable`, `noqa`, and `type: ignore`. Expected: no match.

- [ ] T-PR. FR-012. Commit, rebase, push, and open the pull request.
  - Paths: `MistHelper.py`, `tests/unit/test_issue_1709_narrow_except.py`, `changelog.d/issue-4132-w0706-try-except-raise.md`, and the record folder
  - Acceptance: The commit subject is `style(MistHelper.py): remove re-raise-only except handlers`. The commit body holds `Closes #4132` and the Co-authored-by trailer. Rebase onto `origin/main` before the push. The pull request body fills the template and holds `Closes #4132`. The pull request carries no `auto-merge` label.
  - Verification: Compile gate `python -m py_compile MistHelper.py`
  - Status: open

- [ ] T-REMOTE-CI. FR-012. Watch the CI checks on the pull request head.
  - Paths: `.github/workflows/ci.yml`
  - Acceptance: `gh pr checks <number> --watch` reports each required check as passing. The `quality_gate_issues` job reports no failed gate. Record the advisory `speckit-task-audit` result in the pull request.
  - Verification: Full tests gate, the two `pytest-chunks` commands in `.github/copilot-instructions.md`
  - Status: open

- [ ] T-MERGE. FR-012. Merge after human review and orchestrator authorization.
  - Paths: `MistHelper.py` and `changelog.d/issue-4132-w0706-try-except-raise.md`
  - Acceptance: A human reviewer approves the pull request. The orchestrator authorizes the merge. The squash commit reaches `main`. `container-build.yml` completes on the merged revision. The image revision label equals the merged commit SHA. The deployed container passes its health checks. The branch and the worktree are removed.
  - Verification: Compile gate `python -m py_compile MistHelper.py`
  - Status: open
  - Warning: a squash merge reaches `main`. Deleting the branch does not undo it. Revert with a new pull request instead.

## Dependencies and Execution Order

- T001 and T002 run first, in order.
- T003 to T007 edit the same test module, so they run in order.
- T008 runs after T003 to T007. T009 runs after T008.
- T010 and T011 are [P]. They edit different paths and can run beside T008 and T009.
- T-LOCAL-GATES runs after T008 to T011. T-PR, T-REMOTE-CI, and T-MERGE run in order after T-LOCAL-GATES.

## Requirement Coverage

| Requirement | Tasks | Tests or gates |
| - | - | - |
| FR-001 | T008 | Test B, Test A |
| FR-002 | T005, T008 | `test_ordinary_exception_is_still_handled` |
| FR-003 | T004, T008 | `test_operator_stop_propagates` |
| FR-004 | T006, T008 | `test_main_block_keeps_keyboard_interrupt_and_finally` |
| FR-005 | T003 | Test A, Test B |
| FR-006 | T002, T-LOCAL-GATES | Test B, pylint gate 19 |
| FR-007 | T003, T-LOCAL-GATES | Test B, suppression check gate 20 |
| FR-008 | T007, T009 | `test_touched_fast_mode_readers_log_before_and_after`, review of comments |
| FR-009 | T010 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-010 | T-LOCAL-GATES | Symbols gate 16, menu gate 15, `tests/unit/test_menu_entry_metadata.py` |
| FR-011 | T011, T-LOCAL-GATES | STE gate 17, changelog guard |
| FR-012 | T-PR, T-REMOTE-CI, T-MERGE | CI checks on the pull request head |
