# Tasks: Duplicate PDF Corpus

**Input**: Numeric record `specs\numbered\0\0\0\4\3\4\0\2\2977-duplicate-pdf-corpus\`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design\research.md`, `design\data-model.md`, `design\contracts\`.

**Format**: An identifier such as T001, then an optional P marker, then the description. The P marker means the task can run in parallel with other P tasks. A task status is one of `open`, `verified-present`, `partial`, or `absent`. A blocked task names its blocker in the description.

## Phase 1: Verification of Merged Work

### T001 Confirm the prevention code on main

- Requirements: FR-001, FR-002, FR-004, FR-005, FR-006.
- Files: `src/mist/intelligence/juniper_docs/harvest/content_index.py`, `src/mist/intelligence/juniper_docs/acquire/downloader.py`, `tests/unit/juniper_docs/test_content_dedup.py`.
- Acceptance: Remote checks R02 to R06 hold on `main`. The CI checks of PR #4823 report SUCCESS (R54).
- Verification: `python -m pytest tests/unit/juniper_docs/test_content_dedup.py`.
- Status: verified-present.

### T002 Confirm the legacy record and its release note

- Requirements: FR-005, FR-006.
- Files: `specs/numbered/0/0/0/4/3/4/0/2/2977-harvest-index-moves/spec.md`, `changelog.d/issue-2977-harvest-index-moves.md`.
- Acceptance: Remote checks R27, R28, and R30 hold. The legacy claims are recorded in `analysis.md`. The legacy record remains unchanged.
- Verification: `python -m pytest tests/unit/juniper_docs/test_content_dedup.py`.
- Status: verified-present.

## Phase 2: Code and Tests

### T003 [P] Add the equal-size regression test

- Requirements: FR-003.
- Files: `tests/unit/juniper_docs/test_content_dedup.py`.
- Acceptance: The test `test_same_size_different_bytes_are_both_kept` registers one payload, then checks that `find` returns no match for a different payload of equal length. The test uses `tmp_path` only.
- Verification: `python -m pytest tests/unit/juniper_docs/test_content_dedup.py`.
- Status: absent.

### T004 [P] Write the manual sorter tests

- Requirements: FR-007, FR-008.
- Files: `tests/unit/juniper_docs/test_manual_sorter.py` (new).
- Acceptance: Three tests exist. `test_apply_moves_file_and_updates_local_path` checks the moved file and the new row value. `test_dry_run_changes_no_file_and_no_row` checks both stay unchanged. `test_missing_source_counts_missing_and_keeps_row` checks the missing count and the unchanged row. The apply test fails before T005.
- Verification: `python -m pytest tests/unit/juniper_docs/test_manual_sorter.py`.
- Status: absent.

### T005 Record new paths in the manual sorter

- Requirements: FR-007, FR-008.
- Depends on: T004.
- Files: `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py`.
- Acceptance: Apply mode runs `UPDATE documents SET local_path = ?, updated_at = ? WHERE root_url = ?` after each move. Dry-run mode writes nothing. `SortStats` holds `unrecorded`. Each new executable line carries an inline comment. Each write has an info line before it and a debug line after it. The contract `manual-sort-update.md` matches the code.
- Verification: `python -m pytest tests/unit/juniper_docs/test_manual_sorter.py`.
- Status: absent.

### T006 [P] Write the consolidator tests

- Requirements: FR-009, FR-013.
- Files: `tests/unit/juniper_docs/test_library_consolidator.py` (new).
- Acceptance: Four tests exist. `test_identical_bytes_under_two_sources_are_copied_once`, `test_same_name_different_bytes_keeps_both_with_suffix`, `test_source_files_are_unchanged_after_run`, and `test_stats_satisfy_duplicates_equals_scanned_minus_unique`. The tests use `tmp_path` and synthetic bytes. The tests pass on the current consolidator (R08, R09).
- Verification: `python -m pytest tests/unit/juniper_docs/test_library_consolidator.py`.
- Status: absent.

### T007 [P] Write the copy verifier tests

- Requirements: FR-010, FR-011, FR-012, FR-013.
- Files: `tests/unit/juniper_docs/test_copy_verifier.py` (new).
- Acceptance: Five tests exist. `test_inventory_records_relative_path_size_and_digest`, `test_compare_passes_when_library_matches_source_digests`, `test_compare_fails_when_a_library_file_has_no_source_match`, `test_source_changed_detects_a_modified_source_file`, and `test_preconditions_refuse_missing_or_overlapping_paths`. The tests fail before T008 because the module is absent.
- Verification: `python -m pytest tests/unit/juniper_docs/test_copy_verifier.py`.
- Status: absent.

### T008 Add the copy verifier module

- Requirements: FR-010, FR-011, FR-012, FR-013.
- Depends on: T007.
- Files: `src/mist/intelligence/juniper_docs/harvest/copy_verifier.py` (new).
- Acceptance: The module defines `CopyRunPreconditions`, `InventoryRow`, `CopyVerificationReport`, and `CorpusCopyVerifier`. All five tests pass. The contract `copy-run-verifier.md` matches the code. The module logs ASCII text only.
- Verification: `python -m pytest tests/unit/juniper_docs/test_copy_verifier.py`.
- Status: absent.

### T009 Add the two changelog fragments

- Requirements: FR-007, FR-010.
- Depends on: T005, T008.
- Files: `changelog.d/issue-2977-manual-sort-paths.md` (new), `changelog.d/issue-2977-copy-run-verifier.md` (new).
- Acceptance: Each fragment holds one `###` heading and one bullet. Each bullet names issue #2977. The fragment names the change type from `changelog.d/README.md`.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-2977-manual-sort-paths.md changelog.d/issue-2977-copy-run-verifier.md`.
- Status: absent.

## Phase 3: Historical Copy Run (blocked)

### T010 Record the copy-run inputs

- Requirements: FR-012.
- Depends on: T008.
- Blocker: The owner must record the source host, source path, copy root, output root, and target free bytes. The inputs appear in the checklist `design\checklists\copy-run-preconditions.md`.
- Files: `design\checklists\copy-run-preconditions.md` (this record).
- Acceptance: The checklist holds each owner value. The verifier accepts the five values. The copy root sits under `data\` and differs from the source root.
- Verification: `python -m pytest tests/unit/juniper_docs/test_copy_verifier.py`. Test `test_preconditions_refuse_missing_or_overlapping_paths` refuses a partial input set.
- Status: absent (blocked by owner input).

### T011 Copy the verified source into an empty library root

- Requirements: FR-009, FR-010.
- Depends on: T010.
- Blocker: Requires T010 and a stop of every harvest on the owner machine.
- Files: The source root and the copy root named in T010. No repository file changes.
- Acceptance: The copy root is empty before the run. The source inventory is saved before the copy. The consolidator statistics are saved after the copy.
- Verification: `python -m pytest tests/unit/juniper_docs/test_library_consolidator.py`.
- Status: absent (blocked by T010).

### T012 Verify the library copy and the source

- Requirements: FR-011, FR-013.
- Depends on: T011.
- Files: The report file named by the owner in T010. No repository file changes.
- Acceptance: The report passes. `source_changed` is false. The duplicate count is recorded in the successor issue. A mismatch stops the run.
- Verification: `python -m pytest tests/unit/juniper_docs/test_copy_verifier.py`.
- Status: absent (blocked by T011).

### T013 HUMAN-DECISION-REQUIRED: delete redundant copies from the source

- Requirements: FR-013.
- Depends on: T012 and a recorded human approval in the successor issue.
- Decision: D-10 in `design\research.md`. Warning: deletion removes production data and cannot be undone. The agent performs no deletion.
- Acceptance: No file in the source corpus is deleted without a recorded approval. Any approved deletion keeps one copy for each digest.
- Verification: `python -m pytest tests/unit/juniper_docs/test_copy_verifier.py`. Its source-change test confirms the source stays unchanged before any approval.
- Status: absent (blocked by human decision).

## Phase 4: Delivery

### T-LOCAL-GATES Run the applicable local gates

- Requirements: FR-001 to FR-013 (all changed code).
- Depends on: T003, T005, T006, T007, T008, T009.
- Files: The changed files listed in `plan.md`, section File Change Map.
- Acceptance: Each command below reports the expected result. The measured radon and pylint values for each touched file appear in the pull request body.
- Commands:
  - Compile: `python -m py_compile src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py src/mist/intelligence/juniper_docs/harvest/copy_verifier.py`. Expected: no output.
  - Lint: `python -m ruff check .`. Expected: `All checks passed`.
  - Format: `python -m black --check .`. Expected: no file needs a change.
  - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Expected: `Success`.
  - Tests: `python -m pytest tests/unit/juniper_docs`. Expected: all tests pass.
  - Preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. Expected: the preflight passes.
  - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected: coverage at 80 percent or above.
  - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. Expected: `gate: 0 new findings vs baseline`.
  - Complexity: `radon cc src/mist/intelligence/juniper_docs -j | complexity-gate --max 10`. Expected: no block above 10.
  - Security lint: `bandit -c pyproject.toml -r src/mist/intelligence/juniper_docs -q`. Expected: no finding.
  - Code quality: `pylint src/ --fail-under=9.5`. Expected: score 9.5 or above.
  - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`. Expected: no finding.
  - Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`. Expected: no violation.
  - Symbols: `symbol-diff --base origin/main` on each changed existing Python file listed in `plan.md`. Expected: exit code 0 and no lost name.
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file listed in `plan.md`. Expected: score 80 or above.
  - Not applicable: `python MistHelper.py --test` (no menu change), `pip-audit -r requirements.txt` (no dependency change), and the menu reference commands (no menu change).
- Verification: The commands above.
- Status: absent.

### T-PR Commit and open the pull request

- Requirements: All.
- Depends on: T-LOCAL-GATES, T009, and the owner confirmation of D-11.
- Files: The changed files, added by explicit path. Do not use `git add -A`.
- Acceptance: The title is `fix(juniper-docs): record manual sort paths and add copy verifier`. The branch is `fix/2977-duplicate-pdf-corpus`. The body holds `Closes #2977`, the successor issue number, the follow-up issue numbers for D-5 and D-6, and the local gate results. Before the pull request opens, the branch shows no file overlap with an open pull request.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`.
- Status: absent.

### T-REMOTE-CI Watch the remote checks

- Requirements: FR-001 to FR-013 (through the remote tests).
- Depends on: T-PR.
- Files: None changed.
- Acceptance: Each required check and the CodeQL check pass on the pull request head. A failed check opens a repair task. The repair uses a new commit on the same branch.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` (full-suite check, table row Test quality).
- Remote check: `gh pr checks --watch -R jmorrison-juniper/MistHelper` for the pull request that T-PR opens.
- Status: absent.

### T-MERGE Merge after authorization

- Requirements: All.
- Depends on: T-REMOTE-CI and the orchestrator authorization.
- Files: None changed.
- Acceptance: The `auto-merge` label is added only after each check passes. The squash merge produces one commit on `main`. The branch and worktree are removed after the merge.
- Verification: `python -m pytest tests/unit/juniper_docs` on the merged `main`.
- Status: absent.

## Dependencies

- T001 and T002 have no dependency.
- T003, T004, T006, and T007 are parallel. T005 depends on T004. T008 depends on T007. T009 depends on T005 and T008.
- T010 depends on T008. T011 depends on T010. T012 depends on T011. T013 depends on T012 and a human approval.
- T-LOCAL-GATES depends on the code and test tasks. T-PR depends on T-LOCAL-GATES and T009. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI and authorization.
