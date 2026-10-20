# Research: Unit Test Domain Packages

**Date**: 2026-10-20

## Decision: Reuse four existing root containers

**Decision**: Keep `config`, `marvis`, `maps`, and `prod_readiness` as the four root containers. Put the source-aligned domain groups under those existing directories, as shown in [plan.md](../plan.md).

**Rationale**: The root already has 158 children. These containers have one, two, one, and three direct children. Each can accept one domain group while remaining within the five-child limit. The final root keeps those four existing directories and `tests/unit/__init__.py`.

**Alternatives considered**:

- Keep each current package at the root. This preserves paths but leaves 158 direct entries.
- Use arbitrary numbered buckets. This meets the child limit but does not help engineers find tests.
- Move every path at once. This conflicts with active pull requests that edit current test paths.

**Grouping assumption**: Use `config/foundation`, `marvis/mist`, `prod_readiness/operations`, and `maps/interfaces`. Move each anchor package into its matching leaf group. Do not create any direct child under `tests/unit/`.

## Decision: Preserve recursive test discovery

**Decision**: Keep the test filename patterns and the `tests/` test root. Update explicit selectors to the new paths.

**Rationale**: `pyproject.toml` lists `tests` as a test path and collects `test_*.py` and `*_test.py`. Recursive collection supports nested groups. Existing direct imports such as `tests.unit.firmware_policy` prove that import references also need updates.

**Alternatives considered**:

- Add a separate test run for each new group. This duplicates configuration and can omit a group.
- Change test discovery to a custom enumerated path list. This adds maintenance and does not preserve the existing recursive contract.

## Decision: Defer paths owned by active pull requests

**Decision**: Keep each path owned by an open pull request at its current location until that pull request merges. Refresh the ownership list before each move batch.

**Rationale**: A path move would conflict with the owner's pending changes. The issue owner authorized work on unowned paths while those changes proceed.

**Alternatives considered**:

- Move the reserved paths and ask each owner to rebase. This creates avoidable conflict and can delay their work.
- Delay all work until every pull request merges. This blocks independent, unowned moves.

## Decision: Preserve historical path references

**Decision**: Update active code, test configuration, CI selectors, and current documentation when a test path moves. Preserve historical specifications, incident records, and handoff records.

**Rationale**: Historical records describe the paths that existed when their work completed. Rewriting them would change that record without improving current test discovery.

**Scope evidence**: A repository-wide scan found 3,264 `tests/unit/` path mentions in 650 files. The scan includes historical records. Inventory active references in T003 and exclude historical records from the move.

## Decision: Bound each destination group

**Decision**: Reduce the direct children under `tests/unit/` to five and keep every new grouping directory at five children or fewer. Split each unowned, claim-cleared package by test topic when its destination would exceed five direct children.

**Rationale**: The user approved this grouping rule on 2026-10-20. Keep claimed paths at their current locations until each owner releases them. Apply the same topic-splitting rule after each claim clears.

**Implementation state**: The topic maps in `design/standalone-test-map.md` cover each currently unreserved package that exceeds five children. Keep other packages deferred while their exact paths remain reserved. Do not report final compliance until every reserved package moves and the root reaches five children.

## Inventory Evidence

At `origin/main` revision `afb26d826e1d40aa46906093e69fda64407f4b49`, `tests/unit/` contains 158 direct entries: 48 directories, 108 test modules, and two support files. The support files are `__init__.py` and `_test_arango_writer_helpers.py`. The change from `ef92a475` modifies files inside existing packages and does not change the root entry count.

At `origin/main` revision `afb26d826e1d40aa46906093e69fda64407f4b49`, `python -m pytest -p no:cacheprovider tests/unit/ --collect-only -q` collected 29,459 tests. This verifies collection only. The full unit suite passed at revision `cdc965f5f59a99c1ae25fcca55871b6c14f4a19b`. It reported 29,414 passed, 25 skipped, and five warnings in 831.49 seconds. The result was recorded at `2026-10-19T23:25:22Z`.

The previous full unit run used revision `ef92a475`. It passed 29,412 tests, skipped 25, reported zero failures and zero errors, and emitted 10 warnings. It took 807.76 seconds. Do not use these results as the current-main baseline.

The feature branch comparison used base `ef92a47522a1b8ba8f6eadd3379d96d595fad17c`. At `2026-10-20T00:37:58Z`, the base and current worktree each collected 29,437 test node IDs. After mapping 112 moved file paths, the comparison found zero missing IDs and zero new IDs. This verifies the current move set against its branch base. The latest `origin/main` collection count is not this comparison baseline.

The serial-console move placed 11 tests in the five groups above. It updated 26 baseline fields across six test paths. The focused command `.venv/bin/python -m pytest -p no:cacheprovider tests/unit/config tests/unit/test_fast_mode_flag.py` passed 568 tests in 6.96 seconds. Ruff passed for the same paths, and Black reported that 39 files would remain unchanged. The full test-quality gate was not rerun because its documented procedure requires committed test inputs.

The audit and auth moves placed nine files in their mapped groups. They updated four baseline fields across two auth test paths. The command `.venv/bin/python -m pytest -p no:cacheprovider tests/unit/marvis/mist/access/audit tests/unit/marvis/mist/access/auth` passed 141 tests in 0.62 seconds. Ruff passed, and Black reported that nine files would remain unchanged.

The analytics and site moves used their mapped groups. The first focused site run found 22 collection errors because pytest resolved `site` as the standard-library module. Package markers in `mist/` and `mist/resources/` fixed the import root. The rerun command `.venv/bin/python -m pytest -p no:cacheprovider tests/unit/marvis/mist/intelligence/analytics tests/unit/marvis/mist/resources/site` passed 455 tests in 1.19 seconds. Ruff passed, and Black reported that 32 files would remain unchanged.

## Active Path Reference Inventory

At `origin/main` revision `cdc965f5f59a99c1ae25fcca55871b6c14f4a19b`, a search for `tests/unit/` and `tests.unit.` found 174 tracked files outside `specs/`, `CHANGELOG.md`, and `changelog.d/`. The search found 153 files under `tests/` and 21 other files in configuration, source comments, and current or historical documents. Update references as each path moves.

The broad scan gives the search scope and totals. This table records the exact references for the foundation packages in the current move batch. Recheck each package before its move.

| Source package | Active references or consumers | Historical references |
| - | - | - |
| `audit` | No active path references found. | None found. |
| `analytics` | Baseline findings now name the destination paths. | None found. |
| `auth` | Two findings in `.github/test-quality-baseline.json`; both now name the destination path. | None found. |
| `bootstrap` | Two findings in `.github/test-quality-baseline.json`; both now name the destination path. | None found. |
| `config`, `benchmarks`, `dataproc`, `helpers`, `time`, `validation` | No active path references found. | None found. |
| `db` | No active path references found. | `CHANGELOG.md` names one moved test. Preserve that release record. |
| `input` | One finding in `.github/test-quality-baseline.json`; it now names the destination path. | None found. |
| `arango_indexes` | Package imports and two consumers in `tests/contract/test_arango_declared_indexes.py` and `tests/unit/db_discovery/test_probe.py`; all now use the destination path. | None found. |
| `cache` | The package marker named its old path; it now describes package collection without a path. | None found. |
| `serial_cc` | The baseline now names the destination paths. The note in `tests/unit/test_fast_mode_flag.py` now refers to the telemetry test. | None found. |
| `site` | Baseline findings now name the destination paths. Its new package parents need marker files to prevent collision with the standard-library `site` module. | None found. |
| `prod_readiness` | Two test modules now use `tests/unit/prod_readiness/operations/execution/prod_readiness/`. | None found. |
| `security` | Six baseline fields across two tests now name `tests/unit/prod_readiness/operations/protection/security/`. No old active path remains. | None found. |
| `firmware_policy_jobs` | The two `ManualExecutor` consumers now import from the destination package. Comparison evidence tests now find the repository root after the move. | None found. |
| `container` | Internal imports, shell-module names, and current container documentation now name `tests/unit/prod_readiness/operations/exporting/container/`. Repository-root lookups account for the added group levels. No old active path remains. | None found. |

At `2026-10-20T00:37:27Z`, the open pull request refresh found the same reserved test paths listed above. PR #4208 remains draft. The test-quality session remains active on PR #4312 and claims only `tests/unit/ssh/test_cli_shell_manager.py`. The coordinator has not claimed the moved operations or container paths. The recorded PR #4309 merge commit `cdc965f5f59a99c1ae25fcca55871b6c14f4a19b` is an ancestor of current `origin/main`.

At `2026-10-20T00:37:58Z`, the operations batch moved the unclaimed `prod_readiness`, `security`, and `firmware_policy_jobs` packages. It updated six baseline fields across two security test paths and both `ManualExecutor` imports. The command `.venv/bin/python -m pytest -q -p no:cacheprovider tests/unit/prod_readiness/operations/execution/prod_readiness tests/unit/prod_readiness/operations/protection/security tests/unit/prod_readiness/operations/execution/firmware/policy_jobs tests/e2e/web_portal/test_firmware_jobs.py` passed 199 tests. Ruff passed, and Black reported 18 files unchanged.

The container batch moved 18 tracked files to `tests/unit/prod_readiness/operations/exporting/container/`. It updated the internal package imports, shell module name, and two current documentation references. The first test run exposed stale repository-root indexes and moved bytecode paths. The tests now use the root indexes for the new group depth, and the stale bytecode caches were removed. The command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/operations/exporting/container` passed 278 tests in 92.13 seconds. Ruff passed, and Black reported 18 files unchanged. A search found no active `tests/unit/container` or `tests.unit.container` reference.

The latest collection command, `.venv/bin/python -m pytest --collect-only -q tests/unit/`, collected 29,437 tests. A node-ID comparison against the feature branch base mapped 112 renamed paths and found zero missing IDs and zero new IDs.
| `db_discovery` | `tests/unit/test_redis_writer.py` and `tests/unit/upgrade_portal/test_store.py` import its test helpers. The second consumer remains reserved. | None found. |

The current CI workflow selects `tests/unit/scripts/` and `tests/unit/upgrade_portal/`. It does not select `bootstrap`, `container`, or `config`. The bootstrap path appears in the test-quality baseline. The first unclaimed move placed bootstrap tests under `config/foundation/runtime/startup/bootstrap/`. A five-child check required a topic split: dependency tests use `dependency/`, and DNS and account preflight tests use `preflight/`. The `container` path appears in test helper imports, the `Containerfile` and `Dockerfile` comments, and current container documentation. Preserve `documentation/development-tooling-migration.md`, `.github/copilot-handoff.md`, historical bug records, and release notes. The `mist-ops-platform` reference names that subproject's own tests and remains unchanged.

The refreshed open pull request paths are:

| Pull request | Reserved test paths |
| - | - |
| #4312 | `tests/unit/ssh/test_cli_shell_manager.py` |
| #4311 | `tests/unit/juniper_docs/test_content_dedup.py` |
| #4310 | `tests/unit/org/test_org_config_migration_conflicts.py` |
| #4313 | `tests/unit/api/test_api_fetch_utils.py` and `tests/unit/export/test_gateway_test_exporter.py` |
| #4314 | `tests/unit/dataclasses/test_operation_outcome.py` |
| #4315 | `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` |
| #4287 | `tests/unit/dataclasses/test_service_measurement.py` |
| #4226 | `tests/unit/gateway/overrides/test_cisco_config_converter.py` |
| #4208 | `tests/unit/wan_performance/` and `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py` |

The ownership snapshot is `2026-10-20T00:12:09Z`. PR #4289 merged at `afb26d826e1d40aa46906093e69fda64407f4b49`, so its test path is no longer reserved. PRs #4287 and #4314 still reserve tests under `tests/unit/dataclasses/`. The test-quality session reports one active claim, `tests/unit/ssh/test_cli_shell_manager.py`, under PR #4312. Recheck that session before each move.

At `2026-10-19T23:44:00Z`, the test-quality session confirmed its only active file claim remains `tests/unit/ssh/test_cli_shell_manager.py`. It has no current claim under `tests/unit/config/`, `tests/unit/container/`, `tests/unit/bootstrap/`, `tests/unit/benchmarks/`, `tests/unit/cache/`, `tests/unit/db/`, `tests/unit/db_discovery/`, `tests/unit/dataproc/`, `tests/unit/helpers/`, `tests/unit/input/`, `tests/unit/refactors/`, `tests/unit/serial_cc/`, `tests/unit/time/`, or `tests/unit/validation/`. Its next test-quality slices will use selected 4xx/5xx tests under `refactors/` and `tests/unit/utils/test_tls_policy.py`. The owner will claim each file on issue #4142 before editing and will skip each path moved by this issue.

The current PR refresh at `2026-10-20T00:12:09Z` found no open PR file under the moved bootstrap, config, benchmark, database, time, validation, input, helper, dataproc, Arango index, or cache packages. Defer `db_discovery` because `tests/unit/upgrade_portal/test_store.py` imports `tests.unit.db_discovery.fakes`, and the upgrade-portal files remain reserved for issue #2752 and PR #4208 ownership and human review.

At `2026-10-20T00:17:25Z`, no open PR owned `tests/unit/audit/` or `tests/unit/auth/`. The issue had no new claim comment, and the chore coordinator confirmed that no active session claim covered either package. The coordinator also agreed to exclude both moved source and destination paths from future claims.

`tests/unit/wan_performance/` does not exist on the inspected main revision. PR #4208 adds it and owns `.github/workflows/ci.yml`, `tests/unit/wan_performance/**`, and `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. PR #4208 remains draft and unmerged. Do not rebase, edit, or move its paths. Keep `scripts` and `upgrade_portal` in place until PR #4208 merges and its owner accepts the handoff.

PR #4309 merged as `cdc965f5`. At this snapshot, PR #4313 owned the listed API and export files and records. PR #4313 later merged. Issue #2752 still holds API, export, and related record paths, so keep those packages reserved until that owner clears each claim.

Issue #2752 also reserves `tests/unit/upgrade_portal/` and related files for capture-timeout and tracker read or rename error work. Its confirmed source paths are `src/interfaces/portals/upgrade_portal/capture/service.py`, `src/interfaces/portals/upgrade_portal/upgrade/driver.py`, and `src/interfaces/portals/upgrade_portal/settle/service.py`, plus their tests. Keep this portal work for human review. Do not enable auto-merge.

At this snapshot, PR #4310 owned the organization migration files. PR #4310 later merged. Issue #2746 still lists organization tests as campaign candidates, but its active exact-file claims do not include those tests. Refresh claims before moving the package.

The root helper `_test_arango_writer_helpers.py` is imported by `tests/unit/test_arango_writer.py`. Move these two files together to `tests/unit/config/standalone/foundation/persistence/arango_writer/` and update the import.

## Grouping Assumption

The map follows the production source package that each current test package covers. Standalone root tests will use their primary tested source package. A cross-domain test will use `foundation/support/`. The move batch will verify each choice against imports and assertions before it changes the path.

The four top-level domain names plus the existing `__init__.py` fill the five direct-child limit. The groups in the map hold no more than five existing packages. A group for standalone tests will split into subgroups before it exceeds five children, including any `__init__.py` file. The map records all 108 test modules and the helper file.

At `2026-10-20T02:06:05Z`, the current-main revision was `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`. The smallest cleared candidate was `tests/unit/maps/test_handler_narrowing.py`, mapped to `tests/unit/maps/interfaces/maps/test_handler_narrowing.py`. The open-PR path scan found no overlap. PR #4312 owns only `tests/unit/ssh/test_cli_shell_manager.py`, and its coordinator confirmed no maps claim. Issue #4142 and issue #2752 had no maps claim. The serial-console, audit, and auth destinations remained untouched and reserved.

The maps test moved as a 100-percent content-preserving rename. The focused command `.venv/bin/python -m pytest tests/unit/maps/interfaces/maps/test_handler_narrowing.py -q` passed 16 tests. Ruff passed, Black reported one file unchanged, and full unit collection found 29,437 tests. The old source path has no remaining active reference. Rebase the current work branch onto the recorded main revision before you open a pull request.

At `2026-10-20T02:11:59Z`, the metrics-gateway package ownership refresh found no open PR overlap and no issue #4142 or #2752 claim. The Chore issues coordinator confirmed no active issue or session claim on `tests/unit/metrics_gateway/` or `tests/unit/maps/interfaces/monitoring/metrics_gateway/`. The current-main revision remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

Five metrics-gateway test files moved to `tests/unit/maps/interfaces/monitoring/metrics_gateway/`. Three helper imports now use the destination path. The first package run found a stale repository-root lookup in the SNMP subprocess tests. Updating its parent index resolved the failure. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/maps/interfaces/monitoring/metrics_gateway` passed 124 tests. Ruff passed, and Black reported five files unchanged. The old package import path has no active reference.

At `2026-10-20T02:18:20Z`, the Juniper RMA ownership refresh found no open PR overlap and no issue #4142 or #2752 claim. The Chore issues coordinator confirmed no claim on either path. The current-main revision was `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

The Juniper RMA package moved to `tests/unit/prod_readiness/operations/exporting/juniper_rma/`. Its test imports and the browser-test helper imports now use the destination. The repository-root lookup uses the new package depth. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/operations/exporting/juniper_rma` passed 183 tests, and 15 live tests skipped because live mode was off. The browser test command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/e2e/web_portal/test_juniper_menus_browser.py` passed 18 tests. Ruff and Black passed. Full unit collection found 29,437 tests. After applying the staged rename map, node-ID comparison against the saved baseline found zero missing IDs and zero new IDs across 152 renamed paths.

At `2026-10-20T02:59:02Z`, the current-main revision was `e70e573b56284f89893657a3266d6e797821b5ea`. The PR scan found no open PR for either Arango source file or destination. The issue search found no claim for the helper. The recent session search found no helper-path claim. The earlier exact check found the test path clear.

The Arango writer test and helper moved together to `tests/unit/config/standalone/foundation/persistence/arango_writer/`. The test now imports its sibling helper through the `tests.unit` package path. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py` passed 249 tests. Ruff passed, and Black reported two files unchanged. Full unit collection matched the saved 29,438 node IDs after the one path substitution, with zero missing IDs and zero added IDs. The baseline still has 733 entries. Its 396 changed path fields match the detected test-file renames, and no other baseline field changed.

At `2026-10-20T03:00:29Z`, the open-PR scan found no claim on the three audit source files or their destination files. The issue search and the recent session search found no claim. The current-main revision was `e70e573b56284f89893657a3266d6e797821b5ea`.

The three audit tests moved to `tests/unit/marvis/standalone/mist/access/audit/`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/marvis/standalone/mist/access/audit` passed 81 tests. Ruff passed, and Black reported three files unchanged. Full unit collection matched all 29,438 saved node IDs after the three path substitutions, with zero missing IDs and zero added IDs. These tests have no test-quality baseline entries, so this move required no baseline edit.

At `2026-10-20T03:02:15Z`, the open-PR scan found no claim on the three firmware source files or their destinations. The issue search and recent session search found no claim. No open PR or recent session claim owned `pyproject.toml`. The current-main revision was `e70e573b56284f89893657a3266d6e797821b5ea`.

The three firmware tests moved to `tests/unit/prod_readiness/standalone/operations/execution/firmware/`. The per-file Ruff override in `pyproject.toml` now names the moved switch-upgrader test. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/standalone/operations/execution/firmware` passed 399 tests. Ruff passed, and Black reported three files unchanged. Full unit collection matched all 29,438 saved node IDs after the three path substitutions, with zero missing IDs and zero added IDs. The baseline still has 733 entries. Its 464 changed path fields match the detected test-file renames, and no other baseline field changed.

At `2026-10-20T03:03:55Z`, the open-PR scan found no claim on `tests/unit/test_router.py` or its destination. The issue search found #2861 for `tests/unit/test_standalone.py`; keep that path reserved. The recent session search found no claim on either test. The open-PR scan also confirmed the known #4321 retention reservation remains separate.

The router test moved to `tests/unit/config/standalone/foundation/persistence/database/test_router.py`. Its focused command passed 40 tests. Ruff passed, and Black reported one file unchanged. Full unit collection matched all 29,438 saved node IDs after the path substitution, with zero missing IDs and zero added IDs. The baseline still has 733 entries. Its 484 changed path fields match the detected test-file renames, and no other baseline field changed.

At `2026-10-20T03:04:53Z`, the open-PR scan found no claim on the three Redis source files or destination files. The issue search and recent session search found no claim. The current-main revision was `e70e573b56284f89893657a3266d6e797821b5ea`.

The Redis writer and webhook tests moved to `tests/unit/config/standalone/foundation/persistence/redis/`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/persistence/redis` passed 48 tests. Ruff passed, and Black reported three files unchanged. Full unit collection matched all 29,438 saved node IDs after the detected path substitutions, with zero missing IDs and zero added IDs. The baseline still has 733 entries. Its 496 changed path fields match the detected test-file renames, and no other baseline field changed.

At `2026-10-20T03:08:58Z`, the current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`. No open PR or recent session claim covered the startup test files. Issues #2746, #2747, and #2861 named `tests/unit/test_credential_preflight.py`; keep it reserved. An unstaged change existed in `tests/unit/test_fast_mode_flag.py`; leave that file unchanged.

Three clear startup tests moved to `tests/unit/config/standalone/foundation/runtime/startup/`. The runner test uses the unique destination name `test_standalone_interactive_test_runner.py`, because the repository already has another test with the old name. The container probe test uses the new repository-root depth. The focused command passed 52 tests with one existing collection warning. Ruff passed, and Black reported three files unchanged. Full collection matched 29,434 node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test from both collections.

At `2026-10-20T03:10:04Z`, the open-PR scan found no claim on `tests/unit/test_source_dependency_external_symbols.py` or its destination. The issue search and recent session search found no claim. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

The test moved to `tests/unit/config/standalone/foundation/runtime/release/test_source_dependency_external_symbols.py`. Its focused command passed seven tests. Ruff passed, and Black reported one file unchanged. Full collection matched 29,434 saved node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline has 733 entries, and this test has no baseline records.

At `2026-10-20T03:11:00Z`, the open-PR scan found no claim on either standalone site test or its destination. The issue search and recent session search found no claim. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

The two standalone site tests moved to `tests/unit/marvis/standalone/mist/resources/site/`. Their focused command passed 80 tests. Ruff passed, and Black reported two files unchanged. Full collection matched 29,434 saved node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline still has 733 entries. Its 504 changed path fields match the detected test-file renames, and no other baseline field changed.

At `2026-10-20T03:12:35Z`, the open-PR scan found no claim on the four standalone API tests or their destination files. The issue search and recent session search found no claim. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

The four API tests moved to `tests/unit/marvis/standalone/mist/access/api/`. The OpenAPI test now resolves the repository root from its mapped package depth. Its first post-move run exposed the old depth and failed one test. The focused command then passed 64 tests. Ruff passed, and Black reported four files unchanged. Full collection matched 29,434 saved node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline still has 733 entries and 504 changed path fields. No baseline field changed in this batch.

At `2026-10-20T03:14:01Z`, the open-PR scan found no claim on the three registry tests that moved. Issue searches found #4133 and #4126 for `tests/unit/test_menu_entry_metadata.py`, and #2746 and #2747 for `tests/unit/test_msp_privilege_detection.py`. Keep both files reserved. No claim appeared for the three moved tests. The recent session search found no claim on the five candidates. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

The three unclaimed registry tests moved to `tests/unit/config/standalone/foundation/support/registry/`. Their focused command passed 11 tests. Ruff passed, and Black reported three files unchanged. Full collection matched 29,434 saved node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline still has 733 entries and 504 changed path fields. No baseline field changed in this batch.

At `2026-10-20T03:16:20Z`, the open-PR scan found no claim on the five device tests or their destinations. Issue #2746 names `tests/unit/test_prompt_network_device_utils.py`; keep that file reserved. The other four issue searches and the recent session search found no claim. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

Three unclaimed device tests moved to `tests/unit/marvis/standalone/mist/resources/device/`. The multi-AP test uses the unique name `test_device_multi_ap_scan_workflow.py`, because another test has the old basename. The focused command passed 4,099 tests. Ruff passed, and Black reported three files unchanged. Full collection matched 29,434 saved node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline still has 733 entries and 504 changed path fields. No baseline field changed in this batch.

At `2026-10-20T03:17:33Z`, the open-PR scan found no claim on the two report tests or their destinations. The issue search and recent session search found no claim. The repository has another `test_offline_device_reporter.py`, so the moved test uses the unique destination name `test_standalone_offline_device_reporter.py`. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

The two report tests moved to `tests/unit/marvis/standalone/mist/intelligence/reports/`. The focused command passed 51 tests. Ruff passed, and Black reported two files unchanged. Full collection matched 29,434 saved node IDs after path changes, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline still has 733 entries. Its 506 changed path fields match the detected test-file renames, and no other baseline field changed.

At `2026-10-20T03:18:29Z`, the open-PR scan found no claim on `tests/unit/test_gateway_override_analysis.py` or its destination. The issue search and recent session search found no claim. The current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`.

The gateway analysis test moved to `tests/unit/marvis/standalone/mist/resources/gateway/test_gateway_override_analysis.py`. Its focused command passed one test. Ruff passed, and Black reported one file unchanged. Full collection matched 29,434 saved node IDs after the path change, with zero missing IDs and zero added IDs. The comparison excluded the externally modified fast-mode test. The baseline still has 733 entries and 506 changed path fields. No baseline field changed in this batch.

At `2026-10-20T02:20:46Z`, the standalone metrics-gateway test had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan showed no claim on either path. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_metrics_gateway_org_selection.py` moved to its mapped path, `tests/unit/maps/standalone/interfaces/monitoring/test_metrics_gateway_org_selection.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/maps/standalone/interfaces/monitoring/test_metrics_gateway_org_selection.py` passed 3 tests. Ruff passed, Black reported one file unchanged, and both staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 152 renamed paths and found zero missing IDs and zero new IDs.

At `2026-10-20T02:22:00Z`, `tests/unit/test_operation_output_file_discovery.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_operation_output_file_discovery.py` moved to `tests/unit/prod_readiness/standalone/operations/exporting/quality/test_operation_output_file_discovery.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/standalone/operations/exporting/quality/test_operation_output_file_discovery.py` passed 25 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 153 renamed paths and found zero missing IDs and zero new IDs. Remaining old-path references occur in historical issue and specification records, which T013 says to preserve.

At `2026-10-20T02:22:58Z`, `tests/unit/test_wan_hub_group_manager.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_wan_hub_group_manager.py` moved to `tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py` passed 52 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 154 renamed paths and found zero missing IDs and zero new IDs. The baseline file also contains the old test path. The #3102 test-quality session is being asked whether it owns baseline edits.

The #3102 session confirmed that it does not claim `.github/test-quality-baseline.json`. It made no file changes and remains blocked by its shared-tool repair. It approved path-only changes for moved tests. The baseline rewrite preserved 733 entries and changed only 22 path fields across 11 entries. A session-state backup preserves the pre-edit baseline.

At `2026-10-20T02:24:52Z`, `tests/unit/test_org_data_collector.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_org_data_collector.py` moved to `tests/unit/prod_readiness/standalone/operations/wan/test_org_data_collector.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/standalone/operations/wan/test_org_data_collector.py` passed 15 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 155 renamed paths and found zero missing IDs and zero new IDs.

At `2026-10-20T02:25:34Z`, `tests/unit/test_wan_vpn_builder.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_wan_vpn_builder.py` moved to `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` passed 61 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 156 renamed paths and found zero missing IDs and zero new IDs.

The #3102 session permits #4142 to change only moved-test path fields in `.github/test-quality-baseline.json`. The VPN-builder move changed 14 path fields across seven entries and preserved all 733 entries.

At `2026-10-20T02:26:25Z`, `tests/unit/test_tqdm_wrapper.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_tqdm_wrapper.py` moved to `tests/unit/config/standalone/foundation/support/utilities/system/test_tqdm_wrapper.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/support/utilities/system/test_tqdm_wrapper.py` passed 4 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 157 renamed paths and found zero missing IDs and zero new IDs.

At `2026-10-20T02:27:22Z`, the open-PR scan found no overlap for `tests/unit/test_file_path_utils.py`, `tests/unit/test_logger_utils.py`, or `tests/unit/test_subprocess_runner.py`. Issues #4142 and #2752 and the active-session scan had no matching claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

The three tests moved to `tests/unit/config/standalone/foundation/support/utilities/system/`. Their focused command passed 48 tests. Ruff passed, Black reported three files unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 160 renamed paths and found zero missing IDs and zero new IDs. The group now has four files and stays below the five-child limit. The baseline has 733 entries and no stale path fields for moved tests.

At `2026-10-20T02:28:13Z`, the open-PR scan found no overlap for `tests/unit/test_adaptive_pacer.py`, `tests/unit/test_address_utils.py`, or `tests/unit/test_rate_limiting.py`. Issues #4142 and #2752 and the active-session scan had no matching claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

The three tests moved to `tests/unit/config/standalone/foundation/support/utilities/network/`. Their focused command passed 221 tests. Ruff passed, Black reported three files unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 163 renamed paths and found zero missing IDs and zero new IDs. The allowed baseline update changed 12 path fields across six entries and preserved all 733 entries.

At `2026-10-20T02:29:07Z`, `tests/unit/test_environment_guards.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main remained `531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede`.

`tests/unit/test_environment_guards.py` moved to `tests/unit/config/standalone/foundation/runtime/configuration/test_environment_guards.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/runtime/configuration/test_environment_guards.py` passed 7 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 164 renamed paths and found zero missing IDs and zero new IDs. The baseline had 733 entries and no stale path fields for moved tests.

At `2026-10-20T02:32:25Z`, the open-PR scan found no overlap for `tests/unit/test_config_utils.py`, `tests/unit/test_config_utils_org_id_preflight.py`, `tests/unit/test_config_utils_wave3.py`, or `tests/unit/test_dotenv_precedence.py`. Issues #4142 and #2752 and the active-session scan had no matching claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

The configuration group first failed full collection because `test_config_utils.py` shared a bare pytest module name with an existing test. The three config utility tests now use the unique package `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/`. The group has three direct children. The new package has four children, including its package marker. The focused group passed 32 tests. Ruff passed, Black reported six files unchanged, and staged and unstaged `git diff --check` passed. Full collection found 29,437 test IDs. The baseline comparison applied 168 renamed paths and found zero missing IDs and zero new IDs. The baseline path update changed four path fields and preserved all 733 entries.

The #2746 coordinator proposed `tests/unit/api/test_api_fetch_utils.py`. That exact path remains reserved by the active #2752 gateway-retry evidence claim, even though PR #4313 merged. I informed the coordinator to choose another path. The #4142 diff does not move that API test.

At `2026-10-20T02:35:11Z`, `tests/unit/test_version_compare.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_version_compare.py` moved to `tests/unit/config/standalone/foundation/runtime/release/test_version_compare.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/runtime/release/test_version_compare.py` passed 7 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 169 renamed paths and found zero missing IDs and zero new IDs. The baseline retained all 733 entries and had no stale path fields for moved tests.

The #2746 coordinator proposed `tests/unit/inventory/test_org_device_inventory_summary.py`. It is not in the current diff, but the #4142 map assigns its package to `tests/unit/marvis/mist/resources/inventory/`. I asked the coordinator to choose a test outside the mapped source and destination paths.

At `2026-10-20T02:36:30Z`, `tests/unit/test_log_rotation.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_log_rotation.py` moved to `tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py` passed 5 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 170 renamed paths and found zero missing IDs and zero new IDs. The baseline path update changed four path fields and preserved all 733 entries.

The #2746 coordinator proposed `tests/test_upgrade_portal_mist.py`. The path is outside the #4142 unit-test map and diff. The open-PR, issue, and session scans found no exact-path claim. I confirmed that it is clear for #2746, subject to the portal work review policy.

At `2026-10-20T02:38:11Z`, `tests/unit/test_release_body.py` had no open-PR path overlap and no issue #4142 or #2752 claim. The active-session scan had no matching path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_release_body.py` moved to `tests/unit/config/standalone/foundation/runtime/release/test_release_body.py`. The focused run first exposed two failures because a subprocess test still used the old repository-root depth. The test now derives the correct root from its deeper destination. The focused command passed 106 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 171 renamed paths and found zero missing IDs and zero new IDs.

At `2026-10-20T02:39:40Z`, `tests/unit/test_thread_scoped_sleep.py` had no open-PR overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_thread_scoped_sleep.py` moved to `tests/unit/config/standalone/foundation/runtime/release/test_thread_scoped_sleep.py`. The focused command `.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/unit/config/standalone/foundation/runtime/release/test_thread_scoped_sleep.py` passed 5 tests. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 172 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 150 moved-test path fields and no other fields.

At `2026-10-20T02:42:12Z`, `tests/unit/test_data_processing.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_data_processing.py` moved to `tests/unit/config/standalone/foundation/models/core/test_data_processing.py`. Its focused run passed 22 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 173 renamed paths and found zero missing IDs and zero new IDs. The baseline had no entry for this test, so it did not change.

At `2026-10-20T02:43:12Z`, `tests/unit/test_telemetry.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_telemetry.py` moved to `tests/unit/config/standalone/foundation/models/core/test_telemetry.py`. Its focused run passed 20 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 174 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 154 moved-test path fields and no other fields.

The current #2746 claim comment reserves `tests/test_upgrade_portal_mist.py` on branch `jmorrison-juniper-2746-http-4xx-tests`. The path remains outside the #4142 map and worktree diff, so the claims do not overlap.

The active #2753 claim now names `tests/unit/test_zone_analyzer.py` in its remediation matrix and test command. The #4142 map includes this source, so defer that move until the #2753 owner clears it.

The open #4317 pull request claims `tests/unit/test_routing_utils.py`. The active #4006 issue also names `tests/unit/test_routing_utils.py` and `tests/unit/test_unparseable_response_guards.py` in its scope. Defer both mapped moves until those claims clear.

The active #3959 issue comment lists `tests/unit/test_ssh_runner.py` in its claimed file set. Defer that mapped move until the claim clears.

At `2026-10-20T02:44:36Z`, `tests/unit/test_top5_risk_controls.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_top5_risk_controls.py` moved to `tests/unit/config/standalone/foundation/support/quality/risk/test_top5_risk_controls.py`. Its focused run passed 3 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 175 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It had no path entry for this test, and no baseline value changed.

At `2026-10-20T02:45:21Z`, `tests/unit/test_marvis_utils.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_marvis_utils.py` moved to `tests/unit/marvis/standalone/mist/intelligence/marvis/test_marvis_utils.py`. Its focused run passed 16 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 176 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries and had no path entry for this test.

At `2026-10-20T02:47:24Z`, `tests/unit/test_org_license_async_claim_status.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_org_license_async_claim_status.py` moved to `tests/unit/marvis/standalone/mist/resources/org/test_org_license_async_claim_status.py`. Its focused run passed 4 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 177 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries and had no path entry for this test.

At `2026-10-20T02:48:16Z`, `tests/unit/test_org_ticket_manager.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_org_ticket_manager.py` moved to `tests/unit/marvis/standalone/mist/resources/org/test_org_ticket_manager.py`. Its focused run passed 56 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 178 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 160 moved-test path fields and no other fields.

At `2026-10-20T02:49:06Z`, `tests/unit/test_e911_bssid.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_e911_bssid.py` moved to `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py`. Its focused run passed 88 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 179 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 172 moved-test path fields and no other fields.

At `2026-10-20T02:50:06Z`, `tests/unit/test_packet_capture.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_packet_capture.py` moved to `tests/unit/prod_readiness/standalone/operations/execution/capture/test_packet_capture.py`. Its focused run passed 256 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 180 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 220 moved-test path fields and no other fields.

At `2026-10-20T02:50:53Z`, `tests/unit/test_org_pcap_wait_download.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_org_pcap_wait_download.py` moved to `tests/unit/prod_readiness/standalone/operations/execution/capture/test_org_pcap_wait_download.py`. Its focused run passed 1 test before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 181 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries and had no path entry for this test.

At `2026-10-20T02:51:33Z`, `tests/unit/test_site_pcap_wait_download.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_site_pcap_wait_download.py` moved to `tests/unit/prod_readiness/standalone/operations/execution/capture/test_site_pcap_wait_download.py`. Its focused run passed 1 test before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 182 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries and had no path entry for this test.

At `2026-10-20T02:52:23Z`, `tests/unit/test_ssid_template_consolidation.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_ssid_template_consolidation.py` moved to `tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py`. Its focused run passed 241 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 183 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 286 moved-test path fields and no other fields.

At `2026-10-20T02:53:18Z`, `tests/unit/test_ssh_host_key_tofu.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_ssh_host_key_tofu.py` moved to `tests/unit/prod_readiness/standalone/operations/execution/ssh/test_ssh_host_key_tofu.py`. Its focused run passed 4 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 184 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 292 moved-test path fields and no other fields.

At `2026-10-20T02:54:33Z`, `tests/unit/test_data_browser_path_guard.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_data_browser_path_guard.py` moved to `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py`. Its focused run passed 12 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 185 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 296 moved-test path fields and no other fields.

At `2026-10-20T02:55:56Z`, `tests/unit/test_data_browser_sqlite_handles.py` had no open-PR path overlap, no matching open issue claim, and no active-session path claim. Current main was `e70e573b56284f89893657a3266d6e797821b5ea`.

`tests/unit/test_data_browser_sqlite_handles.py` moved to `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_sqlite_handles.py`. Its root lookup now uses `Path` and reaches the repository root from the nested destination. Its focused run passed 8 tests before and after the move. Ruff passed, Black reported one file unchanged, and staged and unstaged `git diff --check` passed. Full unit collection found 29,437 test IDs. The baseline comparison applied 186 renamed paths and found zero missing IDs and zero new IDs. The baseline retained 733 entries. It changed 298 moved-test path fields and no other fields.

At `2026-10-20T03:22:24Z`, the current-main revision was `e34553278301ea0715902fa905be3975b3cc8c13`. Open PR, issue, and session scans found no claim on the five inventory test sources or their destination. The issue #4142 worktree had no prior changes to those five paths.

Five inventory tests moved to `tests/unit/prod_readiness/standalone/operations/exporting/inventory/`. The first post-move run failed because three tests patched `MistHelper.APIDataFetcher`, while the source resolver loaded the canonical API fetcher module. The tests now patch `src.mist.access.api.api_data_fetcher.APIDataFetcher` directly. This preserves the intended test seam under the new pytest module name. The focused run then passed all 24 tests. Full unit collection found 29,434 test IDs. Comparing with the saved collection after applying the rename map found zero missing IDs and zero added IDs, with the externally modified fast-mode test excluded. The baseline retained 733 entries and changed only moved-path values. This batch changed 10 path fields. The full diff contains 516 changed path fields across 222 detected rename mappings. Ruff passed, Black reported five files unchanged, and `git diff --check` passed.

The #2746 candidate `tests/test_upgrade_portal_mist.py` is reserved by open PR #4324 and the active #2746 and #2747 test-quality issues. It remains outside the #4142 map and worktree diff. Do not offer it for another claim until each owner clears its reservation.

At `2026-10-20T03:24:09Z`, open PR, issue, and session scans found no claim on four quality-test sources or their destination. Issue #2746 and issue #2747 claim `tests/unit/test_issue_1709_narrow_except.py`, so that fifth mapped test remains at the root.

Four quality tests moved to `tests/unit/config/standalone/foundation/support/quality/assertions/`. Their first focused run found stale repository-root indexes in the Markdown scan and writing-guide tests. Both tests now resolve the repository root from the nested path. The current documentation path in `documentation/development-tooling-migration.md` now names the new test location. The focused command passed 35 tests. Ruff passed, Black reported four files unchanged, the STE linter scored the documentation 97/100, and `git diff --check` passed. Full unit collection found 29,434 test IDs. After mapping 226 renames, the comparison found zero missing IDs and zero added IDs, with the externally modified fast-mode test excluded. The baseline retained 733 entries, changed no fields for this batch, and differs from `HEAD` only in 516 moved-path fields.

At `2026-10-20T03:27:00Z`, the current-main revision remained `e34553278301ea0715902fa905be3975b3cc8c13`. Open PR, issue, and session scans found no claim on `tests/unit/test_device_utility_commands.py` or its mapped device-test destination. The source test passed 210 tests before the move. It moved to `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands.py`. The new path retains the E402 Ruff override. The baseline changed 20 path fields and kept all 733 entries. The moved test passed 210 tests, Ruff passed, Black reported one file unchanged, and `git diff --check` passed.

At `2026-10-20T03:26:24Z`, open PR, issue, and session scans found no claim on the three scope-test sources or their destination. They moved to `tests/unit/config/standalone/foundation/support/quality/scope/`. The first focused run found stale root indexes in `test_config_package_tracked.py`. Updating its repository root to the new path depth fixed all failures. The focused command passed seven tests and skipped one. Ruff passed, Black reported three files unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 230 renames, comparison found zero missing IDs and zero added IDs. The baseline retained 733 entries and changed only 536 path fields across all moved tests.

At `2026-10-20T03:27:00Z`, open PR, issue, and session scans found no claim on `tests/unit/test_template_config.py`, `tests/unit/test_wan2_variable.py`, or their mapped gateway-test destination. Both modules passed 224 tests before the move. They moved to `tests/unit/marvis/standalone/mist/resources/gateway/`. The existing per-file Ruff overrides now name the destination paths. The group passed 225 tests, including the already-moved gateway test. Ruff passed, Black reported three files unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 232 renames, comparison found zero missing IDs and zero added IDs. The baseline retained 733 entries and had no path fields for these tests.

At `2026-10-20T03:28:43Z`, current main remained `e34553278301ea0715902fa905be3975b3cc8c13`. Open PR, issue, and session scans found no claim on `tests/unit/test_device_events_52w_exporter_extended.py` or its mapped destination. The source passed 41 tests before the move. It moved to `tests/unit/config/standalone/foundation/support/quality/cross_domain/test_device_events_52w_exporter_extended.py`. The focused run passed 41 tests, Ruff passed, Black reported one file unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 233 renames, comparison found zero missing IDs and zero added IDs. The baseline retained 733 entries and changed no fields for this test.

At `2026-10-20T03:29:46Z`, current main remained `e34553278301ea0715902fa905be3975b3cc8c13`. Open PR, issue, and session scans found no claim on three import-quality test sources or their destinations. The baseline had one finding for `test_no_mistapi_stub_leak.py`. All three modules moved to `tests/unit/config/standalone/foundation/support/quality/imports/`, and the baseline changed only the two path fields for that finding. Moving the files exposed a failing legacy-facade guard because its exception list still named two moved device stats tests. The guard now uses their destination paths and its own new path. It also resolves the repository root from the nested path. The focused command passed all four tests, Ruff passed, Black reported three files unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 236 renames, comparison found zero missing IDs and zero added IDs. The baseline retained all 733 entries and changed only 538 moved-path fields.

At `2026-10-20T03:30:49Z`, open PR, issue, and session scans found no claim on `tests/unit/test_exports.py`, `tests/unit/test_pk_strategies.py`, `tests/unit/test_wifi_clients_exporter.py`, or their destinations. The issue searches found claims on the other two tests in the reports map, so those remain unchanged. The three cleared tests passed 42 tests before and after moving to `tests/unit/prod_readiness/standalone/operations/exporting/reports/`. The legacy-facade guard now names the moved `test_exports.py` exception. Ruff passed for the moved group and updated guard, Black reported four files unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 239 renames, comparison found zero missing IDs and zero added IDs. The baseline retained 733 entries and changed no fields for these tests.

At `2026-10-20T03:32:13Z`, open PR, issue, and session scans found no claim on `tests/unit/test_web_portal_bind_address.py` or its mapped destination. It passed eight tests before and after moving to `tests/unit/maps/standalone/interfaces/portals/`. Ruff passed, Black reported one file unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. The baseline retained 733 entries and had no path fields for this test.

At `2026-10-20T03:32:13Z`, open PR, issue, and session scans found no claim on `tests/unit/test_site_auto_upgrade.py` or its mapped cross-domain destination. The source passed 192 tests before the move. It moved to `tests/unit/config/standalone/foundation/support/quality/cross_domain/`, and its E402 Ruff override now names the destination. The group passed 233 tests. Ruff passed, Black reported two files unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 241 renames, comparison found zero missing IDs and zero added IDs. The baseline retained 733 entries and changed only 564 moved-path fields. This move added 26 path fields.

At `2026-10-20T03:33:03Z`, open PR, issue, and session scans found no claim on `tests/unit/test_issue_2971_status_final.py`, `tests/unit/test_issue_2971_status_slice5.py`, or their interface UI destinations. The source tests passed 15 tests before and after moving to `tests/unit/maps/standalone/interfaces/ui/`. Ruff passed, Black reported two files unchanged, and `git diff --check` passed. Full unit collection remained 29,434 IDs after excluding the externally modified fast-mode test. After mapping 243 renames, comparison found zero missing IDs and zero added IDs. The baseline retained 733 entries and changed only 576 moved-path fields. This move changed 12 path fields.

At `2026-10-20T03:49:58Z`, the current `main` revision was `0eb5043d1da4445954c7565030e9989b9957b581`. Open PR, issue, and session scans found no claim on `tests/unit/test_issue_2971_status_slice3.py`, `tests/unit/test_favicon.py`, or their mapped destinations. The first test passed eight tests before and after its move to `tests/unit/config/standalone/foundation/support/quality/cross_domain/`. The favicon test passed two tests before its move to `tests/unit/maps/standalone/interfaces/portals/`. The portal group passed 10 tests after both moves.

The MIB generator package had no open PR, issue, or session claim. It moved to `tests/unit/prod_readiness/operations/hardware/mib_generator/`. The first moved test run failed eight tests because two tests used the old repository-root index. Both tests now use `parents[6]`. The focused command passed 54 tests with one existing unknown-mark warning. Ruff passed, and Black reported five files unchanged.

The troubleshooting package had no open PR, issue, or session claim. It moved to `tests/unit/marvis/mist/intelligence/troubleshooting/`. Its first moved test run failed because one test used the old repository-root index. That test now uses `parents[7]`. The moved package and its updated test consumer passed 251 tests with two collection warnings. Ruff passed, and Black reported 24 files unchanged. The existing handoff record keeps its historical source path.

The firmware-policy package had no open PR, issue, or session claim. It moved to `tests/unit/prod_readiness/operations/execution/firmware/policy/`. Its helper imports changed in 23 Python files. An AST comparison found no change to module-level names. The focused command passed 438 tests across the unit, integration, contract, and web tests. Ruff and Black passed after formatting two long imports. The baseline retained 733 entries and had no firmware-policy path fields.

The baseline backup `4142-baseline-before-troubleshooting-path-update.json` confirms that the troubleshooting batch changed only 54 `file_path` and `related_source` values. The entry count remained 733. The earlier user approval permits path-only changes and forbids regeneration.

The current unit collection has 29,437 test IDs. After mapping all 288 detected test-file renames, comparison with the saved collection found zero missing IDs and zero added IDs. The comparison excluded four IDs from the externally modified `tests/unit/test_fast_mode_flag.py`.

The root test `tests/test_upgrade_portal_mist.py` remains reserved by PR #4324 and active issues #2746 and #2747. It is outside the #4142 move map. Do not claim or move this path until its owners clear every reservation.

At `2026-10-20T03:55:11Z`, `main` was `0eb5043d1da4445954c7565030e9989b9957b581`. PR #4324 remains open and claims only `tests/test_upgrade_portal_mist.py`. Issues #2746 and #2747 remain open with `in-progress` labels. The #2746 campaign lists this exact path, and the #2747 campaign reserves the SSH test path below. The portal test remains outside the #4142 map and is not clear for a new claim.

The standalone test `tests/unit/test_ssh_runner.py` had no exact-path PR, issue, or session claim. PR #4312 merged and owns only `tests/unit/ssh/test_cli_shell_manager.py`. The test moved to `tests/unit/prod_readiness/standalone/operations/execution/ssh/`. Its group passed 174 tests. The changed SSH configuration test passed 30 tests. Ruff and Black passed. The package `tests/unit/ssh/` remains reserved because the active #2746 and #2747 campaigns include `tests/unit/ssh/test_cli_shell_manager.py`; do not move that package or its claimed file.

## Current Ownership Snapshot

At `2026-10-20T04:40:03Z`, fetched `origin/main` was `eb1aa85187d3d683aa79ab4a9192c3fc75193a5e`. Its tracked `tests/unit/` root has 158 entries: 48 directories, 108 test modules, and two support files. The root test map covers all 48 directories and all 108 test modules.

The command `python -m pytest -p no:cacheprovider tests/unit/ --collect-only -q` collected 29,536 tests in 16.91 seconds. It exited with code 0 and reported one `PytestUnknownMarkWarning` for `pytest.mark.slow` in `tests/unit/mib_generator/test_performance.py`. The output is preserved in the session artifact `4142-origin-main-eb1aa-collection.txt`. This records collection only. The full unit suite was not run on this revision.

The open PR scan found claims from PRs #4208, #4226, #4287, #4316, #4317, and #4323. PR #4208 remains draft and owns its workflow selectors, `tests/unit/wan_performance/`, and `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. PR #4226 owns `tests/unit/gateway/overrides/test_cisco_config_converter.py`. PR #4287 owns `tests/unit/dataclasses/test_service_measurement.py`. PR #4316 owns `tests/unit/upgrade_portal/test_phase2_service_wiring.py`, `tests/unit/upgrade_portal/test_settle_gate_service.py`, and `tests/unit/upgrade_portal/test_upgrade_driver.py`. PR #4317 owns `tests/unit/device/test_arp_command_manager.py`, `tests/unit/test_routing_utils.py`, and `tests/unit/websocket/test_manager.py`. PR #4323 owns `tests/unit/reports/psk_hygiene/test_operation.py`. PR #4324 remains open and owns only `tests/test_upgrade_portal_mist.py`, outside this feature map. PRs #4308, #4310, #4311, #4312, #4313, #4314, #4315, and #4289 merged.

Issue #4142 remains open with the `in-progress` label. Issues #2746 and #2747 remain open and claim `tests/unit/ssh/test_cli_shell_manager.py`. Issue #2746 also claims `tests/test_upgrade_portal_mist.py`. Issue #2752 retains API, export, upgrade-portal, and related record claims. Its owner requires human review for portal work. Other #2746 path mentions remain campaign candidates unless the owner makes an exact claim.

The #2746 session `jmorrison-juniper-2746-http-4xx-tests` is busy and has open PR #4324 for `tests/test_upgrade_portal_mist.py`. The #2746 SSH session remains active after PR #4312 merged. Recent local and cloud session-file queries returned no rows for `tests/unit/`; these queries do not replace live owner confirmation. The portal test is outside the #4142 move map but is not available for another claim or edit. Refresh PR, issue, session, and workflow claims immediately before each file batch.

At `2026-10-20T04:48:21Z`, the open PR, issue, and session checks found no claim on `tests/unit/capture/` or its mapped destination. The eight capture modules moved into the four groups in `design/standalone-test-map.md`. Three forwarding imports and one sibling-file reference now use the new paths. The focused command passed 8,124 tests. The move-module guard passed 15 tests. Ruff passed after a long docstring reference was shortened. Black left all 11 checked files unchanged.

The pre-move and post-move unit collections each contained 29,437 test IDs. After mapping the eight moved module paths, comparison found zero missing and zero added IDs. The test-quality baseline retained 733 entries. It changed only 10 `file_path` and `related_source` fields across five findings and three source files. A structured comparison confirmed that every other baseline field stayed unchanged. The tracked `tests/unit/` root decreased from 39 to 38 entries, with no new root child. Both staged and unstaged `git diff --check` passed.

This base collection is separate from the feature-branch comparison below. Keep the feature-branch baseline, moved-path comparisons, and test-quality baseline evidence distinct.

The exact-path PR scan, active issue search, and recent session-file query found no claim on `tests/unit/test_retention.py` or its destination. The module moved to `tests/unit/config/standalone/foundation/persistence/database/`. Its pre-move test passed 14 tests. The full destination group passed 74 tests. Ruff passed, and Black reported one unchanged file. Unit collection remained at 29,437 IDs with no missing or added tests. The baseline retained 733 entries. The path comparison confirmed that each baseline record changed only in `file_path` or `related_source`. It also found four stale path fields for the earlier favicon move, which now name the destination.

At `2026-10-20T05:00:57Z`, GitHub reported `origin/main` as `eb1aa85187d3d683aa79ab4a9192c3fc75193a5e`. The live open-PR, issue, and session checks found no claim on `tests/unit/test_msp_privilege_detection.py` or its mapped destination. Issues #2746 and #2747 had no exact-path claim. Issue #2753 still claims `tests/unit/test_zone_analyzer.py`. The baseline records a missing 5xx finding for `tests/unit/test_issue_1709_narrow_except.py`. Issue #2861 includes `tests/unit/test_credential_preflight.py` in a validation command. Defer those paths.

`tests/unit/test_msp_privilege_detection.py` moved to `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py`. The destination group now has four test files. Its one remaining mapped file stays reserved. The group remains within the five-child limit.

The focused source and destination runs each passed 35 tests. Full unit collection found 29,437 tests before and after the move. Mapping the 35 module node IDs found zero missing IDs and zero added IDs. Ruff passed. Black reported one file unchanged. `git diff --check` passed. The test-quality baseline retains 733 entries and remains byte-identical to its pre-move snapshot.

At `2026-10-20T05:10:07Z`, GitHub and fetched `origin/main` resolved to `06148e617ded13399fe9ecf9a35cfb2ffcaeb226`. The open-PR scan checked 13 pull requests and found no claim on either firmware test or its destination. The recent session-file query found zero rows for these paths. Issue #3246 is closed. Issues #2746 and #2747 name `tests/unit/firmware/test_running_version.py`, which remains reserved. Neither issue names the two moved tests.

`tests/unit/firmware/test_org_advanced_bodies.py` and `tests/unit/firmware/test_org_cancel_sort.py` moved to `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/`. The destination group has two direct children and remains within the five-child limit. The combined focused test command passed 55 tests before and after the move. The full unit collection found 29,437 tests after the move. Mapping the 55 module node IDs found zero missing IDs and zero added IDs. The 733-entry test-quality baseline remains byte-identical to its pre-move snapshot. `git diff --check` passed.

At `2026-10-20T05:15:41Z`, the exact-path PR scan found no open PR claim on `tests/unit/juniper_docs/` or its destination. The recent session-file query found zero rows. Issue #3158 is open and claims the package path. Issue #2977 is open and lists canonical test paths in its branch. Defer the Juniper Docs package until both issue owners clear their claims.

At `2026-10-20T05:18:01Z`, the open-PR scan checked 14 pull requests and found no claim on four remaining standalone tests. The recent session-file query found zero rows for those paths. Issue #2861 claims `test_standalone.py`. Issue #2746 claims `test_prompt_network_device_utils.py` and `test_org_inventory_exporter_helpers.py`. Issue #4006 claims `test_unparseable_response_guards.py`. Issue #2747 also claims `test_org_inventory_exporter_helpers.py`. Keep these files unchanged until their owners clear the claims.

At `2026-10-20T05:22:45Z`, the open-PR scan checked 14 pull requests. PR #4317 claims `tests/unit/device/test_arp_command_manager.py`. Issue #2753 claims `test_ap_profile_migration_manager.py`. Issues #2746 and #2747 claim `test_device_utils.py`. The recent session-file query found zero rows for the package. No PR, issue, or session claim named `test_device_handler_narrowing.py`.

`tests/unit/device/test_device_handler_narrowing.py` moved to `tests/unit/marvis/mist/resources/device/test_device_handler_narrowing.py`. The destination contains two direct children, including its package marker. The focused test passed all 10 tests before and after the move. Full unit collection found 29,437 tests before and after the move. Mapping the moved module path found zero missing or added node IDs. The 733-entry test-quality baseline remains byte-identical to its pre-move snapshot. Ruff, Black, and `git diff --check` passed.

At `2026-10-20T05:24:37Z`, the open-PR scan checked 14 pull requests. PR #4226 claims `tests/unit/gateway/overrides/test_cisco_config_converter.py`. Issues #2746 and #2747 claim the WAN probe and export tests. The recent session-file query found zero rows for `tests/unit/gateway/`. No PR, issue, or session claim named the two WAN override walker tests.

The two WAN override walker tests moved to `tests/unit/marvis/mist/resources/gateway/wan_overrides/`. The new group has three direct children, including its package marker. The focused command passed 16 tests before and after the move. Full unit collection found 29,437 tests before and after the move. Mapping the moved module paths found zero missing or added node IDs. The 733-entry test-quality baseline changed only four path fields for two findings. Ruff, Black, and `git diff --check` passed.

At `2026-10-20T05:25:48Z`, the open-PR scan checked 14 pull requests and found no claim on the gateway exporter tests or their destinations. The recent session-file query found zero rows. Issue searches found no open claim on either test.

`test_gateway_ha_exporter.py` and `test_gateway_stats_exporter.py` moved to `tests/unit/marvis/mist/resources/gateway/exporters/`. The new group has three direct children, including its package marker. The gateway root has four direct children, including its package marker. The focused command passed 51 tests before and after the move. Full unit collection found 29,437 tests before and after the move. Mapping the moved module paths found zero missing or added node IDs. The 733-entry test-quality baseline changed only four path fields for two findings. Ruff, Black, and `git diff --check` passed.

At `2026-10-20T05:27:08Z`, the open-PR scan found PR #4226 as the only claim under the gateway source package. It owns `tests/unit/gateway/overrides/test_cisco_config_converter.py`. Issue searches found no claim on the three override tests or the SSR registration test. The recent session-file query found zero rows for those source and destination paths.

The three unclaimed gateway override tests moved to `tests/unit/marvis/mist/resources/gateway/overrides/`. The SSR registration test moved to `tests/unit/marvis/mist/resources/gateway/ssr_registration/`. The focused command passed 54 tests before and after the move. Full unit collection found 29,437 tests before and after the move. Mapping the four moved module paths found zero missing or added node IDs. The 733-entry test-quality baseline remains byte-identical to its pre-move snapshot. Ruff, Black, and `git diff --check` passed. The gateway root and each topic group contain five children or fewer.

At `2026-10-20T05:29:10Z`, the open-PR scan checked 14 pull requests and found no claim on `tests/unit/reports/test_issue_4053_manufacturer_input.py` or its destination. Issues #2746 and #2747 had no exact-path mention in their bodies or comments. The recent session-file query found zero rows for both paths.

`test_issue_4053_manufacturer_input.py` moved to `tests/unit/marvis/mist/intelligence/reports/manufacturer_input/`. The source package now has 17 direct children. The destination root and topic group each have two children, including package markers.

The focused test passed seven tests before and after the move. Mapping the seven source node IDs to the destination found zero missing or added IDs. Full unit collection found 29,437 tests before and after the move. The 733-entry test-quality baseline remains byte-identical to its pre-move snapshot.

## Continued implementation on 2026-10-20

Fetched main resolved to `729a75613f971bddbee7f5e29e321b87a4efc719`.
The preserved branch remains at `ef92a47522a1b8ba8f6eadd3379d96d595fad17c`, with 35 newer main commits.
Main has 159 tracked direct unit-root children.
The preserved worktree has 38 unit-root children.
No preserved changed path intersects the current nine open pull request file lists.
PR #4350 owns three remaining source paths listed in the plan.
PR #4208 still owns its workflow selectors and test paths.
Keep those paths and the other active claims deferred.
No rebase or pull request action occurred.

### Prerequisite runtime

The required PowerShell command could not run because `pwsh` was unavailable.
An official PowerShell 7.6.7 runtime now resides under ignored `.venv/tools/pwsh/`.
Its source is `https://github.com/PowerShell/PowerShell/releases/download/v7.6.7/powershell-7.6.7-osx-arm64.tar.gz`.
The archive matches the official release `hashes.sha256` entry:
`50dde99bb066adacbb9a748182d09eb9beff25119dc3b12e85c84b6b6b1c5da9`.
No dependency manifest changed.

The first prerequisite command resolved the existing feature pointer to #4258.
An explicit `SPECIFY_FEATURE_DIRECTORY` environment value selected this #4142 record without changing `.specify/feature.json`.
Both implementation and analysis prerequisite commands then passed.
They returned this feature directory, `design/research.md`, `design/quickstart.md`, and `tasks.md`.
The requirement checklist has 16 checked items and zero unchecked items.
The extension file parsed successfully.
Implementation and analysis hooks offer only optional commits.
Those optional commits were not executed.

### Juniper RMA bounded groups

The initial destination retained four oversized groups.
The updated map splits API tests into service and transport groups, row tests into a row group, and workflow tests into menu and lookup groups.
Saved JSON replies now reside under `fixtures/payloads/`.
The fixture reader uses that root.
All existing helper imports remain unchanged.
All 13 directories in the RMA tree now contain five children or fewer.

The live pull request scan found no RMA path claim.
The recent session-file query found zero matching paths.
Issues #2746 and #2747 had no RMA path mentions.
Issue #4168 explicitly limits its RMA scope to production source packages.
The specification analysis covered all 12 requirements with 27 tasks and found no blocking artifact inconsistency.

The combined RMA, browser, move-guidance, and portal-coverage command passed 233 tests before and after the split.
It skipped 16 tests under the existing live-mode and optional-runtime conditions.
Full unit collection contained 29,437 IDs before and after.
The comparison applied the 12 exact module moves and found zero missing or added IDs.
The 733-entry test-quality baseline remains byte-identical to the pre-split copy.
Ruff passed. Black left 26 files unchanged.
Staged and unstaged whitespace checks passed.
The active reference scan found no old RMA test or JSON fixture path.
Task T027 is complete. The overall move tasks remain incomplete while owned paths remain deferred.

### Firmware aggregate cancellation tests

Main remained at `729a75613f971bddbee7f5e29e321b87a4efc719`.
The refreshed PR scan found no ownership match for the four aggregate-cancellation tests.
Exact open-issue searches found no claim.
The recent session-file query returned no matching paths.
Open upgrade issues name `test_aggregate_upgrade_service.py`, which remains at its source path.

The four cancellation tests moved to the mapped `upgraders/aggregations/` group.
The group has four direct children.
The focused source command passed 46 tests.
The destination tests and the move-guidance and portal-coverage guards passed 78 tests, with one existing optional-runtime skip.
Full unit collection remained at 29,437 IDs.
The exact four-path comparison found zero missing or added IDs.
The 733-entry baseline remains byte-identical to its pre-move copy.
Ruff passed. Black left four files unchanged.
Staged and unstaged whitespace checks passed.
Task T028 is complete.

### Firmware manager tests

The exact-path PR, issue, and recent session checks cleared the proxy and SSR manager tests.
The other manager candidates remain deferred because issues #2746, #2747, or #2752 name them.
The proxy test moved to `upgraders/manager/site/`.
The SSR test moved to `upgraders/manager/platform/`.
Each new topic group contains one file.
The manager root contains two groups.

The source command passed 199 tests.
The destination tests and applicable guards passed 231 tests, with one existing optional-runtime skip.
Full unit collection remained at 29,437 IDs.
The exact two-path comparison found zero missing or added IDs.
The baseline retained 733 entries and changed only eight path fields for four SSR findings.
Every non-path field and entry order remained unchanged.
Ruff passed. Black left two files unchanged.
Staged and unstaged whitespace checks passed.
Task T029 is complete.

### Device health reports

The refreshed PR and exact issue searches found no claim on the three device health report tests.
The recent session-file query returned zero matching paths.
The tests moved to the recorded `reports/device_health/` group.
The group has three files.
The source command passed 58 tests.
The destination tests and applicable guards passed 90 tests, with one existing optional-runtime skip.
Full unit collection remained at 29,437 IDs.
The exact three-path comparison found zero missing or added IDs.
The baseline retained 733 entries and changed only four path fields for two findings.
Every non-path field and entry order remained unchanged.
Ruff passed. Black left three files unchanged.
Staged and unstaged whitespace checks passed.
Task T030 is complete.

### Assurance report packages

Live PR, issue, campaign, and recent session-file checks found no ownership conflict for the four mapped assurance packages.
The source tests passed 96 tests.
The AP behavior tests moved into a three-file cases group.
The AP support-file test retains its package-root location and now resolves the repository through its new depth.
The other packages moved without content changes.

The destination tests and applicable guards passed 128 tests, with one existing optional-runtime skip.
Full unit collection remained at 29,437 IDs, with zero missing or added IDs after the exact mapping.
The baseline remained byte-identical with 733 entries.
Every assurance directory has five children or fewer.
Ruff passed. Black left 19 files unchanged.
Staged and unstaged whitespace checks passed.
Task T031 is complete.

### Certificate, subscription, rogue-evidence, and client-census reports

The exact PR, issue, campaign, and recent session checks cleared the four audit packages.
The packages moved into the mapped credential and posture groups.
Certificate helper imports now use the destination.
Certificate and census repository-root checks use the new package depth.
The source command passed 64 tests.
The destination tests and applicable guards passed 96 tests, with one existing optional-runtime skip.
Full unit collection remained at 29,437 IDs, with zero missing or added IDs after the exact mapping.
The baseline remained byte-identical with 733 entries.
Ruff passed. Black left 16 files unchanged.
Staged and unstaged whitespace checks passed.
Task T032 is complete.

### Remaining unowned report audits

Live PR, exact issue, campaign, and recent session checks cleared the admin-token, organization-posture, and site-variable packages.
Their source tests passed 69 tests.
Each package now uses the bounded groups in the map.
The first lint check found eight long helper imports.
Shorter helper module names resolved those errors without suppressions.
The site-variable helper retains its `*_test.py` suffix and its collected test.
Test helper module paths changed. No production module or logger name changed.

The destination audit tests and applicable guards passed 165 tests, with one existing optional-runtime skip.
Full unit collection remained at 29,437 IDs.
The exact mapping, including the fixture test rename, found zero missing or added IDs.
The baseline remained byte-identical with 733 entries.
Every moved report directory now has five children or fewer.
Ruff passed. Black left 42 files unchanged.
Staged and unstaged whitespace checks passed.
Task T033 is complete.

The report source root now has three direct children: PSK hygiene and the two wired-client report tests.
Those paths retain their previous ownership holds until their owners release them.
The destination report root has five direct children.
No direct unit-root child was added.
