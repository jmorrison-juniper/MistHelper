# Specification Analysis Report: Test quality: repair remaining missing_fm_http_4xx findings

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, and the constitution (version 1.9.0).

**Method**: Read-only evidence from remote `main` (`gh api`) and from the installed packages in `.venv`. The census was not run, because the brief forbids running an analyzer. Each family assignment uses the detector source at the pinned commit (research R-61 to R-68) and each test body on `main` (research R-23 to R-60).

## Census Summary

- Baseline 4xx entries on `main`: 38 (research R-17).
- Census findings for the 4xx rule: not measured in this record (Unverified U-1). Task T004 records the count.
- Pre-census families for the 38 entries:
  - F1 (real gap): 0 entries.
  - F2 (applicability) only: 12 entries.
  - F2 and F3 together: 1 entry (row 1).
  - F3 (coverage) only: 25 entries.
- The census decides between "present" and "stale" for each entry. A stale entry leaves the census and remains in the baseline.

## Triage Table

Columns show the baseline line, the test module on `main`, and the 4xx status evidence (line). Other columns show the source import (line), the pre-census family, and the repair rule after the census.

| # | Baseline line | Test module (main) | 4xx status evidence in test (line) | Source import (line) | Pre-census family | Repair rule after census |
|---|---|---|---|---|---|---|
| 1 | 131 | `mist-ops-platform/tests/unit/api/test_session_security.py` | L30 constant 401. L333-334 native 401 refusal | `src.api.deps` and five other `src` modules (L21-26). Module-level `import httpx` (L17) | F2 and F3 | Present: T006 and T007. Stale: T012. |
| 2 | 230 | `mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py` | none | `src.shared.mist.types` (L14). SDK attribute string `mistapi.api.v1.` (L27) | F2 | Present: T006. Stale: T012. |
| 3 | 274 | `mist-ops-platform/tests/unit/mist/test_registry_validation.py` | none | `src.shared.mist.types` (L16). SDK attribute string `mistapi.api.v1.` (L22) | F2 | Present: T006. Stale: T012. |
| 4 | 1165 | `tests/test_upgrade_portal_mist.py` | L123 status 403 with `requests.HTTPError`. L286 status 400 assertion | `src.interfaces.portals.upgrade_portal.api.mist_client` (L14) | F3 | Present: T007. Stale: T012. |
| 5 | 2342 | `tests/unit/firmware/test_bulk_ap_running_version.py` | L218 status 403 in a refusal test | `src.operations.execution.firmware.bulk_ap_upgrader` (L25). `running_version` (L30) | F3 | Present: T007. Stale: T012. |
| 6 | 2364 | `tests/unit/firmware/test_firmware_manager_config.py` | L298 `SimpleNamespace(status_code=403)` | `src.operations.execution.firmware.firmware_manager` (L22) | F3 | Present: T007. Stale: T012. |
| 7 | 2496 | `tests/unit/gateway/test_device_template_cloner_extended.py` | L100, L185, L305 `_build_api_response(403, data)` | `src.mist.resources.gateway.device_template_cloner` (L19) | F3 | Present: T007. Stale: T012. |
| 8 | 2584 | `tests/unit/gateway/test_wan2_migration_manager.py` | L147 `SimpleNamespace(status_code=400)`. The test name at L118 names HTTP 503 | `src.mist.resources.gateway.wan2_migration_manager` (L8) | F3 | Present: T007. Stale: T012. |
| 9 | 2606 | `tests/unit/gateway/test_wan2_migration_manager_extended.py` | L1023 `response.status_code = 403` | `src.mist.resources.gateway.wan2_migration_manager` (L14) | F3 | Present: T007. Stale: T012. |
| 10 | 2639 | `tests/unit/gateway/test_wan_probe_device_override_manager.py` | L157 and L274 `response.status_code = 403` | `src.mist.resources.gateway.wan_probe_device_override_manager` (L9) | F3 | Present: T007. Stale: T012. |
| 11 | 2870 | `tests/unit/inventory/test_org_device_inventory_summary.py` | L299 `response.status_code = 403` | `src.mist.resources.inventory.org_device_inventory_summary` (L11) | F3 | Present: T007. Stale: T012. |
| 12 | 2892 | `tests/unit/inventory/test_org_device_inventory_summary_wave8.py` | L735 `response.status_code = 404` | `src.mist.resources.inventory.org_device_inventory_summary` (L13) | F3 | Present: T007. Stale: T012. |
| 13 | 2914 | `tests/unit/org/test_org_config_migration_conflicts.py` | L515 `raw_response.status_code = 403` | `src.mist.resources.org.org_config_migration_manager` (L21) | F3 | Present: T007. Stale: T012. |
| 14 | 2958 | `tests/unit/org/test_org_config_migration_workflow.py` | L122 parametrize `status` with eight values, including 403 and 404 | `src.mist.resources.org.org_config_migration_manager` (L23) | F3 | Present: T007. Stale: T012. |
| 15 | 3068 | `tests/unit/refactors/test_app_context_session_state.py` | none | `MistHelper` (L16). `config_utils` (L17). `initialize_mist_session` (L18, with source line 26 importing `requests.adapters`, R-77). `main_entrypoint` (L21) | F2 | Present: T006. Stale: T012. |
| 16 | 3134 | `tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py` | none | Package imports from `src.foundation.support.refactors` (L29-36). `src.foundation.support.refactors.main_entrypoint` (L37) | F2 | Present: T006. Stale: T012. |
| 17 | 3156 | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` | none | `MistHelper` (L23). `src.foundation.support.refactors.main_entrypoint` (L28). `source_dependency_resolver` (L25) | F2 | Present: T006. Stale: T012. |
| 18 | 3189 | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py` | none | `src.foundation.support.refactors.main_entrypoint` (L14). `MistHelper` (L74) | F2 | Present: T006. Stale: T012. |
| 19 | 3244 | `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | L284 status 404. L334 status 403. L721 status 400. L749 status 404 | `source_dependency_resolver` (L20). `src.foundation.support.refactors.wlanradius_timer_manager` (L24) | F3 | HELD by open PR #4208 (FR-013). After the hold ends: present, T007. Stale, T012. |
| 20 | 3387 | `tests/unit/security/rogue_dhcp/test_scanner.py` | L249 parametrize `status_code` with 403 and 503 | `src.operations.protection.security.rogue_dhcp.scanner` (L19) | F3 | Present: T007. Stale: T012. |
| 21 | 3596 | `tests/unit/site/address_audit/test_audit_engine.py` | L391 parametrize `status_code` with 403 and 503 | `src.mist.resources.site.address_audit.audit_engine` (L10) | F3 | Present: T007. Stale: T012. |
| 22 | 3827 | `tests/unit/ssh/test_cli_shell_manager.py` | L542 `self._refused_response(403)` (class-scoped helper). L596 `response.status_code = 403` | `src.operations.execution.ssh.cli_shell_manager` (L25) | F3 | Present: T007. Stale: T012. |
| 23 | 3992 | `tests/unit/config/standalone/foundation/support/utilities/network/test_address_utils.py` | L903 `mock_resp.status_code = 404` | `src.foundation.support.utils.address_utils` (L12) | F3 | Present: T007. Stale: T012. |
| 24 | 4916 | `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils_wave3.py` | none | `src.foundation.runtime.config.config_utils` (L16). Source docstring names `mistapi.APISession` (R-79) | F2 | Present: T006. Stale: T012. |
| 25 | 5268 | `tests/unit/test_issue_2971_census_repairs.py` | L161 `status_code = 403` | `src.operations.exporting.export` site exporters (L11-L30) | F3 | Present: T007. Stale: T012. |
| 26 | 5389 | `tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py` | none | `MistHelper` (L8): `GlobalImportManager`, `LogRotationSettings`, `_early_file_handler` | F2 | Present: T006. Stale: T012. |
| 27 | 5851 | `tests/unit/test_prompt_network_device_utils.py` | L1076 `response.status_code = 403` | `src.mist.resources.device.prompt_utils` (L19) | F3 | Present: T007. Stale: T012. |
| 28 | 5873 | `tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py` | L966 parametrize `status_code` with 403, 503, and None | `src.foundation.support.utils.rate_limiting` (L15) | F3 | Present: T007. Stale: T012. |
| 29 | 6687 | `tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py` | L290 parametrize `status_code` with 403. L723 `response.status_code = 403` | `src.operations.wan.wan_hub_group_manager` (L15) | F3 | Present: T007. Stale: T012. |
| 30 | 6808 | `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` | L627-630 parametrize `status_code` with 403 and 503 | `src.operations.wan.wan_vpn_builder` (L17) | F3 | Present: T007. Stale: T012. |
| 31 | 7259 | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_device_prompt_rename_guard.py` | none (source-text guard) | `src.interfaces.visualization.ui.prompt_utils` (L19). Source imports `mistapi` and `requests` (R-73) | F2 | Present: T006. Stale: T012. |
| 32 | 7292 | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_interactive_display_utils.py` | none | `src.interfaces.visualization.ui.interactive_display_utils` (L15). Source references `mistapi.api.v1` (R-74) | F2 | Present: T006. Stale: T012. |
| 33 | 7358 | `tests/unit/ui/test_level_discoverer.py` | none | `src.interfaces.visualization.ui.runtime.level_discoverer` (L11). Source strings `mistapi.api.v1` (R-75) | F2 | Present: T006. Stale: T012. |
| 34 | 7402 | `tests/unit/ui/test_prompt_utils.py` | L958 `SimpleNamespace` with `status_code=403` | `src.interfaces.visualization.ui.prompt_utils` (L27) | F3 | Present: T007. Stale: T012. |
| 35 | 7600 | `tests/unit/upgrade_portal/test_upgrade_service_classify.py` | none | `src.operations.execution.firmware.firmware_manager` (L27). Class-wide SDK references in the source (R-76) | F2 | Present: T006. Stale: T012. |
| 36 | 7622 | `tests/unit/utils/test_tls_policy.py` | L140 `response.status_code = 403`. L145 status assertion 403 | `src.mist.resources.inventory.csv_comparator` (L20). `src.mist.resources.site.address_audit.audit_engine` (L21) | F3 | Present: T007. Stale: T012. |
| 37 | 7831 | `tests/unit/web_portal/test_operations_silent_failure.py` | L251 `response.status_code = 403` | `web_portal.routes.operations` (L25) | F3 | Present: T007. Stale: T012. |
| 38 | 7985 | `tests/unit/websocket/test_service_ping_discovery.py` | L342 and L367 parametrize `status_code` with 302 to 503, and None. L396 parametrize with 200, 404, and 503 | `src.mist.realtime.websocket.service_ping_discovery` (L21) | F3 | Present: T007. Stale: T012. |

## Family Rules

- **F1, real gap.** The source under test has a 4xx-capable status guard or raise path. No source-driving test asserts a 4xx status for that path. Repair: T011, one native 4xx test in the same module. Pre-census count: 0.
- **F2, applicability noise.** The detector infers HTTP status risk for a test that calls no HTTP-capable path. The risk comes from a module-level SDK import, from an `mistapi.api.` string constant, from class-wide body scope, or from the nested-path rule. Repair: T006 in misthelper-devtools. Forbidden repairs: an exclusion, a marker, or a synthetic HTTP test.
- **F3, coverage miss.** A 4xx status literal exists in the test module, but the slicer does not count it. The usual causes are a class-scoped helper, an instance-method driver, or a fixture-driven driver. Repair: T007 in misthelper-devtools. Forbidden repair: a duplicate test.
- **F4, stale or held.** The census no longer reports the entry (stale), or an open pull request owns the file (held). Repair: T012 for stale entries. Hold for owned files (FR-013).

## Detector Evidence at the Pinned Commit

The pinned devtools commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` holds `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` (blob `6e1da59538ea9df663d17d72d54f6d870f74a234`, research R-61 to R-68). The installed copy in `.venv` has the same blob (research R-69).

- `_findings_for_coverage` emits `missing_fm_http_4xx` only when `risk.http_status` is true and `coverage.http_4xx` is false (lines 704 and 708).
- `_node_has_http_status_risk` treats the string `mistapi.api.` as cloud API scope (line 378). Rows 2, 3, and 33 depend on this string rule.
- `_node_has_http_status_risk` also treats `mistapi` or `requests` imports (lines 371 to 374) and dotted `mistapi` attributes (lines 375 to 376) as HTTP status risk. Rows 31, 32, and 35 depend on these rules.
- `_allows_local_source` returns true for every test path outside `<root>/tests` (lines 348 and 351). Nested-project tests therefore inherit module-level imports as risk. Row 1 depends on this rule.
- `SourceDrivenCoverageSlicer` keeps only test functions that call a source root (line 438 and `_calls_source` at line 500). A call on an instance of a source class does not count. Row 22 depends on this rule.
- Local driver names (`_collect_source_driver_names`, line 538) cover top-level helper functions only. A class-scoped helper does not count. Row 22 depends on this rule, as the issue comment of 2026-11-09 records.
- `HttpStatusCoverageInferer` (line 84) counts a 4xx literal in a status context. A status context is an assignment, keyword, comparison, mapping key, parametrize name, or top-level helper argument (`_is_status_name`, line 240).

The mistapi response class stores the status (`self.status_code`, `__api_response.py` line 48, research R-71). A 4xx status from the SDK reaches the caller as an attribute, not as an exception.

## Defects in Existing Work

1. **Prior triage labels are superseded.** The 2700 triage row for `missing_fm_http_4xx` reads "Real gap" (`specs/2700-missing-failure-modes/triage.md` line 10, research R-19). The 1772 triage row reads "Real defect, repair later" (R-20). Both predate the current detector evidence. Twenty-six of 38 entries already hold a 4xx status literal (rows 1, 4-14, 19-23, 25, 27-30, 34, 36-38).
2. **The baseline likely holds stale entries.** The baseline holds 38 4xx and 42 5xx entries (research R-17 and the remote read of 2026-11-26). Issue comments report 15 current 5xx findings on 2026-11-09. The census (T003 and T004) confirms the count.
3. **Issue scope conflict.** Issue #2747 names the 5xx rule. The orchestrator task names the 4xx rule. Issue #2746 has the title "Test quality: repair remaining missing_fm_http_4xx findings" and is open with labels `chore`, `tests`, `in-progress`. Decisions D-1 and D-10 record the resolution.
4. **Reservations in comments are historical.** Comments on #2747 cite PRs #4404, #4619, #4503, #4514, #4497, #4357, #4324, #4312, #4478, #4402, #4385, and #4387 as reservations. All of them are merged. The open pull request census (7 pull requests) overlaps the 38 test paths in one file only (PR #4208, row 19).
5. **Comments cite older test paths.** Some comments cite `tests/unit/test_config_utils_wave3.py` and `tests/unit/refactors/test_app_context_session_state.py`. Pull request #4358 (merged 2026-11-13) changed 87 test paths. The baseline and the tree use the current paths. This record uses the current paths.
6. **Cited PR #4133 does not resolve.** A comment cites a held "#4133 test candidate". The GitHub lookup for pull request #4133 in MistHelper fails (Unverified U-5).
7. **Candidate commits are not the pin.** Commits `b15d4f91` and `66449a34` exist in misthelper-devtools. The MistHelper pin names `2239e7bd`. The repair is not in the pin.

## Consistency Review

Coverage check (spec to tasks):

| Requirement | Tasks |
|-------------|-------|
| FR-001 | T002, T003, T004 |
| FR-002 | T005 |
| FR-003 | T011 |
| FR-004 | T011 |
| FR-005 | T006 |
| FR-006 | T007 |
| FR-007 | T013 (marker check) |
| FR-008 | T012 |
| FR-009 | T008, T009, T010 |
| FR-010 | T011 |
| FR-011 | T013 (inline comment review of new test code) |
| FR-012 | T012 (restore each non-4xx entry) |
| FR-013 | T011 (held file skipped) |
| FR-014 | `design/research.md` remote table and Unverified list |
| FR-015 | T-PR |

Success criteria: SC-001 (T005), SC-002 (T010, T-LOCAL-GATES), SC-003 (T011), SC-004 (T013, T-LOCAL-GATES), SC-005 (T-REMOTE-CI), SC-006 (T-PR file list in `plan.md`).

Defects found during the review, all repaired in this draft:

- A first draft of T012 wrote the baseline without restoring non-4xx entries. Repaired: T012 restores each non-4xx entry (FR-008, FR-012).
- A first draft of T-PR used a closing keyword. Repaired: FR-015 and D-6.
- A first draft expected F1 rows. Repaired: remote evidence shows zero F1 rows before the census.
- A first draft cited the candidate devtools commit as the fix. Repaired: the record cites the commit as existing, not as the pin (R-61 to R-68).

## Unresolved Items

- U-1: The census was not run. T003 and T004 record the counts.
- U-2: The upstream release date is unknown. T008 is the blocker for T009 onward.
- U-3: The record links the 4xx title to issue #2746 only by reference. D-10 keeps the record under issue #2747 as instructed.
- U-4: The family assignments for rows marked "Present" or "Stale" change after the census. The census overrides the pre-census family.
- U-5: Pull request #4133 cited in a comment does not resolve in MistHelper.
