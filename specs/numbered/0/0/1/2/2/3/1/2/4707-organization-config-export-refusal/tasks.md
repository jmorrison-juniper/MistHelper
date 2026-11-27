# Tasks: Organization Config Export Refusal

**Input**: Specification in `spec.md`, plan in `plan.md`, and supporting artifacts under `design/`.

**Precondition P-1**: Start T002 only after issue #4707 holds an explicit handover comment for the manager file. See `spec.md` Preconditions.

**Tests**: The specification requires tests. Write each red test task before its implementation task, and see it fail first.

**Ownership**: Do not modify `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. Add the changelog fragment by explicit path only.

**Format**: Each task lists requirements, exact paths, acceptance, verification, and status. Status values are `absent`, `partial`, `verified-present`, or `open`.

## Phase 1: Baseline and Red Tests

- [ ] T001 [US1] Confirm the untouched manager file and its module-level names before any edit.
  - Requirements: FR-017
  - Files: `src/mist/resources/org/org_config_migration_manager.py` (read only)
  - Acceptance: The file blob matches `358a2cc226d550a0d838b10ae0738944894f5655` on main. The symbol check reports no module-level name changed.
  - Verification: `symbol-diff --base origin/main src/mist/resources/org/org_config_migration_manager.py` (Symbols row). Expected: no module-level name changed, exit code 0.
  - Status: verified-present

- [ ] T002 [US1] Add red export tests to `TestExportConfig`.
  - Requirements: FR-006, FR-007, FR-008, FR-016, FR-018
  - Files: `tests/unit/org/test_org_config_migration_workflow.py`
  - Acceptance: Add `test_a_partial_fetch_saves_no_bundle`, `test_a_partial_fetch_never_logs_completion`, and `test_a_verified_fetch_records_the_fetch_status`. Update the four existing export tests to return fetch outcomes. The three new tests fail before T006.
  - Verification: `python -m pytest tests/unit/org/test_org_config_migration_workflow.py -q -k TestExportConfig` (Tests row). Expected: the new tests fail, and the updated tests pass.
  - Status: absent

- [ ] T003 [P] [US1] Add red reader tests in the conflicts module.
  - Requirements: FR-002, FR-003, FR-004, FR-005, FR-014, FR-015, FR-016, FR-018
  - Files: `tests/unit/org/test_org_config_migration_conflicts.py`
  - Acceptance: Replace `TestExtractResponseData` with `TestConfigFetchReader`, which holds ten tests. Move `TestFetchConfigType` to `TestConfigFetchCalls`, which holds `test_each_list_call_uses_the_documented_path` and two updated tests. The status matrix uses native `requests.Response` objects. The new tests fail before T005.
  - Verification: `python -m pytest tests/unit/org/test_org_config_migration_conflicts.py -q` (Tests row). Expected: the new tests fail, and the updated tests pass.
  - Status: absent

- [ ] T004 [US2] Add red import tests and update the bundle helper.
  - Requirements: FR-010, FR-011, FR-012, FR-018
  - Files: `tests/unit/org/test_org_config_migration_workflow.py`
  - Acceptance: Add `test_a_legacy_bundle_is_refused`, `test_a_bundle_without_fetch_status_is_refused`, and `test_a_bundle_with_a_not_verified_type_is_refused` to `TestValidateBundleStructure`. Add `test_an_unverified_destination_caches_nothing_and_returns_false` to `TestFetchExistingObjects`. Add `test_an_unverified_destination_stops_before_any_create` and `test_a_refused_bundle_stops_before_the_prompt` to `TestImportConfig`. Update `_valid_bundle` to schema 1.1 with six verified statuses. The new tests fail before T007.
  - Verification: `python -m pytest tests/unit/org/test_org_config_migration_workflow.py -q -k "TestValidateBundleStructure or TestFetchExistingObjects or TestImportConfig"` (Tests row). Expected: the new tests fail, and the updated tests pass.
  - Status: absent

## Phase 2: Implementation

- [ ] T005 [US1] Implement the fetch outcome and the reader in the manager module.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-014, FR-015, FR-016
  - Files: `src/mist/resources/org/org_config_migration_manager.py`
  - Acceptance: Add `ConfigFetchOutcome` and `ConfigFetchReader`. Remove `_fetch_config_type` and `_extract_response_data`. Keep `limit=1000` and the configured keyword arguments. Read follow-up pages with `mistapi.get_next`. Log before and after each fetch.
  - Verification: `python -m pytest tests/unit/org/test_org_config_migration_conflicts.py -q` (Tests row). Expected: every reader test passes.
  - Status: absent

- [ ] T006 [US1] Implement the export gate and the bundle schema 1.1.
  - Requirements: FR-006, FR-007, FR-008, FR-009
  - Files: `src/mist/resources/org/org_config_migration_manager.py`
  - Acceptance: Add `BundleVerification` with `SCHEMA_VERSION = "1.1"`, `fetch_status`, `unverified_keys`, and `bundle_problem`. `export_config` writes no file and logs the stop message when a type is not verified. `_build_export_bundle` writes schema 1.1 and the fetch status map.
  - Verification: `python -m pytest tests/unit/org/test_org_config_migration_workflow.py -q -k "TestExportConfig or TestBuildExportBundle"` (Tests row). Expected: every export test passes.
  - Status: absent

- [ ] T007 [US2] Implement the import gates.
  - Requirements: FR-010, FR-011, FR-012, FR-013
  - Files: `src/mist/resources/org/org_config_migration_manager.py`
  - Acceptance: `_validate_bundle_structure` calls `bundle_problem` after the key check. `_fetch_existing_objects` returns a boolean and caches nothing when a destination type is not verified. `import_config` returns before `_execute_import` when the boolean is `False`.
  - Verification: `python -m pytest tests/unit/org/test_org_config_migration_workflow.py -q -k "TestValidateBundleStructure or TestFetchExistingObjects or TestImportConfig"` (Tests row). Expected: every import test passes.
  - Status: absent

- [ ] T008 [US1] Update the remaining tests that depend on the old contract.
  - Requirements: FR-013, FR-017, FR-018
  - Files: `tests/unit/org/test_org_config_migration_conflicts.py`, `tests/unit/org/test_org_config_migration_workflow.py`
  - Acceptance: `TestFetchAllTypes`, `TestBuildExportBundle`, `TestFetchExistingObjects`, and `TestImportConfig` pass with fetch outcomes. `TestGetOrgName` and `TestCreateWithoutIdentifier` pass unchanged. No assertion is weakened.
  - Verification: `python -m pytest tests/unit/org -q` (Tests row). Expected: every test in the folder passes.
  - Status: absent

- [ ] T009 [US3] Write the docstrings, inline comments, and log messages.
  - Requirements: FR-016, FR-019
  - Files: `src/mist/resources/org/org_config_migration_manager.py`
  - Acceptance: The module docstring states the verification rule and schema 1.1. Each new class and method has a docstring. Each executable line has an inline comment. Each action logs before and after. Messages match `design/contracts/menu-messages.md`.
  - Verification: Docstrings row, expanded from `ci.yml` lines 104 and 107: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`. Expected: no violation and coverage at 90 percent or above.
  - Status: absent

## Phase 3: Finish Support Work

- [ ] T010 [P] [US1] Add the changelog fragment.
  - Requirements: FR-019
  - Files: `changelog.d/issue-4707-organization-config-export-refusal.md` (add)
  - Acceptance: The fragment holds one `###` heading and one Fixed bullet that names issue #4707. The fragment name follows the rule in `changelog.d/README.md`, because the pull request does not exist when the commit is made.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4707-organization-config-export-refusal.md` (STE row). Expected: score 80 or above.
  - Status: absent

- [ ] T011 [P] [US1] Check the SDK compatibility guard.
  - Requirements: FR-014
  - Files: `tests/integration/test_mistapi_sdk_compatibility.py` (read only)
  - Acceptance: The guard reports 10 or fewer unresolved call sites and 366 or fewer unverifiable call sites. Neither count grows.
  - Verification: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -q` (Tests row). Expected: every guard test passes.
  - Status: absent

## Phase 4: Delivery

- [ ] T-LOCAL-GATES [US1] [US2] [US3] Run each applicable local gate on the changed files.
  - Requirements: FR-001 through FR-019
  - Files: `src/mist/resources/org/org_config_migration_manager.py`, `tests/unit/org/test_org_config_migration_conflicts.py`, `tests/unit/org/test_org_config_migration_workflow.py`, `changelog.d/issue-4707-organization-config-export-refusal.md`, and the record files under `specs/numbered/0/0/1/2/2/3/1/2/4707-organization-config-export-refusal/`.
  - Acceptance: These gates pass, with each result recorded: Compile, Lint, Format, Types, Tests, Full tests, Safe sweep, Coverage, Test quality, Complexity, Security lint, Code quality, Dead code, Docstrings, Menu reference, Symbols, and STE. Dependency audit, Ops portal, and Ops platform do not apply.
  - Verification: These commands from the Local gates table.
    - Compile: `python -m py_compile MistHelper.py`
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
    - Tests: `python -m pytest tests/unit/org/test_org_config_migration_conflicts.py tests/unit/org/test_org_config_migration_workflow.py`
    - Full tests: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal`
    - Safe sweep: `python MistHelper.py --test`
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
    - Test quality: the preflight, the changed-from check, and the full-suite check in `.github/copilot-instructions.md`. Expected: `gate: 0 new findings vs baseline`.
    - Complexity: `radon cc src/mist/resources/org -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r src/mist/resources/org -q`
    - Code quality: `pylint src/ --fail-under=9.5`
    - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
    - Menu reference: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Expected: no changed file.
    - Symbols: `symbol-diff --base origin/main src/mist/resources/org/org_config_migration_manager.py`
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` with each Markdown file of the record and the changelog fragment.
  - Status: absent

- [ ] T-PR [US1] [US2] [US3] Commit the change and open the pull request.
  - Requirements: FR-001 through FR-019
  - Files: branch `fix/4707-organization-config-export-refusal`, the files listed in T-LOCAL-GATES, and `.github/PULL_REQUEST_TEMPLATE.md`
  - Acceptance: Add the `in-progress` label before the branch exists, after precondition P-1 holds. Stage explicit paths only. The commit subject is `fix(org): stop config export on a fetch that is not verified`. The body holds `Closes #4707` and the Copilot trailer. The pull request body holds `Closes #4707`, the changed-file list, and the local gate results. The `needs-human-review` label stays.
  - Verification: Tests row on the branch head: `python -m pytest tests/unit/org/test_org_config_migration_conflicts.py tests/unit/org/test_org_config_migration_workflow.py`. Expected: all tests pass.
  - Status: absent

- [ ] T-REMOTE-CI [US1] [US2] [US3] Watch the remote checks until each required check passes.
  - Requirements: FR-001 through FR-019
  - Files: none. The checks run for the pull request from T-PR.
  - Acceptance: Each required check in `.github/workflows/ci.yml` passes on the pull request head. The checks include `test_quality_gate`, `pylint`, `interrogate`, `pytest_coverage_shards`, and CodeQL. No required check is skipped.
  - Verification: Full tests row and Coverage row, on the remote run. Watch with `gh pr checks` for the pull request from T-PR. Expected: every required check reports success.
  - Status: absent

- [ ] T-MERGE [US1] [US2] [US3] Hand the merge to a human reviewer.
  - Requirements: FR-001 through FR-019
  - Files: the pull request from T-PR
  - Acceptance: A human reviews the pull request and removes `needs-human-review` only after that review. Enable auto-merge only after remote CI passes and the orchestrator authorizes the merge. Until then, a human merges. After the merge, `main` still holds the module-level names that T001 recorded.
  - Verification: Symbols row on the merged `main` checkout: `symbol-diff --base origin/main src/mist/resources/org/org_config_migration_manager.py`. Expected: exit code 0.
  - Status: absent

## Test Inventory

The plan adds or renames 20 test functions. Parameterized cases count inside their function.

| # | Module | Class | Test function | Task |
| --- | --- | --- | --- | --- |
| 1 | conflicts | TestConfigFetchReader | test_a_list_reply_is_verified (renamed) | T003 |
| 2 | conflicts | TestConfigFetchReader | test_a_results_reply_is_verified | T003 |
| 3 | conflicts | TestConfigFetchReader | test_a_verified_empty_reply_has_no_objects | T003 |
| 4 | conflicts | TestConfigFetchReader | test_status_boundaries_decide_verification | T003 |
| 5 | conflicts | TestConfigFetchReader | test_a_missing_status_is_unavailable | T003 |
| 6 | conflicts | TestConfigFetchReader | test_a_reply_without_a_list_is_invalid | T003 |
| 7 | conflicts | TestConfigFetchReader | test_a_refused_follow_up_page_fails_the_whole_type | T003 |
| 8 | conflicts | TestConfigFetchReader | test_a_missing_follow_up_page_is_unavailable | T003 |
| 9 | conflicts | TestConfigFetchReader | test_an_exception_is_not_verified_and_logs_the_type_only | T003 |
| 10 | conflicts | TestConfigFetchReader | test_the_sdk_paging_helper_hides_a_refused_body | T003 |
| 11 | conflicts | TestConfigFetchCalls | test_each_list_call_uses_the_documented_path | T003 |
| 12 | workflow | TestExportConfig | test_a_partial_fetch_saves_no_bundle | T002 |
| 13 | workflow | TestExportConfig | test_a_partial_fetch_never_logs_completion | T002 |
| 14 | workflow | TestExportConfig | test_a_verified_fetch_records_the_fetch_status | T002 |
| 15 | workflow | TestValidateBundleStructure | test_a_legacy_bundle_is_refused | T004 |
| 16 | workflow | TestValidateBundleStructure | test_a_bundle_without_fetch_status_is_refused | T004 |
| 17 | workflow | TestValidateBundleStructure | test_a_bundle_with_a_not_verified_type_is_refused | T004 |
| 18 | workflow | TestFetchExistingObjects | test_an_unverified_destination_caches_nothing_and_returns_false | T004 |
| 19 | workflow | TestImportConfig | test_an_unverified_destination_stops_before_any_create | T004 |
| 20 | workflow | TestImportConfig | test_a_refused_bundle_stops_before_the_prompt | T004 |

## Dependencies & Execution Order

- T001 comes first. It records the baseline before any edit.
- T002 and T004 edit the same workflow test module, so they run in sequence.
- T003 runs in parallel with T002, because it edits the conflicts module.
- T005 needs T003. T006 needs T002 and T005. T007 needs T004, T005, and T006.
- T008 needs T007. T009 needs T005 through T007.
- T010 and T011 need T006 and T007, and they run in parallel.
- T-LOCAL-GATES needs T008 through T011. T-PR needs T-LOCAL-GATES. T-REMOTE-CI needs T-PR. T-MERGE needs T-REMOTE-CI and a human approval.

## Parallel Opportunities

- T002 and T003 run in parallel, because they edit different files.
- T010 and T011 run in parallel after the implementation tasks.
