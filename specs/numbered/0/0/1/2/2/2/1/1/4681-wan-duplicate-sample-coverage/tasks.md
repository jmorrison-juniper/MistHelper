# Tasks: WAN Duplicate Sample Coverage

**Input**: `plan.md`, `spec.md`, and the `design/` artifacts in this folder.

**Prerequisite**: PR #4208 releases both affected files. Task T002 tracks this prerequisite.

**Format**: `ID [P?] [Requirement IDs] Description`. The `[P]` marker shows that a task can run in parallel with other `[P]` tasks in the same phase. Each task lists its paths, acceptance statement, verification command, and status. Status values are `open`, `verified-present`, `partial`, or `absent`. Code tasks use one command from the local gates table in `design/quickstart.md`. Process tasks use a read-only `gh` check.

## Phase 1: Verify the Defect and Wait for the Dependency

- [ ] T001 [FR-012] Verify that the PR #4208 head holds the defect. Status: verified-present.
  - Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`, `src/interfaces/wan_performance/domain/summary.py`.
  - Acceptance: Blob `88899eecece6666c6c3a7b377fe1e3d703ee1bd4` and blob `d9862865a7236ada781de566e35c5b5aa57dd130` match. Lines 266, 285, 322, 357, and 435 match.
  - Verify: `gh api "repos/jmorrison-juniper/MistHelper/contents/src/interfaces/wan_performance/collection/snapshot_client.py?ref=843be63bc837513b4442dae69da9f0db922e0ed1" --jq .sha`

- [ ] T002 [FR-012] Wait for PR #4208 to merge or release both files. Status: open.
  - Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`, `src/interfaces/wan_performance/domain/summary.py`.
  - Acceptance: The PR #4208 state is `MERGED`. Or the owner records a written release on issue #4681.
  - Verify: `gh pr view 4208 -R jmorrison-juniper/MistHelper --json state --jq .state`
  - Depends on: none.

## Phase 2: Write the Tests First

- [ ] T003 [P] [FR-001, FR-002, FR-003, FR-004, FR-005, FR-010] Add three in-response duplicate tests to the gateway insight test module. Status: absent.
  - Paths: `tests/unit/wan_performance/test_gateway_insights.py`.
  - Acceptance: The tests cover an identical duplicate, a conflicting duplicate with a log assertion, and a duplicate plus a missing interval. The tests fail before T006.
  - Verify: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py -k duplicate`
  - Depends on: T002.

- [ ] T004 [FR-006, FR-007] Add congestion and utilization tests for six known intervals, five known intervals, and unique aligned points. Status: absent.
  - Paths: `tests/unit/wan_performance/test_gateway_insights.py`.
  - Acceptance: Six known intervals produce congestion values. Five known intervals produce no congestion value. Utilization counts unique aligned points.
  - Verify: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py -k "congestion or utilization"`
  - Depends on: T003. This task edits the same file as T003.

- [ ] T005 [P] [FR-008] Add summary tests for five samples and six samples at full coverage. Status: absent.
  - Paths: `tests/unit/wan_performance/test_calendar_summaries.py`.
  - Acceptance: Five samples add no minutes and no complete hour. Six samples add minutes and one complete hour.
  - Verify: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -k congestion`
  - Depends on: T002.

## Phase 3: Implement the Fix

- [ ] T006 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-009, FR-010] Keep one point for each expected interval and reject conflicting duplicates in `GatewayInsights._sample_points`. Status: absent.
  - Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`.
  - Acceptance: The T003 tests pass. The signature keeps six parameters, and the plan records that violation. Each changed line has an inline comment.
  - Verify: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py`
  - Depends on: T003.

- [ ] T007 [FR-006, FR-007, FR-009] Confirm that the utilization, alignment, and congestion code reads unique points after T006. Status: open.
  - Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`.
  - Acceptance: No logic change is needed in `_sample`, `_utilization`, `_validate_rate_alignment`, or `_congestion_metric`. The existing contract tests pass.
  - Verify: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py -k "raw_utilization or selected_port or insights_use_actual"`
  - Depends on: T004, T006.

- [ ] T008 [P] [FR-008] Add the sample-count guard with the class attribute `SAMPLES_PER_HOUR` to `CongestionDurations`. Status: absent.
  - Paths: `src/interfaces/wan_performance/domain/summary.py`.
  - Acceptance: The T005 tests pass. The class adds one attribute and no top-level name.
  - Verify: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py`
  - Depends on: T005.

- [ ] T009 [FR-010] Add inline comments and action logs to each touched block. Status: absent.
  - Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`, `src/interfaces/wan_performance/domain/summary.py`.
  - Acceptance: Each changed executable line has a same-line comment. `_sample_points` logs before and after validation. Logs use ASCII only.
  - Verify: `python -m ruff check .` and a line-by-line review of the diff.
  - Depends on: T006, T008.

## Phase 4: Release Note and Documentation

- [ ] T010 [P] [FR-011] Add the changelog fragment. Status: absent.
  - Paths: `changelog.d/issue-4681-wan-duplicate-sample-coverage.md`.
  - Acceptance: The file has one `###` heading and one `**Fixed**` bullet that names issue #4681. The file name follows the rule in `changelog.d/README.md`.
  - Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Depends on: T006, T008.

- [ ] T011 [P] [FR-011] Update the coverage rule in the WAN documentation. Status: absent.
  - Paths: `documentation/wan-performance.md`.
  - Acceptance: Lines 321 and 431 state the one-count rule and the conflict rule. The text contains the phrase "Each expected interval counts once."
  - Verify: `git grep -n "Each expected interval counts once" -- documentation/wan-performance.md`
  - Depends on: T006, T008.

## Phase 5: Gates, Pull Request, CI, and Merge

- [ ] T-LOCAL-GATES [FR-009, FR-010] Run each applicable local gate on the changed files. Status: open.
  - Paths: the six paths in `plan.md`, section "Source Code (repository paths)".
  - Acceptance: Each gate in `design/quickstart.md`, section "Local gates", reports its expected result.
  - Verify: The commands in `design/quickstart.md`, section "Local gates".
  - Depends on: T007, T009, T010, T011.

- [ ] T-PR [FR-011] Commit, push, and open the pull request. Status: open.
  - Paths: The branch `fix/4681-wan-duplicate-sample-coverage`.
  - Acceptance: The commit subject is `fix(web-portal): count each WAN sample interval once`. The pull request body contains `Closes #4681`.
  - Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json body --jq .body`
  - Depends on: T-LOCAL-GATES.

- [ ] T-REMOTE-CI [SC-005] Watch the CI run on the pull request. Status: open.
  - Paths: None.
  - Acceptance: Each required check reports success on the latest commit.
  - Verify: `gh pr checks <number> -R jmorrison-juniper/MistHelper`
  - Depends on: T-PR.

- [ ] T-MERGE [FR-012] Add the `auto-merge` label and squash merge after the orchestrator authorizes the merge. Status: open.
  - Paths: None.
  - Acceptance: The pull request state is `MERGED`. The branch and the worktree are removed.
  - Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state --jq .state`
  - Depends on: T-REMOTE-CI.
