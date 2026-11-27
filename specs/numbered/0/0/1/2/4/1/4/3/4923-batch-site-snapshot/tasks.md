# Tasks: Batch target site snapshot

**Input**: Feature record `specs\numbered\0\0\1\2\4\1\4\3\4923-batch-site-snapshot`. Read `spec.md` and `plan.md` before you start.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, and `design/contracts/`.

**Tests**: The spec requires tests. Write the tests first, then run them to see each new test fail before the code change.

**Order**: Tasks marked `[P]` touch different files, so they can run in parallel. Each task names one verification command from the local gates table.

## Format

- **[P]**: Safe to run in parallel with another `[P]` task. The files differ.
- **Requirements**: The FR-### IDs from `spec.md` that the task covers.
- **Status**: `open` for work not started. The status changes only after a verification command succeeds.

## Phase 1: Baseline

### T001 Record the baseline of the unit test file

- **Requirements**: FR-001, FR-008
- **Files**: `tests/unit/websocket_streams/web/test_ws_web_services.py` (modify, no edit in this task)
- **Acceptance**: The file passes before any edit. Record the pass count in the pull request body.
- **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q`
- **Depends**: none
- **Status**: open

## Phase 2: Tests first

### T002 [P] Write seven unit tests for the site snapshot

- **Requirements**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-010
- **Files**: `tests/unit/websocket_streams/web/test_ws_web_services.py` (modify)
- **Acceptance**: Add seven tests with a counting fake picker. Each new test fails before the code tasks.
- **Test list**: `test_site_checks_share_one_organization_read`, `test_discovery_refreshes_the_snapshot_for_later_checks`, `test_snapshot_older_than_the_lifetime_is_read_again`, `test_failed_refresh_clears_the_snapshot_and_raises`, `test_concurrent_site_checks_share_one_read`, `test_empty_organization_snapshot_is_reused`, `test_refresh_logs_start_and_finish_without_identifiers`
- **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q`
- **Depends**: T001
- **Status**: open

### T003 [P] Assert one read for each organization in the MSP integration test

- **Requirements**: FR-001
- **Files**: `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` (modify, lines 557 to 563)
- **Acceptance**: The read list equals `[ORG_A, ORG_B, ORG_C]`. The docstring states one read for each organization. The test fails before the code tasks.
- **Verification**: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py -q`
- **Depends**: T001
- **Status**: open

### T004 [P] Assert one organization B read after a site target read

- **Requirements**: FR-001
- **Files**: `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py` (modify, lines 137 to 147)
- **Acceptance**: After the site target read for site B, organization B has one `listOrgSites` read. The test fails before the code tasks.
- **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py -q`
- **Depends**: T001
- **Status**: open

## Phase 3: Implementation

### T005 Create the site snapshot module

- **Requirements**: FR-001, FR-003, FR-004, FR-005, FR-006, FR-010, FR-011
- **Files**: `src/mist/realtime/websocket_streams/web/services/pickers/site_snapshot.py` (add)
- **Acceptance**: The class holds rows, a read time, and a lock. Each line has an inline comment. Each read logs before and after.
- **Verification**: `python -m ruff check .`
- **Depends**: T002, T003, T004
- **Status**: open

### T006 Wire the snapshot into the batch target service

- **Requirements**: FR-002, FR-008, FR-012
- **Files**: `src/mist/realtime/websocket_streams/web/services/pickers/related.py` (modify, class `BatchTargetPickerService`, lines 49 to 100)
- **Acceptance**: `sites()` refreshes the snapshot. `targets()` passes the snapshot to the resolver. The response fields stay the same.
- **Verification**: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
- **Depends**: T005
- **Status**: open

### T007 Read the snapshot in the resolver

- **Requirements**: FR-001, FR-003, FR-007
- **Files**: `src/mist/realtime/websocket_streams/web/services/pickers/related.py` (modify, class `BatchTargetResolver`, lines 107 to 176)
- **Acceptance**: `_site_rows` reads the snapshot. The foreign-site refusal still occurs before any resource read.
- **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q`
- **Depends**: T006
- **Status**: open

### T008 [P] Add the changelog fragment

- **Requirements**: FR-009
- **Files**: `changelog.d/issue-4923-batch-site-snapshot.md` (add)
- **Acceptance**: The fragment has one `###` heading and one `Changed` bullet. The bullet names issue 4923.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Depends**: none
- **Status**: open

## Phase 4: Verification

### T009 Run the three affected test files together

- **Requirements**: FR-001 to FR-010
- **Files**: the three test files in T002, T003, and T004
- **Acceptance**: Each file passes. The seven new tests and the two updated tests pass.
- **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py tests/unit/ex_hardware_inventory/run/test_hardware_routing.py tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py -q`
- **Depends**: T003, T004, T007
- **Status**: open

## Final tasks

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-001 to FR-012
- **Files**: all changed files and the record Markdown files
- **Acceptance**: Each gate prints its expected result. A gate that does not apply has a stated reason.
- **Verification**: Run each command below separately, in this order, and stop at the first failure.
  1. `python -m py_compile MistHelper.py` gives no output. The constitution requires it before each commit.
  2. `python -m ruff check .` gives `All checks passed`.
  3. `python -m black --check .` reports that no file needs a change.
  4. `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` gives `Success`.
  5. `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` reports coverage of 80 percent or above.
  6. `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` prints one summary line.
  7. `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` prints one summary line for each shard.
  8. `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` passes the input preflight.
  9. `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` reports `gate: 0 new findings vs baseline`.
  10. `radon cc src/mist/realtime/websocket_streams/web/services/pickers -j | complexity-gate --max 10` reports no block above 10.
  11. `bandit -c pyproject.toml -r src/mist/realtime/websocket_streams/web/services/pickers -q` reports no finding.
  12. `pylint src/ --fail-under=9.5` reports a score of 9.5 or above.
  13. `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` reports no finding.
  14. `pydocstyle src/ wsgi.py web_portal` reports no violation, and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` passes.
  15. `symbol-diff --base origin/main src/mist/realtime/websocket_streams/web/services/pickers/related.py` reports `no module-level name changed`.
  16. `python -m pytest tests/guardrails tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py -q` passes.
  17. `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4923-batch-site-snapshot.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/spec.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/plan.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/tasks.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/analysis.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/research.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/data-model.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/quickstart.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/contracts/site-snapshot-interface.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/contracts/batch-target-route.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/checklists/requirements.md specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot/design/checklists/security.md` reports a score of 80 or above for each file.
  18. Not applicable: the menu reference gate, because no menu changes. The safe sweep, because `MistHelper.py` does not change. The ops portal and ops platform gates, because those trees do not change. The pip-audit gate, because no dependency file changes.
- **Depends**: T008, T009
- **Status**: open

### T-PR Commit, check the test quality diff, push, and open the pull request

- **Requirements**: FR-009, FR-010
- **Files**: the changed files and the record folder, added by explicit path
- **Acceptance**: The commit uses the title `perf(web-portal): read the organization site list once for each batch preview`. The diff review confirms an inline comment on each new or changed line. The body ends with `Closes #4923` and the session co-author trailer.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- **Depends**: T-LOCAL-GATES
- **Status**: open

### T-REMOTE-CI Watch the remote checks

- **Requirements**: FR-001 to FR-012
- **Files**: the pull request opened in T-PR
- **Acceptance**: Each required check shows green, including CodeQL. A failed check gets an issue with its full output before any fix.
- **Verification**: `gh pr checks fix/4923-batch-site-snapshot -R jmorrison-juniper/MistHelper --watch`
- **Depends**: T-PR
- **Status**: open

### T-MERGE Squash merge after authorization

- **Requirements**: FR-001 to FR-012
- **Files**: the pull request from T-PR
- **Acceptance**: Add the `auto-merge` label only after the orchestrator authorizes the merge. Confirm the container build on the merge commit passes.
- **Verification**: `gh run list -R jmorrison-juniper/MistHelper --workflow container-build.yml --limit 1 --json headSha,conclusion`
- **Depends**: T-REMOTE-CI
- **Status**: open

Caution: a squash merge changes `main`. Revert it with a new pull request. Do not force-push `main`.

Deployment and the health check need orchestrator approval. Record their result in the pull request.

## Requirement coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T002, T003, T004, T006, T007 | `test_site_checks_share_one_organization_read`, `test_discovery_refreshes_the_snapshot_for_later_checks`, the integration read-order test, the routing read-count test |
| FR-002 | T006 | `test_discovery_refreshes_the_snapshot_for_later_checks` |
| FR-003 | T005, T007 | `test_site_checks_share_one_organization_read`, `test_empty_organization_snapshot_is_reused` |
| FR-004 | T005 | `test_snapshot_older_than_the_lifetime_is_read_again` |
| FR-005 | T005 | `test_concurrent_site_checks_share_one_read` |
| FR-006 | T005 | `test_failed_refresh_clears_the_snapshot_and_raises` |
| FR-007 | T007 | `test_batch_target_picker_filters_families_and_rejects_foreign_sites` (existing, line 389) |
| FR-008 | T006 | `test_batch_target_picker_filters_families_and_rejects_foreign_sites` (existing, asserts `rows` and `excluded`) |
| FR-009 | T008 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-010 | T005 | `test_refresh_logs_start_and_finish_without_identifiers`. Inline comments are checked in the diff review of T-PR. |
| FR-011 | T005, T006, T007 | `tests/guardrails/test_move_module_guidance.py` and `tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py` in T-LOCAL-GATES |
| FR-012 | T006 | The existing site picker test at `test_ws_web_services.py`, line 326 |
