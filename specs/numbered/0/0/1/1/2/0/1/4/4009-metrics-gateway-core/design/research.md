# Research: Metrics Gateway Core Modules

Each decision lists the choice, the rationale, the alternatives, and the risk. Facts come from `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, the candidate commit, and read-only local checks.

## Decisions

### D-1. Build the change fresh from main

- **Decision**: Build the change on a new branch from `main`. Do not replay candidate commit `033553b3`.
- **Rationale**: Two legacy test paths are absent on main (L03 and L04). The candidate omits the hook rows (C28), the nested baseline update (C26), and the nested totals. Its guard edit conflicts with PR #4208 (C42).
- **Alternatives considered**: (a) Cherry-pick the candidate. (b) Rebase the candidate onto main. (c) Build fresh and use the candidate as a reference. The chosen option is (c).
- **Risk**: The work takes more effort. The candidate diff serves as the reference for each mechanical edit.

### D-2. Move the four modules with `git mv`

- **Decision**: Move each module with `git mv`.
- **Rationale**: Git keeps the file history. The candidate shows a similarity of 97 to 100 percent for each move.
- **Alternatives considered**: Copy the file and delete the original. This option loses the rename record.
- **Risk**: Low.

### D-3. Add no shim, alias, or fallback at the old module paths

- **Decision**: Rewrite every caller to the core path. Add no module at an old path.
- **Rationale**: AGENTS.md forbids a compatibility shim. Rows C01, C03 to C09, C11 to C13, C15, C16, C17 to C24, C28, and C33 to C37 confirm 27 active files on main that name a moved module, and each file changes.
- **Alternatives considered**: Keep stub modules that re-export the names. This option hides stale callers, and the repository rule forbids it.
- **Risk**: An external caller breaks. The assumption in `spec.md` covers this case, and U-6 records it as unverified.

### D-4. Keep the root package exports

- **Decision**: Keep every export name in the gateway `__init__.py`. Import each name from its core module.
- **Rationale**: The issue requires the root exports to remain. The `__all__` list at line 68 names them (C54).
- **Alternatives considered**: Remove the names from the root. This option breaks callers that import from the package.
- **Risk**: Low.

### D-5. Add four entries to `MODULE_PATHS`

- **Decision**: Add four entries from each old path to each core path, relative to `src`.
- **Rationale**: The guard function `current_path` resolves a moved path only through `MODULE_PATHS` or a package group. Without an entry, the guard reports a missing module (L12 and the guard file line 36).
- **Alternatives considered**: Rely on a path-limited `symbol-diff`. The guard docstring says it replaces that check for renamed files.
- **Risk**: The guard file overlaps PR #4208 (C42). Task T012 waits for the release.

### D-6. Add a structure test with exact child sets

- **Decision**: Add the test named in task T011. It asserts the exact names of the gateway children and the core children.
- **Rationale**: The issue states exact child counts. The nested ratchet counts totals, and it accepts any five children.
- **Alternatives considered**: Rely on the nested ratchet. This option does not check the names.
- **Risk**: Low.

### D-7. Remove the gateway baseline entry and set the totals

- **Decision**: Remove the gateway root entry from `nested_package_baseline.json`. Set the expected text to 32 violations and 233 total excess.
- **Rationale**: The guard rejects a stale entry, and it rejects a total that does not match (C26). A recount from the tracked files gives 190 directories, 33 violations, and 236 total excess on main. The same method gives 191, 32, and 233 after the move.
- **Alternatives considered**: Keep the entry. This option fails the guard.
- **Risk**: The recount method differs from the guard method. The recount reproduces the main totals exactly, so the risk is low.

### D-8. Update the eight hook rows

- **Decision**: Rewrite the file path in the eight active rows. Keep the inventory and the hook summary unchanged.
- **Rationale**: The #4117 contract keeps `hook-catalog.csv` active (C27). The summary holds no moved path (C30). The inventory is historical (C29).
- **Alternatives considered**: Add the four paths to `_HISTORICAL_PATH_MOVES`. That map serves immutable catalog rows. Regenerate the inventory. The contract forbids that action.
- **Risk**: Low.

### D-9. Regenerate the MIB and the menu pages

- **Decision**: Regenerate the MIB with `--mib-generate`, and regenerate the menu pages with the menu tools. Do not edit either output by hand.
- **Rationale**: The generated pages state that a person must not edit them (`scripts/menu_api_map/render/pages.py` line 20). The `--mib-check` option is the continuous integration check (`MistHelper.py` line 7450).
- **Alternatives considered**: Edit the header by hand, which the candidate did. A hand edit can drift from the generator.
- **Risk**: The generator changes lines outside the header. Task T015 stops the change when that happens.

### D-10. Let the moved loggers use the core names

- **Decision**: Keep `logging.getLogger(__name__)` in each moved module. Update the five logger assertions to the core names.
- **Rationale**: The moved modules name their loggers with `__name__`, so each logger name follows its module path. Rows C02, C51, C52, and C53 confirm the logger lines on main. The repository search finds five assertions.
- **Alternatives considered**: Pin the old logger names with explicit strings. Those names would point at no module.
- **Risk**: A log filter outside the repository names an old logger. U-7 records this risk as unverified.

### D-11. Keep the change local until the coordinator authorizes it

- **Decision**: Do not push or open a pull request until the coordinator assigns the serial slot. Also wait for PR #4208 to release the symbol guard file.
- **Rationale**: The issue states both conditions in its comments of 2026-10-31 and 2026-11-17. AGENTS.md requires a file-overlap check before work starts.
- **Alternatives considered**: Publish now. This option creates the conflict in C42.
- **Risk**: The delivery waits.

### D-12. Use the branch `chore/4009-metrics-gateway-core`

- **Decision**: Name the branch `chore/4009-metrics-gateway-core`. Use the commit type `refactor` in the subject.
- **Rationale**: AGENTS.md lists the branch types `feat`, `fix`, `chore`, and `docs`. It allows a more precise commit type.
- **Alternatives considered**: Name the branch `refactor/4009-metrics-gateway-core`. That type is not a listed branch type.
- **Risk**: Low.

### D-13. Name the changelog fragment for the issue

- **Decision**: Name the fragment `changelog.d/issue-4009-metrics-gateway-core.md`.
- **Rationale**: The copilot instructions name this form when no pull request exists yet.
- **Alternatives considered**: Name the fragment for the pull request number. No pull request exists yet.
- **Risk**: Low.

### D-14. Keep the candidate commit and its archive branch

- **Decision**: Do not delete commit `033553b3` or the archive branch until a replacement merges. Record a preservation proof then.
- **Rationale**: AGENTS.md requires a preservation proof before the closure of unmerged work. C43 and C44 confirm that the archive holds the commit.
- **Alternatives considered**: Delete the archive branch now. The branch is the only remote evidence of the candidate.
- **Risk**: Branch clutter remains until the merge.

### D-15. Read "public symbol map" as the `MODULE_PATHS` mapping

- **Decision**: Treat the issue term as the `MODULE_PATHS` mapping in the symbol guard.
- **Rationale**: The repository search found no other map that names the moved modules.
- **Alternatives considered**: Create a new map file. A second map drifts from the guard.
- **Risk**: The issue author meant another file. The coordinator can redirect the change.

### D-16. Comment each changed line and add no new action logging

- **Decision**: Add an inline comment to each changed Python line. Add no action logging to an import-only edit.
- **Rationale**: Principle VI requires inline comments on changed lines. Principle VII applies to new actions. The changed lines are import statements and path strings.
- **Alternatives considered**: Add logging to each touched test function. The logging would record no action.
- **Risk**: A reviewer requests logging in a test function. Finding A13 in `analysis.md` records the reason.

### D-17. Place supporting files under `design/`

- **Decision**: Place the research, the data model, the quickstart, the contract, and the checklist under `design/`.
- **Rationale**: The five-item rule limits the feature root to five children. The root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
- **Alternatives considered**: Place the design files at the root. That placement exceeds the limit.
- **Risk**: Low.

## Linked Work

| Item | State | Evidence |
| - | - | - |
| Issue #4009 | Open | Labels `refactor` and `src`. Last update on 2026-11-17. Source: https://github.com/jmorrison-juniper/MistHelper/issues/4009 |
| Issue #3824 | Open | Parent issue. Title: "Refactor: reduce nested source package child counts." |
| Issue #4117 | Closed on 2026-10-19 | Contract for the performance artifacts. Closed by PR #4306. |
| PR #4306 | Merged on 2026-10-19 | "chore(tests): define performance catalog artifact contract." 11 files. |
| PR #4208 | Open | Head `jmorrison-juniper-4200-migrate-mistwanperformance`. Changes `tests/guardrails/test_src_public_symbol_preservation.py`. 82 files in total. |
| PR #4557 | Merged on 2026-11-05 | "refactor(websocket): move utility text into catalog utilities." Named in the issue comments. |
| PR #4607 | Merged on 2026-11-13 | "refactor(troubleshooting): relocate modules to cohesive packages." Named in the issue comments. |
| PR #3873 | Merged on 2026-10-06 | Dependency update. It matched the search text only. |
| Open pull requests | 7 open | Only PR #4208 changes a file in the overlap pattern. |
| Candidate commit `033553b3` | Exists on GitHub | Head of `archive/laptop-20261121/jmorrison-juniper-refactor/4009-metrics-gateway-core`. No pull request names it. |
| Issue #2448 | Closed on 2026-09-12 | Title: "[Poliwag] Local Git cleanup." The folder `2448-misthelper-performance-monitoring` does not link to this issue. |

## Remote Verification

Method: One call to `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` returned 11,404 entries, and the tree was not truncated. The blob SHA of each path came from that tree. Each line number came from the decoded body of the contents endpoint for that file, with `?ref=main`. The filter ran in memory over the same tree call. The `--jq` form in the brief was not used, because PowerShell broke its regular expression quoting. Commit and pull request checks used `gh api` and `gh pr view`. No HTTP 403 or 429 response occurred, so no retry ran.

Source values: Current rows use the blob SHAs from the tree. Legacy rows use the claim text of the legacy record in commit `033553b3`. The local line numbers match the remote line numbers for each checked file.

| ID | Source | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - | - |
| C01 | Current | cache.py at its old path imports catalog, collector, and samples | src/interfaces/monitoring/metrics_gateway/cache.py | main | d549c23ee8fc8fb55e059c00a08060a4f1051d16 | present | 28 |
| C02 | Current | catalog.py at its old path sets a `__name__` logger | src/interfaces/monitoring/metrics_gateway/catalog.py | main | 43bacaefc1e1d3fab3532405b42af6238a631813 | present | 35 |
| C03 | Current | collector.py at its old path imports catalog and samples | src/interfaces/monitoring/metrics_gateway/collector.py | main | 1b9ce53054222c61ebc0d42208741058faba9484 | present | 28 |
| C04 | Current | samples.py at its old path imports catalog | src/interfaces/monitoring/metrics_gateway/samples.py | main | 6fc75a57ab664d0bf7472c79286db130e9acb94f | present | 19 |
| C05 | Current | Gateway `__init__.py` imports the four moved modules | src/interfaces/monitoring/metrics_gateway/__init__.py | main | a77d0509169b386e89e82af025d17d861d84d6a7 | present | 26 |
| C06 | Current | prometheus.py stays at the root and imports catalog and samples | src/interfaces/monitoring/metrics_gateway/prometheus.py | main | fa73e9523cd46dbe52c6ae15f1ef7338678ddedb | present | 25 |
| C07 | Current | service.py stays at the root and imports cache and collector | src/interfaces/monitoring/metrics_gateway/service.py | main | df1013a9c52eeda83f6061231aa812adf76485cf | present | 22 |
| C08 | Current | snmp.py stays at the root and imports catalog, samples, and cache | src/interfaces/monitoring/metrics_gateway/snmp.py | main | 6861023495ac0edf1326f64395995aa8eb030997 | present | 39 |
| C09 | Current | web.py stays at the root and imports cache | src/interfaces/monitoring/metrics_gateway/web.py | main | c3ffcb10c910ada334c3b0f7868fd8fe1b472c46 | present | 16 |
| C10 | Current | The core package directory is absent | src/interfaces/monitoring/metrics_gateway/core/ | main | none | absent | 0 |
| C11 | Current | The MIB generator docstring names the catalog path | src/operations/hardware/mib_generator/__init__.py | main | cefb36bd3abe26e7d196345a646629a6b3eac608 | present | 14 |
| C12 | Current | assignment.py imports the catalog | src/operations/hardware/mib_generator/assignment.py | main | e1b5b9cba2a9b3b46f91ef9a57be5562e5224401 | present | 24 |
| C13 | Current | mib.py imports the catalog | src/operations/hardware/mib_generator/mib.py | main | 54283f4e3c9a6301b9506c0591d0a6530f24ff78 | present | 22 |
| C14 | Current | mib.py template writes the catalog path into the MIB header | src/operations/hardware/mib_generator/mib.py | main | 54283f4e3c9a6301b9506c0591d0a6530f24ff78 | present | 428 |
| C15 | Current | runner.py imports the catalog | src/operations/hardware/mib_generator/runner.py | main | db5583d778b0ecd866bce05b82ecaaa9d2af834a | present | 17 |
| C16 | Current | schema.py imports the catalog | src/operations/hardware/mib_generator/schema.py | main | 2784719c200dfb04d62c4fa51f3d0e09f4873cf2 | present | 22 |
| C17 | Current | The generated-MIB agent contract imports the catalog | tests/contract/test_generated_mib_matches_agent.py | main | a642e1eeeac1b2a1b10fed1174489d8cda7bdc1c | present | 17 |
| C18 | Current | The MIB catalog contract imports the catalog | tests/contract/test_mib_matches_catalog.py | main | 626f8103c7cf1f6f906ec9cf31822330e6da6335 | present | 26 |
| C19 | Current | The collector unit test imports from line 10 and asserts a logger at line 221 | tests/unit/maps/interfaces/monitoring/metrics_gateway/test_collector.py | main | 96eceb13f0c15d60b483f28f4c11965caa99f540 | present | 10 |
| C20 | Current | The prometheus and cache unit test imports from line 9 and asserts loggers at lines 151 and 347 | tests/unit/maps/interfaces/monitoring/metrics_gateway/test_prometheus_and_cache.py | main | 79cdacd28f55e3f5d06b93e2e0ceb9e75da9cdb7 | present | 9 |
| C21 | Current | The SNMP and service unit test imports from line 11 and asserts loggers at lines 59 and 70 | tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_and_service.py | main | 0cddb8a6d2fdd3556c063210a960af7c2133c1b5 | present | 11 |
| C22 | Current | The SNMP integration unit test imports the cache and collector | tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_integration.py | main | 251e1b5de8b1e4e148de798c9f93e5d5a49f6c60 | present | 45 |
| C23 | Current | The MIB generator unit test imports the catalog | tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_mib_generator.py | main | b60d7e24d0b5bd29334c33d2cb530c28fab986af | present | 16 |
| C24 | Current | The MIB properties unit test imports the catalog | tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_properties.py | main | 4e92b32126e53d690e7ade928769a9d27ae42d0a | present | 16 |
| C25 | Current | The structure guard defines visible_children | tests/guardrails/test_src_domain_structure.py | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | present | 75 |
| C26 | Current | The nested guard test expects 33 violations and 236 total excess | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 177 |
| C27 | Current | The hook guard reads hook-catalog.csv | tests/guardrails/test_performance_hook_catalog.py | main | 36593fd74460c1023614fb84e8523303c94ea507 | present | 199 |
| C28 | Current | The hook catalog holds eight active rows that name the moved modules | specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv | main | ee7a997df2dba3086122086f16a21d4807b23509 | present | 266 |
| C29 | Current | The historical inventory exists and must not be regenerated | specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv | main | 96a433783013ac8c97f6bcb01bcebdb0a067a140 | present | 0 |
| C30 | Current | The hook summary holds no moved module path | specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog-summary.json | main | 115a4e16d6fa308b4cf913b8588846d55aed5de5 | present | 0 |
| C31 | Current | The quickstart names inventory source revision 7c4e57f3 | specs/2448-misthelper-performance-monitoring/quickstart.md | main | 8fc4bdc86e3463b7be747e613af7471b4bc65570 | present | 6 |
| C32 | Current | The inventory source revision exists on GitHub | specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv | 7c4e57f3db93afda4c93ef0aec1e73c35fb7774e | none | present | 0 |
| C33 | Current | The MIB guide names the catalog path | documentation/mib_generator.md | main | 208324223684c698a9e8c9224d75a4b9919e1167 | present | 13 |
| C34 | Current | The generated MIB header names the catalog path | documentation/mibs/MISTHELPER-MIB.mib | main | 5803cfca32706552442833ccc7aa5bd7b0cd47ce | present | 20 |
| C35 | Current | The generated interactive-safe page links the collector path | documentation/menu-api/interactive-safe.md | main | 57b580ddc1c4b9fe4971c72fb26a592764e7ac53 | present | 1149 |
| C36 | Current | The generated interactive-safe wiki page links the collector path | documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md | main | 4a8af3e00177b136124c62e47bb0fb87caebeb96 | present | 1149 |
| C37 | Current | The Observium script comment names the catalog path | container/observium/20-add-mist-static-sensors.sh | main | 80e8dd5c4cbfc670fdec935785d00ca96749c11d | present | 120 |
| C38 | Current | The collector imports the mistapi orgs stats module | src/interfaces/monitoring/metrics_gateway/collector.py | main | 1b9ce53054222c61ebc0d42208741058faba9484 | present | 157 |
| C39 | Current | The pinned SDK defines the three stats functions | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local .venv | none | present | 17 |
| C40 | Current | The installed mistapi distribution is version 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local .venv | none | present | 0 |
| C41 | Current | The main branch head is f03c6c9b36d612a48d7b9652998c2fd87dd777ca | refs/heads/main | main | none | present | 0 |
| C42 | Current | Open PR #4208 changes the symbol guard file | tests/guardrails/test_src_public_symbol_preservation.py | PR #4208 | none | present | 0 |
| C43 | Current | The archive branch holds the candidate commit and its legacy record | specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/spec.md | refs/heads/archive/laptop-20261121/jmorrison-juniper-refactor/4009-metrics-gateway-core | none | present | 0 |
| C44 | Current | The candidate commit exists on GitHub | specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/spec.md | 033553b3d83b1a30e3c1745c9d6c2fb658f9205f | none | present | 0 |
| C45 | Current | The changelog policy test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| C46 | Current | The menu generator script exists | scripts/generate_menu_wiki.py | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| C47 | Current | The menu map entry point exists | scripts/menu_api_map/__main__.py | main | 19f72aa767a1821f2ccf88680b8778b89012873d | present | 0 |
| C48 | Current | The Mist OpenAPI JSON input is tracked on main | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| C49 | Current | The OID ledger input is tracked on main | data/mib_generator/oid_assignments.json | main | 883178068836b7f9e636d2ba19c87bfa59729fba | present | 0 |
| C50 | Current | The allowlist input is tracked on main | data/mib_generator/allowlist.json | main | d014bd95a4c0dff35c804454d6720761cffb4fa5 | present | 0 |
| C51 | Current | cache.py names its logger with `__name__` | src/interfaces/monitoring/metrics_gateway/cache.py | main | d549c23ee8fc8fb55e059c00a08060a4f1051d16 | present | 32 |
| C52 | Current | collector.py names its logger with `__name__` | src/interfaces/monitoring/metrics_gateway/collector.py | main | 1b9ce53054222c61ebc0d42208741058faba9484 | present | 31 |
| C53 | Current | samples.py names its logger with `__name__` | src/interfaces/monitoring/metrics_gateway/samples.py | main | 6fc75a57ab664d0bf7472c79286db130e9acb94f | present | 21 |
| C54 | Current | The gateway `__all__` list names the root exports | src/interfaces/monitoring/metrics_gateway/__init__.py | main | a77d0509169b386e89e82af025d17d861d84d6a7 | present | 68 |
| L01 | Legacy | The core module file cache.py exists under core/ | src/interfaces/monitoring/metrics_gateway/core/cache.py | main | none | absent | 0 |
| L02 | Legacy | core/__init__.py exists | src/interfaces/monitoring/metrics_gateway/core/__init__.py | main | none | absent | 0 |
| L03 | Legacy | Gateway unit tests live under tests/unit/metrics_gateway | tests/unit/metrics_gateway/test_collector.py | main | none | stale | 0 |
| L04 | Legacy | MIB unit tests live under tests/unit/mib_generator | tests/unit/mib_generator/test_mib_generator.py | main | none | stale | 0 |
| L05 | Legacy | The changelog fragment exists | changelog.d/issue-4009-metrics-gateway-core.md | main | none | absent | 0 |
| L06 | Legacy | The structure test for gateway children exists | tests/guardrails/test_src_domain_structure.py | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | absent | 0 |
| L07 | Legacy | MODULE_PATHS names the four moved modules | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | absent | 0 |
| L08 | Legacy | The routed record exists on main | specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/spec.md | main | none | absent | 0 |
| L09 | Legacy | MistHelper.py imports root service, web, and SNMP modules | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7093 |
| L10 | Legacy | The web module stays at the gateway root | src/interfaces/monitoring/metrics_gateway/web.py | main | c3ffcb10c910ada334c3b0f7868fd8fe1b472c46 | present | 16 |
| L11 | Legacy | The plan names Python 3.13 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 23 |
| L12 | Legacy | The public symbol guard file exists to extend | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 36 |

The table holds 66 remote checks: 54 current checks and 12 legacy checks.

## Legacy Record Verification

- The legacy record lives only in commit `033553b3` and its archive branch. It does not exist on main or in the working tree.
- The 12 legacy checks give 3 verified, 3 stale, and 6 absent results. Verified: L09, L10, and L12. Stale: L03, L04, and L11. Absent: L01, L02, L05, L06, L07, and L08.
- The stale claims are the Python 3.13 pin and the two test paths. The absent claims cover the core modules, the core initializer, the changelog, the structure test, the symbol guard entries, and the routed record.
- The legacy record cannot count as proof. Its tasks T001 to T006 carry the `[X]` mark, and main holds none of their artifacts.

## Local Evidence (Read-Only)

- `git show --name-status 033553b3` lists 34 changed paths in the candidate.
- `git for-each-ref --contains 033553b3` lists `refs/remotes/origin/archive/laptop-20261121/jmorrison-juniper-refactor/4009-metrics-gateway-core`.
- `git merge-base --is-ancestor 033553b3 origin/main` exits with status 1, so the candidate is not on the local main ref.
- The local `main` ref and `origin/main` both point at `f03c6c9b3`. The remote `main` head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, the same commit. So the local tracked files equal the remote tree for this commit.
- `git status --porcelain` lists five unrelated modified files: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, and two test files. The implementation does not stage these files.
- The recount of `git ls-files src/**/*.py` gives 930 Python files, 190 directories, 33 violations, and 236 total excess. These values match the expected text in C26. The gateway root counts 8 children, and the MIB generator root counts 5.

## Linked Pull Request Scope

- Only the open PR #4208 changes a file that this change also changes.
- Each other open pull request changes no gateway, MIB, guard, hook, or menu file.

## Sources

Local paths:

- `AGENTS.md`, read in full.
- `.github/copilot-instructions.md`, read in full. The local gates table and the Spec Kit rules came from this file.
- `.specify/memory/constitution.md`, read in full. Version 1.9.0.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`, the reference record. Its shape came from the headings and from the `design/` layout.
- `.specify/scripts/powershell/spec-route.ps1`, which computes the route with `Get-SpecRadixSegments`.
- `documentation/quality-gates.md`, read in full.
- `documentation/architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md`, searched for the gateway, MIB, port, and module terms. None of the four names a moved module path. `architecture.md` line 227 shows an older package layout, and it is out of scope.
- `scripts/menu_api_map/render/pages.py` line 20, which holds the generated-page notice.
- `MistHelper.py` lines 7426 to 7456, which define the `--mib-*` options.
- `tests/guardrails/test_src_public_symbol_preservation.py`, `test_src_domain_structure.py`, `test_nested_package_structure.py`, `test_performance_hook_catalog.py`, and `nested_package_baseline.json`, read for the guard logic.
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py`, read for the function lines in C39.
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`, read for the installed version in C40.

Remote sources:

- Issue #4009 and its comments: https://github.com/jmorrison-juniper/MistHelper/issues/4009
- PR #4208: https://github.com/jmorrison-juniper/MistHelper/pull/4208
- PR #4306: https://github.com/jmorrison-juniper/MistHelper/pull/4306

Mist API:

- No endpoint behavior claim appears in this record. The OpenAPI file is not cited. The coverage files `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md` were searched for the moved module names, and no match appeared.

Skills:

- No skill loaded. The issue has no Podman question and no Juniper device question.

Upstream checks:

- None. No upstream URL was fetched.

## Unverified

- U-1: The MIB regeneration output is unverified. The spec phase forbids the generator run.
- U-2: The menu regeneration output is unverified. The spec phase forbids the generator run.
- U-3: The test outcomes after the change are unverified. The spec phase forbids test runs.
- U-4: The `symbol-diff` behavior for renamed files is unverified. The tool did not run.
- U-5: The test-quality analyzer result for the edited guard file is unverified. The analyzer did not run.
- U-6: External callers of the old module paths are unverified. No source outside the repository was available.
- U-7: Log filters outside the repository that name an old logger are unverified. No search outside the repository ran.
- U-8: The STE scores of the new Markdown files are unverified. The linter did not run. Task T021 runs it.
