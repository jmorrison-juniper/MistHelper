# Implementation Plan: Split tests/unit into domain packages

**Branch**: `chore/4142-unit-test-domain-packages` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/`. The route is the eight-digit base-5 encoding of 4142, which `.specify/scripts/powershell/spec-route.ps1` produces.

## Summary

Move the 45 remaining root entries of `tests/unit/` into the four existing containers. Each container gains source-aligned grouping directories. Split each source package that would exceed five children by test topic. Move a path only when no hold applies. Update each active reference in the same batch as its moved path. The final root holds `__init__.py` and the four containers.

## Current State On Main

The state below is read from GitHub `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on 2026-11-26. Remote check IDs (RC) refer to [research.md](design/research.md).

| Fact | Value | Check |
| - | - | - |
| Direct children of `tests/unit/` | 50 distinct tracked names | RC-01 |
| Containers present | `config`, `marvis`, `maps`, `prod_readiness` | RC-03 to RC-06 |
| Files under `tests/unit/` | 1,038 files in 285 directories | research section 2 |
| Files in the four containers | 391 | research section 2 |
| Files in the 45 remaining root entries | 646, including 15 root test modules | research section 2 |
| Oversized directories under `tests/unit/` | 30 directories hold six or more children | research section 2 |
| Final root required | 5 children | FR-001 |
| Juniper RMA files still at root | 22 (12 moved to `prod_readiness/operations/exporting/juniper_rma/`) | RC-07 |
| Issue #4142 | OPEN, reopened 2026-11-13 after partial PR #4358 | ledger V-5 in research section 7 |

The local working tree at the same commit holds 22 untracked directories under `tests/unit/` and one `__pycache__`. These entries are not on `main`. No batch counts or moves them.

## Technical Context

**Language/Version**: Python 3.15 or newer (`pyproject.toml` requires `>=3.15`).

**Primary Dependencies**: pytest, Ruff, Black, mypy, and the `misthelper-devtools` gates (`ste-linter`, `test-quality-analyzer`, `symbol-diff`).

**Storage**: None.

**Testing**: pytest collection, focused tests per batch, guard tests under `tests/guardrails`, and the test-quality ratchet.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python command-line application with a unit test suite.

**Performance Goals**: Collection after each batch yields the baseline node IDs. Test runtime does not change by design.

**Constraints**: Five children or fewer for each directory. No executable production change. No open-pull-request path moves. Package-relative imports keep working.

**Scale/Scope**: 1,038 test files, 45 root entries, 30 root directories, and about 40 oversized directories.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass with recorded debt | The final tree meets the limit. Until the final batch, the root holds 50 children. Debt C-1 stays open. `tests/unit/marvis/actions/` (11 children) is grandfathered until hold H-7 releases. |
| I. Five-Item Rule, new specs route | Pass | The route is `specs/numbered/0/0/1/1/3/0/3/2`. The base-5 encoding of 4142 matches the route. |
| II. Class-based architecture | Pass | No Python class or function changes. The new guard, if added, uses a class. |
| III. Safety-first | Pass | No input handling changes. |
| IV. Full deployment pipeline | Pass with staged work | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run after the last batch. |
| V. Observability | Pass | No logging changes in product code. |
| VI. Inline comments | Pass | Moved files keep their comments. A new guard line carries an inline comment. |
| VII. Action logging | Pass | No action code changes. |
| Mist Cloud transport | Not applicable | No Mist REST or WebSocket call changes. |
| File paths | Pass | Any new guard uses `pathlib.Path`. |
| Data directory and container rules | Not applicable | No product output and no container start. |
| Branch and commit rules | Pass | Branch `chore/4142-unit-test-domain-packages`. Commit type `refactor(tests)`. |
| Labels | Pass | Type `refactor`, scope `tests`, status `in-progress`. |

**Gate result**: Pass for this record. The implementation passes only after the final batch and the release of each hold.

## Holds

A hold stops a move. A hold has one of four types (D-2).

| ID | Type | Owner | Paths | Release condition |
| - | - | - | - | - |
| H-1 | Open pull request | PR #4208, draft | `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`, `tests/unit/wan_dashboard/wan_performance/**` (8 files), new root path `tests/unit/wan_performance/**` in the PR | PR #4208 merges, its owner accepts the handoff, and the PR rebases its new paths into the final layout |
| H-2 | Open pull request | PR #4813, draft | `tests/unit/db/sle_window_summary/test_backend_preservation.py`, `tests/unit/export/test_data_exporter.py`, `tests/unit/export/test_endpoint_family_exporter.py` | PR #4813 merges or closes, and its owner releases the three paths |
| H-3 | Planned edit | Issue #4721, open | `tests/unit/test_device_events_52w_exporter.py`, `tests/unit/test_device_events_52w_exporter_extended.py`, and the new file `tests/unit/export/test_device_events_checkpoint_recovery.py` named in its scope | Issue #4721 closes, or its owner releases both root files |
| H-4 | Exact claim | Issues #2746 and #2747, open | `tests/unit/ssh/test_cli_shell_manager.py` | The issue owner releases the exact path in a comment |
| H-5 | Planned edit | Issue #4133, open | `tests/unit/test_menu_entry_metadata.py` (session-only candidate) | The issue owner releases the path |
| H-6 | Planned edit | Issue #2711, open | `tests/unit/ui/test_parameter_collector.py` | The issue owner releases the path |
| H-7 | Planned edit | Issue #4008, open | `tests/unit/marvis/actions/**` (11 files) | The issue owner releases the path |
| H-8 | Conservative hold | Issue #2746 scope | `tests/unit/test_issue_2971_census_repairs.py` | The issue owner confirms that the file is not in its edit scope |

Issues #2753 and #4126 name paths only as inventory. They create no hold (D-2). Issue #2752 is closed. PR #4287, PR #4323, and PR #4317 do not appear among the open pull requests that change a `tests/` path, so they create no hold. The seven open pull requests on 2026-11-26 do not change `.github/workflows/ci.yml` or `pyproject.toml`.

## Decisions

The full decision records appear in [research.md](design/research.md) section 5.

| ID | Decision |
| - | - |
| D-1 | Keep the four existing containers as root domain groups. |
| D-2 | Use four hold types. Inventory mentions create no hold. |
| D-3 | Move `tests/unit/analytics/test_insight_metrics_utils.py` now. Its historical link becomes stale. |
| D-4 | Move the whole `tests/unit/container/output_defaults/` package. Its relative imports stay valid. |
| D-5 | Place the root `org` package in `marvis/standalone/mist/resources/org/`, because `marvis/mist/resources/` is full. |
| D-6 | Create `marvis/mist/realtime/` for WebSocket packages and for `marvis/actions/`. |
| D-7 | Update CI and `pyproject.toml` selectors in the same batch as the moved paths they name. |
| D-8 | Leave `src/`, `web_portal/`, `Dockerfile`, and `Containerfile` comments unchanged in this issue. Track them in a follow-up issue. |
| D-9 | Use topic groups. Each group holds five children or fewer, including package markers. |
| D-10 | Keep `tests/unit/__init__.py` at the root as the fifth child. |

## Target Parents And Child Counts

Each row shows the directory children after its batch. The count includes files and directories. Each count is five or fewer.

| Parent (under `tests/unit/`) | Children after the batch | Count |
| - | - | - |
| `./` | `__init__.py`, `config`, `marvis`, `maps`, `prod_readiness` | 5 |
| `config/foundation/` | `models`, `persistence`, `runtime`, `support` | 4 |
| `config/foundation/models/` | `dataclasses`, `dataproc` | 2 |
| `config/foundation/persistence/storage/` | `arango_indexes`, `cache`, `db`, `db_discovery` | 4 |
| `config/foundation/persistence/storage/db/` | `__init__.py`, `sle_window_summary`, `test_database_schema_utils.py`, `test_retention_redis_scan.py`, `test_sqlite_database_writer_logging.py` | 5 |
| `config/foundation/runtime/core/input/` | `test_prompt_client_utils.py`, `test_prompt_network_device_utils.py` | 2 |
| `config/foundation/runtime/startup/bootstrap/preflight/` | `test_dns_preflight.py`, `test_github_account_checker.py`, `test_credential_preflight.py` | 3 |
| `config/foundation/support/` | `benchmarks`, `helpers`, `refactors`, `serial_cc`, `utils` | 5 |
| `config/foundation/support/refactors/` | `__init__.py`, `data`, `network`, `runtime`, `telemetry` | 5 |
| `config/foundation/support/refactors/data/inventory/` | 2 existing, plus `test_csv_comparator.py` and `test_device_data_fetcher.py` | 4 |
| `config/foundation/support/refactors/network/clients/` | `test_service_ping_launcher.py`, `test_service_ping_discovery.py`, `test_service_ping_manager.py` | 3 |
| `config/foundation/support/refactors/network/configuration/` | 2 existing, `test_wan_probe_device_override_manager.py`, and `test_wlanradius_timer_manager_paths.py` after H-1 | 4 |
| `config/foundation/support/refactors/runtime/console/` | 3 existing, plus `test_tui_launcher.py` | 4 |
| `config/foundation/support/refactors/runtime/session/` | 2 existing, plus `test_app_context_session_state.py` and `test_initialize_mist_session.py` | 4 |
| `config/standalone/foundation/runtime/startup/` | 4 existing, plus `test_standalone.py` | 5 |
| `config/standalone/foundation/support/quality/imports/` | 3 existing, plus `test_module_relocation.py` | 4 |
| `config/standalone/foundation/support/quality/risk/` | 1 existing, plus `test_issue_1709_narrow_except.py` | 2 |
| `config/standalone/foundation/support/utilities/network/` | 3 existing, plus `test_routing_utils.py` | 4 |
| `marvis/mist/` | `__init__.py`, `access`, `intelligence`, `realtime`, `resources` | 5 |
| `marvis/mist/access/` | `api`, `audit`, `auth` | 3 |
| `marvis/mist/access/api/` | 4 moved modules, plus `test_unparseable_response_guards.py` | 5 |
| `marvis/mist/intelligence/` | `analytics`, `ap_warning_report`, `juniper_docs`, `reports`, `troubleshooting` | 5 |
| `marvis/mist/intelligence/analytics/` | 4 existing, plus `test_insight_metrics_utils.py` | 5 |
| `marvis/mist/intelligence/ap_warning_report/` | 5 moved modules | 5 |
| `marvis/mist/intelligence/reports/audits/posture/` | 4 existing, plus `psk_hygiene` | 5 |
| `marvis/mist/intelligence/reports/device_health/` | 3 existing, plus 2 wired-client generator modules | 5 |
| `marvis/mist/realtime/` | `actions`, `websocket`, `websocket_streams` | 3 |
| `marvis/mist/resources/` | `__init__.py`, `device`, `gateway`, `inventory`, `site` | 5 |
| `marvis/mist/resources/device/` | `__init__.py`, `test_device_handler_narrowing.py`, `client_session_control`, `test_ap_profile_migration_manager.py`, `test_arp_command_manager.py` | 5 |
| `marvis/mist/resources/gateway/` | `__init__.py`, `exporters`, `overrides`, `ssr_registration`, `wan_overrides` | 5 |
| `marvis/mist/resources/gateway/exporters/` | 3 existing, plus 2 gateway export-utility modules | 5 |
| `marvis/mist/resources/gateway/wan_overrides/` | 3 existing, plus 2 WAN probe modules | 5 |
| `marvis/mist/resources/gateway/ssr_registration/` | 2 existing, plus 2 WAN2 migration modules | 4 |
| `marvis/mist/resources/inventory/` | `csv_imports`, `device_replace`, `inventory_summary`, `org_device`, `support` | 5 |
| `marvis/mist/resources/inventory/csv_imports/` | 4 existing, plus `test_csv_comparator_broad_handlers.py` | 5 |
| `marvis/mist/resources/inventory/org_device/` | 4 moved modules | 4 |
| `marvis/mist/resources/site/` | `__init__.py`, `address_audit`, `rrm_reset`, 2 existing modules | 5 |
| `marvis/standalone/mist/intelligence/` | `analytics`, `marvis`, `reports` | 3 |
| `marvis/standalone/mist/resources/device/` | `test_device_multi_ap_scan_workflow.py`, `utility`, `test_device_reboot_manager.py`, `test_device_utils.py`, `test_virtual_chassis.py` | 5 |
| `marvis/standalone/mist/resources/device/utility/` | 2 existing modules moved from the device standalone group | 2 |
| `marvis/standalone/mist/resources/gateway/` | 3 existing, plus `device_template_cloner` | 4 |
| `marvis/standalone/mist/resources/org/` | 2 existing, plus split groups from the root `org` package | 5 or fewer after split |
| `maps/interfaces/` | `handlers`, `maps`, `monitoring`, `portals`, `ui` | 5 |
| `maps/interfaces/handlers/` | `scripts` | 1 |
| `maps/interfaces/portals/` | `upgrade_portal`, `web_portal`, `wan_dashboard` | 3 |
| `maps/interfaces/portals/wan_dashboard/` | `test_worker.py`, `wan_performance` after H-1 | 2 |
| `maps/standalone/interfaces/ui/` | 2 existing, plus `test_menu_entry_metadata.py` and `test_issue_2971_census_repairs.py` after holds | 4 |
| `prod_readiness/operations/` | `execution`, `exporting`, `hardware`, `protection` | 4 |
| `prod_readiness/operations/execution/` | `capture`, `firmware`, `prod_readiness`, `ssh` | 4 |
| `prod_readiness/operations/execution/firmware/` | `__init__.py`, `policy`, `policy_jobs`, `upgraders` | 4 |
| `prod_readiness/operations/execution/firmware/upgraders/` | `aggregations`, `manager`, `upgrades` | 3 |
| `prod_readiness/operations/execution/firmware/upgraders/aggregations/` | 4 existing, plus `test_aggregate_upgrade_service.py` | 5 |
| `prod_readiness/operations/execution/firmware/upgraders/manager/` | 2 existing, plus 3 firmware manager modules | 5 |
| `prod_readiness/operations/execution/firmware/upgraders/upgrades/` | 2 existing, plus `test_firmware_manager_version.py` and `test_bulk_ap_running_version.py` | 4 |
| `prod_readiness/operations/exporting/` | `container`, `export`, `juniper_rma` | 3 |
| `prod_readiness/operations/exporting/container/` | `__init__.py`, `build_support`, `output_defaults`, `runtime`, `session_database` | 5 |
| `prod_readiness/operations/hardware/` | `ex_hardware_inventory`, `mib_generator` | 2 |
| `prod_readiness/operations/protection/security/` | `__init__.py`, `test_credential_redaction.py`, `rogue_dhcp` | 3 |
| `prod_readiness/standalone/operations/execution/firmware/` | 3 existing, plus `test_firmware_upgrade_status_checker.py` and `test_running_version.py` | 5 |

Split groups inside the large packages must also hold five children or fewer. Each split task records its group table before its move. The split rule appears in section 6 of [tasks.md](tasks.md).

## Change Map

The change map names each source path, its destination, its batch, and its hold. A batch can run only when its holds are clear.

| Source | Files | Destination | Mode | Batch | Hold |
| - | - | - | - | - | - |
| `tests/unit/analytics/` | 1 | `tests/unit/marvis/mist/intelligence/analytics/` | Move directory contents | A | None |
| `tests/unit/ap_warning_report/` | 5 | `tests/unit/marvis/mist/intelligence/ap_warning_report/` | Move directory | A | None |
| `tests/unit/api/` | 4 | `tests/unit/marvis/mist/access/api/` | Move directory | A | None |
| `tests/unit/test_unparseable_response_guards.py` | 1 | `tests/unit/marvis/mist/access/api/` | Move file | A | None |
| `tests/unit/container/output_defaults/` | 5 | `tests/unit/prod_readiness/operations/exporting/container/output_defaults/` | Move directory | A | None |
| `tests/unit/dataclasses/` | 5 | `tests/unit/config/foundation/models/dataclasses/` | Move directory | A | None |
| `tests/unit/db_discovery/` | 5 | `tests/unit/config/foundation/persistence/storage/db_discovery/` | Move directory | A | None |
| `tests/unit/db/test_database_schema_utils.py` | 1 | `tests/unit/config/foundation/persistence/storage/db/` | Move file | A | None |
| `tests/unit/db/sle_window_summary/test_export_identity.py` | 1 | `tests/unit/config/foundation/persistence/storage/db/sle_window_summary/` | Move file | A | None |
| `tests/unit/db/sle_window_summary/test_backend_preservation.py` | 1 | `tests/unit/config/foundation/persistence/storage/db/sle_window_summary/` | Move file | D | H-2 |
| `tests/unit/device/test_ap_profile_migration_manager.py` | 1 | `tests/unit/marvis/mist/resources/device/` | Move file | A | None |
| `tests/unit/device/test_arp_command_manager.py` | 1 | `tests/unit/marvis/mist/resources/device/` | Move file | A | None |
| `tests/unit/device/test_device_reboot_manager.py` | 1 | `tests/unit/marvis/standalone/mist/resources/device/` | Move file | A | None |
| `tests/unit/device/test_device_utils.py` | 1 | `tests/unit/marvis/standalone/mist/resources/device/` | Move file | A | None |
| `tests/unit/device/__init__.py` | 1 | Deleted, because `marvis/mist/resources/device/__init__.py` exists | Delete after import smoke | A | None |
| `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py` and `_wave3.py` | 2 | `tests/unit/marvis/standalone/mist/resources/device/utility/` | Regroup existing files | A | None |
| `tests/unit/test_virtual_chassis.py` | 1 | `tests/unit/marvis/standalone/mist/resources/device/` | Move file | A | None |
| `tests/unit/device/client_session_control/` | 6 | `tests/unit/marvis/mist/resources/device/client_session_control/` | Split and move | B | None |
| `tests/unit/gateway/` export utilities | 2 | `tests/unit/marvis/mist/resources/gateway/exporters/` | Move files | A | None |
| `tests/unit/gateway/` WAN probe modules | 2 | `tests/unit/marvis/mist/resources/gateway/wan_overrides/` | Move files | A | None |
| `tests/unit/gateway/` WAN2 migration modules | 2 | `tests/unit/marvis/mist/resources/gateway/ssr_registration/` | Move files | A | None |
| `tests/unit/gateway/` template cloner modules | 2 | `tests/unit/marvis/standalone/mist/resources/gateway/device_template_cloner/` | Move files | A | None |
| `tests/unit/inventory/test_csv_comparator_broad_handlers.py` | 1 | `tests/unit/marvis/mist/resources/inventory/csv_imports/` | Move file | A | None |
| `tests/unit/inventory/` org device modules | 4 | `tests/unit/marvis/mist/resources/inventory/org_device/` | Move files | A | None |
| `tests/unit/reports/psk_hygiene/` | 5 | `tests/unit/marvis/mist/intelligence/reports/audits/posture/psk_hygiene/` | Move directory | A | None |
| `tests/unit/reports/` wired-client modules | 2 | `tests/unit/marvis/mist/intelligence/reports/device_health/` | Move files | A | None |
| `tests/unit/refactors/__init__.py` | 1 | `tests/unit/config/foundation/support/refactors/__init__.py` | Move file | A | None |
| `tests/unit/refactors/` runtime session modules | 2 | `tests/unit/config/foundation/support/refactors/runtime/session/` | Move files | A | None |
| `tests/unit/refactors/test_device_data_fetcher.py` | 1 | `tests/unit/config/foundation/support/refactors/data/inventory/` | Move file | A | None |
| `tests/unit/refactors/test_issue_3732_read_retry.py` | 1 | `tests/unit/config/foundation/support/refactors/data/storage/` | Move file | A | None |
| `tests/unit/refactors/test_tui_launcher.py` | 1 | `tests/unit/config/foundation/support/refactors/runtime/console/` | Move file | A | None |
| `tests/unit/refactors/test_wan_probe_device_override_manager.py` | 1 | `tests/unit/config/foundation/support/refactors/network/configuration/` | Move file | A | None |
| `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | 1 | `tests/unit/config/foundation/support/refactors/network/configuration/` | Move file | D | H-1 |
| `tests/unit/troubleshooting/test_module_relocation.py` | 1 | `tests/unit/config/standalone/foundation/support/quality/imports/` | Move file | A | None |
| `tests/unit/test_credential_preflight.py` | 1 | `tests/unit/config/foundation/runtime/startup/bootstrap/preflight/` | Move file | A | None |
| `tests/unit/test_csv_comparator.py` | 1 | `tests/unit/config/foundation/support/refactors/data/inventory/` | Move file | A | None |
| `tests/unit/test_issue_1709_narrow_except.py` | 1 | `tests/unit/config/standalone/foundation/support/quality/risk/` | Move file | A | None |
| `tests/unit/test_prompt_network_device_utils.py` | 1 | `tests/unit/config/foundation/runtime/core/input/` | Move file | A | None |
| `tests/unit/test_routing_utils.py` | 1 | `tests/unit/config/standalone/foundation/support/utilities/network/` | Move file | A | None |
| `tests/unit/test_standalone.py` | 1 | `tests/unit/config/standalone/foundation/runtime/startup/` | Move file | A | None |
| `tests/unit/test_zone_analyzer.py` | 1 | `tests/unit/marvis/standalone/mist/intelligence/analytics/` | Move file | A | None |
| `tests/unit/wan_dashboard/test_worker.py` | 1 | `tests/unit/maps/interfaces/portals/wan_dashboard/` | Move file | A | None |
| `tests/unit/wan_dashboard/wan_performance/` | 8 | `tests/unit/maps/interfaces/portals/wan_dashboard/wan_performance/` | Split and move | D | H-1 |
| `tests/unit/firmware/__init__.py` | 1 | `tests/unit/prod_readiness/operations/execution/firmware/__init__.py` | Move file | A | None |
| `tests/unit/firmware/test_aggregate_upgrade_service.py` | 1 | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/` | Move file | A | None |
| `tests/unit/firmware/` manager modules | 3 | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/` | Move files | A | None |
| `tests/unit/firmware/` version and bulk modules | 2 | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/` | Move files | A | None |
| `tests/unit/firmware/` status and running modules | 2 | `tests/unit/prod_readiness/standalone/operations/execution/firmware/` | Move files | A | None |
| `tests/unit/ex_hardware_inventory/` | 25 | `tests/unit/prod_readiness/operations/hardware/ex_hardware_inventory/` | Split and move | B | None |
| `tests/unit/juniper_docs/` | 34 | `tests/unit/marvis/mist/intelligence/juniper_docs/` | Split and move | B | None |
| `tests/unit/juniper_rma/` remainder | 22 | `tests/unit/prod_readiness/operations/exporting/juniper_rma/` | Split and merge | B | None |
| `tests/unit/scripts/` | 14 | `tests/unit/maps/interfaces/handlers/scripts/` | Split and move | B | None |
| `tests/unit/security/rogue_dhcp/` | 6 | `tests/unit/prod_readiness/operations/protection/security/rogue_dhcp/` | Split and move | B | None |
| `tests/unit/site/address_audit/` | 16 | `tests/unit/marvis/mist/resources/site/address_audit/` | Split and move | B | None |
| `tests/unit/site/__init__.py` | 1 | Deleted, because `marvis/mist/resources/site/__init__.py` exists | Delete after import smoke | B | None |
| `tests/unit/ssh/` (except `test_cli_shell_manager.py`) | 11 | `tests/unit/prod_readiness/operations/execution/ssh/` | Split and move | B | None |
| `tests/unit/ssh/test_cli_shell_manager.py` | 1 | `tests/unit/prod_readiness/operations/execution/ssh/` | Move file | D | H-4 |
| `tests/unit/test_ssh_host_key_tofu.py` | 1 | `tests/unit/prod_readiness/operations/execution/ssh/` | Move file | B | None |
| `tests/unit/ui/` (except `test_parameter_collector.py`) | 13 | `tests/unit/maps/interfaces/ui/` | Split and move | B | None |
| `tests/unit/ui/test_parameter_collector.py` | 1 | `tests/unit/maps/interfaces/ui/` | Move file | D | H-6 |
| `tests/unit/utils/` | 17 | `tests/unit/config/foundation/support/utils/` | Split and move | B | None |
| `tests/unit/websocket/` service-ping modules | 2 | `tests/unit/config/foundation/support/refactors/network/clients/` | Move files | B | None |
| `tests/unit/websocket/` remaining modules | 11 | `tests/unit/marvis/mist/realtime/websocket/` | Split and move | B | None |
| `tests/unit/org/` | 18 | `tests/unit/marvis/standalone/mist/resources/org/` | Split and move | B | None |
| `tests/unit/marvis/actions/` | 11 | `tests/unit/marvis/mist/realtime/actions/` | Split and move | D | H-7 |
| `tests/unit/upgrade_portal/` | 176 | `tests/unit/maps/interfaces/portals/upgrade_portal/` | Split and move | C | None |
| `tests/unit/web_portal/` | 53 | `tests/unit/maps/interfaces/portals/web_portal/` | Split and move | C | None |
| `tests/unit/websocket_streams/` | 64 | `tests/unit/marvis/mist/realtime/websocket_streams/` | Split and move | C | None |
| `tests/unit/export/` (except H-2 files) | 58 | `tests/unit/prod_readiness/operations/exporting/export/` | Split and move | C | None |
| `tests/unit/export/test_data_exporter.py` and `test_endpoint_family_exporter.py` | 2 | `tests/unit/prod_readiness/operations/exporting/export/` | Move files | D | H-2 |
| `tests/unit/test_org_inventory_exporter_helpers.py` | 1 | `tests/unit/prod_readiness/operations/exporting/export/` | Move file | C | None |
| `tests/unit/test_device_events_52w_exporter.py` and `_extended.py` | 2 | `tests/unit/prod_readiness/operations/exporting/export/` | Move files | D | H-3 |
| `tests/unit/test_menu_entry_metadata.py` | 1 | `tests/unit/maps/standalone/interfaces/ui/` | Move file | D | H-5 |
| `tests/unit/test_issue_2971_census_repairs.py` | 1 | `tests/unit/maps/standalone/interfaces/ui/` | Move file | D | H-8 |

Batch A moves unowned directories and files with fixed destinations. Batch B splits unowned packages by topic. Batch C moves the largest unowned packages. Batch D runs after each hold releases. The root `tests/unit/__init__.py` stays in place.

## Reference Updates

Each row names an active reference that the batch changes. Historical records stay unchanged (FR-004).

| File | Lines on main | Change | Batch |
| - | - | - | - |
| `.github/workflows/ci.yml` | 263, 264, 267 | Update `test_paths` and `--ignore` values for `tests/unit/upgrade_portal` | C |
| `.github/workflows/ci.yml` | 99 and comment 96 | Update the RADON path for `tests/unit/utils/test_zscaler_catalogue.py` | B |
| `.github/workflows/ci.yml` | 303 | Update `tests/unit/scripts/test_script_imports.py` | B |
| `pyproject.toml` | 269, 271, 275 | Update root E402 entries for `test_csv_comparator.py`, `test_routing_utils.py`, and `test_zone_analyzer.py` | A |
| `pyproject.toml` | 516 | Update the `testpaths` entry for `tests/unit/upgrade_portal` | C |
| `.github/copilot-instructions.md` | 87 | Update the `pytest-chunks --split` path for `upgrade_portal` | C |
| `.github/copilot-instructions.md` | 255 | Update the output-scan test path | C |
| `.github/test-quality-baseline.json` | 624 `file_path` values that name `tests/unit/` (RC-26) | Update each moved `file_path` and `related_source` value in the batch that moves the file | Each batch |
| `tests/e2e/upgrade_portal/conftest.py` | 2881 | Update the comment path | C |
| `tests/e2e/upgrade_portal/test_alert_prefix_space.py`, `test_capture_identifier_paint.py`, `test_narrow_action_cells.py` | One line each | Update the path in the comment or string | C |
| `tests/e2e/web_portal/juniper_browser_harness.py` | One line | Update the path | C |
| `tests/support/rehearsal/clock.py` | 10 | Update the path in the docstring | C |
| `tests/tools/test_quality_analyzer/test_golden_repo.py` | 15 | Update the path only if the test reads it | B |
| `tests/guardrails/test_e2e_shard_partition.py` and `test_guard_proof_audit.py` | One line each | Update the path when it names a moved file | Each batch |
| `documentation/diagrams/infrastructure/deployment-pipeline.md` | One line | Update the path when it names a moved file | Each batch |

Historical records stay unchanged. These records include `CHANGELOG.md`, `.github/copilot-handoff.md`, `documentation/release-notes.md`, `documentation/development-tooling-migration.md`, and `.specify/bugs/`. The production references in `src/` and `web_portal/` and the build-file comments in `Dockerfile` and `Containerfile` stay unchanged (D-8).

## Test Plan

| ID | Test | Requirement | Success criterion |
| - | - | - | - |
| TP-1 | Child-count assertions for `tests/unit/` and each grouping directory in an existing guard test | FR-001, FR-002 | SC-001, SC-002 |
| TP-2 | Collection parity, comparing node IDs before and after normalization | FR-003 | SC-003 |
| TP-3 | Focused pytest on each moved directory after its batch | FR-005 | SC-004 |
| TP-4 | Guard suite `tests/guardrails` | FR-004 | SC-006 |
| TP-5 | Reference scan with `git grep` for each old path | FR-004 | SC-006 |
| TP-6 | Import smoke for each moved package | FR-005 | SC-004 |
| TP-7 | Hold check against open pull request files and issue comments | FR-006 | SC-005 |
| TP-8 | Production diff check that finds no executable change in `src/`, `web_portal/`, `Dockerfile`, or `Containerfile` | FR-007 | SC-005 |

The commands appear in [quickstart.md](design/quickstart.md). The tests use the existing `pytest` and `git` tools.

## Dependencies

1. Batch A has no hold dependency. Batch A runs first.
2. Batch B runs after Batch A. Batch B holds no path owned by a pull request.
3. Batch C runs after Batch B. It changes CI and `pyproject.toml` selectors in the same pull request.
4. Batch D runs after each named release. Each release must produce a record comment.
5. The final tasks run after Batch D.

## Risks And Mitigations

| Risk | Mitigation |
| - | - |
| An open issue edits a moved file | Refresh the holds before each batch. Rebase the batch on the current file. |
| PR #4208 adds `tests/unit/wan_performance/` as a direct child | Require the owner to rebase the new paths into `maps/interfaces/portals/` before merge. |
| Two modules share a file name in different packages | Keep every package marker. Check collection parity after each batch. |
| A moved package uses a relative import | Move each package as one unit. Run import smoke. |
| A CI selector names a moved path | Update the selector in the same batch. Run the CI workflow. |
| An untracked local directory shadows a tracked path | Do not move untracked directories. Check `git status` before each batch. |
| A historical link becomes stale | FR-004 keeps historical text unchanged. Accept the stale link (D-3). |
| A batch changes a production file by mistake | Run TP-8 before commit. |

## Rollback

Each batch is one squash commit on its branch. To undo a batch, revert that commit on a new branch. Do not rewrite history on a shared branch. A revert restores each moved path. No holds change during a revert.

## Documentation

Update `.github/copilot-instructions.md` in Batch C, because it names two moved paths. Add one changelog fragment, `changelog.d/issue-4142-test-domain-packages.md`, in the final batch. The fragment names issue #4142 in one `Changed` bullet.

## Contracts

No interface contract applies. This change adds no CLI command, no output column, no API request, and no API response. The `design/contracts/` folder is omitted.

## Complexity Tracking

| Violation | Why needed | Rejected alternative |
| - | - | - |
| Root holds 50 children until the final batch (debt C-1) | Held paths must stay in place until their owners release them. | Moving held paths early creates conflicts with open work. |
| `marvis/actions/` holds 11 children until H-7 releases | Issue #4008 plans edits in that package. | Moving it now conflicts with the planned edits. |
| `tests/unit/marvis/standalone/mist/resources/org/` receives a root package (D-5) | `marvis/mist/resources/` holds five children. | Restructuring `marvis/mist/resources/` moves merged paths again. |
| `marvis/mist/realtime/` is a new group (D-6) | `marvis/mist/` has one free slot, and `realtime` fits the WebSocket and action modules. | Placing these modules under a full group violates FR-002. |
