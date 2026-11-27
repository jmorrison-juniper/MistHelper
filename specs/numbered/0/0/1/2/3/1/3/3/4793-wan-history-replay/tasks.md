# Tasks: WAN history replay safety

**Input**: Numeric records from `specs/numbered/0/0/1/2/3/1/3/3/4793-wan-history-replay/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `design/research.md`, `design/data-model.md`, `design/contracts/sample-replay.md`, and `design/quickstart.md`.

**Tests**: The specification requires tests. Seven new tests are planned. Tests N1 to N4 target missing behavior, so they fail before their implementation tasks. Tests N5 to N7 guard behavior that the candidate already has, so they pass before and after Phase 3. Use mocked Arango responses and real SQLite under `tmp_path`.

**Organization**: Tasks run in five phases. Phase 1 verifies present code. Phase 2 writes tests, and tests N1 to N4 fail first. Phase 3 changes code. Phase 4 updates documents. The final tasks run the gates, the pull request, the remote checks, and the merge.

**Ownership**: Edit only the files named in each task. Do not edit `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. Use explicit paths for each `git add`.

**Environment**: Run Python from the worktree of the candidate branch, in the `.venv` of that worktree.

## Format

- `[P]`: The task can run in parallel with other `[P]` tasks of its phase. It edits a different file.
- Requirement IDs name the `FR-###` rows of `spec.md` that the task serves.
- Status is one of `open`, `verified-present`, `partial`, or `absent`.
- Tick a box only after the delivered file passes the verification command.

## Phase 1: Verify present behavior (read-only)

- [ ] T001 [FR-001, FR-003, FR-004, FR-011]
  - Files: `src/interfaces/wan_performance/integration/sqlite_history.py`, `tests/unit/wan_performance/test_history_repository.py`
  - Acceptance: Tests `test_sqlite_api_sample_replay_keeps_one_original_sample`, `test_sqlite_rejects_changed_api_sample_without_replacing_prior_rows`, `test_sqlite_rolls_back_entire_failed_batch`, and `test_round_trip_and_idempotent_upsert` exist and pass.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: verified-present

- [ ] T002 [FR-005, FR-006]
  - Files: `src/interfaces/wan_performance/integration/record_codec.py`
  - Acceptance: `SampleReplayPolicy._source_payload` removes `collected_at_utc` before the comparison.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: verified-present

- [ ] T003 [FR-002, FR-004]
  - Files: `src/interfaces/wan_performance/integration/arango_history.py`, `tests/unit/wan_performance/test_history_repository.py`
  - Acceptance: Test `test_arango_api_sample_replay_is_idempotent_and_rejects_changes` exists. The commit result on line 178 is not checked.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: partial

## Phase 2: Write tests (N1 to N4 fail first)

- [ ] T004 [FR-007]
  - Files: `tests/unit/wan_performance/test_history_repository.py`
  - Acceptance: Test `test_arango_upsert_rejects_unconfirmed_commit` makes `commit_transaction` return False and expects ConnectionError.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: absent

- [ ] T005 [FR-008]
  - Files: `tests/unit/wan_performance/test_history_repository.py`
  - Acceptance: Test `test_arango_rollback_failure_keeps_original_error` makes `abort_transaction` raise OSError and expects the original ConnectionError.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: absent

- [ ] T006 [FR-013]
  - Files: `tests/unit/wan_performance/test_history_repository.py`
  - Acceptance: Test `test_changed_sample_error_names_source_time` expects the sampled time isoformat in the ValueError text.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: absent

- [ ] T007 [P] [FR-009]
  - Files: `tests/unit/wan_performance/test_snapshot_records.py`
  - Acceptance: Test `test_rate_samples_reject_conflicting_duplicate_values` expects ValueError. Test `test_rate_samples_accept_identical_duplicate_values` expects one sample.
  - Verify: `python -m pytest tests/unit/wan_performance/test_snapshot_records.py`
  - Status: absent

- [ ] T008 [P] [FR-010, FR-012]
  - Files: `tests/unit/wan_performance/test_live_service.py`
  - Acceptance: Test `test_port_refresh_stores_repeated_api_samples_once` stores six API samples once. Test `test_port_refresh_keeps_distinct_poll_observations` keeps two poll samples.
  - Verify: `python -m pytest tests/unit/wan_performance/test_live_service.py`
  - Status: absent

## Phase 3: Change code after Phase 2 fails

- [ ] T009 [FR-007, FR-002]
  - Files: `src/interfaces/wan_performance/integration/arango_history.py` (lines 133 to 183), `tests/unit/wan_performance/test_history_repository.py` (lines 824 to 836, 859 to 873, 881 to 907)
  - Acceptance: `ArangoHistory.upsert` raises ConnectionError when the commit result is not True. Three mocked tests return True from the commit.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: absent

- [ ] T010 [FR-008]
  - Files: `src/interfaces/wan_performance/integration/arango_history.py` (lines 179 to 182)
  - Acceptance: The error branch calls `ArangoArchive._abort` and re-raises the original error.
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: absent

- [ ] T011 [P] [FR-013]
  - Files: `src/interfaces/wan_performance/integration/record_codec.py` (lines 421 to 424)
  - Acceptance: The ValueError text includes `current.sampled_at_utc.isoformat()` and keeps the phrase "conflicts with stored source data".
  - Verify: `python -m pytest tests/unit/wan_performance/test_history_repository.py`
  - Status: absent

- [ ] T012 [P] [FR-009]
  - Files: `src/interfaces/wan_performance/collection/snapshot_records.py` (lines 230 to 255)
  - Acceptance: A second value for one metric and timestamp raises ValueError. An equal second value passes.
  - Verify: `python -m pytest tests/unit/wan_performance/test_snapshot_records.py`
  - Status: absent

## Phase 4: Update documents

- [ ] T013 [P] [FR-014]
  - Files: `documentation/wan-performance.md` (lines 46 and 437 to 443), `changelog.d/pr-4208.md` (line 19)
  - Acceptance: The raw sample section states the rules of FR-004, FR-007, and FR-009. The #4793 sentence names the within-response rule.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/wan-performance.md changelog.d/pr-4208.md`
  - Status: partial

## Final tasks

- [ ] T-LOCAL-GATES [FR-001 to FR-014]
  - Files: Every file named in T001 to T013 and in `plan.md` Source Code.
  - Acceptance: Each applicable gate row of the local gates table reports its expected result. Each changed module passes the Symbols gate. The `tests/unit` shard reports one summary line.
  - Verify: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - Status: open

- [ ] T-PR [FR-014, FR-012]
  - Files: The changed files of T-LOCAL-GATES. The body of pull request #4208.
  - Acceptance: The branch rebases onto `origin/main`. The body contains `Closes #4793` and the local gate results. Warning: a rebase rewrites the candidate head. Confirm the head SHA first.
  - Verify: `symbol-diff --base origin/main src/interfaces/wan_performance/integration/arango_history.py`
  - Status: open

- [ ] T-REMOTE-CI [FR-014]
  - Files: Pull request #4208.
  - Acceptance: `gh pr checks 4208 -R jmorrison-juniper/MistHelper --watch` reports success for each required check, including CodeQL.
  - Verify: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - Status: open

- [ ] T-MERGE [FR-012]
  - Files: Pull request #4208. Blocked until the owner decides Decision D-8.
  - Acceptance: Before the merge, run the Symbols gate against `origin/main` for each changed module. After owner approval, add the `auto-merge` label and squash merge. Then confirm `main` holds the changed files, the `container-build.yml` revision equals the merged SHA, and issue #4793 closes.
  - Verify: `symbol-diff --base origin/main src/interfaces/wan_performance/integration/record_codec.py`
  - Status: open

## Dependencies and Order

- T001, T002, and T003 run first. They read the candidate code only.
- T004 to T006 share one file, so they run in order. T007 and T008 run in parallel with them.
- T009 needs T004 and T005 to fail first. T010 follows T009 in the same file.
- T011 and T012 run in parallel after T006 and T007 fail.
- T013 runs in parallel with Phase 3.
- T-LOCAL-GATES needs T009 to T013. T-PR needs T-LOCAL-GATES. T-REMOTE-CI needs T-PR. T-MERGE needs T-REMOTE-CI and Decision D-8.
