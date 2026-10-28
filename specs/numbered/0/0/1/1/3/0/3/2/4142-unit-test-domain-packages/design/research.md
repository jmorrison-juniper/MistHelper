# Research: Unit Test Domain Packages

**Date**: 2026-10-20

## Bounded troubleshooting split, 2026-10-26

Task T042 applies the existing troubleshooting map without a grouping change.
The coordinator confirmed no active session claim for either package path, its standalone consumer, or the baseline.
The exact-path scan checked 42 other open pull requests and 316 file records, including previous filenames.
No source, destination, consumer, or baseline path overlapped another pull request.
The required explicit-feature prerequisite check passed again.
The fully checked requirements checklist remains unchanged.

The split moves 22 Python files into the mapped core, credential, SMS, synthetic, and RF diagnostic groups.
It updates the existing standalone test consumer import and one repository-root depth for the RF manifest test.
Each resulting directory has five children or fewer.
No production behavior, historical record, workflow, or dependency manifest changes.

The before-move command passed 251 tests with two existing collection warnings:

```bash
.venv/bin/python -m pytest -q tests/unit/marvis/mist/intelligence/troubleshooting tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py
```

The after-move command passed 311 tests and skipped one optional-runtime check, with the same two collection warnings:

```bash
.venv/bin/python -m pytest -q tests/unit/marvis/mist/intelligence/troubleshooting tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py tests/guardrails/test_move_module_guidance.py tests/guardrails/test_portal_operation_coverage.py
```

The before and after collection-finish hooks each saved 29,603 complete unit-test node IDs.
Mapping the 22 exact moves gives zero missing IDs and zero added IDs.
An AST comparison checked all 22 moved modules and found no lost module-level function or class declaration.
The baseline keeps all 733 entries in order and changes only 54 verified path fields.
The initial estimate of 60 fields was incorrect.
The pre-write assertion rejected that estimate before changing the file.
The corrected check verified all 54 target files and every non-path field before writing.
The ignored backup is `.venv/tmp/4142-before-troubleshooting-baseline.json`.

Ruff passed and Black reported 24 files unchanged:

```bash
.venv/bin/python -m ruff check tests/unit/marvis/mist/intelligence/troubleshooting tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py
.venv/bin/python -m black --check tests/unit/marvis/mist/intelligence/troubleshooting tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py
```

The remaining root candidates require ownership clearance.
Open issue #2746 names `tests/unit/test_issue_2971_census_repairs.py`.
Open issues #4133 and #4126 name `tests/unit/test_menu_entry_metadata.py`.
The utility package cannot move while the reserved workflow selects `tests/unit/utils/test_zscaler_catalogue.py`.
Keep these files unchanged and keep the final acceptance tasks open.
Do not rebase, push, edit the draft, or enable auto-merge while whole-branch ownership conflicts remain.

### Cleared fast-mode root move

The coordinator found no active session or pull request reservation for `tests/unit/test_fast_mode_flag.py`.
The prior external-edit hold no longer applies to the clean committed file.
Task T043 moves it without a content change to `tests/unit/config/standalone/foundation/runtime/startup/test_fast_mode_flag.py`.
No active consumer, workflow selector, baseline entry, lint override, or historical Markdown link requires another edit.
The destination contains four tracked files, and the unit root decreases from 40 tracked direct children to 39.
The existing source-aligned map remains unchanged.

The before-move command passed all four tests:

```bash
.venv/bin/python -m pytest -q tests/unit/test_fast_mode_flag.py
```

The combined after-move command passed 315 tests, skipped one optional-runtime check, and retained the two existing collection warnings:

```bash
.venv/bin/python -m pytest -q tests/unit/config/standalone/foundation/runtime/startup/test_fast_mode_flag.py tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py tests/unit/marvis/mist/intelligence/troubleshooting tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py tests/guardrails/test_move_module_guidance.py tests/guardrails/test_portal_operation_coverage.py
```

The combined 23-move node-ID comparison again contains 29,603 tests with zero missing IDs and zero added IDs.
Ruff passed for the troubleshooting and startup packages.
Black reported 27 files unchanged.
Compile and both whitespace checks passed.

The remaining oversized groups have unresolved issue owners.
Issues #2746, #2747, and #2753 name address-audit paths.
Issue #2746 names rogue-DHCP paths.
Open issue #4008 names `tests/unit/marvis/actions/`.
Issue #2752 is closed, but the other issue owners and PR #4208 retain their independent holds.
Keep these groups deferred rather than infer a handover.

### Committed quality evidence

The implementation commit is `177559d8d6c2d94110136b90be6561115e5ee227`.
The preserved earlier commit remains `01a97580539fb9dbb21ec2ed51d807b45a348ed0`.
The worktree was clean before each analyzer command.
The required fetch resolved `origin/main` to `8e44db09dddfdc15ff73d7247b6501b0943351ad`.
This updated comparison reference did not rebase or change the branch.

The required input preflight passed one test and validated all four inputs:

```bash
.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Both commands passed with 1,198 files checked, 669 findings checked, zero parse errors, and zero new findings:

```bash
.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

The three revised feature documents passed STE with scores of 95, 97, and 93.
The optional implementation commit hooks require no further action.
No rebase, push, pull request edit, auto-merge action, merge, or deployment occurred.
The published draft still points to `63faa487ad441c27b348911aaf34c04ae1ad3244`.
The final issue acceptance remains incomplete because reserved paths cannot move.

## Independent bounded splits, 2026-10-26

The coordinator authorized continued independent work while the partial pull request remains draft.
The supported prerequisite command passed:

```bash
SPECIFY_FEATURE_DIRECTORY="$PWD/specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages" .venv/tools/pwsh/pwsh -NoLogo -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks -RequireSpec
```

The requirements checklist has 16 checked items and zero unchecked items.
The optional before-implementation commit hook needed no action because the worktree was clean.
An initial prerequisite invocation used unsupported `-FeatureDir` and failed before execution.
The supported environment override above resolved that invocation error without a file change.

Tasks T039 through T041 apply the existing exact map to three unclaimed packages.
The coordinator confirmed no matching session reservation.
The pull request scan checked 42 other open pull requests and 316 file records, including previous filenames.
Both current and original package paths were clear.
The 21 moves and related helper and document changes have zero intersection with that inventory.

The MIB split retains its marker and introduces CLI, generator, and performance groups.
Its fixture remains beside the generator test.
The firmware policy split retains shared fixtures and helpers, and introduces changes, bundles, and selection groups.
The container split retains its marker, output-defaults group, and session-database group.
Its new build-support group holds shared helpers and build tests, while the runtime group holds script tests.
Every directory in these three packages has five children or fewer.
No new direct child enters `tests/unit/`, which still has 40 tracked direct children.

The before-move MIB command passed 54 tests:

```bash
.venv/bin/python -m pytest -q tests/unit/prod_readiness/operations/hardware/mib_generator
```

The after-move command passed 114 tests and skipped one optional-runtime check:

```bash
.venv/bin/python -m pytest -q tests/unit/prod_readiness/operations/hardware/mib_generator tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py tests/guardrails/test_move_module_guidance.py tests/guardrails/test_portal_operation_coverage.py
```

The before-move policy and container command passed 462 tests:

```bash
.venv/bin/python -m pytest -q tests/unit/prod_readiness/operations/execution/firmware/policy tests/unit/prod_readiness/operations/exporting/container
```

The after-move command passed 522 tests and skipped one optional-runtime check:

```bash
.venv/bin/python -m pytest -q tests/unit/prod_readiness/operations/execution/firmware/policy tests/unit/prod_readiness/operations/exporting/container tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py tests/guardrails/test_move_module_guidance.py tests/guardrails/test_portal_operation_coverage.py
```

Collection used `pytest.main(['--collect-only', '-q', 'tests/unit'], plugins=[Recorder()])`.
The collection-finish hook saved each complete node ID, including parameters, before and after each batch.
Both full collections contain 29,603 node IDs.
Mapping the exact 21 file moves gives zero missing IDs and zero added IDs.
The baseline remains byte-identical to the published head and retains all 733 ordered entries.
None of these three packages has a baseline path field.
No historical specification, dependency manifest, workflow, production source, or held test changed in these batches.

Ruff initially reported one long helper import after the container move.
Its import formatter corrected that line.
The final commands passed, and Black reported 36 files unchanged:

```bash
.venv/bin/python -m ruff check tests/unit/prod_readiness/operations/hardware/mib_generator tests/unit/prod_readiness/operations/execution/firmware/policy tests/unit/prod_readiness/operations/exporting/container
.venv/bin/python -m black --check tests/unit/prod_readiness/operations/hardware/mib_generator tests/unit/prod_readiness/operations/execution/firmware/policy tests/unit/prod_readiness/operations/exporting/container
```

The local implementation commit is `4772a8aeca431bc74b4fb285b075fb1256f43295`.
The worktree was clean before both committed-input quality checks.
The fetch and commit-resolution commands confirmed main `ef0e7e5991950aec9b8f094e32e47fc3f68b4d2f`.
Each analyzer command checked 1,198 files and 669 findings, reported zero parse errors, and passed with zero new findings:

```bash
.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

The required input preflight passed one test and validated all four inputs:

```bash
.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

`python -m py_compile MistHelper.py` passed without output.
Both staged and unstaged `git diff --check` commands passed.
An AST comparison checked all 20 moved Python modules and found no lost module-level function or class declaration.
The four changed documents passed STE with scores from 93 through 97.
The optional after-implementation commit hook has no mandatory action.
No CI run, rebase, push, pull request edit, deployment, or merge occurred for these local batches.

The whole-branch ownership scan found a new conflict at rename source `tests/unit/test_wan_hub_group_manager.py`, owned by PR #4415.
Existing `pyproject.toml` changes also overlap PRs #4471, #4438, and #4436.
The coordinator received these exact blockers.
Keep the existing draft and auto-merge state unchanged.
Do not publish or rebase this scope until the ownership conflicts clear.
The older green CI does not validate current main or these local changes.

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

## Approved-base rebase after PR #4353

The coordinator approved base `efd178c3f76e580afc0b5511734498b61f3a0090`.
Preservation commit `e7e9cf4644f723aea000e04555b1562534dcb0e5` retained the complete work before rebase.
The rebase produced commit `20b200389124433e2737eb3b666805a7c738862e`, whose parent is the approved base.

Git stopped because main added `org_security_posture/test_operation_outcome.py` while this branch split its directory.
The test now occupies the fifth position in the mapped `contracts/` group.
Its fixture import uses `org_security_posture.fixtures.representative`.
The focused posture run verified this import and main's typed-outcome behavior.
No textual conflict required a large resolution.

The earlier ownership check missed old rename paths.
The corrected check reads `git diff --name-only --no-renames` and both API rename endpoints.
It found the earlier Arango move intersected PR #4350.
The entire five-file Arango package now remains at its original source.
Every file matches the approved main byte for byte.
The contract and discovery callers also retain main's exact imports.
This move remains deferred in the map and task T005.

The first full collection found one missed discovery caller of the returned Arango helper.
Restoring that caller's original import resolved the collection error.
The first style run reported that same import. The final style run passed.

The live scan checked all eight open pull requests: #4350, #4327, #4322, #4318, #4317, #4316, #4226, and #4208.
Their complete file lists included previous filenames.
The corrected branch scan found no shared source or destination path.

### Post-rebase evidence

The approved-main snapshot came from `git archive` in ignored `.venv/tmp/4142-exact-main/`.
Both trees collected exactly 29,601 unit tests.
The recorder retained every complete node ID, including parameter values.
The deterministic comparison used 374 Git rename pairs and four explicit filename changes already recorded in the map.
The complete node-ID multisets matched after these 378 exact path changes.
No test was missing or added.

The baseline retained 733 entries in their original order.
Exactly 668 `file_path` or `related_source` values changed through the verified move map.
Every changed target exists. No other baseline field changed.

The focused Arango, contract, posture, and path-guard run passed 135 tests, with one existing optional-runtime skip.
The ten moved modules also changed on main passed 267 tests.
These modules cover prompt input, retention, Redis output, SDK isolation, address handling, digest output, and posture outcomes.
Ruff passed for all 397 changed Python files.
Black reported that all 397 files need no change.
`python -m py_compile MistHelper.py` passed.
The required `TestLiveGuides` preflight passed one test and read all four required inputs.
The restored discovery caller passed all 27 tests.
The managed-record and baseline guards passed all 25 tests.
The five updated Spec Kit records passed the STE threshold with scores from 93 through 97.
The explicit feature prerequisite check passed with `-RequireTasks -IncludeTasks -RequireSpec`.
The optional commit hook requires no action. The companion hook is disabled.

Task T034 is complete.
Tasks T004 through T026 remain incomplete where ownership or final layout acceptance prevents completion.
This evidence does not establish full-suite execution, coverage, final five-child compliance, deployment, or merge readiness.
The pull request must remain draft, and issue #4142 must remain open.

## Historical-link deferral after the first CI run

Run `39464451697` failed the root-and-contracts shard on one historical Markdown link.
The shard passed 2,033 tests, skipped 19 tests, and reported five expected failures.
The failing guard named `specs/3300-selective-insight-definitions/checklists/requirements.md:94`.
That record links to `tests/unit/analytics/test_insight_metrics_utils.py`.
FR-004 requires the historical specification to remain unchanged.
The coordinator approved deferral of this single move.

The test now remains at its original source path with the exact approved-main bytes.
No shim or duplicate exists. The historical specification remains unchanged.
No baseline entry names either endpoint, so this correction requires no baseline edit.
Both endpoints were clear of other open pull requests before the move.

The test, Markdown-link guard, module-move guard, and baseline guard passed all 80 tests.
Full collection still contains 29,601 unit tests.
The complete node-ID comparison uses 377 exact move pairs and finds no missing or added IDs.
The baseline still contains 733 ordered entries and exactly 668 mapped path-field changes.
Every non-path field remains unchanged.
Targeted Ruff and Black passed, and the required quality preflight passed one test.
Task T035 is complete. The committed and full quality gates remain required before the correction push.

## Current-main rebase and SDK test isolation

Both required quality gates passed after commit `c0063b9d22d80d088160a85dcee087597e08d3e2`.
Each checked 1,198 files and 671 findings, with zero new findings and zero parse errors.
The final ownership scan found no intersection across 794 raw paths and 11 other open pull requests.
The correction push replaced the failed revision deliberately.

Run `39467158622` passed the historical-link guard and the root-and-contracts shard.
Its root-unit shard reported 26 failures, 24,809 passes, and 24 skips.
The coverage aggregator failed because that shard failed.
These failures did not establish green CI.

The six affected test modules passed 371 tests when run together.
Adding the moved MSP privilege module before those modules reproduced all 26 failures, with 380 passes.
Its autouse fixture removed every `mistapi` module from `sys.modules` before each test.
Other collected modules retained references to the previous SDK objects.
Later patches therefore changed different objects from the objects used by those modules.
The new test order exposed this existing fixture defect.

The fixture now imports its two endpoint modules without removing cached SDK modules.
It uses `monkeypatch` for temporary parent bindings and restores those bindings after each test.
The same seven-module command now passes all 406 tests.
No production code or held test changed.

After the corrected-head run finished, the coordinator approved rebase onto current main.
Published commit `c0063b9d22d80d088160a85dcee087597e08d3e2` preserves the complete correction remotely.
Rebase onto `aaab7b4541c2e578fb8c46d69da0446bfbd338a9` completed without conflicts or a merge commit.
Its head before the fixture repair was `696a905cbe03a9a66e687c953b8d5a4402f8aba4`.

Current main and the rebased branch each collect 29,602 unit tests.
The complete node-ID multisets match through 377 exact moves, with zero missing or added IDs.
The baseline retains 733 ordered entries, 668 mapped path-field changes, and no other changes.
The merged UI package, deferred insight test, and historical specification match current main exactly.
The UI tests, deferred test, and applicable guards passed 181 tests, with one optional-runtime skip.
Ruff passed all 396 changed Python files. Black reported that all 396 files need no change.
The entry-point compile passed.

The complete local root-unit shard passed 24,836 tests and skipped 24 tests.
It reported 76 warnings and completed in 706.43 seconds.
The command was:

```bash
COVERAGE_FILE=.venv/tmp/4142-local-root-units.coverage .venv/bin/python -m pytest tests/unit --ignore=tests/unit/upgrade_portal --ignore=tests/e2e --cov=src --cov-report= --cov-fail-under=0 --timeout=120
```

This command uses the CI shard selection and its per-test timeout.
The zero coverage threshold matches this individual shard, not the combined coverage gate.
The existing combined gate still requires 80 percent.
The local run establishes that the fixture repair removes all 26 full-shard failures.
The feature prerequisites and quality-input preflight passed again.
The revised records passed STE with scores from 93 through 97.
Task T036 is complete. The committed and full quality gates remain required before publication.

## Rebase after PR #4361

Both quality gates passed for commit `aead58f70015778e229c99311a9242ceb9c271a3`.
Each checked 1,198 files and 670 findings, with zero new findings and zero parse errors.
Its CI completed with 36 passed checks, seven intentional skips, and zero failed or pending checks.
Run `39473235677` passed the complete root-unit shard and combined coverage gate.
The combined coverage report measured 93 percent against the unchanged 80-percent requirement.

Main then advanced through PR #4361.
The coordinator approved another rebase onto `57d718be98ab2716127578d33b80326c641e64af`.
The green commit remains preserved on the remote branch before this rebase.
The clean rebase completed without a merge commit and retained both fixes.
The only main change adds one credential-preflight test with a mocked HTTP 503 response.

The new credential tests and seven-module SDK isolation regression passed all 426 tests.
The UI tests, deferred insight test, and applicable guards passed 181 tests, with one optional-runtime skip.
Current main and the rebased branch each collect 29,603 unit tests.
Their complete node-ID multisets match through 377 exact moves, with zero missing or added IDs.
The baseline retains 733 ordered entries, 668 mapped path-field changes, and no other changes.
The merged credential and UI tests, deferred insight test, and historical specification match current main exactly.
The final ownership scan found zero intersections across 794 raw paths and 11 other open pull requests.
Ruff and Black passed all 396 changed Python files.
The entry-point compile and required quality-input preflight passed.

## Cisco converter test relocation (2026-10-28)

PR #4226 merged at `14ac97942f1e575edd7dbf8c4bbfb517ef58fad3`.
Its owner released the Cisco test path for this move.
The open-PR scan checked five pull requests. It found no source or destination path conflict.

Move only `tests/unit/gateway/overrides/test_cisco_config_converter.py` to
`tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`.
The moved file matches approved blob `31a84e3795665ebea1a9346fd835fffc619a9fe7`.
That blob has 99 lines. Do not copy the separate untracked test from the old PR worktree.
The old source path is absent. The destination has five direct children, including `__init__.py`.

The base and candidate each collect 29,836 unit tests.
The full node-ID multisets match after mapping the 29 Cisco node IDs to the destination path.
The comparison reports zero missing and zero added IDs.
The focused Cisco test collects 29 tests. The converter route tests pass 14 tests.
The converter tests and move and structure guards pass 55 tests.

Ruff passes the moved test. Black reports that it would leave the file unchanged.
Python compilation passes. The STE linter and test-quality preflight pass.
The full test-quality gate checks 1,209 files and 613 findings.
It skips 52 files, reports zero parse errors, and finds zero new baseline findings.
The baseline keeps 733 ordered entries. It has no reference to either test path.
Its blob is unchanged by this move.

The current Cisco quickstart commands now use the destination path.
The earlier implementation command remains unchanged as historical evidence.
No other main content, historical record, or policy changed.

The previous local full root-unit result remains evidence for the identical fixture repair.
This rebase reruns the changed main test and the exact shared-state regression locally.
CI must rerun its complete unchanged gate set for the new head.
Task T037 is complete. The committed and full quality gates remain required before the rebase push.

## Coordinated rebase after PR #4364

Published head `4cf81839ce904153434e0aef5336252cfa7d5a3c` passed all 36 checks, with seven intentional skips.
Run `39477418333` measured 93-percent combined coverage.
Its root-unit shard passed 24,837 tests, skipped 24, and reported 76 warnings.
The coordinator then requested exact base `1c089ed07ba865a7e505df4774a79751c72187cf`.

The clean published branch preserved both fixes before rebase.
The rebase completed without conflicts or a merge commit.
The new base changes WAN dashboard source, integration tests, browser tests, and its existing specification.
This branch introduces no change to those production paths.
Its scope remains the unowned test-layout slices and the verified fixture repair.

The merged WAN service tests, SDK isolation regression, merged credential and UI tests, deferred test, and guards passed 653 tests.
One existing optional-runtime test skipped.
The base unit tree is unchanged from `57d718be98ab2716127578d33b80326c641e64af`.
The retained exact-main node snapshot therefore remains valid for this unit-tree comparison.
Fresh branch collection contains 29,603 unit tests.
The complete multisets match through 377 exact moves, with zero missing or added IDs.
The baseline retains 733 ordered entries, 668 mapped path-field changes, and no other changes.
Both fixes remain intact. The SDK fixture matches the previous green head exactly.
The original insight test and historical specification remain unchanged.

The live ownership scan found zero intersections across 794 raw paths and ten other open pull requests.
Ruff and Black passed all 396 changed Python files.
The compile, feature prerequisites, and required quality-input preflight passed.
Task T038 is complete. The committed and full quality gates remain required before publication.

## CSV-import test relocation

The approved base remains `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
PR #4358 was open and draft at `1ca0e9c6c78e7163a418311818b2ace4375a6839`.
Auto-merge remained disabled.
Fresh CI reported 36 successful checks, seven intentional skips, and zero failures.
CodeQL and the coverage gate passed.
The live `main` branch still matched the approved base.

The open-PR scan inspected five pull requests and found no source or destination overlap.
The seven-day session-file scan found no claim on either path.
The source group had four tracked files, and the destination did not exist.
The four files moved to `tests/unit/marvis/mist/resources/inventory/csv_imports/`.
Two tests now create scratch files under the moved package.
No other active path reference used the old test path.
The full quality baseline kept 733 ordered entries and no reference to either test path.
The baseline blob remained unchanged.

The full unit collection had 29,836 node IDs before and after the move.
An explicit path mapping covered all 17 CSV-import node IDs.
The comparison found zero missing and zero added IDs.
The root retained 39 direct children.
The `inventory` group fell from nine direct children to eight.
The `resources` group rose from four children to five.
The new `inventory` group has one child, and `csv_imports` has four.
Each checked group remains within the five-child limit.

The focused command `python -m pytest tests/unit/marvis/mist/resources/inventory/csv_imports tests/guardrails/test_move_module_guidance.py tests/guardrails/test_process_folder_structure.py -q` passed 43 tests.
Ruff passed for the four moved files.
Black left all four files unchanged.
Compilation and `git diff --check` passed.
The test-quality input preflight passed one test and read and validated all four required inputs.
The full analyzer checked 1,209 files and 613 findings.
It skipped 52 files, reported zero parse errors, and found zero new findings.
The baseline retained its original 733 entries.
The source directory is absent.

## Device-replacement and SQLite test relocation, 2026-10-28

The coordinator approved this batch after every check on `feaf7f331b7d33f3405e7468441cb42386e612de` completed.
The check report had 36 successes, seven skips, and zero failures.
CodeQL and coverage passed.
The live `main` and the branch base both remained `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
PR #4358 remained open and draft, with auto-merge disabled.

The final ownership refresh checked five open pull requests.
It found no exact source or destination path claim.
The seven-day session-file search found no claim on these paths.
Issue searches found #2753 and #3824 for related source-package work, but no exact test-path claim.
The SQLite writer issue search returned no result.
PR #4350 released the SQLite writer test for this batch.

The four device-replacement files moved to the mapped inventory group.
The SQLite writer test moved to the mapped storage group.
The five SHA-256 values match the files at their old paths.

| Destination file | SHA-256 |
| - | - |
| `tests/unit/marvis/mist/resources/inventory/device_replace/__init__.py` | `8bb8b7e1433b56a44e7805156336d5f26a9b9c13a77205809f092785e679b560` |
| `tests/unit/marvis/mist/resources/inventory/device_replace/test_rma_device_replace_client.py` | `c3a8cd847ee56f273acee5aaaefe3889dc3f4383e6b820ce4e4813c9c7a1735c` |
| `tests/unit/marvis/mist/resources/inventory/device_replace/test_rma_device_replace_model.py` | `f498cf230c675ed8224e8edeb76d7c7e65595d126985cbb203678c5756f8f647` |
| `tests/unit/marvis/mist/resources/inventory/device_replace/test_rma_device_replace_operation.py` | `28845f2a2f312df6c4f4cc684d932c540e810f62ee2cd672b32b97dd9548b3ba` |
| `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py` | `ce12a486daf1b964b2bf0420d81593c65a373e0bde689c36341e741534286140` |

The tracked root retains 39 children.
The `resources` group retains five children.
The inventory group now has two children, and the device-replacement group has four.
The `config`, `foundation`, and `support` groups have two, four, and four children.
The refactors, data, and storage groups have one child each.
Every affected group remains within the five-child limit.
The old source package and SQLite test path are absent.

The full unit collection has 29,836 node IDs before and after the move.
An explicit path mapping covers 14 device-replacement IDs and 55 SQLite-writer IDs.
The multiset comparison found zero missing and zero added IDs.
The quality baseline retains 733 records and its original SHA-256 value.
Its SHA-256 value is `f738363caa5d2d8b42e54c38ccca0252cc51e57d30791c81bf1e272a396a2af0`.
It has no source or destination path record.
The active-reference scan found no old test path outside the specification map and history.

The focused command
`.venv/bin/python -m pytest -q -p no:cacheprovider --tb=short tests/unit/marvis/mist/resources/inventory/device_replace tests/unit/config/foundation/support/refactors/data/storage tests/guardrails/test_move_module_guidance.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py`
passed 109 tests.
The test-quality input preflight passed one test.
Ruff passed, Black left four files unchanged, compilation passed, and both diff checks passed.
The full analyzer checked 1,209 files and 613 findings.
It skipped 52 files, reported zero parse errors, and found zero new findings.
The required committed changed-from gate passed with zero new findings.
It checked 1,209 files and 613 findings, skipped 52 files, and reported zero parse errors.
The exact command was
`.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`.

The PR #4350 owner also released `tests/unit/export/test_endpoint_family_exporter.py`.
That test remains outside T046 for a later ownership review.
The PR #4208 owner approved the five Arango tests for T047.
That handoff permits internal helper-reference changes in the moved package and changes to
`tests/unit/db_discovery/test_probe.py` and `tests/contract/test_arango_declared_indexes.py`.
No other `db_discovery`, workflow, or portal path is included.

## Arango storage test relocation, 2026-10-28

The PR #4208 owner approved these five files and the two external helper references listed above.
The immediate ownership refresh found no newer conflicting path claim.
The move changed no test behavior.

| Source file | Destination file | Pre-move SHA-256 |
| - | - | - |
| `tests/unit/arango_indexes/conftest.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/conftest.py` | `0009fa3905ad1ee9739314ea06330953b76622d3ec2e55160cf10a5bb416bafb` |
| `tests/unit/arango_indexes/fakes.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/fakes.py` | `0c1ee8bfefd74bb563c94a8c54c2a8bb9d5500e1b0bc9e7c9234e65c0887d7c6` |
| `tests/unit/arango_indexes/test_declared_indexes.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_declared_indexes.py` | `45fe998b3df66d351d3f5b876aa81b669648a6636ffe901d2fceff75d3f9a19b` |
| `tests/unit/arango_indexes/test_preservation.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` | `984d5bc36aa5a5386e2c724126c46aeb233383ee6179d4b05581d9fd7177420c` |
| `tests/unit/arango_indexes/test_retry_concurrency.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_retry_concurrency.py` | `d197533ccc6e5ac37eeccfd7d0edea0d358d3a7563676ddaf78be44558974969` |

## Refactor test relocation, 2026-10-28

The approved batch moved these three tests to the mapped groups.
The open-PR scan checked every paginated file list and found no source or destination overlap.
Issue comments and recent local session messages contain no exact claim for these paths.

| Source file | Destination file | Pre-move SHA-256 |
| - | - | - |
| `tests/unit/refactors/test_inventory_csvcomparator.py` | `tests/unit/config/foundation/support/refactors/data/inventory/test_inventory_csvcomparator.py` | `37c3c29b439a6325694ce361b31f2c7383a05e8630402959ed7d81b79f6dc35d` |
| `tests/unit/refactors/test_marvis_data_utils.py` | `tests/unit/config/foundation/support/refactors/data/inventory/test_marvis_data_utils.py` | `9a602dd13a5b99f3e30eb2e4918c777503d8b0301d20336cf4bd09d8838ff24d` |
| `tests/unit/refactors/test_anomaly_metrics_discovery.py` | `tests/unit/config/foundation/support/refactors/telemetry/test_anomaly_metrics_discovery.py` | `e0a3f521a6730b6fe99810c63d1f4a7ba8224d19acaacd87a73c1542bd7009ee` |

The three file hashes still match after the move.
Git reports each move as a content-identical rename.
The unit root retains 38 tracked children, and the source group drops from 26 to 23.
The destination parent groups change from one to two children.
The inventory group has two children, and the telemetry group has one.
Every affected group remains within the five-child limit.

The full unit collection has 29,836 node IDs before and after the move.
An explicit path mapping produces zero missing and zero added IDs.
The quality baseline retains 733 records and its original SHA-256 value,
`f738363caa5d2d8b42e54c38ccca0252cc51e57d30791c81bf1e272a396a2af0`.
No baseline record names any source or destination.
The historical Python inventory artifact remains unchanged.

The focused command
`.venv/bin/python -m pytest -q -p no:cacheprovider --tb=short tests/unit/config/foundation/support/refactors/data/inventory/test_inventory_csvcomparator.py tests/unit/config/foundation/support/refactors/data/inventory/test_marvis_data_utils.py tests/unit/config/foundation/support/refactors/telemetry/test_anomaly_metrics_discovery.py tests/guardrails/test_move_module_guidance.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py`
passed 61 tests.
The test-quality guide preflight passed one test.
Ruff passed, Black left three files unchanged, compilation passed, and the diff check passed.
The complete node-ID comparison found zero differences after the explicit mapping.
The full test-quality gate checked 1,209 files and 613 findings.
It skipped 52 files, found zero parse errors, and reported zero new findings.
The committed changed-from gate passed with the same counts and zero new findings.
The Markdown link scan found zero broken links.
The STE checks scored 97 and 93, and both files passed.

The only content edits replace the moved package's helper imports and the two approved external imports.
The `fakes.py` file retains its captured SHA-256 value.
The unit root has 38 tracked direct children after the move, one fewer than before this batch.
The destination package has five tracked direct children.
Its `storage` parent has three tracked direct children.
The process-folder and module-move guards passed.

The complete unit collection has 29,836 node IDs before and after the move.
The explicit mapping covers 75 Arango node IDs.
The multiset comparison found zero missing and zero added IDs.
The quality baseline retains 733 records and its original SHA-256 value,
`f738363caa5d2d8b42e54c38ccca0252cc51e57d30791c81bf1e272a396a2af0`.
No baseline path record names the source or destination.
The active-reference scan found no old import or path outside specification history.

The focused command
`.venv/bin/python -m pytest -q -p no:cacheprovider --tb=short tests/unit/config/foundation/persistence/storage/arango_indexes tests/unit/db_discovery/test_probe.py tests/contract/test_arango_declared_indexes.py tests/guardrails/test_move_module_guidance.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_quality_ratchet_files.py`
passed 164 tests.
Ruff passed, Black left seven files unchanged, compilation passed, and both diff checks passed.
Full unit collection matched the explicit path mapping with zero missing or added node IDs.
The test-quality input preflight passed one test.
The committed changed-from gate checked 1,209 files and 613 findings.
It skipped 52 files, reported zero parse errors, and found zero new findings.

## Launcher test relocation, 2026-10-28

The ownership scan found no open pull request or issue claim on these source or destination paths.
At the scan, `origin/main` was `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
The branch head was `f6ec876def65851f043a415b7972fa9c631704e2`.
PR #4358 remained open and draft. Auto-merge remained disabled.

| Source file | Destination file | Pre-move SHA-256 |
| - | - | - |
| `tests/unit/refactors/test_connection_pool_executor.py` | `tests/unit/config/foundation/support/refactors/network/launchers/test_connection_pool_executor.py` | `ab4c28df28d74ce94d5e8e1a4c23213080fb6327ce2362adc69bcfd966ae3c6f` |
| `tests/unit/refactors/test_maps_manager_launcher.py` | `tests/unit/config/foundation/support/refactors/network/launchers/test_maps_manager_launcher.py` | `0844cdc162e297cf2118cf34d297c9ed526d246f7e6e572cbfcd30e451c67a2b` |
| `tests/unit/refactors/test_wan2_migration_launcher.py` | `tests/unit/config/foundation/support/refactors/network/launchers/test_wan2_migration_launcher.py` | `0f7b2e8015a9588686be768c32623f092c23ae5280234a79203c0c8b02a5458b` |

Each destination hash matches its source hash.
The source group has 18 tracked direct children.
The mapped refactors parent has four tracked direct children.
The network group has one tracked direct child.
The launcher group has three tracked direct children.
The historical performance inventory remains unchanged.

The full unit collection has 29,836 node IDs before and after the move.
The explicit path mapping produces zero missing or added IDs.
Neither collection has duplicate IDs.
The three focused test files pass: 50 passed.
The package structure and move guidance guards pass: 24 passed.
The baseline guard passes: 14 passed.
The test-quality input preflight passes: one passed.
Ruff and Black pass. Compilation succeeds for all three files.
The three feature records score 97, 96, and 93 for STE.
The Markdown link scan finds zero broken links.

The baseline retains 733 records and two findings for these moved tests.
Only the four approved path fields changed.
All other finding fields, record order, and record count remain unchanged.
The committed changed-from gate checked 1,209 files and 613 findings.
It skipped 52 files and reported zero parse errors.
It found zero new findings against the baseline.
The gate passed after commit `78f15231fe239b615a2a581706d7eddc4af16f95`.
The preceding PR check run reported 36 passed, zero failed, and seven skipped or cancelled checks.
The three changed Markdown files passed the STE score threshold and link scan.
Keep every other `db_discovery`, workflow, and portal path deferred.

## Entrypoint test relocation, 2026-10-28

The approved batch moves these two tests to the mapped runtime entrypoint group.
The source and destination paths had no exact overlap with open pull requests.

| Source file | Destination file | Pre-move SHA-256 |
| - | - | - |
| `tests/unit/refactors/test_help_invocation_side_effect_free.py` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py` | `07ba8a2725aaa7fb7464d37a39bdefdd39394cf234030017821863f260c9dc3a` |
| `tests/unit/refactors/test_run_interactive_test.py` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_run_interactive_test.py` | `684eead3bec9e20ae9148281c4c14371b1732895bc923757748f3c0f6de4a7f2` |

Both post-move hashes match their pre-move values.
Git reports each move as a content-identical rename.
The entrypoint group has two tracked children.
Its ancestors have one to four tracked children, except the existing unit root.
The unit root has 38 tracked children, and this batch does not increase that count.

The complete unit collection has 29,836 node IDs before and after the move.
An explicit path mapping produces zero missing and zero added IDs.
Neither collection has duplicate node IDs.
The 733-record quality baseline has no path record for either moved test.
The historical test inventory artifact remains unchanged.

The two focused tests pass: 20 passed.
The module-move guidance guard passes: 15 passed.
Ruff, Black, compilation, and the diff check pass.
The test-quality input preflight passed one test.

The full guardrail command
`.venv/bin/python -m pytest -p no:cacheprovider tests/guardrails -q`
exited with code 1 after 103.87 seconds.
It reported 1,054 passed, 3 skipped, and 36 failed.
Every failure came from `tests/guardrails/test_spec_route_contract.py`.
Each failure reported that PowerShell must be installed to verify feature commands.
The environment has no `pwsh`, so no retry was made.
The full guardrail result remains failed and is not reported as a pass.

The test-quality input preflight passed one test.
The committed changed-from gate checked 1,209 files and 613 findings.
It skipped 52 files, reported zero parse errors, and found zero new findings.

## Filesystem test relocation, 2026-10-28

The user approved this one-file move and publication directly.
Move `tests/unit/refactors/test_data_directory_checker.py` to
`tests/unit/config/foundation/support/refactors/data/filesystem/test_data_directory_checker.py`.
The pre-edit scan found no external exact-path claim in five open pull requests.
The open-issue body and comment search returned zero matching issues.
The worktree was clean before the move.
The live main commit was `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
The preceding branch commit was `1cf3d4bcda5e0bb078cd5936956e8b7068abba82`.
Its checks reported 36 successful checks and seven skipped checks.

The moved file retains every byte.
The baseline, historical changelog, and historical performance inventory retain every byte.
The source group decreases from 18 to 17 tracked direct children.
The mapped data group increases from two to three children.
The new filesystem group has one child.
The other mapped ancestors retain two or four children.
No package marker, fixture, runtime file, or pytest setting changes.

The complete unit collection retains 29,836 node IDs.
An explicit source-to-destination mapping produces identical node-ID multisets without duplicate IDs.
The focused test and narrow structure, move, and baseline guards report 47 passed.
The required test-quality input preflight reports one passed.
Ruff, Black, compilation, and whitespace checks pass.
The committed test-quality check examined 1,209 files and 613 findings.
It skipped 52 files and reported zero parse errors.
It found zero new findings against the baseline after commit `f8d486a8d`.
The three feature records passed STE with scores of 97, 96, and 93.
The Markdown link check found zero broken links.
The held actions and analytics paths remain unchanged.

## Main entrypoint test relocation, 2026-10-28

The user directly approved this one-file batch and publication.
Move `tests/unit/refactors/test_main_entrypoint.py` to
`tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py`.
The ownership scan found no external exact-path pull request or open issue claim.
The branch started clean at `ac5c3716e5856d5d5321aeb50c81fddafb4a844f`.
Main remained `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
The preceding head had 36 successful checks and seven skipped checks.

The test file retains every byte.
The complete unit collection retains 29,836 node IDs.
An explicit path mapping produces identical node-ID multisets without duplicate IDs.
The baseline retains 733 records, their order, and all non-path fields.
Only four baseline path fields change.
The older quickstart changes only three approved command path tokens.
The historical changelog, performance inventory, and other historical specifications remain unchanged.

The source group decreases from 17 to 16 tracked direct children.
The runtime group retains one child.
The entrypoint group increases from two to three children.
The higher mapped ancestors retain two or four children.
The focused test and narrow structure, move, and baseline guards report 55 passed.
Ruff, Black, and compilation pass.
The committed test-quality check examined 1,209 files and 613 findings.
It skipped 52 files and reported zero parse errors.
It found zero new findings against the baseline after commit `7baa0b5d3`.
The required input preflight reported one passed.
The four Markdown files passed STE with scores of 94, 97, 96, and 93.
The link check found zero broken links.
The unsupported-flag test, actions, analytics, fixtures, and pytest settings remain unchanged.

## Unsupported-flag test relocation, 2026-10-28

The user directly authorized continued bounded batches with green checks between publications.
This batch completes the four-test mapped runtime entrypoint group.
Move `tests/unit/refactors/test_reject_unsupported_flag_variants.py` to
`tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py`.
The ownership scan found no external exact-path pull request or open issue claim.
The branch started clean at `f4ecb4648f9d07716f9ec84039efc83b1972119d`.
Main remained `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
The preceding head had 36 successful checks and seven skipped checks.

The test changes only its repository-root line.
The destination requires `parents[8]` instead of `parents[3]`.
A direct path comparison verifies that the new value resolves to this worktree.
The full entrypoint group and narrow structure, move, and baseline guards report 78 passed.
This includes the fresh-interpreter passive-import test that requires the correct working directory.
The complete unit collection retains 29,836 node IDs.
An explicit path mapping produces identical node-ID multisets without duplicate IDs.
The baseline retains 733 records, their order, and all non-path fields.
Only four baseline path fields change.
The historical changelog, performance inventory, and completed feature 1701 records remain unchanged.
The source group decreases from 16 to 15 tracked direct children.
The entrypoint group increases from three to four children.
The mapped ancestors retain one, two, or four children.
Ruff, Black, and compilation pass.
The committed test-quality check examined 1,209 files and 613 findings.
It skipped 52 files and reported zero parse errors.
It found zero new findings against the baseline after commit `00319c526`.
The required input preflight reported one passed.
The three feature records passed STE with scores of 97, 96, and 93.
The link check found zero broken links.
The held actions and analytics paths, fixtures, markers, and pytest settings remain unchanged.

## Configuration relocation fixture repair, 2026-10-28

CI run `40692675966` failed on head `d53e5626f381d6ce1d8024859a9cffa91e072e69`.
The root unit shard reported 21 failed, 25,017 passed, and 24 skipped.
The dependent coverage check also failed.
The E2E shards and CodeQL passed.
This is a test-order regression, not a transient runner failure.

The relocated WLAN fixture bound a mock resolver host without teardown.
Earlier execution exposed that retained mock to later exporters, inventory tests, session initialization, and TUI tests.
The same six downstream modules reproduced all 21 failures locally with 417 passed.
The WLAN module alone followed by two representative consumers reported two failed and 169 passed.
No whole-shard retry occurred.

The authorized repair changes only the moved WLAN test fixture and adds two regression cases.
The fixture uses `patch.object` to restore the exact previous `_root_module` object.
The existing module patch still restores `sys.modules`.
Both regression cases fail with the original fixture.
They pass after the repair for normal teardown and an exception.
The full targeted sequence reports 440 passed.
The configuration tests, affected consumers, and narrow structure, move, and input guards report 504 passed.
The full collection retains all 29,836 original node IDs.
It adds exactly two regression cases, for 29,838 total, without duplicates.
No production code, shared fixture, pytest setting, baseline record, or historical artifact changes.
The original committed test content remains identical outside the two authorized fixture lines and appended regression.
The committed HTTP 503 test remains unchanged.

The refreshed five-PR file inventory has no external exact-path overlap.
Main remains `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
The remote branch remains `d53e5626f381d6ce1d8024859a9cffa91e072e69`.
PR #4358 remains a draft with auto-merge disabled.

Issue #2746 retains an unpublished 31-line HTTP 403 append on `jmorrison-juniper-http-4xx-test-local-slice`.
Its source path is `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`.
Later integration must use `tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py`.
This repair neither imports that append nor changes its branch or hold.
The owner released the fixture and mapped-path repair through an explicit session handoff.
Commit `4f25cf00a74a41095e487af7836cae49d4f9f12e` must remain intact and unpublished.
Later integration must preserve the fixture repair and must not duplicate the HTTP 403 test.
The user then explicitly authorized the remaining gates and publication of this fixture repair.
The #4008 actions and analytics holds remain unchanged.
Publication requires the scoped gates and an exact remote-head lease.
Another batch requires green CI on the published repair head.

## Network configuration test relocation, 2026-10-28

The preceding head `05e90edc2fd344e0270df7ecb0c7d2f6758a8e4b` passed all 36 checks.
Seven automation checks skipped. The worktree was clean.
Main remained `a0fac53c5b5d5f57e6d05ff2d6225570cda07691`.
Exact open pull request and issue searches found no external claims for this batch.
The existing map assigns these three files to `network/configuration/`.

| Source file | Destination file |
| - | - |
| `tests/unit/refactors/test_device_config_template_cloner_manager.py` | `tests/unit/config/foundation/support/refactors/network/configuration/test_device_config_template_cloner_manager.py` |
| `tests/unit/refactors/test_wanprobe_config_manager.py` | `tests/unit/config/foundation/support/refactors/network/configuration/test_wanprobe_config_manager.py` |
| `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | `tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py` |

All three files retain every byte.
The focused configuration tests and narrow structure, move, and baseline guards report 273 passed.
The complete unit collection retains 29,836 node IDs.
An explicit path mapping produces identical node-ID multisets without duplicate IDs.
The baseline retains 733 records, their order, and all non-path fields.
Only 18 path fields change across nine existing WLAN RADIUS findings.
The historical changelog, performance inventory, and test-quality triage remain unchanged.
The source group decreases from 15 to 12 tracked direct children.
The network group increases from one to two children.
The new configuration group has three children.
Higher mapped ancestors retain two or four children.
Ruff, Black, and compilation pass.
The committed test-quality check examined 1,209 files and 613 findings.
It skipped 52 files and reported zero parse errors.
It found zero new findings against the baseline after commit `ba2d97d9f`.
The required input preflight reported one passed.
The three feature records passed STE with scores of 97, 96, and 93.
The link check found zero broken links.
The separate WAN override test and its quickstart consumer remain unchanged.
This exclusion bounds the batch and does not assert an ownership block.
The held actions and analytics paths, fixtures, markers, and pytest settings remain unchanged.
