# Tasks: Multi-Site Confirm Page Plan Detail

**Input**: `spec.md` and `plan.md` in this record. The design files under `design/` define the contracts.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, and `design/contracts/`.

**Format**: Each task has an ID, a parallel marker, requirement IDs, exact repository paths, an acceptance statement, one verification command, and a status. The status values are `absent`, `partial`, `verified-present`, and `open`. Every task starts as `absent` because no change exists on `main` at base `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Tests**: The spec requires tests. Sixteen tests are planned: unit tests U1 to U8, contract tests C1 to C6, browser test E1, and journey test J1. Tests come before the implementation.

## Phase 1: Setup

### T001 Create the worktree and baseline

- Parallel: no
- Requirements: FR-015
- Paths: `scripts/bootstrap_worktree.py`
- Acceptance: The worktree starts from the current `origin/main`. The branch name is `fix/3222-multi-site-confirm-details`. The bootstrap completes and the Lint gate passes on the clean tree.
- Verify: `python -m ruff check .`
- Status: absent

## Phase 2: Tests first

### T002 Add unit tests U1 to U8

- Parallel: yes, different file from T003, T004, and T005
- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-008, FR-012
- Paths: `tests/unit/upgrade_portal/test_org_child_controls.py`
- Acceptance: Eight tests cover site, device, route, and phase rows, the cloud call count, the stable build flag, unknown families, missing details, and AP-only plans. Each test fails before T006.
- Verify: `python -m pytest tests\unit\upgrade_portal\test_org_child_controls.py`
- Status: absent

### T003 Add contract tests C1 to C6

- Parallel: yes, different file from T002, T004, and T005
- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-008, FR-009, FR-011, FR-012, FR-013, FR-014
- Paths: `tests/contract/upgrade_portal/test_org_upgrade_routes.py`
- Acceptance: Six tests cover the rendered sections, the disabled typed field, the refusal before any write, and escaped names. They also cover the AP-only page and the zero extra cloud calls. The refusal test and the disabled-field test fail before T007 and T008.
- Verify: `python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py`
- Status: absent

### T004 Replace the journey expected failure with row assertions

- Parallel: yes, different file from T002, T003, and T005
- Requirements: FR-001, FR-002, FR-003, FR-004, SC-006
- Paths: `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`
- Acceptance: The test `test_confirm_page_names_the_sites_and_the_schedule` loses its expected-failure marker. The test selects the canary strategy. It sets the phases and the failure limit, and asserts each site row, each route row, each device row, and the phase row. The test fails before T008.
- Verify: `python -m pytest tests\e2e\upgrade_portal\journeys\test_upj_multisite_journeys.py`
- Status: absent

### T005 Add device row checks to the browser flow

- Parallel: yes, different file from T002, T003, and T004
- Requirements: FR-003, FR-008, FR-014
- Paths: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`
- Acceptance: The test `test_multisite_options_confirmation_progress_and_cancel` asserts one device row for each of the six planned devices. It also asserts that the start control stays disabled until `CONFIRM` is typed. The row assertion fails before T008.
- Verify: `python -m pytest tests\e2e\upgrade_portal\test_org_upgrade_flow.py`
- Status: absent

## Phase 3: Implementation

### T006 Implement the OrgConfirmPlanView builder

- Parallel: no
- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-008, FR-012, FR-014
- Paths: `src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py`
- Acceptance: The class `OrgConfirmPlanView` has five members. The method `build` returns the keys in the data model and the rules in `design/contracts/confirm-plan-view.md`. The method makes no cloud call. Each line has an inline comment. The info and debug log lines carry counts only. Tests U1 to U8 pass.
- Verify: `python -m pytest tests\unit\upgrade_portal\test_org_child_controls.py`
- Status: absent

### T007 Wire the view into the confirm and submit routes

- Parallel: no
- Requirements: FR-008, FR-009, FR-012, FR-013
- Paths: `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
- Acceptance: `confirm_page()` passes `confirm_plan` to the template. `submit_upgrade()` returns the refusal in `design/contracts/submit-refusal.md` for an incomplete plan. The refusal runs before the pre-check gate and before any lock or submit call. An AP-only request keeps its current path. Tests C2, C3, and C5 pass.
- Verify: `python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py`
- Status: absent

### T008 Render the sections and update the render helper

- Parallel: no
- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-010, FR-011, FR-014
- Paths: `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html`, `tests/contract/upgrade_portal/test_issue_3390_confirm_strategy_wording.py`
- Acceptance: The template renders the sections and the labels in `design/contracts/confirm-page.md`. The family line at line 54 uses the labels. The disabled condition at line 189 includes `confirm_plan.complete`. The strict render helper passes `confirm_plan`, and its existing assertions still pass. Tests C1, C2, C4, and C6 pass.
- Verify: `python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py`
- Status: absent

### T009 Confirm the preserved texts and identifiers

- Parallel: no
- Requirements: FR-010, FR-013
- Paths: `tests/contract/upgrade_portal/test_issue_3452_confirm_scope_text.py`, `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`, `tests/e2e/upgrade_portal/test_org_empty_site.py`
- Acceptance: The scope warning text, the pre-check button text, the "Sites: 1" line, the strategy line, and the start identifiers stay byte-identical. The existing tests pass without edits to their assertions.
- Verify: `python -m pytest tests\contract\upgrade_portal\test_issue_3452_confirm_scope_text.py`
- Status: absent

## Phase 4: Browser proof and documentation

### T010 Prove the journey passes

- Parallel: yes, different file from T011
- Requirements: FR-001, FR-002, FR-003, FR-004, SC-006
- Paths: `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py`
- Acceptance: Test J1 passes without an expected-failure marker. The run records the Playwright output in the pull request body.
- Verify: `python -m pytest tests\e2e\upgrade_portal\journeys\test_upj_multisite_journeys.py`
- Status: absent

### T011 Prove the browser flow passes

- Parallel: yes, different file from T010
- Requirements: FR-003, FR-008, FR-014
- Paths: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`
- Acceptance: Test E1 passes. The start control stays disabled until the operator types `CONFIRM`.
- Verify: `python -m pytest tests\e2e\upgrade_portal\test_org_upgrade_flow.py`
- Status: absent

### T012 Update the parity matrix row C25 when J1 passes

- Parallel: no
- Requirements: FR-016
- Paths: `tests/e2e/upgrade_portal/journeys/parity_matrix.json`, `specs/3200-upgrade-portal-journeys/parity-matrix.md`
- Acceptance: Run this task only after T010 passes. Row C25 changes its multi-site status and verdict. Its issue field becomes null. Both files carry the same row. If T010 fails, make no change to either file.
- Verify: `python -m pytest tests\contract\upgrade_portal\test_journey_parity_matrix.py`
- Status: absent

### T013 Update the portal document

- Parallel: yes, different file from T014
- Requirements: FR-016
- Paths: `documentation/upgrade_capture_portal.md`
- Acceptance: The section "Confirm and start the upgrade" names each new section of the multi-site confirm page. It states that a missing detail blocks the start. The text follows Simplified Technical English.
- Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/upgrade_capture_portal.md`
- Status: absent

### T014 Add the release note

- Parallel: yes, different file from T013
- Requirements: FR-016
- Paths: `changelog.d/issue-3222-multi-site-confirm-details.md`
- Acceptance: The fragment has one `###` heading and one `Fixed` item. The item names issue 3222 and states the new confirm page content.
- Verify: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-3222-multi-site-confirm-details.md`
- Status: absent

### T015 Copy the record into the branch

- Parallel: no
- Requirements: FR-015
- Paths: `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/spec.md`, `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/plan.md`, `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/tasks.md`, `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/analysis.md`, `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/design/research.md`
- Acceptance: The record folder holds the same files as the draft folder. Each file passes the STE gate. The folder holds five children or fewer at each level.
- Verify: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/spec.md`
- Status: absent

## Phase 5: Gates and delivery

### T-LOCAL-GATES Run each applicable local gate

- Parallel: no
- Requirements: FR-015, FR-016
- Paths: the 12 changed paths in `plan.md`, section "File-by-File Change Map"
- Acceptance: Every gate in `plan.md`, section "Local Gates for This Change", passes with its expected result. The full test shards run every planned test. The record shows the actual output of each command.
- Verify: `python -m ruff check .`
- Status: absent

### T-PR Commit, push, and open the pull request

- Parallel: no
- Requirements: FR-015
- Paths: the 12 changed paths in `plan.md`, section "File-by-File Change Map", and the five record paths in T015
- Acceptance: One Conventional Commit has the subject `fix(upgrade-portal): show planned sites, child routes, devices, and phases on the confirm page`. The pull request body contains `Closes #3222`. The overlap check finds no other open pull request on the same route file. The branch name is `fix/3222-multi-site-confirm-details`.
- Verify: `symbol-diff --base origin/main src\interfaces\portals\upgrade_portal\app\routes\org_upgrade.py`
- Status: absent

### T-REMOTE-CI Watch the remote checks

- Parallel: no
- Requirements: FR-015
- Paths: the pull request created by T-PR
- Acceptance: Every required check is green. The Full tests gate matches the local result. Run `gh pr checks <number> --watch` once for the final commit.
- Verify: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
- Status: absent

### T-MERGE Enable auto-merge after the human review

- Parallel: no
- Requirements: FR-015
- Paths: the pull request created by T-PR
- Acceptance: The orchestrator authorizes the merge. A human completes the safety review that the `needs-human-review` label names. After both conditions hold, enable auto-merge. Do not enable it before the review.
- Verify: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: absent

## Dependencies and Execution Order

- T001 comes first.
- T002, T003, T004, and T005 run in parallel after T001.
- T006 depends on T002.
- T007 depends on T003 and T006.
- T008 depends on T007.
- T009 depends on T008.
- T010 and T011 depend on T008. They run in parallel.
- T012 depends on T010.
- T013 and T014 depend on T008. They run in parallel.
- T015 depends on T013 and T014.
- T-LOCAL-GATES depends on T009, T010, T011, T012, T013, T014, and T015.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the human safety review.

## Requirement Traceability

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T002, T003, T004, T006, T008, T010 | U1, C1, J1 |
| FR-002 | T002, T003, T004, T006, T008, T010 | U3, C1, J1 |
| FR-003 | T002, T003, T004, T005, T006, T008, T011 | U2, C1, E1, J1 |
| FR-004 | T002, T003, T004, T006, T008, T010 | U4, C1, J1 |
| FR-005 | T002, T003, T006, T008 | U3, C1 |
| FR-006 | T003, T008 | C1 |
| FR-007 | T002, T006, T008 | U6 |
| FR-008 | T002, T003, T005, T006, T007, T008, T011 | U5, U7, C2, E1 |
| FR-009 | T003, T007 | C3 |
| FR-010 | T008, T009 | Existing regression tests in T009 and the updated helper in T008 |
| FR-011 | T003, T008 | C4 |
| FR-012 | T002, T006, T007 | U8, C5 |
| FR-013 | T003, T007, T009 | C6 and existing regression tests |
| FR-014 | T003, T005, T006, T008, T011 | C1, E1 |
| FR-015 | T001, T015, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE | All sixteen planned tests in the full test shards |
| FR-016 | T012, T013, T014, T-LOCAL-GATES | STE gate on the changed Markdown files and the full guardrail shard |

## Planned Tests

| ID | File | Test name | Requirements |
| - | - | - | - |
| U1 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_site_rows_name_each_selected_site_and_its_device_count` | FR-001 |
| U2 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_device_rows_carry_site_name_mac_model_family_and_versions` | FR-003 |
| U3 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_route_rows_and_cloud_call_count_follow_the_child_routes` | FR-002, FR-005 |
| U4 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_phase_rows_list_the_phases_and_failure_limits_each_body_sends` | FR-004 |
| U5 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_an_unknown_device_family_token_blocks_the_plan` | FR-008 |
| U6 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_a_stable_child_marks_its_switch_and_gateway_devices_as_stable` | FR-007 |
| U7 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_each_missing_detail_blocks_the_plan_and_names_its_subject` | FR-008 |
| U8 | `tests/unit/upgrade_portal/test_org_child_controls.py` | `test_a_plan_without_child_routes_stays_complete_with_empty_rows` | FR-012 |
| C1 | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | `test_confirm_page_renders_sites_routes_devices_phases_and_call_count` | FR-001 to FR-006, FR-014 |
| C2 | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | `test_missing_detail_keeps_the_typed_field_disabled_with_ready_prechecks` | FR-008 |
| C3 | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | `test_submit_refuses_an_incomplete_plan_before_any_write` | FR-009 |
| C4 | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | `test_device_and_site_names_render_as_escaped_text` | FR-011 |
| C5 | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | `test_a_plan_without_child_routes_keeps_the_ap_only_page` | FR-012 |
| C6 | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | `test_confirm_page_get_adds_no_cloud_call_beyond_the_existing_reads` | FR-013 |
| E1 | `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` | `test_multisite_options_confirmation_progress_and_cancel` (extended) | FR-003, FR-008, FR-014 |
| J1 | `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py` | `test_confirm_page_names_the_sites_and_the_schedule` (expected failure removed) | FR-001 to FR-004, SC-006 |
