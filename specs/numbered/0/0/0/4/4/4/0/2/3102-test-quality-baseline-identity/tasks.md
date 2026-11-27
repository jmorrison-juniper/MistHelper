# Tasks: Test-quality baseline identity by content

**Input**: Numeric record at `specs/numbered/0/0/0/4/4/4/0/2/3102-test-quality-baseline-identity/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

**Tests**: The tests are required. Fifteen new tests are planned, and each names its file. Five upstream tests and four MistHelper tests cover the behaviors in FR-001 to FR-010.

**Organization**: Tasks T001 to T009 run in misthelper-devtools. Tasks T010 to T017 run in MistHelper after the release. The final four tasks run in the MistHelper pull request.

## Format

- `[P]` marks a task that can run in parallel with other `[P]` tasks. The files differ, and no task depends on another.
- `[US#]` names the user story that the task serves.
- Each task names its requirements, its exact files, its acceptance statement, one verification command, and its status.
- Status values are `open`, `verified-present`, `partial`, and `absent`.
- A task with status `verified-present` carries a check mark and an evidence note.

## Verification commands

- The upstream commands use the Tests row of the local gates table in `.github/copilot-instructions.md`, applied to the misthelper-devtools checkout.
- The MistHelper commands use the Lint, Tests, Test quality, and STE rows of the same table.

## Upstream: misthelper-devtools (release 0.7.0)

Caution: the upstream issue and pull request come first. Open the issue before the branch, as AGENTS.md section "Issue first" requires.

- [ ] T001 [P] [US1] Add the optional `content_anchor` field to `Finding`.
  - Requirements: FR-001, FR-003
  - Files: `src/misthelper_devtools/test_quality_analyzer/detection/types.py` (modify, class at line 53, R-43)
  - Acceptance: `Finding` gains one optional string field after `related_source`. No other field changes. Existing tests pass.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_types.py`
  - Status: absent

- [ ] T002 [P] [US1] Give the `_finding` helper the file-level sentinel.
  - Requirements: FR-010
  - Files: `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` (modify, lines 747-760, R-45)
  - Tests: `test_file_level_finding_carries_sentinel` in `tests/tools/test_quality_analyzer/test_gate_decision.py`. The test proves that a header line inserted above line 1 keeps the identity.
  - Acceptance: The analyzer reports each finding at the line that the rule names. The `_finding` helper sets `file-level`. `tautological.py` and `missing_edge_case.py` report node lines, not line 1, or the task records each exception. A header insertion keeps the identity of each file-level finding. The gate exits 0 after a header insertion.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_gate_decision.py`
  - Status: absent

- [ ] T003 [US2] Key the identity by content anchor and count occurrences.
  - Requirements: FR-001, FR-002, FR-004
  - Files: `src/misthelper_devtools/test_quality_analyzer/baseline.py` (modify, identity key and diff, R-31 to R-34). `tests/tools/test_quality_analyzer/test_baseline_differ.py` (modify, round-trip case, R-47)
  - Tests: `test_line_number_shift_is_not_new`, `test_second_identical_occurrence_is_new`, and `test_removed_occurrence_is_not_new` are new. `test_round_trip_keeps_content_anchor` replaces the line-number round trip.
  - Acceptance: The identity key is `(category, rule_id, file_path, explanation, content_anchor)`. The diff uses multiset counts. A line shift produces no new finding. A second identical occurrence produces one new finding.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_baseline_differ.py`
  - Status: absent

- [ ] T004 [US1] Compute content anchors in the pipeline.
  - Requirements: FR-001, FR-003
  - Files: `src/misthelper_devtools/test_quality_analyzer/baseline.py` (modify, add `ContentAnchorResolver`). `src/misthelper_devtools/test_quality_analyzer/__main__.py` (modify, call the resolver in `_run_pipeline` after step 6, R-39)
  - Tests: `test_changed_flagged_line_is_new` in `test_gate_decision.py`. `test_unreadable_untested_source_exits_two` in `test_cli.py`.
  - Acceptance: The resolver reads the flagged line from each analyzed file and from each untested source module. A changed flagged line produces a new finding. An unreadable source file exits 2 and names the path.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_cli.py`
  - Status: absent

- [ ] T005 [US3] Add count-based prune, parse-error retention, and the removed count.
  - Requirements: FR-005, FR-006, FR-009
  - Files: `src/misthelper_devtools/test_quality_analyzer/__main__.py` (modify, R-39, R-40, R-41). `src/misthelper_devtools/test_quality_analyzer/baseline.py` (modify, prune, R-35)
  - Tests: `test_prune_removes_unmatched_occurrences_in_analyzed_files`, `test_prune_keeps_entries_of_parse_error_files`, and `test_gate_prints_removed_count_for_analyzed_files` in `test_cli.py`.
  - Acceptance: Prune removes unmatched occurrences in analyzed files only. Prune keeps entries of parse-error and skipped files. The gate prints `gate_removed` for analyzed files. The second prune line prints the occurrence count.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_cli.py`
  - Status: absent

- [ ] T006 [US4] Fail closed on a missing or invalid content anchor.
  - Requirements: FR-007
  - Files: `src/misthelper_devtools/test_quality_analyzer/baseline.py` (modify, serialization and validation, R-31 same blob)
  - Tests: `test_missing_content_anchor_exits_two` in `test_gate_decision.py`.
  - Acceptance: The loader rejects an entry without a valid anchor. The gate exits 2 and prints a baseline error. The loader reads no legacy format.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_gate_decision.py`
  - Status: absent

- [ ] T007 [US2] Prove the change isolates the identity behavior.
  - Requirements: FR-001, FR-002, FR-003
  - Files: `tests/tools/test_quality_analyzer/test_gate_decision.py` (modify, helper at line 20, R-48)
  - Tests: `test_three_configurations_isolate_the_identity_change`. The test runs three inputs: identical inputs, a line-only change, and a flagged-line change. It checks that only the flagged-line change adds a new finding.
  - Acceptance: The test passes. The line-only configuration produces zero new findings. The flagged-line configuration produces one new finding.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_gate_decision.py`
  - Status: absent

- [ ] T008 [US5] Bump the version to 0.7.0 and create the release commit and tag.
  - Requirements: FR-014
  - Files: `pyproject.toml` (modify, line 3, R-49)
  - Acceptance: The version reads 0.7.0. The release commit names the version. The tag `v0.7.0` points at the release commit.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer/test_cli.py`
  - Status: absent

Warning: a pushed release tag is public. Create the tag only after the pull request merges and the owner approves the release.

- [ ] T009 [US5] Open the upstream issue and pull request, then merge after owner review.
  - Requirements: FR-014
  - Files: the misthelper-devtools issue and pull request. No repository file beyond those in T001 to T008.
  - Acceptance: The issue names this record. The pull request body contains `Closes` for the issue. The title uses Conventional Commits. The owner approves the squash merge.
  - Verification: `python -m pytest tests/tools/test_quality_analyzer`
  - Status: absent

## MistHelper: after the release

- [x] T010 [P] [US1] Verify that the gate passes on main before the migration. (verified: CI run 45774119357 on head `f03c6c9b`, job `Test quality ratchet (gate)` succeeded, R-03, R-04)
  - Requirements: FR-016
  - Files: `.github/workflows/ci.yml` (lines 602-632, R-03, R-04). `.github/test-quality-baseline.json` (R-01)
  - Acceptance: The job exists, and the main gate passes before the migration.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: verified-present

- [x] T011 [P] [US4] Verify that the pinned analyzer prints the gate scope line. (verified: `__main__.py` lines 377 and 848-851, R-37, R-38)
  - Requirements: FR-008
  - Files: `.github/workflows/ci.yml` (R-04). misthelper-devtools `src/misthelper_devtools/test_quality_analyzer/__main__.py` (R-37, R-38)
  - Acceptance: The gate prints `gate_scope` with file and finding counts on each run.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: verified-present

- [ ] T012 [US3] Record that the pinned prune is file-level only.
  - Requirements: FR-005, FR-006
  - Files: `src/misthelper_devtools/test_quality_analyzer/baseline.py` (prune, R-35)
  - Acceptance: The record names the file-level prune as the current behavior, and the migration replaces it.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: partial

- [ ] T013 [P] [US1] Bump the analyzer pin to the 0.7.0 release commit.
  - Requirements: FR-014
  - Files: `requirements-dev.txt` (modify, line 197, R-06)
  - Acceptance: The line names the 0.7.0 release commit. No other line changes.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: absent

- [ ] T014 [US5] Regenerate the baseline with the new analyzer and record every dropped entry.
  - Requirements: FR-011, FR-012
  - Files: `.github/test-quality-baseline.json` (modify, R-01, R-24)
  - Acceptance: Each retained entry has a valid content anchor. Each retained `line_number` matches its entry on main. The migration proof in `design/quickstart.md` Step 7 prints `new_not_in_old=0`. The pull request lists each dropped entry and the total.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: absent

- [ ] T015 [P] [US1] Add the four end-to-end cases to the scope test file.
  - Requirements: FR-013
  - Files: `tests/guardrails/local_test_quality_loop/test_scope.py` (modify, add `TestBaselineIdentity` at the end of the file, R-13). `tests/guardrails/local_test_quality_loop/fixtures.py` (read, `AnalyzerFixture`, R-14)
  - Tests: `test_blank_line_above_finding_keeps_gate_green`, `test_added_weak_assertion_fails_gate`, `test_full_gate_reports_scope_counts`, and `test_baseline_entries_carry_content_anchors`.
  - Acceptance: Each test uses the installed analyzer through `AnalyzerFixture`. The line-move test exits 0. The new-assertion test exits 1 and prints one `gate_new` line. The scope test prints counts above 0. The anchor test checks the 64-character or `file-level` form on each entry.
  - Verification: `python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py`
  - Status: absent

- [ ] T016 [P] [US1] Update the test quality documentation.
  - Requirements: FR-015
  - Files: `.github/copilot-instructions.md` (modify, paragraph at lines 148-150, R-09, R-10). `documentation/quality-gates.md` (modify, lines 21-43, R-07, R-08)
  - Acceptance: The text names the content anchor, the occurrence count, the prune rule, and the migration. Every command line stays unchanged.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 .github/copilot-instructions.md documentation/quality-gates.md`
  - Status: absent

- [ ] T017 [P] [US5] Add the changelog fragment.
  - Requirements: FR-015
  - Files: `changelog.d/issue-3102-test-quality-baseline-identity.md` (add, R-19)
  - Acceptance: The fragment has one `###` heading. It has one bullet for each change type, and it names issue 3102 in the bullet.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-3102-test-quality-baseline-identity.md`
  - Status: absent

## MistHelper: pull request

- [ ] T-LOCAL-GATES Run each applicable local gate.
  - Requirements: FR-013, FR-016
  - Files: every file changed by T013 to T017
  - Acceptance: The preflight passes. The full-suite gate prints `gate: 0 new findings vs baseline`. The changed-scope gate exits 0. The scope tests pass. Ruff and Black pass. STE scores each changed document at 80 or above. The gates that do not apply are Types, Complexity, Security lint, Docstrings, Symbols, and Menu reference. They do not apply because no file under `src/` or `MistHelper.py` changes.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: absent

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-015
  - Files: the spec record folder `specs/numbered/0/0/0/4/4/4/0/2/3102-test-quality-baseline-identity/`, copied from the draft folder. The changelog fragment is renamed to `changelog.d/pr-<number>.md` with the actual pull request number (R-19).
  - Acceptance: The branch is `fix/3102-test-quality-baseline-identity`, created from `main` in a worktree. The commit uses a Conventional Commits subject, and its body contains `Closes #3102`. The pull request body lists the dropped entries and the local gate results.
  - Verification: `python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py`
  - Status: absent

- [ ] T-REMOTE-CI Watch the remote checks.
  - Requirements: FR-016
  - Files: none changed. The task reads the checks of the pull request.
  - Acceptance: `gh pr checks <number> --watch` reports every required check as successful. The job `Test quality ratchet (gate)` prints `gate: 0 new findings vs baseline`.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: absent

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes it, then verify main.
  - Requirements: FR-014, FR-016
  - Files: none changed. The task reads main after the merge.
  - Acceptance: Auto-merge starts only after remote checks pass and the orchestrator authorizes the merge. The squash merge creates one commit on main. `container-build.yml` runs on the merged revision, and its image revision label equals the merged commit SHA. The gate passes on main.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: absent

Caution: a commit pushed after a squash merge does not join the merged pull request. Open a new issue and branch from `main` for any later fix.

## Dependencies and execution order

- T001 to T007 form one upstream pull request. Task T009 opens that pull request and merges it after review.
- Task T008 runs after T009. It creates the release commit and the tag on the merged commit.
- Tasks T010 to T012 verify the MistHelper state before the migration.
- Tasks T013 and T014 run after T008. They merge in one MistHelper pull request.
- Tasks T015, T016, and T017 run in parallel after T013 and before T-LOCAL-GATES.
- T-LOCAL-GATES runs before T-PR. T-PR runs before T-REMOTE-CI. T-REMOTE-CI runs before T-MERGE.

## Notes

- Each `[P]` task changes a different file. The tasks can run in parallel.
- Record each task status change in this file.
- The count of planned tests is fifteen. Eleven tests are upstream, and four are MistHelper tests.
