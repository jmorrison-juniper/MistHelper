# Research: WLAN fixture host teardown

This file holds the evidence, the gate analysis, the decisions, the remote verification table, and the unverified items. Row IDs R-01 to R-77 match the `remote_checks` array in `4492-STATUS.json`.

## 1. How the leak starts

- The `fake_mh` fixture at lines 37 to 46 calls `_MH.bind_root_module(fake)` at line 45 (R-01). It yields with no restore of the resolver host.
- The `patch.dict` call restores `sys.modules` at teardown. Nothing restores `_root_module`.
- `root_module()` returns `_root_module` (R-05). `_mh_module()` returns `root_module()` (R-08). The named test reads `module.__name__` (R-09). The CI log shows `AttributeError: __name__` for that read (R-41).
- `_get_debug_mode` reads `args` from the dependency host (R-10). The resolver reads the fake host through its mock path (R-06). The named test asserts `False`, and the CI log shows `<MagicMock name='mock.args.debug'>` (R-11, R-41).
- The real module is bound at import (R-12, R-13). The restore must return the real module, not `None`.

## 2. Why main CI passes

- Pytest sorts directory entries by name (R-37). Pytest keeps the order of explicit command-line arguments (R-38).
- On the PR branch, the WLAN file lived under the `tests/unit/config` tree (R-03). That path sorts before `tests/unit/export`, `tests/unit/prod_readiness`, and `tests/unit/refactors`. All 21 failing IDs sit in those three directories (section 3).
- On main, the file lives at `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` (R-01). Within that directory, the WLAN file sorts after `test_initialize_mist_session.py` and `test_tui_launcher.py`. The export and prod_readiness tests run earlier.
- The main root-units run passed (R-40). The defect is latent, not fixed.
- The issue reproduction puts the WLAN file first on the command line. Explicit order keeps that order (R-38), so the reproduction fails.
- Linux CI uses the same sorted order. This is an inference (U-3).

## 3. Regression set

The 21 failing IDs from the PR-branch root-units shard (R-41). The summary line reports `21 failed, 25017 passed, 24 skipped, 76 warnings in 1080.82s`.

| # | Test ID | Error text in the CI log |
| - | - | - |
| 1 | `tests/unit/export/test_count_exporter.py::test_choose_rejects_a_non_numeric_answer` | `OSError: pytest: reading from stdin while output is captured!` |
| 2 | `tests/unit/export/test_count_exporter.py::test_choose_rejects_an_out_of_range_answer` | `OSError: pytest: reading from stdin while output is captured!` |
| 3 | `tests/unit/export/test_count_exporter.py::test_choose_returns_the_selected_operation` | `OSError: pytest: reading from stdin while output is captured!` |
| 4 | `tests/unit/export/test_count_exporter.py::test_persist_routes_the_operation_name_to_the_exporter` | `TypeError: cannot unpack non-iterable NoneType object` |
| 5 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py::TestInventoryAPIDataFetcherWiring::test_creates_fetcher_with_correct_params` | `SystemExit: 1` |
| 6 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py::TestInventoryAPIDataFetcherWiring::test_calls_execute_exactly_once` | `SystemExit: 1` |
| 7 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py::TestInventoryAPIDataFetcherWiring::test_handles_empty_api_response` | `SystemExit: 1` |
| 8 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py::TestInventoryProgressEmitter::test_emits_start_and_complete` | `SystemExit: 1` |
| 9 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py::TestInventoryProgressEmitter::test_handles_no_emitter_gracefully` | `SystemExit: 1` |
| 10 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsAPIDataFetcherWiring::test_creates_fetcher_with_correct_params` | `SystemExit: 1` |
| 11 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsAPIDataFetcherWiring::test_calls_execute_exactly_once` | `SystemExit: 1` |
| 12 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsAPIDataFetcherWiring::test_handles_empty_api_response` | `SystemExit: 1` |
| 13 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsProgressEmitter::test_emits_start_and_complete` | `SystemExit: 1` |
| 14 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsProgressEmitter::test_handles_no_emitter_gracefully` | `SystemExit: 1` |
| 15 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsFastMode::test_fast_mode_cache_miss_stale_file` | `SystemExit: 1` |
| 16 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsFastMode::test_fast_mode_cache_miss_no_file` | `SystemExit: 1` |
| 17 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsFastMode::test_fast_mode_disabled_by_default` | `SystemExit: 1` |
| 18 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py::TestDeviceStatsDynamicLookback::test_dynamic_lookback_value_passed_to_fetcher` | `SystemExit: 1` |
| 19 | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_19_device_port_stats.py::TestDevicePortStatsOrchestration::test_non_fast_mode_uses_api_data_fetcher` | `SystemExit: 1` |
| 20 | `tests/unit/refactors/test_initialize_mist_session.py::TestMhModule::test_returns_misthelper_module` | `AttributeError: __name__` at the assertion `module.__name__ == "MistHelper"` (line 57, R-09) |
| 21 | `tests/unit/refactors/test_tui_launcher.py::TestGetDebugMode::test_returns_false_when_args_absent` | `AssertionError: assert <MagicMock name='mock.args.debug' id='140564443284544'> is False` (line 180, R-11) |

The three-node sequence in quickstart Scenario 2 is the WLAN module plus IDs 20 and 21.

## 4. Path and state

- The issue path is absent on main (R-02). The same blob exists at the CI commit (R-03). PR #4358 moved the file and merged on 2026-11-13 (R-43).
- Only the WLAN fixture calls `bind_root_module` without a restore. The other seams restore their values. Three use monkeypatch (R-20, R-21, R-76). One uses a patch fixture (R-22). Startup binding is intentional (R-13). See U-9 for the search scope.
- The resolver keeps `_root_module` on the instance during writes (R-07). A `patch.object` call with a string attribute name uses the same write path.

## 5. Baseline and analyzer

- The canonical key holds `line_number` (R-24). The gate counts keys absent from the baseline and exits 1 when that count is above zero (R-25).
- The WLAN file has nine baseline entries (R-23). Two are file-level entries at line 1: `missing_fm_http_4xx` and `missing_fm_http_5xx`. Seven are `weak_zero_assertions` entries at lines 351, 694, 729, 737, 807, 817, and 841.
- The fixture change adds four lines above all seven entries. Each key changes unless its line number moves by four (D-4).

## 6. Gate applicability

| Gate | Applies | Reason |
| - | - | - |
| Compile (`python -m py_compile MistHelper.py`) | No | `MistHelper.py` does not change. |
| Lint (`python -m ruff check .`) | Yes | The changed test file is in scope. The line length is 120 (R-35). |
| Format (`python -m black --check .`) | Yes | The changed test file is in scope. The line length is 120 (R-36). |
| Types (mypy) | No | `MYPY_PATHS` excludes tests (R-28). |
| Tests (`python -m pytest` on the changed file) | Yes | The changed test file is the unit under change (R-57). |
| Full tests (two pytest-chunks commands) | Yes | The root-units shard failed on the PR branch (R-41, R-58). |
| Safe sweep | No | The change touches no product code. |
| Coverage | Yes | The CI coverage gate failed on the PR branch (R-42). Run it or rely on CI (U-6). |
| Test quality | Yes | The changed test file and the baseline change (R-25, R-26, R-59). |
| Complexity (radon) | No | `RADON_PATHS` excludes this test file (R-32). |
| Security lint (bandit) | No | Bandit excludes tests in configuration (R-34), and CI runs that configuration (R-33). |
| Dependency audit | No | No dependency changes. |
| Code quality (pylint) | No | The gate runs on `src/` only (R-57, line 69 of the gate table). |
| Dead code (vulture) | No | `VULTURE_PATHS` excludes tests (R-29). |
| Docstrings (pydocstyle, interrogate) | No | `PYDOCSTYLE_PATHS` (R-30) and `INTERROGATE_PATHS` (R-31) exclude tests. |
| Menu reference | No | No menu file changes. |
| Symbols (`symbol-diff`) | Yes | The changed Python file is in scope (R-57, line 73). Expected result: no removed module-level name. |
| STE (`ste-linter`) | No | The STE gate covers five named files (R-60). This test file and this record are outside that list. |
| Ops portal and ops platform | No | No ops file changes. |
| Playwright end-to-end | No | No `tests/e2e` file changes. |

## 7. Decisions

Each decision has one chosen option, the alternatives, the reason, and the risk. No decision needs a human (`human_decision_required` is false for all rows).

### D-1 Scope: repair the fixture only

- Chosen: Change the `fake_mh` fixture in the WLAN module. Make no production change.
- Alternatives: (a) Add an unbind method to the resolver. (b) Add a conftest autouse fixture that restores the resolver host for every test. Issue #2892 used that pattern for `ConfigUtils` (R-14, line 61).
- Reason: One fixture causes the leak (R-01). The issue states that production code needs no change. AGENTS requires repair of the leaking test (R-53).
- Risk: A future fixture can repeat the leak. A follow-up issue owns a conftest guard.

### D-2 Restore mechanism

- Chosen: Use `patch.object(_MH, "_root_module", fake)` inside the same `with` block as the existing `patch.dict`.
- Alternatives: (a) A `try` and `finally` block that rebinds the saved value. (b) `monkeypatch.setattr` with a new fixture parameter.
- Reason: `patch.object` saves the prior value and restores it on exit. The same file already uses `patch.object` in the `api` fixture at line 53.
- Risk: The write touches a private attribute. The resolver keeps that write on the instance (R-07).

### D-3 Logging

- Chosen: One `info` line before the bind and one `debug` line after the restore.
- Alternatives: (a) No log lines. (b) Log lines that keep the line count. Each statement adds a line, so (b) is not feasible.
- Reason: Principle VII is non-negotiable (R-65). AGENTS requires logging when a touched block has none (R-54).
- Risk: Seven baseline entries move (D-4).

### D-4 Baseline line numbers

- Chosen: Edit the seven WLAN `line_number` values by +4.
- Alternatives: (a) Regenerate the baseline with `--write-baseline`. (b) Leave the values unchanged.
- Reason: Option (b) creates seven new findings, because each key includes `line_number` (R-24, R-25). Option (a) rewrites 733 entries and can hide unrelated drift. The targeted edit moves only the keys that changed.
- Risk: Black can change the measured line count (U-8). The gate proves the result.

### D-5 Regression proof

- Chosen: Add no test. Use the three-node sequence, the 21 named IDs, and a mutation proof.
- Alternatives: (a) An autouse teardown guard in the WLAN module. (b) A helper context manager with a direct test. (c) Two order-dependent tests.
- Reason: Options (a) and (b) add module-level names, which affects the symbol gate. Option (a) also adds a baseline shift. Option (c) depends on test order. The named tests already fail on the PR branch (R-41), so they can fail.
- Risk: No guard exists. D-1 names the follow-up.

### D-6 File path

- Chosen: Edit `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`.
- Alternatives: Restore the file at the issue path.
- Reason: The issue path is absent on main (R-02). PR #4358 moved the file (R-01, R-03). A restored copy would duplicate the moved file.
- Risk: A reviewer may expect the issue path. The PR body states the path change.

### D-7 Other failing tests

- Chosen: Change no other test in this PR.
- Alternatives: Repair each of the 19 other failing tests now.
- Reason: The causal path for those tests is unverified (U-1). AGENTS requires one concern in each pull request (R-53).
- Risk: A residual failure remains after the fix. The implementer files a new issue for it.

### D-8 Issue closure

- Chosen: Keep issue #4492 open until the merge. The PR body contains `Closes #4492` (R-55).
- Alternatives: Close the issue now.
- Reason: The owner comment of 2026-11-09 requires independent verification. PR #4358 merged without closing the issue.
- Risk: The merge closes the issue before the main run finishes. T-MERGE checks the main run and reports any failure.

### D-9 Labels and review

- Chosen: Add `in-progress` when the implementation claims the issue. Keep `bug`, `tests`, and `needs-human-review`. Merge only after a human review.
- Alternatives: Remove `needs-human-review`.
- Reason: The owner sets that label, and its description requires a human review before merge. The rule on auto-merge applies to destructive changes (R-56). This change touches no destructive operation.
- Risk: The merge waits for review. The orchestrator tracks that wait.

### D-10 Gates

- Chosen: Run the gates that apply to a test-only change. Name the reason for each skipped gate.
- Alternatives: Run all quality jobs locally.
- Reason: Most gates read `src/` or `MistHelper.py` only (R-28 to R-33). The root-units shard (R-27) and the analyzer (R-26) cover the changed behavior.
- Risk: A skipped gate can hide a defect. The skip reasons cite the rows in section 6.

### D-11 Changelog

- Chosen: Add no changelog fragment.
- Alternatives: Add a fragment under `changelog.d/`.
- Reason: The change alters no operator-visible behavior. The repository rule covers a change that a user sees (R-73).
- Risk: None known.

### D-12 Branch and title

- Chosen: Branch `fix/4492-wlan-fixture-host-teardown`. Title `fix(tests): restore the resolver host after the WLAN fixture`.
- Alternatives: Use the `test` type for the commit.
- Reason: The branch name uses the type and the issue number (R-72). Commits use Conventional Commits (R-74). `fix` names the defect.
- Risk: None known.

### D-13 Record location

- Chosen: `specs\numbered\0\0\1\2\0\4\3\2\4492-wlan-fixture-host-teardown`.
- Alternatives: A timestamp route under `specs\live\`.
- Reason: Numbered records use the eight-level base-5 route (R-61). The eight digits of 4492 in base 5 are 0, 0, 1, 2, 0, 4, 3, 2 (R-51, R-52). The route has no existing directory at the leaf (R-48).
- Risk: A wrong digit changes the path. Quickstart Scenario 1 checks the route with the repository script.

## 8. Remote verification

Each row is one check. The count of rows matches `remote_checks` in `4492-STATUS.json`. Result `present` means the path or object exists. Result `absent` means it does not exist. Result `stale` means the commit exists but is not in the history of `main`. Local-venv rows point to installed packages, not repository paths.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | WLAN fixture binds the resolver host without a restore | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 45 |
| R-02 | Issue path of the WLAN fixture is absent on main | tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py | main | none | absent | 0 |
| R-03 | Issue path of the WLAN fixture existed at CI commit d53e5626 | tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py | d53e5626f381d6ce1d8024859a9cffa91e072e69 | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 0 |
| R-04 | Resolver stores the host in `_root_module` | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 131 |
| R-05 | Resolver `root_module()` returns the stored host | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 142 |
| R-06 | Resolver mock-host read returns fake attributes | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 252 |
| R-07 | Resolver write keeps `_root_module` on the instance | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 178 |
| R-08 | `_mh_module` returns the resolver root module | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 149 |
| R-09 | Named test asserts the module name `MistHelper` | tests/unit/refactors/test_initialize_mist_session.py | main | e5c3a34b490ec082e0d4fc5aeacab99778d8ffbe | present | 57 |
| R-10 | `_get_debug_mode` reads args from the dependency host | src/foundation/support/refactors/tui_launcher.py | main | 4bb4eef81ec63bd78051f35b89417df856ec7452 | present | 130 |
| R-11 | Named test asserts debug is False when args is absent | tests/unit/refactors/test_tui_launcher.py | main | 270a3763c08dd737c9430b83f3abef68e28228c0 | present | 180 |
| R-12 | `MistHelper.py` binds its module as the host at import, and conftest preloads it | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 712 |
| R-13 | `MainEntrypoint.bind_host_module` calls `bind_root_module` | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 375 |
| R-14 | Root conftest resets ConfigUtils state and has no resolver-host reset | tests/conftest.py | main | f55885cafab8f4c346ee7d7a813835bab300e45d | present | 61 |
| R-15 | Failing file `test_count_exporter.py` exists | tests/unit/export/test_count_exporter.py | main | abd5134dbca0f948823607b8a13d0776af3b3b72 | present | 0 |
| R-16 | Failing file `test_menu_12_inventory.py` imports MistHelper | tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py | main | bf29ff0145f237b465fc5eb2ce967bb8b0242fc0 | present | 15 |
| R-17 | Failing file `test_menu_13_device_stats.py` replaces the resolver seam | tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py | main | 7f61d0791f4fd8996a636ef03536b69660f08dd9 | present | 22 |
| R-18 | Failing file `test_menu_19_device_port_stats.py` replaces the resolver seam | tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_19_device_port_stats.py | main | ecc35dea3b31dc0b6c5fe4e71a84e2ba5d5ca4a7 | present | 11 |
| R-19 | `org_inventory_exporter` reads dependencies through the resolver | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 78 |
| R-20 | Another test patches the resolver host through monkeypatch | tests/unit/marvis/mist/resources/site/rrm_reset/test_rrm_dry_run_policy.py | main | 27f79e6e2888c566fcd11f8a0433d77de4c6a63e | present | 43 |
| R-21 | Another test patches the resolver host through monkeypatch | tests/unit/container/output_defaults/test_contract.py | main | fcc94f2064a357b9107351cca7a0dea2cb6e9e27 | present | 213 |
| R-22 | A support seam patches the resolver host through a patch fixture | tests/support/wip_target_controls/native.py | main | bdea5b10003eed53be35c160b519afbec166d3f0 | present | 194 |
| R-23 | Baseline holds the WLAN weak-assertion entries | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 351 |
| R-24 | Analyzer canonical key includes `line_number` | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py | local-venv | not applicable | present | 55 |
| R-25 | Analyzer gate exits 1 when new findings exist | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py | local-venv | not applicable | present | 235 |
| R-26 | CI runs the test-quality gate command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| R-27 | CI matrix holds the root-units shard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 262 |
| R-28 | CI `MYPY_PATHS` excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-29 | CI `VULTURE_PATHS` excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-30 | CI `PYDOCSTYLE_PATHS` excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-31 | CI `INTERROGATE_PATHS` excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-32 | CI `RADON_PATHS` excludes this test file | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| R-33 | CI bandit step scans the repository root with pyproject configuration | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| R-34 | Pyproject bandit `exclude_dirs` holds tests | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 503 |
| R-35 | Ruff line length is 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| R-36 | Black line length is 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 559 |
| R-37 | Pytest sorts directory entries by name | .venv\Lib\site-packages\_pytest\pathlib.py | local-venv | not applicable | present | 1012 |
| R-38 | Pytest keeps the order of command-line arguments | .venv\Lib\site-packages\_pytest\main.py | local-venv | not applicable | present | 1241 |
| R-39 | mistapi is pinned at version 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | not applicable | present | 3 |
| R-40 | Main CI root-units shard passed on head f03c6c9b (run 45774119357) | repos/jmorrison-juniper/MistHelper/actions/runs/45774119357/jobs | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | not applicable | present | 0 |
| R-41 | PR-branch root-units shard failed with 21 failed tests (run 40692675966, job 122832841331) | repos/jmorrison-juniper/MistHelper/actions/runs/40692675966/jobs | d53e5626f381d6ce1d8024859a9cffa91e072e69 | not applicable | present | 0 |
| R-42 | PR-branch coverage gate failed after its shard failed (job 122842739490) | repos/jmorrison-juniper/MistHelper/actions/runs/40692675966/jobs | d53e5626f381d6ce1d8024859a9cffa91e072e69 | not applicable | present | 0 |
| R-43 | PR #4358 merge commit is in the history of main | repos/jmorrison-juniper/MistHelper/commits/2a6a5844698aeb180fea353e0243034890774565 | main | not applicable | present | 0 |
| R-44 | CI commit d53e5626 is not in the history of main | repos/jmorrison-juniper/MistHelper/commits/d53e5626f381d6ce1d8024859a9cffa91e072e69 | main | not applicable | stale | 0 |
| R-45 | PR head commit 4383ca6f is not in the history of main | repos/jmorrison-juniper/MistHelper/commits/4383ca6f0a6bc6837a193d00d458858bdaa9ad88 | main | not applicable | stale | 0 |
| R-46 | Main head commit is f03c6c9b36d612a48d7b9652998c2fd87dd777ca | repos/jmorrison-juniper/MistHelper/commits/main | main | not applicable | present | 0 |
| R-47 | No legacy 4492 record exists on main | repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1 (filter for folders starting with 4492-) | main | not applicable | absent | 0 |
| R-48 | ROUTE folder is absent on main | specs/numbered/0/0/1/2/0/4/3/2 | main | not applicable | absent | 0 |
| R-49 | Parent `specs/numbered/0/0/1/2` holds five children | specs/numbered/0/0/1/2 | main | not applicable | present | 0 |
| R-50 | Reference record folder exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-51 | Route script maps a number to base-5 segments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-52 | Route script builds numbered paths under `specs/numbered` | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 50 |
| R-53 | AGENTS requires repair of a test that leaks shared state | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 138 |
| R-54 | AGENTS requires logging when a touched block has none | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 115 |
| R-55 | AGENTS requires the closing reference in the PR body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R-56 | AGENTS forbids the auto-merge label on reviewed destructive changes | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| R-57 | Local gates table lists the commands for this change | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-58 | Full tests use two pytest-chunks commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 87 |
| R-59 | Test quality ratchet procedure exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| R-60 | STE gate lists five named files | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-61 | Numbered records use the eight-level base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R-62 | Structural directories hold five children or fewer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| R-63 | Constitution Principle I states the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-64 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-65 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-66 | Quality gates list the `test_quality_gate` command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| R-67 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R-68 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R-69 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R-70 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R-71 | Section on running a gate uses `.venv\Scripts\python.exe` commands | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 241 |
| R-72 | AGENTS requires a branch name with the type and the issue number | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| R-73 | Changelog fragment is required only for a change that a user sees | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-74 | AGENTS requires Conventional Commits | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 210 |
| R-75 | AGENTS requires a squash merge | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 235 |
| R-76 | Another test patches the resolver host through monkeypatch | tests/integration/rrm_dry_run/test_rrm_dry_run_registered_paths.py | main | a499fe21300257d2ad99411c0b1d78a2ce9ca241 | present | 26 |
| R-77 | PR #4357 is not linked to issue 4492, and its only 4492 text is a session path token | repos/jmorrison-juniper/MistHelper/pulls/4357 | main | not applicable | absent | 0 |

## 9. Unverified

- U-1: The 19 failures outside the two named tests have no traced cause. No run was made. File-specific seams (R-16 to R-19) hide the host path. Basis: R-41 and section 3.
- U-2: The three-node sequence fails before the fix on this checkout. No run was made (brief rule 2). Basis: R-09 and R-11.
- U-3: Linux CI runs the root-units shard in the sorted order that section 2 describes. Pytest-chunks source was not read. Basis: R-37, R-38, R-40, R-41.
- U-4: The fix clears all 21 failures in the PR-branch order. No run was made.
- U-5: Ruff, Black, `symbol-diff`, and the test-quality gate results are unknown. No tool ran.
- U-6: The coverage gate result after the fix is unknown. Basis for the observed failure: R-42.
- U-7: The STE score of this record is unknown. The `ste-linter` tool did not run. R-60 limits the STE gate to five files.
- U-8: Black keeps the new block at seven lines, a delta of +4. Black did not run. If the count changes, re-measure the delta and update D-4 and the seven baseline values.
- U-9: The bind search covers the local checkout only. A local search of `tests`, `src`, `MistHelper.py`, and `wsgi.py` at HEAD f03c6c9b found seven sites outside the resolver. Remote rows cover all seven: R-01, R-13, R-20 (lines 43 and 53), R-21, R-22, and R-76.

## 10. Sources and skills

- Local files read:
  - `AGENTS.md`.
  - `.github\copilot-instructions.md`, with rule lines cited in section 8.
  - `.specify\memory\constitution.md`.
  - The four files in `.specify\templates\`.
  - `documentation\quality-gates.md`.
  - `pyproject.toml`, lines 202, 492 to 520, and 559.
- Local files searched: `documentation\development-setup.md`, `documentation\architecture.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`. No claim in this record depends on their content beyond R-71.
- Local installed packages read:
  - `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py`.
  - `.venv\Lib\site-packages\_pytest\pathlib.py` and `main.py`.
  - `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA`.
- Reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. The folder shape came from file names and headings only. No content was copied.
- Partial read: `tests\unit\export\test_count_exporter.py` was checked for its existence and its resolver use only. Its failing tests were not traced.
- Remote reads: GitHub API read requests (`gh api`, `gh pr view`, `gh pr list`, `gh issue view`, `gh run view`, `gh run list`). No write request ran.
- Web: no `web_fetch` call. No upstream claim exists in this record.
- Mist API: the OpenAPI file was not read for endpoint behavior. No endpoint claim exists in this record.
- Skills: none loaded. The brief forbids test execution. No listed skill covers pytest fixture isolation without execution.
