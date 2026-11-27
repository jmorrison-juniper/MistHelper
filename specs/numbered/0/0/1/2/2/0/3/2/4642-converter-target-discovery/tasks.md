# Tasks: Read-only Mist target discovery for converter proposals

**Input**: Numeric record `specs/numbered/0/0/1/2/2/0/3/2/4642-converter-target-discovery/`.

**Precondition**: Issues #4634 and #4641 close before task T009 starts. Both are OPEN on 2026-11-26.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

**Format**: `[ID] [P?] Title | Requirements | Status`. The `[P]` marker means that the task can run in parallel with the other `[P]` tasks in its group. Each task names exact paths, an acceptance statement, and one verification command from the Tests row of the local gates table (R89 and R90). Status values: `open`, `verified-present`, `partial`, or `absent`. A status of `absent` means that the deliverable does not exist on `main` (R79 to R83).

## Test Cases

The module `tests/integration/web_portal/cisco_config_converter/test_discovery.py` holds TC-01 to TC-22. The module `tests/e2e/web_portal/test_portal_smoke.py` holds TC-23 and TC-24.

| ID | Test | Covers |
| - | - | - |
| TC-01 | `test_sdk_read_signatures_match_contract` | FR-004 |
| TC-02 | `test_discovery_calls_only_read_functions_and_no_socket` | FR-005, FR-006, FR-020, SC-002, SC-004 |
| TC-03 | `test_status_verified_with_memberships` | FR-001, FR-007 |
| TC-04 | `test_verified_absence_for_empty_site_list` | FR-002, SC-001 |
| TC-05 | `test_sites_collect_all_pages` | FR-010, SC-003 |
| TC-06 | `test_full_page_without_total_header_fails` | FR-003, FR-010 |
| TC-07 | `test_lost_later_page_fails_not_empty` | FR-003, FR-010 |
| TC-08 | `test_page_limit_breach_fails` | FR-010 |
| TC-09 | `test_unavailable_without_session` | FR-001, FR-007, FR-008 |
| TC-10 | `test_unavailable_on_429_502_503_504` | FR-015 |
| TC-11 | `test_unavailable_without_response_status` | FR-015 |
| TC-12 | `test_denied_on_401_and_403` | FR-001, FR-015 |
| TC-13 | `test_denied_when_organization_not_a_membership` | FR-009 |
| TC-14 | `test_failed_on_400_404_500_and_client_exception` | FR-001, FR-015 |
| TC-15 | `test_failed_on_unexpected_payload` | FR-001, FR-003 |
| TC-16 | `test_duplicate_site_names_flagged` | FR-011 |
| TC-17 | `test_gateways_split_assigned_and_unassigned` | FR-012 |
| TC-18 | `test_invalid_organization_identifier_rejected` | FR-018 |
| TC-19 | `test_responses_and_logs_hold_no_token` | FR-016 |
| TC-20 | `test_discovery_responses_send_no_store` | FR-019 |
| TC-21 | `test_preview_available_without_session` | FR-008, FR-013 |
| TC-22 | `test_page_renders_discovery_markers` | FR-013 |
| TC-23 | `test_discovery_unavailable_state_in_browser` (e2e) | FR-013, FR-008 |
| TC-24 | `test_target_change_dispatches_invalidation_event` (e2e) | FR-014 |

## Phase 1: Baseline and Failing Tests

- [ ] **T001** [P] Baseline the offline converter tests. Requirements: FR-001. Status: `verified-present`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_routes.py` (R22 shows the fixture).
  - Acceptance: The existing offline tests pass before any change.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Requires: none.

- [ ] **T002** [P] Write failing SDK-contract, no-write, and no-socket tests (TC-01, TC-02). Requirements: FR-004, FR-005, FR-006, FR-020. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py` (new, R80 shows it is absent).
  - Acceptance: TC-01 and TC-02 fail before implementation, for the reason of the missing module.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

- [ ] **T003** [P] Write failing result and pagination tests (TC-03 to TC-08). Requirements: FR-001, FR-002, FR-003, FR-010. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py`.
  - Acceptance: Each test asserts `state`, `reason`, `pages`, and `items`. Each test fails before implementation.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

- [ ] **T004** [P] Write failing unavailable and session tests (TC-09 to TC-11). Requirements: FR-007, FR-008, FR-015. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py`.
  - Acceptance: The session stub returns no record, so each check answers `no_session`. HTTP statuses 429, 502, 503, and 504 give Unavailable.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

- [ ] **T005** [P] Write failing denied and failed tests (TC-12 to TC-15). Requirements: FR-001, FR-003, FR-009, FR-015. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py`.
  - Acceptance: HTTP 401 and 403 give Denied. HTTP 400, 404, and 500 give Failed. A payload without a list gives Failed.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

- [ ] **T006** [P] Write failing site and gateway tests (TC-16, TC-17). Requirements: FR-011, FR-012. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py`.
  - Acceptance: Two equal names set `duplicate_name` on both rows. An item with no `site_id` gives `assignment` `unassigned`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

- [ ] **T007** [P] Write failing route, redaction, and no-store tests (TC-18 to TC-20). Requirements: FR-016, FR-018, FR-019. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py`.
  - Acceptance: An invalid `org_id` gives HTTP 400 and no SDK call. The synthetic token value appears in no response and no captured log line. Each response carries `Cache-Control: no-store`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

- [ ] **T008** [P] Write failing UI marker and browser tests (TC-21 to TC-24). Requirements: FR-008, FR-013, FR-014. Status: `absent`.
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_discovery.py` (TC-21, TC-22) and `tests/e2e/web_portal/test_portal_smoke.py` (TC-23, TC-24, added to the existing class `TestCiscoOfflinePreview`).
  - Acceptance: TC-22 finds each `data-testid` marker. TC-23 reads the label Unavailable. TC-24 reads the event `cisco-target-changed`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T001.

## Phase 2: Implementation

- [ ] **T009** Implement the result model in `src/mist/access/targets/results.py`. Requirements: FR-001, FR-002, FR-003. Status: `absent`.
  - Paths: `src/mist/access/targets/results.py` (new), `src/mist/access/targets/__init__.py` (new, docstring only).
  - Acceptance: `DiscoveryState` holds four values. `DiscoveryReason` holds the sixteen reasons in `design/contracts/discovery-http.md`. `DiscoveryResult` is frozen. `items` is None for each state except verified.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
  - Requires: T002, T003, T004, T005, T006, T007, T008, and the precondition.

- [ ] **T010** Implement the bounded page walk in `src/mist/access/targets/paging.py`. Requirements: FR-010. Status: `absent`.
  - Paths: `src/mist/access/targets/paging.py` (new).
  - Acceptance: `DiscoveryPager` calls `mistapi.get_next` only when `next` is set. It stops at 50 pages. It applies the completion proof of D-6 and maps each non-200 page with the table in D-5.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
  - Requires: T009.

- [ ] **T011** Implement the check client in `src/mist/access/targets/discovery.py`. Requirements: FR-004, FR-005, FR-006, FR-007, FR-009, FR-011, FR-012, FR-015, FR-016. Status: `absent`.
  - Paths: `src/mist/access/targets/discovery.py` (new).
  - Acceptance: `MistTargetDiscovery.status`, `sites`, and `gateways` call `getSelf`, `listOrgSites`, and `getOrgInventory` with keyword arguments only. The class marks duplicates and assignments. Logs carry state codes and counts only.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
  - Requires: T010.

- [ ] **T012** Implement the route handlers in `src/interfaces/portals/cisco_config_converter/routes.py`. Requirements: FR-007, FR-008, FR-018, FR-019. Status: `absent`.
  - Paths: `src/interfaces/portals/cisco_config_converter/routes.py` (modified).
  - Acceptance: `ConverterDiscoveryRoutes` holds `status`, `sites`, and `gateways`. `ConverterRoutes.blueprint` registers the three GET rules. The handlers call `identity.current_session()`. A missing record gives `no_session`. An invalid `org_id` gives HTTP 400. `ConverterRoutes` keeps five members.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
  - Requires: T011.

- [ ] **T013** Implement the discovery panel in `src/interfaces/portals/cisco_config_converter/presentation/converter.html` and `presentation/converter.js`. Requirements: FR-013, FR-014. Status: `absent`.
  - Paths: `src/interfaces/portals/cisco_config_converter/presentation/converter.html` (modified), `src/interfaces/portals/cisco_config_converter/presentation/converter.js` (modified).
  - Acceptance: The section carries the markers in `design/contracts/ui.md`. The class `CiscoDiscoveryPage` renders the five labels. A target change dispatches `cisco-target-changed`. The script stores nothing in browser storage.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py`
    - Requires: T012.

- [ ] **T014** Make the browser tests pass in `tests/e2e/web_portal/test_portal_smoke.py`. Requirements: FR-013, FR-014. Status: `absent`.
  - Paths: `tests/e2e/web_portal/test_portal_smoke.py` (modified).
  - Acceptance: TC-23 and TC-24 pass against the isolated converter host.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Requires: T013.

## Phase 3: Guards, Fragment, and Delivery

- [ ] **T015** [P] Confirm the nested-package guard and the five-item limits. Requirements: FR-017. Status: `open`.
  - Paths: `src/mist/access/targets/`, `src/interfaces/portals/cisco_config_converter/`, `tests/integration/web_portal/cisco_config_converter/`.
  - Acceptance: The guard passes. `src/mist/access/targets/` holds four children. The converter root holds five children. The test folder holds at most five children.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py`
  - Requires: T011, T012, T013.

- [ ] **T016** [P] Add the changelog fragment `changelog.d/issue-4642-converter-target-discovery.md`. Requirements: SC-005. Status: `absent`.
  - Paths: `changelog.d/issue-4642-converter-target-discovery.md` (new, R82 shows it is absent).
  - Acceptance: One heading, one `Added` bullet, and one reference to issue #4642.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Requires: T012.

- [ ] **T-LOCAL-GATES** Run each applicable local gate on the changed files. Requirements: SC-005, FR-001 to FR-020. Status: `open`.
  - Paths: `src/mist/access/targets/`, `src/interfaces/portals/cisco_config_converter/routes.py`, `src/interfaces/portals/cisco_config_converter/presentation/`, `tests/integration/web_portal/cisco_config_converter/test_discovery.py`, `tests/e2e/web_portal/test_portal_smoke.py`, `changelog.d/issue-4642-converter-target-discovery.md`.
  - Gates that apply are listed in the table below. Each command runs on the changed files.

  | Gate | Command |
  | - | - |
  | Compile | `python -m py_compile MistHelper.py` |
  | Lint | `python -m ruff check .` |
  | Format | `python -m black --check .` |
  | Types | `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, with `MYPY_PATHS` from `.github/workflows/ci.yml` |
  | Tests | `python -m pytest tests/integration/web_portal/cisco_config_converter` |
  | Safe sweep | `python MistHelper.py --test` |
  | Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` |
  | Test quality | `test-quality-analyzer --gate`, with the procedure that the Test quality row names (R91) |
  | Complexity | `radon cc src/mist/access/targets -j \| complexity-gate --max 10` |
  | Security lint | `bandit -c pyproject.toml -r src/mist/access/targets -q` |
  | Code quality | `pylint src/ --fail-under=9.5` |
  | Dead code | `vulture $VULTURE_PATHS --min-confidence 70` |
  | Docstrings | `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90` |
  | Symbols | `symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/routes.py` |
  | SDK compatibility | `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` |
  | Output scan | `python -m pytest tests/unit/web_portal/test_output_scan_runtime_files.py` |
  | E2E smoke | `python -m pytest tests/e2e/web_portal/test_portal_smoke.py` |
  - Not applicable: menu reference, portal registry, dependency audit, STE, Ops portal, and Ops platform. The change touches none of these scopes.
  - Acceptance: Each applicable command exits with the expected result in the table. The record of results lists the command and the count of examined files.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter`
  - Requires: T014, T015, T016.

- [ ] **T-PR** Commit and open the pull request. Requirements: SC-005. Status: `open`.
  - Paths: the files in T-LOCAL-GATES, staged by explicit path only.
  - Acceptance: The commit uses the Conventional Commits subject `feat(web-portal): add read-only Mist target discovery for converter proposals`, the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`, and the branch `feat/4642-converter-target-discovery`. The pull request body holds `Closes #4642` and the result of each local gate.
  - Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
  - Requires: T-LOCAL-GATES.

- [ ] **T-REMOTE-CI** Watch the remote checks. Requirements: SC-005. Status: `open`.
  - Paths: the pull request from T-PR.
  - Action: Run `gh pr checks <number> --watch` until each required check passes. Read each failed job before you change code.
  - Acceptance: Each required check reports success on the latest commit.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter`
  - Requires: T-PR.

- [ ] **T-MERGE** Enable auto-merge after the orchestrator authorizes the merge. Requirements: SC-005. Status: `open`.
  - Paths: the pull request from T-PR.
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes and the orchestrator authorizes the merge. The merge is a squash merge.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`
  - Requires: T-REMOTE-CI and the orchestrator authorization.

## Coverage Matrix

| Requirement | Tasks | Test cases |
| - | - | - |
| FR-001 | T001, T003, T005 | TC-03, TC-09, TC-12, TC-14 |
| FR-002 | T003, T009 | TC-04 |
| FR-003 | T003, T009, T010 | TC-06, TC-07, TC-15 |
| FR-004 | T002, T011 | TC-01 |
| FR-005 | T002, T011 | TC-02 |
| FR-006 | T002, T011 | TC-02 |
| FR-007 | T004, T011, T012 | TC-03, TC-09 |
| FR-008 | T004, T012 | TC-09, TC-21, TC-23 |
| FR-009 | T005, T011 | TC-13 |
| FR-010 | T003, T010 | TC-05, TC-06, TC-07, TC-08 |
| FR-011 | T006, T011 | TC-16 |
| FR-012 | T006, T011 | TC-17 |
| FR-013 | T008, T013, T014 | TC-21, TC-22, TC-23 |
| FR-014 | T008, T013, T014 | TC-24 |
| FR-015 | T004, T005, T011 | TC-10, TC-11, TC-12, TC-14 |
| FR-016 | T007, T011 | TC-19 |
| FR-017 | T015 | Guard `tests/guardrails/test_nested_package_structure.py` |
| FR-018 | T007, T012 | TC-18 |
| FR-019 | T007, T012 | TC-20 |
| FR-020 | T002 | TC-02, and the autouse socket guard in every test |
| SC-001 | T003, T004, T005 | TC-03, TC-04, TC-09, TC-10, TC-12, TC-14 |
| SC-002 | T002 | TC-02 |
| SC-003 | T003 | TC-05 |
| SC-004 | T002 | TC-02 |
| SC-005 | T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE | Local gates and remote checks |
