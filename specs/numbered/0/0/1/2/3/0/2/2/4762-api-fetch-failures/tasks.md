# Tasks: API Fetch Failures

**Input**: `spec.md`, `plan.md`, `design/research.md`, `design/contracts/`, `design/quickstart.md`

**Status values**: open, verified-present, partial, or absent. Every implementation task is absent on `main`. Row R07 confirms that `APIFetchError` is not on `main`.

**[P]**: A task marked [P] can run in parallel with other [P] tasks whose dependencies are met. Each task edits a different file.

## Task List

| ID | [P] | Requirements | Path | Depends on | Acceptance | Verification | Status |
| - | - | - | - | - | - | - | - |
| T001 | [P] | FR-001 to FR-008, FR-015 | `tests/unit/api/test_api_core_fetch_utils.py` | none | Cases U-1 to U-11 exist. Cases U-5 to U-11 fail before T002. | `python -m pytest tests/unit/api/test_api_core_fetch_utils.py` (Tests row) | absent |
| T002 | No | FR-001 to FR-008, FR-013 | `src/mist/access/api/api_core_fetch_utils.py` | T001 | The nested `APIFetchError` and `_collect_pages` exist. Both helpers use them. The unit tests pass. | `symbol-diff --base origin/main src/mist/access/api/api_core_fetch_utils.py` (Symbols row) | absent |
| T003 | [P] | FR-009 to FR-012, FR-014, FR-015 | `tests/integration/export/test_api_fetch_enrichment.py` | none | Cases I-1 to I-13 exist. Each case that uses `APIFetchError` or a warning fails before T004 to T009. | `python -m pytest tests/integration/export/test_api_fetch_enrichment.py` (Tests row) | absent |
| T004 | [P] | FR-009, FR-014 | `src/mist/intelligence/reports/switch_scorecard/site_lookup.py` | T002, T003 | `SiteNameLookup.fetch` catches only `APIFetchError`, logs one warning, and returns an empty lookup. | `symbol-diff --base origin/main src/mist/intelligence/reports/switch_scorecard/site_lookup.py` (Symbols row) | absent |
| T005 | [P] | FR-009 | `src/mist/intelligence/reports/offline_device_reporter.py` | T002, T003 | `_fetch_data` keeps the device statistics after a site read fails. Device rows use `Unknown Site`. | `symbol-diff --base origin/main src/mist/intelligence/reports/offline_device_reporter.py` (Symbols row) | absent |
| T006 | [P] | FR-009 | `src/operations/exporting/export/site_device_exporter.py` | T002, T003 | `_resolve_site_for_stats` uses the site ID as the name after a failure. | `symbol-diff --base origin/main src/operations/exporting/export/site_device_exporter.py` (Symbols row) | absent |
| T007 | [P] | FR-009 | `src/operations/exporting/export/sites_by_ap_model_exporter.py` | T002, T003 | `export_sites_by_ap_model` keeps the AP rows after a site read fails. The inventory read still raises. | `symbol-diff --base origin/main src/operations/exporting/export/sites_by_ap_model_exporter.py` (Symbols row) | absent |
| T008 | [P] | FR-009, FR-010 | `src/operations/exporting/export/org_inventory_exporter.py` | T002, T003 | `_build_site_lookup_from_api` catches only `APIFetchError`. `gateways_with_site_info` calls it. Inventory reads still raise. | `symbol-diff --base origin/main src/operations/exporting/export/org_inventory_exporter.py` (Symbols row) | absent |
| T009 | [P] | FR-011 | `src/operations/exporting/export/msp_inventory_exporter.py` | T003 | `_build_site_lookup` logs its failure at warning level. The broad catch stays. | `symbol-diff --base origin/main src/operations/exporting/export/msp_inventory_exporter.py` (Symbols row) | absent |
| T010 | [P] | FR-016 | `changelog.d/issue-4762-api-fetch-failures.md` | none | One fragment has one `###` heading and one `Fixed` bullet. The bullet names issue 4762. | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests row) | absent |
| T-LOCAL-GATES | No | FR-001 to FR-016, SC-005 | Every changed file | T002, T004, T005, T006, T007, T008, T009, T010 | Each applicable gate in `design/quickstart.md` passes. Each gate prints its result. | `python -m ruff check .` (Lint row) | absent |
| T-PR | No | FR-016, Constitution IV | Pull request for branch `fix/4762-api-fetch-failures` | T-LOCAL-GATES | The title is `fix(api): raise APIFetchError for failed site and inventory reads`. The body contains `Closes #4762`. The test-quality check reports no new finding. | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` (Test quality row) | absent |
| T-REMOTE-CI | No | SC-006 | Pull request checks | T-PR | Every required check reports success on the latest commit. Wait for CodeQL before the auto-merge label. | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` (Test quality row) | absent |
| T-MERGE | No | SC-006 | `main` | T-REMOTE-CI and orchestrator authorization | The squash merge completes. Remote `main` contains the change. The container build runs on the merged revision. | `python -m pytest tests/unit/api/test_api_core_fetch_utils.py` on the merged `main` checkout (Tests row) | absent |

## Dependency Order

1. T001 and T003 start first. They edit different files.
2. T002 starts after T001.
3. T004 starts after T002 and T003.
4. T005, T006, T007, and T008 start after T002 and T003. They can run in parallel.
5. T009 starts after T003. It can run in parallel with T002.
6. T010 can run at any time.
7. T-LOCAL-GATES starts after T002, T004, T005, T006, T007, T008, T009, and T010.
8. T-PR starts after T-LOCAL-GATES.
9. T-REMOTE-CI starts after T-PR.
10. T-MERGE starts after T-REMOTE-CI and orchestrator authorization.

## Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T001, T002 | U-5, U-6, I-1 |
| FR-002 | T001, T002 | U-7, U-8, U-10 |
| FR-003 | T001, T002 | U-9 |
| FR-004 | T001, T002 | U-3 |
| FR-005 | T001, T002 | U-4 |
| FR-006 | T001, T002 | U-5 to U-9, I-11 |
| FR-007 | T001, T002 | U-11 |
| FR-008 | T001, T002 | U-1, U-2 |
| FR-009 | T003, T004, T005, T006, T007, T008 | I-1 to I-6 |
| FR-010 | T003, T008 | I-7 to I-10 |
| FR-011 | T003, T009 | I-12 |
| FR-012 | T003 | I-11 |
| FR-013 | T002, T004 to T009 | G-1 (symbol-diff gate, SC-005) |
| FR-014 | T003, T004 | I-1, I-13 |
| FR-015 | T001, T003 | All 24 cases |
| FR-016 | T010, T-PR | `tests/guardrails/test_changelog_fragment_policy.py` |

## Test Case Index

- U-1: `test_all_sites_with_limit_calls_list_org_sites_and_paginates` (modified)
- U-2: `test_all_inventory_with_limit_requests_vc_members_and_paginates` (modified)
- U-3: `test_fetch_helpers_return_every_page_for_list_and_results_payloads`
- U-4: `test_fetch_helpers_return_empty_list_for_successful_empty_read`
- U-5: `test_fetch_helpers_raise_on_first_page_http_error` (cases HTTP 403 and HTTP 503)
- U-6: `test_fetch_helpers_raise_on_missing_first_page_status`
- U-7: `test_fetch_helpers_raise_on_later_page_http_error_without_partial_result`
- U-8: `test_fetch_helpers_raise_on_missing_later_page_status`
- U-9: `test_fetch_helpers_raise_on_unknown_success_payload`
- U-10: `test_fetch_helpers_raise_when_next_link_repeats`
- U-11: `test_fetch_helpers_request_later_pages_through_get_next`
- I-1: `test_site_name_lookup_warns_and_returns_empty_lookup_on_http_error` (cases HTTP 403 and HTTP 503)
- I-2: `test_offline_report_keeps_device_stats_when_site_read_fails`
- I-3: `test_site_device_stats_uses_site_id_when_site_read_fails`
- I-4: `test_ap_model_export_keeps_ap_rows_when_site_read_fails`
- I-5: `test_org_devices_export_keeps_inventory_when_site_read_fails`
- I-6: `test_gateway_export_keeps_gateway_rows_when_site_read_fails`
- I-7: `test_org_devices_export_propagates_inventory_failure`
- I-8: `test_gateway_export_propagates_inventory_failure`
- I-9: `test_ap_model_read_propagates_inventory_failure`
- I-10: `test_zone_site_read_propagates_failure`
- I-11: `test_prompt_site_cache_warns_and_returns_empty_cache`
- I-12: `test_msp_site_lookup_logs_warning_on_failure`
- I-13: `test_warnings_omit_credentials`
- G-1: repository gate `symbol-diff --base origin/main` run on each of the seven changed source files in T002 and T004 to T009. It is a gate, not a pytest case.

The planned test count is 24. The new and modified test functions are U-1 to U-11 and I-1 to I-13.
