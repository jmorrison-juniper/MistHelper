# Tasks: SQLite schema context errors

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/2/2/4712-schema-context-errors/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, `design/contracts/schema-context-contract.md`.

**Tests**: The spec requires regression tests. Each test task names its test ID from `plan.md`. Write the failing test before the source change.

**Organization**: Tasks are grouped by delivery phase. Phase 2 writes the failing tests. Phase 3 changes the source. Phases 4 and 5 add documents and the record. Phase 6 runs the gates and delivers the change.

## Format

- `[P]` marks a task that can run in parallel, because it edits a different file.
- Each task lists its requirement IDs, its exact paths, its acceptance statement, its verification command, and its status.
- Status values: `open`, `absent`, `partial`, or `verified-present`. Status describes the state of `main` when the record was written.

## Phase 1: Setup and baseline

- [ ] T001 Create branch `fix/4712-schema-context-errors` from current `origin/main` in a new worktree. Requirements: FR-013, D-10. Paths: none changed. Acceptance: the branch base is the current `main` head. The branch name follows `<type>/<issue>-<slug>`. Verification: `python -m pytest tests/unit/db/test_database_schema_utils.py` passes on the base. Status: open.
- [ ] T002 [P] Create the Python 3.15.2 environment with `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`. Requirements: none. Paths: `scripts/bootstrap_worktree.py` (row 33). Acceptance: the venv reports Python 3.15.2. Verification: `python -m py_compile MistHelper.py` produces no output. Status: open.
- [ ] T003 [P] Confirm the route with `Resolve-SpecFeaturePath -SpecsDir specs -BranchName 4712-schema-context-errors -Number 4712` from `.specify\scripts\powershell\spec-route.ps1`. Requirements: FR-013, D-6. Paths: `.specify\scripts\powershell\spec-route.ps1` (rows 21 to 23). Acceptance: the function returns `specs\numbered\0\0\1\2\2\3\2\2\4712-schema-context-errors`. Verification: `python -m pytest tests/guardrails` passes (Guardrails row of the Move a module table). Status: open.
- [ ] T004 [P] Repeat the overlap check before any file changes. Requirements: none. Paths: none changed. Acceptance: no open pull request changes the paths in `plan.md` File Change Map, except pull request #4813 on `data_exporter.py`, which this change does not touch. Verification: `gh pr list --json number,headRefName,files` (AGENTS.md, Parallel agents). Status: open.

## Phase 2: Failing tests first

- [ ] T005 [P] Add the three regression tests TST-1, TST-2, and TST-3 in `tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py`. Requirements: FR-001, FR-002, FR-005, FR-010. Paths: the new file in that folder. Acceptance: each test has a docstring and an inline comment on each line. Each test matches its design in `plan.md` Test Plan. TST-1 and TST-2 patch only the detector path. TST-3 asserts zero `sqlite3.connect` calls. Verification: `python -m pytest tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py` reports three failures on the base. Status: absent.
- [ ] T006 [P] Update the expectation of `test_handles_stack_inspection_error` (TST-4) in `tests/unit/db/test_database_schema_utils.py`, lines 55 to 67. Requirements: FR-001, FR-006, FR-012. Paths: `tests/unit/db/test_database_schema_utils.py` (rows 13 and 71). Acceptance: the test expects `RuntimeError` with the message `frame introspection failed`. The docstring says the failure propagates. The file path stays the same. Verification: `python -m pytest tests/unit/db/test_database_schema_utils.py` reports one failure on the base. Status: absent.

## Phase 3: Source change

- [ ] T007 Remove the broad handler in `src/foundation/persistence/db/database_schema_utils.py`. Requirements: FR-001, FR-002, FR-003, FR-004, FR-011. Paths: `src/foundation/persistence/db/database_schema_utils.py` (rows 1 to 4). Acceptance: lines 62 and 63 (the `except` clause and its log call) are removed. The debug line at line 59 stays inside the loop. The `finally` block at lines 64 and 65 is unchanged. The docstring at line 50 and the fallback comment at line 66 describe the new behavior. Each changed line has an inline comment. Verification: `python -m pytest tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py tests/unit/db/test_database_schema_utils.py` passes. Status: absent. Depends on T005 and T006.
- [ ] T008 Verify that no module-level name changed in `src/foundation/persistence/db/database_schema_utils.py`. Requirements: FR-004. Paths: `src/foundation/persistence/db/database_schema_utils.py`. Acceptance: the symbol gate reports no removed or changed module-level name. Verification: `symbol-diff --base origin/main src\foundation\persistence\db\database_schema_utils.py` reports `no module-level name changed` with exit code 0. Status: open. Depends on T007.

## Phase 4: Documents and changelog

- [ ] T009 [P] Add two sentences to `README.md` after "It writes each output file to `data/`." on line 30. Requirements: FR-007. Paths: `README.md` (row 51). Acceptance: the two sentences describe the stopped SQLite write and the log line. Each sentence has 25 words or fewer. The paragraph has no semicolon. Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` reports each file at 80 or above. Status: absent.
- [ ] T010 [P] Add one paragraph to `documentation/operator-guide.md` after the SQLite row on line 752, in the section Find your output. Requirements: FR-008. Paths: `documentation/operator-guide.md` (rows 52 and 53). Acceptance: the paragraph names the log text, the cause, and one operator action. It has no semicolon. Verification: the STE command in T009 with `documentation/operator-guide.md` added reports 80 or above. Status: absent.
- [ ] T011 [P] Add the changelog fragment `changelog.d/issue-4712-schema-context-errors.md`. Requirements: FR-009. Paths: the new fragment (rows 19 and 20). Acceptance: the file holds one `###` heading and one Fixed bullet that names issue #4712. No version number appears. Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` passes. Status: absent.

## Phase 5: Record

- [ ] T012 Copy the record from the draft folder to `specs\numbered\0\0\1\2\2\3\2\2\4712-schema-context-errors\`. Requirements: FR-013, SC-007. Paths: the record folder only. Acceptance: the feature root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\`. The `design` folder holds `research.md`, `data-model.md`, `quickstart.md`, `contracts\`, and `checklists\`. No other file appears. Verification: `python -m pytest tests/guardrails` passes. Status: absent. Depends on T005 to T011.

## Phase 6: Delivery

- [ ] T-LOCAL-GATES Run each applicable gate on the changed files. Requirements: SC-003, FR-010. Paths: the changed files of T005 to T012. Acceptance: each applicable gate reports its expected result. Each gate that does not apply states its reason. The gate list appears below. Verification: each row of the Local gates table in `.github/copilot-instructions.md` (section starts at line 50) that applies. Status: absent. Depends on T008 and T012.
- [ ] T-PR Commit, push, and open the pull request. Requirements: FR-013, D-9, D-11. Paths: the branch and the changed files. Acceptance: the commit subject is `fix(persistence): stop SQLite writes on local context failures`. The commit body and the PR body include `Closes #4712`. The PR body follows `.github/PULL_REQUEST_TEMPLATE.md` and adds the Closes line (row 35). The changelog file keeps its issue name. The owner lifts the publication hold before this task starts. Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` reports `gate: 0 new findings vs baseline`. Status: absent. Gated by D-11.
- [ ] T-REMOTE-CI Watch the CI checks on the pull request. Requirements: FR-010. Paths: none changed. Acceptance: each required check reports success on the latest commit. Verification: `gh pr checks <number> --watch` (AGENTS.md, Pull request). The local gates table has no remote row, so this command is the only remote check. Status: absent. Depends on T-PR.
- [ ] T-MERGE Add the `auto-merge` label and merge. Requirements: D-11. Paths: none changed. Acceptance: the label is added only after every check is green and the orchestrator authorizes the merge. The squash merge creates one commit on `main`. The container build for the merged revision completes. Its revision label equals the merged commit SHA (constitution Principle IV, steps 9 to 11). Step 12, deploy and health check, follows under the orchestrator. Verification: `gh pr view <number> --json state,mergedAt,mergeCommit` (AGENTS.md, Merge). Status: absent. Depends on T-REMOTE-CI and orchestrator authorization.

### Gate list for T-LOCAL-GATES

- Compile: `python -m py_compile MistHelper.py` produces no output. Applies to every Python change.
- Lint: `python -m ruff check .` reports `All checks passed!`.
- Format: `python -m black --check .` reports that no file needs a change.
- Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` reports `Success`. The path list comes from `MYPY_PATHS` (row 28).
- Tests: `python -m pytest tests/unit/db/test_database_schema_utils.py` and `python -m pytest tests/unit/config/foundation/persistence/storage/db` pass.
- Full tests: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` each print one summary line with no failure.
- Safe sweep: `python MistHelper.py --test` completes each safe operation. Without a Mist token, the Mist API checks skip with a credential reason.
- Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` reports 80 percent or above.
- Test quality: run the live guide preflight `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. Then run the `--changed-from` command in T-PR. At push, run the full-suite command from the Test quality section. Each reports `gate: 0 new findings vs baseline`.
- Complexity: `radon cc src\foundation\persistence\db -j | complexity-gate --max 10` reports no block above 10.
- Security lint: `bandit -c pyproject.toml -r src\foundation\persistence\db -q` reports no finding.
- Dependency audit: not applicable. `requirements.txt` and `requirements-dev.txt` do not change.
- Code quality: `pylint src/ --fail-under=9.5` reports a score of 9.5 or above.
- Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` reports no finding. The path list comes from `VULTURE_PATHS` (row 29).
- Docstrings: `pydocstyle src/ wsgi.py web_portal` reports no violation. `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` reports 90 percent or above. The path lists come from rows 30 and 31.
- Menu reference: not applicable. No menu row, registry entry, or generated page changes.
- Symbols: `symbol-diff --base origin/main src\foundation\persistence\db\database_schema_utils.py` reports `no module-level name changed`.
- STE: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`, with `documentation/operator-guide.md`, the changelog fragment, and each Markdown file of the record folder added to the list. Each file reports 80 or above.
- Ops portal: not applicable. No `ops-portal/` file changes.
- Ops platform: not applicable. No `mist-ops-platform/` file changes.
- Guardrails: `python -m pytest tests/guardrails` passes. This row comes from the Move a module table.

## Dependencies and Execution Order

- T001 precedes T002, T003, and T004.
- T005 and T006 run in parallel. Both precede T007.
- T007 precedes T008.
- T009, T010, and T011 run in parallel with T005 to T008. They edit different files.
- T012 follows T005 to T011, because the record holds the final documents.
- T-LOCAL-GATES follows T008 and T012.
- T-PR follows T-LOCAL-GATES and the lift of the publication hold.
- T-REMOTE-CI follows T-PR. T-MERGE follows T-REMOTE-CI and the orchestrator authorization.

## Notes

- Do not edit `.github/test-quality-baseline.json` to hide a new finding. Fix the test.
- Do not edit `.github/blind-exception-handler-baseline.json`. The change removes a handler and adds none.
- Do not change `.specify/feature.json`. The read-only commands and the record copy leave it unchanged.
- Remove each debug artifact before commit.
