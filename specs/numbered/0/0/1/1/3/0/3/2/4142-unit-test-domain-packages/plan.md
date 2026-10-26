# Implementation Plan: Unit Test Domain Packages

**Branch**: `jmorrison-juniper-4142-test-package-deconfliction` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/spec.md`.

## Summary

Move unit tests from the overloaded `tests/unit/` root into a bounded domain tree. Keep test discovery and behavior unchanged. Update every active path reference. Do not move a pull request path before its owner accepts the post-merge handoff or an active session path before its owner clears the claim.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: pytest, Ruff, Black, mypy

**Storage**: None

**Testing**: pytest collection and focused tests, plus the repository quality gates for changed paths

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python command-line application with a unit test suite

**Performance Goals**: Unit test collection includes every test collected before the moves.

**Constraints**: Keep the final `tests/unit/` root and each new grouping directory at five children or fewer, including any `__init__.py` file. Preserve package helper imports. Keep pull request and active session paths unchanged until their owners release them. Keep paths selected by the PR-owned CI workflow in place until its owner accepts the handoff.

**Scale/Scope**: Current main is `eb1aa85187d3d683aa79ab4a9192c3fc75193a5e`. Its `tests/unit/` root has 158 tracked direct entries: 48 directories, 108 test modules, and two support files. Pytest collected 29,536 tests with `python -m pytest -p no:cacheprovider tests/unit/ --collect-only -q`. The inventory does not include unmerged pull request files.

## Constitution Check

- **Five-Item Rule**: At `eb1aa85187d3d683aa79ab4a9192c3fc75193a5e`, the current `tests/unit/` root has 158 tracked direct entries. Reuse four existing directories as containers. Do not add a direct child to `tests/unit/`. Keep each new grouping directory at five children or fewer. Split an unowned package by test topic when its destination would exceed five children, including package markers.
- **Recorded debt**: Issue #4142 tracks the existing root excess. This plan resolves that debt without increasing any other child count.
- **Incremental remediation**: Move only unowned paths until their open pull requests merge. The root may remain over the limit during these staged changes. Do not merge a partial layout as the final remediation.
- **Test behavior**: Pytest scans `tests/` recursively and uses `test_*.py` and `*_test.py`. Preserve that collection and update explicit path references.
- **Ownership**: Refresh open pull request files, issue claims, and session claims before each move. PR #4208 remains open and draft. It owns its workflow selectors, `tests/unit/scripts/`, `tests/unit/upgrade_portal/`, `tests/unit/wan_performance/`, and `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. PR #4226 owns `tests/unit/gateway/overrides/test_cisco_config_converter.py`. PR #4287 owns `tests/unit/dataclasses/test_service_measurement.py`. PR #4316 owns `tests/unit/upgrade_portal/test_phase2_service_wiring.py`, `tests/unit/upgrade_portal/test_settle_gate_service.py`, and `tests/unit/upgrade_portal/test_upgrade_driver.py`. PR #4317 owns `tests/unit/device/test_arp_command_manager.py`, `tests/unit/test_routing_utils.py`, and `tests/unit/websocket/test_manager.py`. PR #4323 owns `tests/unit/reports/psk_hygiene/test_operation.py`. PR #4324 owns only `tests/test_upgrade_portal_mist.py`, outside this map. PRs #4308, #4310, #4311, #4312, #4313, #4314, #4315, and #4289 merged. Issues #2746 and #2747 claim `tests/unit/ssh/test_cli_shell_manager.py`. Issue #2746 also claims `tests/test_upgrade_portal_mist.py`. Issue #2752 still reserves API, export, upgrade portal, and related paths. Keep each affected package deferred until every path claim clears.
- **Upgrade portal ownership**: Issue #2752 reserves `tests/unit/upgrade_portal/` and related files until its upgrade-path work and human review finish. Its confirmed source paths include `src/interfaces/portals/upgrade_portal/capture/service.py`, `src/interfaces/portals/upgrade_portal/upgrade/driver.py`, and `src/interfaces/portals/upgrade_portal/settle/service.py`, plus their tests. Do not enable auto-merge for that portal work.
- **Workflow ownership**: PR #4208 owns `.github/workflows/ci.yml`. It remains draft and unmerged. Do not rebase, edit, or move its paths. Defer moves of `tests/unit/scripts/`, `tests/unit/upgrade_portal/`, and `tests/unit/wan_performance/` until PR #4208 merges and its owner accepts the handoff. Keep any other path selected by that workflow at its current location until then.
- **Product scope**: Do not change production code or Mist API behavior.

**Gate result**: Pass with staged work. Final compliance requires all reserved pull request paths to become available and move before the layout is complete.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── checklists/
    │   └── requirements.md
    ├── quickstart.md
    ├── research.md
    └── standalone-test-map.md
```

### Source Code

```text
tests/
└── unit/
    ├── __init__.py
    ├── config/
    │   ├── foundation/
    │   └── standalone/
    ├── marvis/
    │   ├── mist/
    │   └── standalone/
    ├── maps/
    │   ├── interfaces/
    │   └── standalone/
    └── prod_readiness/
        ├── operations/
        └── standalone/
```

**Structure Decision**: Keep the existing `config`, `marvis`, `maps`, and `prod_readiness` directories as the four containers. Add one domain directory and one `standalone` directory inside each container. This change adds no direct child to `tests/unit/`. Treat new group directories as namespace packages. Move each container's current test files, subdirectories, and package markers into its mapped domain package. Split a moved package into topic groups when any destination group would exceed five children. For example, move `tests/unit/config/test_config_utils.py` to `tests/unit/config/foundation/runtime/startup/config/test_config_utils.py`. Move the contents of `tests/unit/marvis/` to `tests/unit/marvis/mist/intelligence/marvis/`, the contents of `tests/unit/maps/` to `tests/unit/maps/interfaces/maps/`, and the contents of `tests/unit/prod_readiness/` to `tests/unit/prod_readiness/operations/execution/prod_readiness/`. Move standalone tests into the domain-specific `standalone` directory under the matching container. Add a package marker only when import evidence requires it, and count it as a child.

**Grouping Assumption**: Split `bootstrap` by test topic because its seven direct children exceed the five-child limit. Place dependency checks, package installation, package-index probes, and UV runtime tests under `bootstrap/dependency/`. Place DNS and GitHub-account preflight tests under `bootstrap/preflight/`. Keep the existing `bootstrap/__init__.py`. This gives the parent three children, the dependency group four, and the preflight group two.

**Package Split Assumption**: Split every unowned package by test topic when its destination would have more than five direct children. Preserve each package marker and helper with the tests that import it. Defer a package while any active claim owns a path in that package.

**Container Test Grouping Assumption**: Keep the root container package marker. Place build checks and shared build helpers in `build_support/`. Place session and startup checks in `runtime/`. Keep `output_defaults/` and `session_database/` as separate groups. This gives the container root five direct children, including its package marker.

**Serial Console Grouping Assumption**: Split the 11 `serial_cc` tests into five topic groups to meet the child limit. Use `setup/` for assignment and initialization tests, `security/` for security-event tests, `clients/` for client insight and capture tests, `capture_results/` for site scan and result tests, and `telemetry/` for SLE metrics and switch statistics.

**Additional Topic Grouping Assumption**: Split packet capture, firmware policy, MIB generator, troubleshooting, and Juniper Docs tests into the exact groups in `design/standalone-test-map.md`. The current ownership scan clears these groups. Refresh claims immediately before each move.

## Package Grouping Map

| Existing container / domain | Group | Existing test packages |
| - | - | - |
| `config/foundation` | `models` | `dataclasses`, `dataproc` |
| `config/foundation` | `persistence/storage` | `arango_indexes`, `cache`, `db`, `db_discovery` |
| `config/foundation` | `runtime/startup/bootstrap/dependency` | `test_dependency_check_paths.py`, `test_package_installer_wave9.py`, `test_pip_index_probe.py`, `test_uv_runtime.py` |
| `config/foundation` | `runtime/startup/bootstrap/preflight` | `test_dns_preflight.py`, `test_github_account_checker.py` |
| `config/foundation` | `runtime/startup/config` | `config` |
| `config/foundation` | `runtime/core` | `input`, `time`, `validation` |
| `config/foundation` | `support` | `benchmarks`, `helpers`, `refactors`, `serial_cc`, `utils` |
| `config/foundation` | `support/serial_cc/setup` | `test_global_assignments_builder.py`, `test_import_initialization_service.py` |
| `config/foundation` | `support/serial_cc/security` | `test_security_events.py`, `test_security_events_wave8.py` |
| `config/foundation` | `support/serial_cc/clients` | `test_site_client_insight_path.py`, `test_site_client_insights.py`, `test_start_site_client_capture_wireless.py` |
| `config/foundation` | `support/serial_cc/capture_results` | `test_start_site_scan_capture.py`, `test_test_results_by_site.py` |
| `config/foundation` | `support/serial_cc/telemetry` | `test_sle_metrics.py`, `test_switch_vc_stats.py` |
| `marvis/mist` | `access` | `api`, `audit`, `auth` |
| `marvis/mist` | `intelligence` | `analytics`, `juniper_docs`, `marvis`, `reports`, `troubleshooting` |
| `marvis/mist` | `realtime` | `websocket`, `websocket_streams` |
| `marvis/mist` | `resources` | `device`, `gateway`, `inventory`, `org`, `site` |
| `maps/interfaces` | `handlers` | `scripts` |
| `maps/interfaces` | `maps` | `maps` |
| `maps/interfaces` | `monitoring` | `metrics_gateway` |
| `maps/interfaces` | `portals` | `upgrade_portal`, `web_portal` |
| `maps/interfaces` | `ui` | `ui` |
| `prod_readiness/operations` | `execution/capture` | `capture`, `prod_readiness` |
| `prod_readiness/operations` | `execution/firmware` | `firmware`, `firmware_policy`, `firmware_policy_jobs` |
| `prod_readiness/operations` | `execution/ssh` | `ssh` |
| `prod_readiness/operations` | `exporting` | `export`, `juniper_rma` |
| `prod_readiness/operations` | `exporting/container` | `container/build_support`, `container/runtime`, `container/output_defaults`, `container/session_database` |
| `prod_readiness/operations` | `hardware` | `mib_generator` |
| `prod_readiness/operations` | `protection` | `security` |

This map assigns all 48 existing directories. It gives exact bounded topic groups for each currently unreserved oversized package. The `standalone` directories hold moved root test modules in source-aligned groups. The exact file map, current ownership holds, and group counts are in [design/standalone-test-map.md](design/standalone-test-map.md). Keep package markers with their logical groups. Do not move a claimed package until its owner clears every claim.

Use the tested source imports to select a standalone test group. For a test with no direct source import, use its test subject. Place cross-domain tests in the `foundation` quality group. Keep `_test_arango_writer_helpers.py` beside `test_arango_writer.py` and update its import. Add a package marker only when import evidence requires it. Record each source and destination in `design/standalone-test-map.md` before moving it.

## Implementation Sequence

### Current ownership holds

On 2026-10-26, the coordinator cleared the mapped MIB generator, firmware policy, and container test splits.
The exact-path scan checked 42 other open pull requests and 316 file records, including previous filenames.
The 21 new moves and their helper and document changes had no ownership overlap.
The existing branch now overlaps PR #4415 at rename source `tests/unit/test_wan_hub_group_manager.py`.
PRs #4471, #4438, and #4436 also own `pyproject.toml`, which the existing branch changes.
Keep these paths unchanged and request coordination before publication or rebase.
The local batches do not establish full acceptance or remove the draft hold.
The coordinator also cleared the existing troubleshooting map and its baseline path-only update.
That split moves 22 files, updates one existing consumer import, and changes 54 baseline path fields.
Keep `tests/unit/test_issue_2971_census_repairs.py` deferred because open issue #2746 names it.
Keep `tests/unit/test_menu_entry_metadata.py` deferred for open issues #4133 and #4126.
The utility package remains deferred because the reserved workflow selects `tests/unit/utils/test_zscaler_catalogue.py`.
The coordinator cleared the previous external-edit hold on `tests/unit/test_fast_mode_flag.py`.
Its content-identical move reduces the tracked unit root from 40 children to 39.
Keep oversized address-audit groups deferred for issues #2746, #2747, and #2753.
Keep the rogue-DHCP group deferred for issue #2746 and the Marvis actions group deferred for issue #4008.
Issue #2752 is now closed, but this does not clear other owners or the PR #4208 workflow hold.
Current main is `ef0e7e5991950aec9b8f094e32e47fc3f68b4d2f`.
The published branch head remains `63faa487ad441c27b348911aaf34c04ae1ad3244`.

At the approved base `efd178c3f76e580afc0b5511734498b61f3a0090`, PR #4350 owns three planned source paths.
Defer `tests/unit/arango_indexes/test_preservation.py`, `tests/unit/export/test_endpoint_family_exporter.py`, and `tests/unit/refactors/test_sqlite_database_writer.py`.
Defer the entire five-file Arango package because its tests share helpers.
Restore every Arango file and its contract and discovery imports to the exact approved base.
PR #4208 still owns its workflow and test paths. Other holds remain with PRs #4317, #4316, #4327, and #4226.
Refresh exact file lists before each batch. Keep these paths unchanged until their owners release them.
PR #4353 merged. The coordinator authorized the exact-base rebase and a pull request for completed, unowned moves.
Keep the issue open for incomplete tasks. Do not merge or enable auto-merge.
Compare both rename endpoints with every open pull request before publication.
Keep `tests/unit/analytics/test_insight_metrics_utils.py` at its original path.
The historical specification for issue #3300 links to that path, and FR-004 prohibits changes to historical records.
After PR #4357 merged, the coordinator approved rebase onto current main `aaab7b4541c2e578fb8c46d69da0446bfbd338a9`.
Preserve its UI test change and the historical-link deferral.
The moved MSP test fixture must preserve SDK module identities across test order.
Use scoped parent bindings instead of removing the SDK import cache.
After PR #4361 merged, the coordinator approved rebase onto `57d718be98ab2716127578d33b80326c641e64af`.
Preserve its credential-preflight test and both verified fixes.
The next coordinated base is `1c089ed07ba865a7e505df4774a79751c72187cf`, after PR #4364.
Preserve its WAN dashboard changes without expanding this branch's scope.

### Juniper RMA grouping correction

The initial package move retained four groups with more than five children.
Split API tests into service and transport groups.
Keep row tests together under `model/rows/`.
Group menu tests under `workflows/menus/` and lookup tests under `workflows/lookups/`.
Place saved JSON replies under `fixtures/payloads/` and change the fixture reader root.
Keep helper imports unchanged. Use namespace groups because existing test filenames are unique.
The exact map appears in `design/standalone-test-map.md`.

1. Inventory current test files, path references, and open pull request ownership.
2. Move unowned directories and standalone tests into the package map. Split each moved package into mapped topic groups when a group would exceed five children. Keep all reserved paths and paths selected by `.github/workflows/ci.yml` at their current locations.
3. Update explicit test imports, selectors, workflow paths, lint rules, and documentation for each moved path.
4. After an owning pull request merges and its owner accepts the handoff, move its changed files from the merged tree and update all references in the same batch. For issue #2752, wait until the owner completes the claimed work and human review, then verify the exact test and record paths. Keep actively claimed session paths unchanged until their owners clear the claims.
5. Compare test collection with the baseline and run affected tests and repository path guards.
6. Complete the root reorganization only after each reserved path and workflow selector is clear. Keep PR #4208 draft, unmerged, and unchanged until its owner approves the handoff.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Staged root excess while pull requests remain open | The plan must not move files that active pull requests own. | An immediate move of every package would conflict with the owners' active paths. |
