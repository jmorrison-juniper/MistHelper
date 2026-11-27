# Research: Function and module size for Pylint limits (issue 4135)

## Method and scope

- Base revision: GitHub `main` head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z.
- The local checkout has the same head. The worktree blob SHA equals the remote tree blob SHA for each of the five named files.
- Line counts split the decoded file text on LF. Use this method. A `Get-Content` count gave 7,738 lines for `MistHelper.py`, but the LF count is 8,372.
- Pylint was not run. The brief forbids linters for this research step. Every finding below comes from reading and counting.
- The issue comments of 2026-11-08 and 2026-11-09 describe older commits. Main changed after both comments.

## Findings on main

| Message | Issue report | Main `f03c6c9` by reading | Status |
| - | - | - | - |
| R0911 too-many-return-statements | 8 returns, limit 6, in one `operation.py` method | `_is_user_facing` starts at line 1891 and returns eight times, from line 1894 to line 1908 | Present |
| R0914 too-many-locals | 29 locals, limit 15, in `operation.py` | `_build_registry` starts at line 406 and spans 507 lines | Present, count by reading |
| R0915 too-many-statements | 55 statements, limit 50, in the same function | Same function | Present, count by reading |
| R0913 too-many-arguments | 6 arguments in `MistHelper.py` | No function in `MistHelper.py` has more than five parameters, counting `self` | Not reproduced |
| R0917 too-many-positional-arguments | 6 positional arguments in `MistHelper.py` | Same as R0913 | Not reproduced |
| C0302 too-many-lines, `operation.py` | 1,522 lines | 1,952 LF lines | Present, limit 1,000 |
| C0302 too-many-lines, `MistHelper.py` | 8,107 lines | 8,372 LF lines | Present, limit 1,000 |
| C0302 too-many-lines, endpoint file | 4,128 lines | 4,537 LF lines | Present, limit 1,000 |
| R0801 duplicate-code | Blocks at lines 99 to 109 and 448 to 457 | Those lines hold other code. A normalized common run of 13 lines covers the `_write` method at line 113 of `asset_lookup.py` and at line 471 of `correlation.py` | Present at new locations, approximation only |

The reported R0913 and R0917 finding came from the old branch. Pull requests 4856 and 4857 merged on 2026-11-20 and changed `MistHelper.py`. The record keeps a confirmation task. No code change targets R0913 or R0917.

## Decisions

### D-1 Verify findings on main by reading

- Decision: Count and locate findings by reading decoded `main` text. Confirm them with Pylint during implementation.
- Alternatives: Trust the issue line numbers. Run Pylint now.
- Reason: The issue numbers are stale. This research step forbids linters.
- Risk: Counts for R0914 and R0915 are estimates. Task T002 confirms them.

### D-2 Treat R0913 and R0917 as not reproduced

- Decision: Make no code change for R0913 or R0917. Close the message when Pylint confirms zero findings.
- Alternatives: Refactor a function chosen by guess. Keep the finding open without evidence.
- Reason: The parser found no `MistHelper.py` signature with more than five parameters.
- Risk: A signature the parser missed. Task T002 covers this risk.

### D-3 Reduce returns in `_is_user_facing`

- Decision: Move the plumbing checks into a helper named `_is_plumbing_record`. The method keeps at most six returns.
- Alternatives: Add a Pylint disable comment (forbidden). Reorder branches without a reduction (does not fix R0911). Use a lookup table (larger change).
- Reason: The helper keeps the eight branch outcomes and the order of checks.
- Risk: A changed branch order. Test `test_user_facing_classification_branches` covers each outcome.

### D-4 Split `_build_registry` into static group builders

- Decision: Move each group between the six markers into a static method of a class in `portal_operations/groups/`. `PortalRegistryBuilder.build()` merges the results in the original order.
- Alternatives: Keep one function with a suppression (forbidden). Replace the registry with a data file (changes the source of truth).
- Reason: Each builder stays small. The merged result keeps the same keys and values.
- Risk: A key moved to the wrong group changes order. The registry hash test detects a change in content. Order uses the same merge sequence.

### D-5 Share one Juniper row writer

- Decision: Add class `JuniperRowWriter` to `src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py`. Both workflows call it.
- Alternatives: Reuse `JuniperExportSink`. That class prints rows before it writes, so the behavior differs. Create a new module under `juniper_rma/`. That adds a child that reaches six under a stricter count.
- Reason: The duplicated body becomes one class in the existing Juniper export module. The change adds no child to any directory.
- Risk: The module docstring must name the wider scope. The constructor of each workflow keeps the `exporter` argument. Tests that inject a double keep working.

### D-6 Place new modules only in compliant parents

- Decision: Put new code only under `src/interfaces/`, `src/foundation/support/`, `src/operations/exporting/juniper_rma/`, and `src/foundation/persistence/db/`. Each parent has a free child slot.
- Alternatives: Add children to `workflows/`, `web_portal/services/`, or `refactors/`. Each parent already exceeds five children.
- Reason: The constitution forbids a new child under a noncompliant parent. The ratchet test rejects a count increase.
- Risk: Package names must stay semantic. The new names follow the subject of each module.

### D-7 Split the endpoint dictionary into contiguous blocks

- Decision: Move the 612 entries into six contiguous blocks of 102 entries. Compose the public dictionary by merging the blocks in file order.
- Alternatives: Split by key prefix. This changes the insertion order. Move the data to JSON. This changes the source of truth.
- Reason: The contiguous split keeps the original order. The 612 entries divide evenly into six blocks.
- Risk: A duplicate key in the merge. The composition task checks the key count, which must stay 612.

### D-8 Keep the public names of `operation.py`

- Decision: Keep `OperationExecutor`, the constants, `_read_positive_int_env`, and the `PARAMETER_REGISTRY` assignment in `operation.py`. Move the rest to `portal_operations/`. Import the moved names that `operation.py` uses.
- Alternatives: Move `OperationExecutor`. Many tests import it from `operation.py`.
- Reason: Tests keep their import paths. Each import is used by `operation.py` itself.
- Risk: A moved private helper that a test calls. The test migration task checks each import path.

### D-9 Keep the host contract in `MistHelper.py`

- Decision: Keep the bootstrap block, the module globals, the context module, `__all__`, and the entry guard in `MistHelper.py`. Move the menu, context, runtime, and bootstrap classes into `src/interfaces/cli/`.
- Alternatives: Keep one module and suppress C0302 (forbidden). Move only the menu (leaves about 4,000 lines).
- Reason: The menu, the session code, and the runtime account for about 7,500 of the 8,372 lines. The host block stays near 850 lines.
- Risk: Import-time side effects change order. Task T049 adds an import smoke test.

### D-10 Do not re-export moved names

- Decision: A moved name leaves `MistHelper.py`. No import binding keeps the old name. Call sites and test targets change to the new owner. The pull request lists each removed name.
- Alternatives: Keep import bindings to pass `symbol-diff`. That is a compatibility shim, which AGENTS forbids. Add a waiver to the symbol tool. The tool has no waiver option.
- Reason: The rule in AGENTS and the endpoint move in initiative 1015 both forbid shims. The `symbol-diff` comparator treats each removed module-level name as lost. The record expects these losses and does not claim a pass.
- Risk: A removed name that a caller still imports fails at import time. Task T048 migrates each caller. The full test run finds any missed caller.

### D-11 Update test targets and source-text guards

- Decision: Each patch target and each source-text guard moves to the new owner. `tests/guardrails/test_endpoint_catalog.py` reads the menu package instead of `MistHelper.py`.
- Alternatives: Keep attributes on `MistHelper` for patches. That reintroduces shims and does not change the call sites that the patch must reach.
- Reason: A patch on the old owner does not reach the new call site.
- Risk: A missed patch target. The inventory search covers 805 matches in 108 files.

### D-12 Store parity constants in existing test modules

- Decision: Store SHA-256 constants for the registry, the endpoint dictionary, and the menu key order in the existing test modules. Add no fixture file.
- Alternatives: Add JSON fixtures under `tests/fixtures/`. That folder adds children to a noncompliant parent.
- Reason: The constants prove content and order without a new child.
- Risk: A constant computed on the wrong base. Task T001 computes each constant on `main` before any edit.

### D-13 Keep the nested-package baseline unchanged

- Decision: Make no change to `tests/guardrails/nested_package_baseline.json` or to the expected message in the ratchet test. Every grown directory stays at or below five children.
- Alternatives: Update the baseline for each grown directory. That adds debt that the ratchet does not require.
- Reason: The recomputed ratchet gives 190 directories, 33 violations, and 236 total excess. The counts stay the same.
- Risk: A new violation. Task T003 records the counts before any edit. Task T-LOCAL-GATES repeats the check.

### D-14 Record the blocked menu gate

- Decision: Run `python scripts/generate_menu_wiki.py`. Record `python -m scripts.menu_api_map --check` as blocked, because the module is absent on main. File a repair issue in task T053.
- Alternatives: Skip the gate silently. Create the missing module in this change.
- Reason: Creating a module to satisfy a gate changes scope. The gate must show its true state.
- Risk: A menu drift that the missing gate would catch. The generator output comparison covers the generated pages.

### D-15 Record touched violations and file a remediation issue

- Decision: Record each touched function that exceeds 25 lines, the moved module-level functions outside classes, and each touched directory violation. File one remediation issue for these items in task T052.
- Alternatives: Fix every touched function now. This expands the scope beyond the Pylint messages.
- Reason: The constitution requires a separate remediation action for each touched violation. It forbids new debt.
- Risk: The remediation issue stays open for a long time. Its number appears in the pull request body.

### D-16 Deliver one pull request with ordered commits

- Decision: Use branch `chore/4135-pylint-size-refactor`. Use commit type `refactor(lint)`. Use one pull request titled `refactor(lint): reduce function and module size for pylint limits`. Add changelog fragment `issue-4135-pylint-size-refactor.md`.
- Alternatives: Several pull requests under one issue. The task list has one delivery path.
- Reason: The constitution allows the `chore` branch type for maintenance work. AGENTS allows a commit type more precise than the branch type.
- Risk: A large review. The commit order follows the phases in tasks.md.

## Module budget and child counts

Line budgets use the LF count. Children follow the ratchet definition in `tests/guardrails/test_nested_package_structure.py`, which excludes `__init__.py`. A stricter count that includes `__init__.py` is listed in `analysis.md`.

| Path | LF lines before | Target after | Limit |
| - | - | - | - |
| `MistHelper.py` | 8,372 | 850 | 1,000 |
| `web_portal/services/operation.py` | 1,952 | 880 | 1,000 |
| `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | 4,537 | 170 | 1,000 |
| `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` | 139 | 127 | 1,000 |
| `src/operations/exporting/juniper_rma/workflows/correlation.py` | 498 | 484 | 1,000 |
| `src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py` | 181 | 221 | 1,000 |

| Directory | Children before | Children after | Change |
| - | - | - | - |
| `src/interfaces` | 4 | 5 | Adds `cli/` |
| `src/foundation/support` | 4 | 5 | Adds `portal_operations/` |
| `src/operations/exporting/juniper_rma` | 4 | 4 | No child added. The writer joins `juniper_menu_support.py` |
| `src/foundation/persistence/db` | 2 | 3 | Adds `endpoint_strategies/` |
| `src/interfaces/cli` | new | 4 | `bootstrap/`, `context/`, `menu/`, `runtime/` |
| `src/foundation/support/portal_operations` | new | 5 | Five children, all new |
| `web_portal/services` | 9 | 9 | Unchanged, noncompliant parent |
| `tests/fixtures` | unchanged | unchanged | No file added |

## GlobalImportManager split map

The class spans lines 1207 to 2441 of `MistHelper.py`. `LogRotationSettings` spans lines 109 to 185 and moves to `log_rotation.py`.

- Factories, lines 1270 to 1345: `SiteExportUtilsFactory`, `RoutingUtilsFactory`, `GatewayTemplateConfigManagerFactory`. Target: `cli/bootstrap/factories.py`.
- Installer, lines 1346 to 1735 and 1802 to 1969: `__init__`, `_load_upgrade_configuration`, `_initialize_dependency_tracking`, `_initialize_import_mappings`, `_detect_virtual_environment`, `_setup_logging`, `_build_console_log_handler`, `_build_file_log_handler`, `_define_package_requirements`, the uv methods from `_check_uv_installation` to `_install_one_dependency`, the pip and upgrade methods from `_check_and_upgrade_package` to `_upgrade_and_verify`, `_should_upgrade_package`, `_auto_install_allowed`, `_attempt_install`, `_install_and_retry`. Target: `cli/bootstrap/dependency_installer.py`.
- Initializer, lines 1736 to 1801 and 1877 to 2441: `_import_concurrent_futures`, `_DateTimeHandler`, `_import_datetime`, `_import_tqdm`, `_resolve_and_import`, `_clear_failed_import_cache`, `_retry_import_after_install`, `_record_import_failure`, `import_module_safely`, `_record_successful_import`, `_partition_dependencies` through `get_configuration`. Target: `cli/bootstrap/import_initializer.py`.
- Rule: the initializer may call the installer. The installer must not call the initializer. Task T042 checks this with a name scan.

## Remote verification

Each row cites the remote blob SHA from the `main` tree, or the GitHub object named in the row. The line field gives the decoded line number. The same 62 rows appear in `STATUS.json`.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | `MistHelper.py` has 8,372 LF lines | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8372 |
| 2 | Module-level `__all__` list starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 192 |
| 3 | Class `GlobalImportManager` starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1207 |
| 4 | Function `_build_policy_api` starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3645 |
| 5 | Dictionary `menu_actions` starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3658 |
| 6 | Function `_systematic_test_build_safe_list` starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6502 |
| 7 | Function `_has_meaningful_cli_args` starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8269 |
| 8 | Entry guard `if __name__ == "__main__":` starts | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8276 |
| 9 | Host binding `MainEntrypoint.bind_host_module` is called | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 712 |
| 10 | `operation.py` has 1,952 LF lines | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 1952 |
| 11 | Function `_build_registry` starts | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 406 |
| 12 | Class `OperationExecutor` starts | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 918 |
| 13 | Class `_RunLogHandler` starts | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 1732 |
| 14 | Method `_is_user_facing` returns eight times, lines 1894 to 1908 | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 1894 |
| 15 | Six group markers in `_build_registry` start at line 410 | `web_portal/services/operation.py` | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 410 |
| 16 | Endpoint file has 4,537 LF lines | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 4537 |
| 17 | Classes `SleTrendIdentity` and `SleWindowIdentity` start | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 36 |
| 18 | Dictionary `ENDPOINT_PRIMARY_KEY_STRATEGIES` starts | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 141 |
| 19 | Dictionary holds 612 entries, from line 144 to line 4527 | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 4527 |
| 20 | `asset_lookup.py` has 139 lines and method `_write` starts at line 113 | `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` | main | d4e34076440a8709c409c95a1fed81cbc0091e8a | present | 113 |
| 21 | `correlation.py` has 498 lines and method `_write` starts at line 471 | `src/operations/exporting/juniper_rma/workflows/correlation.py` | main | 5687bf116cae51f8180242a51fb4d4e12c1cf06f | present | 471 |
| 22 | Class `JuniperExportSink` prints rows, then writes through the exporter | `src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py` | main | 2fad0cc40c90f0d7f20997427a27420803bf0b4c | present | 142 |
| 23 | Nested baseline lists `juniper_rma/workflows` with child count 7 | `tests/guardrails/nested_package_baseline.json` | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 167 |
| 24 | Nested baseline lists `juniper_rma/model` with child count 6 | `tests/guardrails/nested_package_baseline.json` | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 162 |
| 25 | Nested baseline lists `src/foundation/support/refactors` with child count 33 | `tests/guardrails/nested_package_baseline.json` | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 12 |
| 26 | Nested test defines `MAX_CHILDREN = 5` | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| 27 | Nested test asserts "33 violations, 236 total excess" | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 177 |
| 28 | CI job `pylint` starts | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 503 |
| 29 | CI runs Pylint on `SRC_PATH` only | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| 30 | CI `SRC_PATH` is `src/` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 78 |
| 31 | CI `VULTURE_PATHS` and `INTERROGATE_PATHS` include `web_portal` and `MistHelper.py` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 32 | CI holds no symbol-diff job | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 0 |
| 33 | `[tool.pylint.main]` starts, and `ignore-paths` names only maps, ssh, and ui | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 564 |
| 34 | No `design` or `similarities` pylint table exists, so default limits apply | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | absent | 0 |
| 35 | Pylint exclusions name other paths only | `quality_gate_exclusions.json` | main | 1dc1e56bb0b8579e3a1cb75f125c6178b2c62f0d | present | 91 |
| 36 | Resolver maps helper names in `_module_symbols` | `src/foundation/runtime/config/source_dependency_resolver.py` | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 40 |
| 37 | Resolver reads host symbols in `_resolve_host_symbol` | `src/foundation/runtime/config/source_dependency_resolver.py` | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 235 |
| 38 | Architecture table states 8,071 lines for `MistHelper.py` | `documentation/architecture.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce | stale | 196 |
| 39 | Copilot instructions state 8,382 lines, measured 2026-10-04 | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 580 |
| 40 | Contributor map section starts | `documentation/CONTRIBUTING-MistHelper.md` | main | 0859587507a8ee27b8f41320c57fb52be93f9a7b | present | 31 |
| 41 | Juniper asset test passes an exporter to `AssetLookupWorkflow` | `tests/unit/juniper_rma/workflows/test_lookups.py` | main | 779b9ae49c4d0642cc5cef9eb8d6ab6c3595cc09 | present | 133 |
| 42 | Correlation test imports `CorrelationWorkflow` | `tests/unit/juniper_rma/workflows/test_correlation.py` | main | 77b384814b86033c4cf9cdd1cc9e91907256f8cb | present | 12 |
| 43 | Portal test imports `PARAMETER_REGISTRY` from `operation.py` | `tests/unit/web_portal/test_portal_required_controls.py` | main | ef6d57b5352eac55ecee9c41f919802dd1e57698 | present | 45 |
| 44 | Log routing test imports `_RunLogHandler` from `operation.py` | `tests/unit/web_portal/test_portal_log_routing.py` | main | e305f0b4745b043cd61a3a9c8dddd800fd2e42d5 | present | 22 |
| 45 | Endpoint catalog test imports `SleTrendIdentity` | `tests/guardrails/test_endpoint_catalog.py` | main | e061f6624a69cbfc7947275c076523c3c8d85fcd | present | 35 |
| 46 | Endpoint catalog test reads `MistHelper.py` text to find `menu_actions` | `tests/guardrails/test_endpoint_catalog.py` | main | e061f6624a69cbfc7947275c076523c3c8d85fcd | present | 566 |
| 47 | Symbol guard lists `INTENTIONAL_SYMBOL_REMOVALS` for `src` modules only | `tests/guardrails/test_src_public_symbol_preservation.py` | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 101 |
| 48 | Constitution Principle I states the five-item rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 49 | AGENTS states the five-parameter function rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 81 |
| 50 | Symbol comparator reports lost module-level names | `.venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py` | local checkout | not applicable | present | 113 |
| 51 | Menu operation registry guard exists | `tests/guardrails/test_operation_registry_menu_coverage.py` | main | 626c6ccc7b1c72069256c6fa57e891695b93358e | present | 0 |
| 52 | Move-module guidance guard exists | `tests/guardrails/test_move_module_guidance.py` | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 0 |
| 53 | Menu wiki generator exists | `scripts/generate_menu_wiki.py` | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| 54 | Menu API map module is absent | `scripts/menu_api_map.py` | main | not applicable | absent | 0 |
| 55 | Changelog fragment rules exist | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| 56 | Commit `f03c6c9` exists and is the main head | `repos/jmorrison-juniper/MistHelper/commits/f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | main | not applicable | present | 0 |
| 57 | Pull requests 4856 and 4857 merged on 2026-11-20 and changed `MistHelper.py` | Pull requests 4856 and 4857 | merged | not applicable | present | 0 |
| 58 | Pull requests 4607 and 4658 merged, so issue comments that call them open or holding the slot are stale | Issue comments on issue 4135 | issue 4135 | not applicable | stale | 0 |
| 59 | Seven open pull requests touch none of the five named files | Open pull requests | GitHub | not applicable | present | 0 |
| 60 | Nine-finding report on commit 3964d21 is stale | Issue comment on issue 4135 | issue 4135 | not applicable | stale | 0 |
| 61 | Pre-move source roots hold no path on main | Pre-move source roots named in the issue body | main | not applicable | absent | 0 |
| 62 | CI job `menu_reference_drift` runs the absent module with `--check` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 732 |

Note on row 35: the pylint exclusion list names source paths for maps, ssh, and ui only. No row names `MistHelper.py` or `web_portal`.

## Sources

Local reads, in order of use:

- `AGENTS.md` and `.github/copilot-instructions.md`, read in full. The local gates table is at lines 60 to 100 of the copilot instructions.
- `.specify/memory/constitution.md`, read in full. The branch rule is in the multi-agent section, and the complexity table rule is in the compliance review.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, read in full.
- Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its headings were read to copy the shape. Its content was not copied.
- `documentation/quality-gates.md`, lines 1 to 75, for the job table and the Pylint row.
- `documentation/architecture.md` and `documentation/development-setup.md`, read by pattern search for module tables and Pylint setup text. Only the module table row at line 196 changes.
- `documentation/container-deployment.md` and `documentation/operator-guide.md` do not apply. No container runs in the gates, and no operator-visible behavior changes.
- `tests/guardrails/test_nested_package_structure.py`, read in full. It defines the ratchet and the expected message.
- `tests/guardrails/test_src_public_symbol_preservation.py`, read in its header, its waiver list, and the test names.
- `.venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py`, read at the comparator core.
- Skills: no listed skill covers Python size refactoring. No skill was loaded.

## Unverified

- Pylint results on `main`. The brief forbids running a linter. Task T002 runs it during implementation.
- Exact statement counts and local counts for `_build_registry`. The counts come from reading, not from Pylint.
- The similarity result for R0801. The approximation normalizes stripped lines, comments, and blank lines. The installed Pylint defaults for docstrings and signatures were not read. Task T002 confirms the result.
- The location of `GlobalImportManager.MenuEntry`. A name scan did not find a class statement for it. Task T044 locates it.
- The 805 matches for `MistHelper` references in tests. The count comes from a pattern search, so Task T048 repeats the search.
- Whether another test depends on the insertion order of a module-level dictionary beyond the endpoint catalog. Task T048 runs the full test shards to check this.
