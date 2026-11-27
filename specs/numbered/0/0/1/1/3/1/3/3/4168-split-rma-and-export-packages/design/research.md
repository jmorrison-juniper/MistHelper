# Research: Split the Juniper RMA and export packages

## Method

1. Read issue #4168 and its comments with `gh issue view`. Read linked pull requests #4125, #4219, #4607, #4658, #4813, and #4208 with `gh pr view` and `gh pr list`.
2. Read the governing files: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four Spec Kit templates, and the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. The reference record gave the section shape and depth.
3. Read the nested package guard, the baseline, the move-module guard, the hook catalog guard, and the route script `.specify/scripts/powershell/spec-route.ps1`.
4. Found the legacy folder `specs/numbered/0/0/1/1/3/1/3/3/4168-org-auto-upgrade-policy/`. A read-only agent read all eight files. This record checks each path that folder cites.
5. Read the remote main tree once with `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree reports `truncated=false` and 11,404 entries. Each remote check below uses this tree or a decoded remote file body.

## Local measurement

Local `HEAD` equals remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. `git status` lists five modified files outside this change: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, and two test files. None of them touches a file in this change. The measure below uses tracked files from `git ls-files`, and it follows the rules of `measure_direct_children` in the guard.

| Measure | Value |
| - | - |
| Python files under `src` | 931 |
| Directories examined | 190 |
| Violations (more than five children) | 33 |
| Total excess | 236 |
| `src/operations/exporting/export` children | 48 |
| `src/operations/exporting/export/site_insights` children | 3 |
| `src/operations/exporting/juniper_rma` children | 4 |
| `src/operations/exporting/juniper_rma/model` children | 6 |
| `src/operations/exporting/juniper_rma/workflows` children | 7 |

The 33 violations match the 33 entries in the baseline. The total excess of 236 matches the baseline sum. The guard test message on remote line 177 states `33 violations, 236 total excess`.

Projected result after the change: 206 directories examined, 30 violations, and 190 total excess. Derivation: 17 new directories (16 new package markers and `site/insights`), minus the removed `site_insights` directory, gives 16 net new directories. The three removed violations carry excess 43 (export), 1 (model), and 2 (workflows). The projection is in `design/quickstart.md`, and `T024` verifies it.

## Decisions

Each decision names its alternatives, the choice, the reason, and the risk. No decision needs a human.

### D-1 Record location

- Decision: `specs\numbered\0\0\1\1\3\1\3\3\4168-split-rma-and-export-packages`.
- Alternatives: (a) a timestamp route under `specs/live/` was rejected, because a numeric issue uses the numbered route. (b) Reusing `4168-org-auto-upgrade-policy` was rejected, because that folder belongs to issue #4217.
- Reason: 4168 equals `00113133` in base 5 (1x5^5 + 1x5^4 + 3x5^3 + 1x5^2 + 3x5^1 + 3x5^0 = 4168). `spec-route.ps1` gives the same eight segments.
- Risk: two folders share the number 4168 under one route. See finding A-1 in `analysis.md`.
- Human decision required: no.

### D-2 Export package layout

- Decision: `export/` keeps `data_exporter.py` in place. It holds four domain packages: `org`, `site`, `wan`, and `generic`.
- Alternatives: (a) moving `data_exporter.py` into a package was rejected, because pull request #4813 changes its content, and a move forces a conflict. (b) A flat layout of 47 modules in five packages was rejected, because one directory holds at most five children.
- Reason: `export/` holds five children: `data_exporter.py` and four packages.
- Risk: the grouping is a judgment. A reviewer can regroup, if each directory still holds five children or fewer.
- Human decision required: no.

### D-3 Site package layout

- Decision: `site/` holds `site_export_utils.py` and four packages: `events`, `devices`, `queries`, and `insights`.
- Alternatives: (a) grouping by scope only was rejected, because 19 site modules exceed the five-child limit at one level. (b) Moving the webhook delivery exporter to `org/events` was rejected. Its endpoint `searchSiteWebhooksDeliveries` is site scoped, as the module docstring states.
- Reason: each group holds one endpoint family or one role.
- Risk: `queries` mixes search, client, and application list endpoints.
- Human decision required: no.

### D-4 Device events package

- Decision: `device_events_52w_exporter.py` moves to `org/events/`.
- Evidence: the module names `_API_FUNCTION_NAME = "searchOrgDeviceEvents"` at line 20, and it calls `self.mistapi.api.v1.orgs.devices.searchOrgDeviceEvents` at line 160. Local `HEAD` equals remote `main`, and `git status` lists no change for this file, so these lines equal the remote lines.
- Alternatives: moving it to `wan/` was rejected, because the endpoint is organization scoped.
- Reason: the endpoint scope decides the package.
- Risk: none known.
- Human decision required: no.

### D-5 Juniper RMA model layout

- Decision: `model/` holds `parsers/` (`asset.py`, `service_request.py`) and `rows/` (`export_rows.py`, `reference_rows.py`, `request_rows.py`). `run_record.py` stays in place.
- Alternatives: moving `run_record.py` into `rows/` was rejected, because a run record is not a row. Keeping all six modules in `model/` was rejected, because `model/` would hold six children.
- Reason: the module docstrings name the parsers, the row builders, and the run record as three roles.
- Risk: none known.
- Human decision required: no.

### D-6 Juniper RMA workflow layout

- Decision: `workflows/` holds `reads/` (`case_reads.py`, `reference_reads.py`, `juniper_menu_support.py`) and `lookups/` (`lookup.py`, `asset_lookup.py`). `access_check.py` and `correlation.py` stay in place.
- Alternatives: keeping `juniper_menu_support.py` at the root was rejected, because the shared support belongs with its readers. The root would still hold five children.
- Reason: the module docstrings name menus 294 to 300 for the reads, and menus 303 and 304 for the lookups.
- Risk: none known.
- Human decision required: no.

### D-7 No shims and docstring-only markers

- Decision: old module paths are removed. Each new `__init__.py` holds one docstring and no re-export.
- Alternatives: (a) re-exporting names from the old packages was rejected. AGENTS.md and the constitution forbid a compatibility shim. (b) Re-exporting names from the new markers was rejected. The current markers hold docstrings only, so a re-export would add a hidden public surface.
- Reason: the guard counts modules and directories, not symbols. The change removes every alias.
- Risk: code outside this repository would break. The repository has no such code (see Assumptions in `spec.md`).
- Human decision required: no.

### D-8 Baseline and guard message

- Decision: remove three objects from the baseline. Keep 30 objects. Change the expected message to `30 violations, 190 total excess`.
- Alternatives: keeping the export entry with a lower count was rejected. Issue #4168 requires the removal, and the export folder reaches five children or fewer.
- Reason: the guard rejects a stale entry whose directory holds five children or fewer.
- Risk: the expected message is a hard-coded string. The change updates it in the same commit.
- Human decision required: no.

### D-9 Exemptions from the old-path search

- Decision: the search excludes `specs/`, `changelog.d/`, `.specify/bugs/`, and `CHANGELOG.md`. The approved move keys in `tests/guardrails/test_performance_hook_catalog.py` and the rejection test in `tests/guardrails/test_nested_package_structure.py` keep old paths.
- Alternatives: (a) rewriting the dated records was rejected. Pull request #4607 states that the historical inventory stays unchanged, and `CHANGELOG.md` forbids edits on a feature branch. (b) Using no exemptions was rejected, because the approved move keys and the rejection test must name old paths.
- Reason: each exempt path is a dated record or a test fixture of old names.
- Risk: a new dated record names an old path. The search output lists each hit for review.
- Human decision required: no.

### D-10 Hook catalog

- Decision: `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` and `python-inventory.csv` stay unchanged. `_HISTORICAL_PATH_MOVES` gains 46 entries.
- Alternatives: (a) editing the CSV rows was rejected. The guard states the catalog is immutable, and the inventory test pins the source revision `7c4e57f3db93afda4c93ef0aec1e73c35fb7774e`. (b) Removing the hook rows was rejected, because the rows are evidence.
- Reason: the 58 rows name 47 unique old paths. `data_exporter.py` is one of them, and it stays in place, so 46 entries remain.
- Risk: a missing entry fails the guard. `T019` checks the map.
- Human decision required: no.

### D-11 Sequencing and pull request count

- Decision: wait for pull request #4813 to merge, then open one pull request.
- Alternatives: (a) three pull requests, one for each package, were possible. This record keeps one pull request, because the ratchet count changes in one step and the issue asks for one closure. The review risk is recorded as A-10 in `analysis.md`. (b) Starting now and rebasing later was rejected, because two open pull requests would edit the same test files.
- Reason: AGENTS.md states that one file cannot carry two open pull requests.
- Risk: a large review. The mitigation uses phase commits in the pull request.
- Human decision required: no.

### D-12 Branch and commit naming

- Decision: branch `chore/4168-split-rma-and-export-packages`. Commit subject and pull request title `refactor(exporting): split juniper rma and export packages`.
- Alternatives: a `refactor/` branch prefix was rejected. AGENTS.md lists the branch types `feat`, `fix`, `chore`, and `docs`.
- Reason: the commit type keeps `refactor`, which the constitution lists.
- Risk: none known.
- Human decision required: no.

### D-13 Logger and class module changes

- Decision: accept the new logger names and `__module__` values.
- Alternatives: pinning old logger names with explicit strings was rejected. It keeps old dotted names in code and adds a second name for each module.
- Reason: the move-module guidance requires a record of this change in the specification (see `plan.md`, section Logger and class module changes).
- Risk: a log filter matches an old name. `T023` searches for old logger names.
- Human decision required: no.

### D-14 Mypy override

- Decision: keep `pyproject.toml` unchanged. The wildcard `src.operations.exporting.export.*` at line 449 covers the new subpackages.
- Alternatives: listing each new package was rejected, because the list would need upkeep. If mypy reports a missing override, the list is the fallback.
- Reason: the wildcard form `src.operations.exporting.export.*` already names the package and its submodules. The claim that mypy applies it to nested packages is listed under Unverified (U-2) until `T-LOCAL-GATES` runs mypy.
- Risk: the claim fails. The fallback is listed above.
- Human decision required: no.

### D-15 Test layout

- Decision: edit imports and patch targets at the existing test paths.
- Alternatives: moving the tests with their modules was rejected. Issue #4142 owns the split of `tests/unit/`.
- Reason: FR-011 keeps the test layout unchanged.
- Risk: a merge conflict with #4142. Finding A-12 in `analysis.md` records the rebase rule.
- Human decision required: no.

### D-16 Legacy record

- Decision: do not reuse, rename, or edit `specs/numbered/0/0/1/1/3/1/3/3/4168-org-auto-upgrade-policy/`. Record the defect in `analysis.md`, and recommend a new issue for the renumber.
- Alternatives: renaming the folder to 4217 in this change was rejected. That change edits merged history outside issue #4168.
- Reason: the folder's header names issue #4217 at `plan.md` line 5. Its cited code is firmware policy code, not RMA code.
- Risk: the duplicate number stays until the new issue merges.
- Human decision required: no.

### D-17 Changelog fragment

- Decision: add `changelog.d/issue-4168-split-rma-and-export-packages.md`.
- Alternatives: editing `CHANGELOG.md` was rejected. AGENTS.md and the constitution forbid that edit on a feature branch.
- Reason: `changelog.d/README.md` names the format `issue-<number>-<slug>.md` for an issue without a pull request.
- Risk: none known.
- Human decision required: no.

## Remote verification

Each row gives one claim, its repository path, the ref `main`, the blob SHA from the remote tree, the result, and the line number from a decoded remote body. A line value of 0 means the row checks presence only.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Baseline holds the export object | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 157 |
| 2 | Baseline holds the model object | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 162 |
| 3 | Baseline holds the workflows object | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 167 |
| 4 | Guard test holds the 33 and 236 message | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 177 |
| 5 | Move-module guard exists | tests/guardrails/test_move_module_guidance.py | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 0 |
| 6 | MistHelper holds export import lines | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 581 |
| 7 | MistHelper holds the DataExporter re-export | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3373 |
| 8 | Resolver holds moved module strings | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 52 |
| 9 | Resolver holds the DataExporter string | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 54 |
| 10 | Public symbol guard exists and stays unchanged | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 0 |
| 11 | DataExporter module stays in place | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 0 |
| 12 | Run record module stays in place | src/operations/exporting/juniper_rma/model/run_record.py | main | 6931573bcc84d2d77d0d65ae0813d32be6f6d61b | present | 0 |
| 13 | Correlation workflow stays in place | src/operations/exporting/juniper_rma/workflows/correlation.py | main | 5687bf116cae51f8180242a51fb4d4e12c1cf06f | present | 0 |
| 14 | Access check workflow stays in place | src/operations/exporting/juniper_rma/workflows/access_check.py | main | ed39f4e1ad8a313041fb5fff0b46458207f75fb2 | present | 0 |
| 15 | Hook guard holds the approved move table | tests/guardrails/test_performance_hook_catalog.py | main | 36593fd74460c1023614fb84e8523303c94ea507 | present | 28 |
| 16 | Hook catalog holds export rows | specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv | main | ee7a997df2dba3086122086f16a21d4807b23509 | present | 155 |
| 17 | Python inventory is the historical record | specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv | main | 96a433783013ac8c97f6bcb01bcebdb0a067a140 | present | 0 |
| 18 | Mypy override names the export wildcard | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 449 |
| 19 | Architecture table names the export folder | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 263 |
| 20 | Menu reference generator imports the export catalog | scripts/generate_menu_wiki.py | main | f959225275536743e93bc95d37cb015865a73d53 | present | 250 |
| 21 | Web portal imports the export catalog | web_portal/services/operation.py | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 285 |
| 22 | Legacy record names issue 4217 in its header | specs/numbered/0/0/1/1/3/1/3/3/4168-org-auto-upgrade-policy/plan.md | main | 5b45f62c9eee1591967d3d7d936a54643c40a8a2 | present | 5 |
| 23 | Legacy record cites the firmware backup module | src/operations/execution/firmware_policy/backup.py | main | none | absent | 0 |
| 24 | The firmware backup module moved | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | stale | 0 |
| 25 | Legacy record cites a unit test for firmware backup | tests/unit/firmware_policy/test_backup.py | main | none | absent | 0 |
| 26 | Ratchet spec record exists | specs/numbered/0/0/1/1/2/4/3/3/4118-nested-source-package-ratchet | main | c95504ab1fd2ec05b21882f519199acf41a5a600 | present | 0 |

The table has 26 rows. `META_DIR\4168-STATUS.json` lists the same 26 checks in `remote_checks`.

## Legacy record verification

The legacy folder cites 30 repository paths. The read-only agent extracted them from the eight files. Each path is checked against the remote tree.

| Result | Count | Paths |
| - | - | - |
| Verified (present on `main` at the cited location) | 27 | Every other cited path, including `MistHelper.py`, `README.md`, `.github/copilot-instructions.md`, `scripts/generate_menu_wiki.py`, the 4 `tests/guardrails/*` test files, and the 5 `web_portal/*` paths. |
| Stale (moved on `main`) | 1 | `src/operations/execution/firmware_policy/backup.py`, moved to `recovery/backup.py` (row 24). |
| Absent (not on `main`) | 2 | `tests/unit/firmware_policy/test_backup.py` and `tests/unit/firmware_policy/test_changes.py`. The tree lists no file under `tests/unit/firmware_policy/`. |

The legacy record also names six mistapi symbols. This record does not check them, because the record is not reused (see Unverified, U-5).

Result for `existing_record` in `STATUS.json`: found true, verified 27, stale 1, absent 2.

## Sources

| Source | Local path or URL | Use |
| - | - | - |
| Governing rules | `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md` | Rules, gates, and layout |
| Templates | `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` | Headings and shape |
| Reference record | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` | Shape and depth |
| Nested guard | `tests/guardrails/test_nested_package_structure.py`, `tests/guardrails/nested_package_baseline.json` | Ratchet rules and counts |
| Move guard | `tests/guardrails/test_move_module_guidance.py` | Table rows and live job checks |
| Hook guard | `tests/guardrails/test_performance_hook_catalog.py`, `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` | Approved moves and immutable rows |
| Route | `.specify/scripts/powershell/spec-route.ps1` | Base-5 route for number 4168 |
| Quality gates | `documentation/quality-gates.md`, lines 63 and 71 | Gate job names |
| Changelog rule | `changelog.d/README.md`, line 27 | Fragment name |
| Issue and pull requests | https://github.com/jmorrison-juniper/MistHelper/issues/4168 and pull requests #4125, #4208, #4219, #4607, #4658, and #4813 | Read with `gh issue view` and `gh pr view`. The URLs were not fetched with `web_fetch`. |
| Related issues | #3824, #4118, #4142, #4217 | Read with `gh issue view` |
| Module docstrings | `src/operations/exporting/export/*.py`, `src/operations/exporting/juniper_rma/model/*.py`, `src/operations/exporting/juniper_rma/workflows/*.py` | Domain grouping |

## Unverified

- U-1: The projected guard counts (206 directories, 30 violations, and 190 total excess) come from the same measure applied to the current tree. The guard has not run after the change. `T024` verifies the counts.
- U-2: The mypy wildcard covers nested packages. The mypy run in `T-LOCAL-GATES` verifies it. Reason: no mypy run is allowed in this research step.
- U-3: `symbol-diff` handles a renamed file. The tool source is outside this repository, so the behavior is unknown. `T-LOCAL-GATES` runs the tool and records the result.
- U-4: The menu reference generators produce no diff on a second run. `T021` verifies it. Reason: no generator run is allowed in this research step.
- U-5: The six mistapi symbols named by the legacy record exist in the pinned SDK. Reason: the legacy record is not reused, so the symbols are not needed.
- U-6: No logger name assertion exists outside the names in the old-path search. `T023` verifies it with the logger search in `design/quickstart.md`, step 4.
