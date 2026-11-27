# Tasks: Mist API Contract Evidence for the Cisco Converter

**Input**: Numeric record in `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design\research.md`, and the four files in `design\contracts\`.

**Status values**: `open` means not started. `verified-present` means the evidence exists in this record. `partial` means some evidence exists. `absent` means no evidence exists.

**Tests**: Tests are required by the spec. The planned test functions are listed in the tasks that create them. The planned total is 32.

## Format

`[ID] [P?] [Requirements] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks. Each task names one verification command from the local gates table in `.github\copilot-instructions.md`.

## Phase 1: Evidence Recorded in This Record

**Purpose**: Evidence that this drafting run recorded. The automated checks that prove the evidence are open tasks in Phase 2.

- [x] T001 [FR-001, FR-002, FR-003, FR-004, FR-005] Record 22 write rows and 18 read rows in `design\contracts\mist-write-operations.md` and `design\contracts\mist-read-operations.md`. Acceptance: each row cites the OpenAPI JSON object, the YAML line, the SDK line, and three statuses. Status: verified-present. Automated proof: T006 and T007. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_openapi_contract.py`.
- [x] T002 [FR-015, FR-016] Record the exclusion of `deleteOrgServicePolicy` and the refusal of null site-template unassignment in `design\research.md`. Acceptance: decisions D-4 and D-8 cite 4645 D-13 and 4645 D-3. Status: verified-present. Automated proof: T012 and T015. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`.
- [x] T003 [FR-020, FR-021] Record stale issue facts and the family alignment in `analysis.md`. Acceptance: findings A-01, A-02, A-12, and A-13 name the correction owner. Status: verified-present. Verification: `ste-linter --config .ste-linter.toml --min-score 80 analysis.md` run in the record folder.
- [x] T004 [FR-017] Record 80 remote checks in `design\research.md` and in `_meta\4634-STATUS.json`. Acceptance: the counts match in the research table, the STATUS file, and the summary. Status: verified-present. Verification: `ste-linter --config .ste-linter.toml --min-score 80 design\research.md` run in the record folder.

## Phase 2: Tests and Repository Changes

**Purpose**: Automated proof and the repository files. Every task in this phase is open.

- [ ] T005 [FR-013] Create `tests\contract\web_portal\cisco_config_converter\conftest.py`. It holds the registry constant for 40 operations, a session-scoped loader for `documentation\mist-api-openapi31json.json`, and an autouse fixture that blocks socket connections. Acceptance: the loader reads the file once. Each socket open raises an error. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter`.
- [ ] T006 [P] [FR-001, FR-003, FR-005, FR-014] Create the OpenAPI write checks in `tests\contract\web_portal\cisco_config_converter\test_mist_openapi_contract.py`. Tests: `test_every_write_operation_exists_with_verb_and_path`, `test_every_write_operation_has_matching_operation_id`, `test_write_request_bodies_reference_declared_schemas`, and `test_write_responses_declare_no_server_errors`. The operation ID test also checks the three status fields of each registry entry. Acceptance: all 22 write operations pass. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_openapi_contract.py`. Depends on T005.
- [ ] T007 [FR-002, FR-003] Add the read checks to `tests\contract\web_portal\cisco_config_converter\test_mist_openapi_contract.py`. Tests: `test_every_read_operation_exists_with_get_verb` and `test_success_response_schemas_resolve`. Acceptance: all 18 read operations pass. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_openapi_contract.py`. Depends on T006.
- [ ] T008 [P] [FR-004, FR-010] Create the SDK signature checks in `tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Tests: `test_sdk_functions_exist_for_every_operation`, `test_sdk_first_argument_is_session_and_no_variadics`, and `test_sdk_argument_names_match_path_and_body_parameters`. Acceptance: each signature matches `design\contracts\mist-sdk-behavior.md`. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Depends on T005.
- [ ] T009 [FR-010] Add the forwarding checks to `tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Tests: `test_write_wrapper_forwards_body_unchanged` (parametrized over write operations with a body), `test_write_wrapper_makes_one_session_call`, and `test_sdk_verb_and_path_match_openapi`. The session call test checks the `json` and `headers` keyword arguments. It also checks that no `timeout` argument exists. Acceptance: each wrapper forwards the same body object and makes one session call. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Depends on T008.
- [ ] T010 [FR-009, FR-008] Add the retry checks to `tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Tests: `test_post_put_delete_retry_three_times_on_429`, `test_retry_waits_follow_retry_after_or_backoff`, and `test_transport_failure_is_not_retried`. Acceptance: a persistent HTTP 429 gives four attempts with waits of 5, 10, and 20 seconds. Sleep calls are patched. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Depends on T009.
- [ ] T011 [FR-008, FR-013] Add the status and socket checks to `tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Tests: `test_http_400_403_404_500_status_forwarded_unchanged` and `test_socket_connections_are_blocked`. Acceptance: each status reaches the caller unchanged. A socket open fails the test. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Depends on T010.
- [ ] T012 [FR-012, FR-015] Add the guard checks to `tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Tests: `test_no_production_module_names_a_write_operation` and `test_excluded_operation_has_no_caller`. Acceptance: no file under `src\interfaces\portals\cisco_config_converter` or `src\mist\resources\gateway\overrides` names a write operation. The excluded operation has no caller in the tests. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py`. Depends on T008.
- [ ] T013 [P] [FR-006, FR-011] Create the positive synthetic fixtures in `tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py`. Tests: `test_gateway_template_fixture_accepts_three_fields`, `test_device_profile_gateway_fixture_accepts`, `test_device_profile_switch_fixture_accepts`, `test_inventory_update_assign_fixture_accepts`, and `test_mac_addresses_fixture_accepts`. Acceptance: each fixture passes the bundled schema. The gateway template fixture uses only `name`, `type`, and `dns_servers`. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py`. Depends on T005.
- [ ] T014 [FR-007] Add the negative synthetic fixtures to `tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py`. Tests: `test_gateway_template_rejects_unknown_type`, `test_device_profile_rejects_switch_type_under_gateway_subtype`, `test_device_profile_rejects_unknown_field`, `test_mac_addresses_rejects_empty_and_duplicate_lists`, and `test_inventory_update_rejects_unknown_operation`. Acceptance: each fixture fails the bundled schema as expected. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py`. Depends on T013.
- [ ] T015 [FR-007, FR-016] Add the allowlist and refusal checks to `tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py`. Tests: `test_allowlist_rejects_unknown_top_level_field_that_schema_accepts`, `test_site_template_null_is_refused_by_local_rule`, and `test_list_or_nameless_body_is_refused`. Acceptance: the allowlist rejects the field that the schema accepts. The null site-template value, a list body, and a service or policy body without `name` fail the local rules. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py`. Depends on T014.
- [ ] T016 [P] [FR-019] Create `changelog.d\issue-4634-mist-api-contract-evidence.md` with one `###` heading and one `- **Added**` bullet that names issue 4634. Acceptance: the changelog guard accepts the fragment. Verification: `python -m pytest tests\guardrails\test_changelog_fragment_policy.py`.
- [ ] T017 [P] [FR-001, FR-017, FR-018, FR-020, FR-021] Copy the reviewed record from the draft folder to `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\`. Acceptance: the repository folder matches the draft folder file for file. Verification: `ste-linter --config .ste-linter.toml --min-score 80` with each Markdown file of the record as an argument.

## Final Tasks

- [ ] T-LOCAL-GATES [FR-012, FR-018, SC-007] Run each local gate in the table that applies to the changed files. Acceptance: each applicable gate reports a pass. Record each gate result in the pull request body. Verification commands:
  - `python -m ruff check .` (expected `All checks passed`).
  - `python -m black --check .` (expected no file to change).
  - `python -m pytest tests\contract\web_portal\cisco_config_converter` (all 32 planned tests pass).
  - `python -m pytest tests\guardrails` (guardrails pass, including nested package and process folder tests).
  - `bandit -c pyproject.toml -r tests\contract\web_portal\cisco_config_converter -q` (no finding).
  - `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` (`gate: 0 new findings vs baseline`).
  - `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` (one summary line).
  - `ste-linter --config .ste-linter.toml --min-score 80` with each changed Markdown file as an argument (each file scores 80 or above).
  - Not applicable: compile, because `MistHelper.py` is unchanged.
  - Not applicable: coverage, because no `src` file changes.
  - Not applicable: types, because `MYPY_PATHS` in `.github\workflows\ci.yml` line 93 excludes tests.
  - Not applicable: complexity, because `RADON_PATHS` in line 99 excludes this folder.
  - Not applicable: dead code, because `VULTURE_PATHS` in line 101 excludes tests.
  - Not applicable: docstrings, because `PYDOCSTYLE_PATHS` in line 104 and `INTERROGATE_PATHS` in line 107 exclude tests.
  - Not applicable: menu reference, because no menu changes.
  - Not applicable: symbols, because no existing Python file changes.
  - Not applicable: safe sweep, because no operation changes.
  - Not applicable: dependency audit, because no requirement changes.
  - Not applicable: code quality, because no `src` file changes.
  - Not applicable: ops portal and ops platform, because they are not affected.
  Depends on T005 through T017.
- [ ] T-PR [FR-019] Commit with the message `test(cisco-converter): verify Mist API contracts`. The commit body holds `Closes #4634` and the Co-authored-by trailer. Push branch `feat/4634-mist-api-contract-evidence`. Open a pull request into `main` with the same title, a body that contains `Closes #4634`, the changed-file summary, and the gate results. Verification: `python -m pytest tests\contract\web_portal\cisco_config_converter`. Depends on T-LOCAL-GATES.
- [ ] T-REMOTE-CI [FR-017] Watch the remote checks of the pull request with `gh pr checks` and the `--watch` option. Acceptance: each required check reports a pass, including CodeQL. A failed check opens a new issue before any repair. Verification: `gh pr checks` with the pull request number returned by T-PR and the `--watch` option. Depends on T-PR.
- [ ] T-MERGE [FR-012] Do not add the `auto-merge` label. A human reviews the pull request because issue 4634 carries `needs-human-review`. The orchestrator authorizes the squash merge after review. Acceptance: one squash commit lands on `main`, and the branch is deleted. Verification: `gh pr view` with the pull request number returned by T-PR shows the state `MERGED`. Depends on T-REMOTE-CI.

## Planned Test Numbers

The contract files and the analysis cite tests by number. The numbers below map each planned test to its module.

| No. | Test function | Module |
| --- | --- | --- |
| 1 | `test_every_write_operation_exists_with_verb_and_path` | `test_mist_openapi_contract.py` |
| 2 | `test_every_write_operation_has_matching_operation_id` | `test_mist_openapi_contract.py` |
| 3 | `test_write_request_bodies_reference_declared_schemas` | `test_mist_openapi_contract.py` |
| 4 | `test_write_responses_declare_no_server_errors` | `test_mist_openapi_contract.py` |
| 5 | `test_every_read_operation_exists_with_get_verb` | `test_mist_openapi_contract.py` |
| 6 | `test_success_response_schemas_resolve` | `test_mist_openapi_contract.py` |
| 7 | `test_sdk_functions_exist_for_every_operation` | `test_mist_sdk_contract.py` |
| 8 | `test_sdk_first_argument_is_session_and_no_variadics` | `test_mist_sdk_contract.py` |
| 9 | `test_sdk_argument_names_match_path_and_body_parameters` | `test_mist_sdk_contract.py` |
| 10 | `test_write_wrapper_forwards_body_unchanged` | `test_mist_sdk_contract.py` |
| 11 | `test_write_wrapper_makes_one_session_call` | `test_mist_sdk_contract.py` |
| 12 | `test_sdk_verb_and_path_match_openapi` | `test_mist_sdk_contract.py` |
| 13 | `test_post_put_delete_retry_three_times_on_429` | `test_mist_sdk_contract.py` |
| 14 | `test_retry_waits_follow_retry_after_or_backoff` | `test_mist_sdk_contract.py` |
| 15 | `test_transport_failure_is_not_retried` | `test_mist_sdk_contract.py` |
| 16 | `test_http_400_403_404_500_status_forwarded_unchanged` | `test_mist_sdk_contract.py` |
| 17 | `test_socket_connections_are_blocked` | `test_mist_sdk_contract.py` |
| 18 | `test_no_production_module_names_a_write_operation` | `test_mist_sdk_contract.py` |
| 19 | `test_excluded_operation_has_no_caller` | `test_mist_sdk_contract.py` |
| 20 | `test_gateway_template_fixture_accepts_three_fields` | `test_mist_payload_fixtures.py` |
| 21 | `test_device_profile_gateway_fixture_accepts` | `test_mist_payload_fixtures.py` |
| 22 | `test_device_profile_switch_fixture_accepts` | `test_mist_payload_fixtures.py` |
| 23 | `test_inventory_update_assign_fixture_accepts` | `test_mist_payload_fixtures.py` |
| 24 | `test_mac_addresses_fixture_accepts` | `test_mist_payload_fixtures.py` |
| 25 | `test_gateway_template_rejects_unknown_type` | `test_mist_payload_fixtures.py` |
| 26 | `test_device_profile_rejects_switch_type_under_gateway_subtype` | `test_mist_payload_fixtures.py` |
| 27 | `test_device_profile_rejects_unknown_field` | `test_mist_payload_fixtures.py` |
| 28 | `test_mac_addresses_rejects_empty_and_duplicate_lists` | `test_mist_payload_fixtures.py` |
| 29 | `test_inventory_update_rejects_unknown_operation` | `test_mist_payload_fixtures.py` |
| 30 | `test_allowlist_rejects_unknown_top_level_field_that_schema_accepts` | `test_mist_payload_fixtures.py` |
| 31 | `test_site_template_null_is_refused_by_local_rule` | `test_mist_payload_fixtures.py` |
| 32 | `test_list_or_nameless_body_is_refused` | `test_mist_payload_fixtures.py` |

## Dependencies and Execution Order

- T005 gates every Phase 2 test task.
- T006 and T007 share one file, so they run in sequence.
- T008 and T013 run in parallel with each other because they edit different files.
- T009, T010, T011, and T012 share the SDK test file, so they run in sequence after T008.
- T014 and T015 share the payload file, so they run in sequence after T013.
- T016 and T017 run in parallel with the test work.
- The final tasks run in order: T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE.

## Notes

- Write each test helper with an inline comment on each executable line.
- Each test helper logs an info line before a file read and a debug line after it.
- Do not add the `auto-merge` label to this pull request.
- Keep each write operation disabled. No task enables a write operation.
