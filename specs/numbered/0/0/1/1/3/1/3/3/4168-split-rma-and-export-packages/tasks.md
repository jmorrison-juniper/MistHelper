# Tasks: Split the Juniper RMA and export packages

**Input**: `plan.md`, `spec.md`, `design/research.md`, `design/quickstart.md`, `design/data-model.md`, and `design/contracts/`.

**Format**: `[ID] [P?] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks. Each task names exact paths, one verification command, and one status: open, verified-present, partial, or absent. A completed task adds `(delivered: path)` to its line.

**Source of paths**: Section A and section B of `plan.md` define each moved path and each new package marker. Section E of `plan.md` defines each modified file.

## Phase 0: Baseline and gate

- [x] T000 Measure the baseline on remote `main` (FR-001, SC-001). Files: `tests/guardrails/nested_package_baseline.json`. Acceptance: the measure reports 190 directories, 33 violations, and 236 total excess. Verify: the measure in `design/quickstart.md`, step 1. Status: verified-present (`design/research.md`, section Local measurement).
- [ ] T001 Wait for pull request #4813 to merge (FR-014). Files: none. Acceptance: pull request #4813 reports state `MERGED`. Verify: `gh pr view 4813 -R jmorrison-juniper/MistHelper --json state,mergedAt`. Status: open.

## Phase 1: Package markers and moves

- [ ] T002 [P] Create the 16 package markers in `plan.md` section B (FR-002, FR-007). Files: the 16 paths in `plan.md` section B. Acceptance: each marker holds its docstring and no other statement. Verify: `python -m py_compile <each marker path>`. Status: open. Depends on T001.
- [ ] T003 Move the 20 organization modules, rows 1 to 20 of `plan.md` section A (FR-004). Files: rows 1 to 20. Acceptance: each new path exists and each old path has no file. Verify: `python -m py_compile` on each new path in rows 1 to 20. Status: open. Depends on T001, T002.
- [ ] T004 Move the site modules and the site insights package, rows 21 to 41 (FR-004). Files: rows 21 to 41. Acceptance: `src/operations/exporting/export/site_insights/` no longer exists. Verify: `python -m py_compile` on each new path in rows 21 to 41. Status: open. Depends on T001, T002.
- [ ] T005 [P] Move the WAN and generic modules, rows 42 to 50 (FR-004). Files: rows 42 to 50. Acceptance: each new path exists. Verify: `python -m py_compile` on each new path in rows 42 to 50. Status: open. Depends on T001, T002.
- [ ] T006 [P] Move the Juniper RMA model modules, rows 51 to 55 (FR-005). Files: rows 51 to 55. Acceptance: `run_record.py` keeps its path. Verify: `python -m py_compile` on each new path in rows 51 to 55. Status: open. Depends on T001, T002.
- [ ] T007 [P] Move the Juniper RMA workflow modules, rows 56 to 60 (FR-006). Files: rows 56 to 60. Acceptance: `access_check.py` and `correlation.py` keep their paths. Verify: `python -m py_compile` on each new path in rows 56 to 60. Status: open. Depends on T001, T002.

## Phase 2: Import and reference updates

- [ ] T008 [P] Update imports in the 21 moved source files listed in `plan.md` section E (FR-008, FR-009). Files: each file at its new path. Acceptance: each import names a new dotted path and no class or function name changes. Verify: `python -m py_compile <each file>`. Status: open. Depends on T003 to T007.
- [ ] T009 [P] Update imports in the 8 source files outside the moved packages listed in `plan.md` section E (FR-008). Files: `src/foundation/runtime/config/source_dependency_resolver.py`, `src/foundation/support/refactors/msp_privilege_detection.py`, `src/foundation/support/refactors/serial_cc/site_client_insights.py`, `src/interfaces/visualization/ui/prompt_utils.py`, `src/mist/intelligence/analytics/data_collection_manager.py`, `src/mist/intelligence/reports/sfp_transceiver_data_processor.py`, `src/mist/resources/device/device_reboot_manager.py`, `src/mist/resources/site/rrm_reset/client.py`. Acceptance: no moved dotted path remains in these files. Verify: `python -m py_compile <each file>`. Status: open. Depends on T003 to T007.
- [ ] T010 Update the 49 export and Juniper RMA import lines in `MistHelper.py` (FR-008). Files: `MistHelper.py`. Acceptance: line 3373 keeps `data_exporter`, and each other import names a new dotted path. Verify: `python -m py_compile MistHelper.py`. Status: open. Depends on T003 to T007.
- [ ] T011 Update the 8 module strings in `src/foundation/runtime/config/source_dependency_resolver.py` (FR-008). Files: `src/foundation/runtime/config/source_dependency_resolver.py`, remote lines 52, 75, 90, 93, 95, 97, 99, and 105. Acceptance: line 54 keeps `data_exporter`. Verify: the direct resolution command in `design/quickstart.md`, step 6. Status: open. Depends on T003 to T007.
- [ ] T012 [P] Update the export imports in `web_portal/services/operation.py` (FR-008). Files: `web_portal/services/operation.py`. Acceptance: each import names a new dotted path. Verify: `python -m py_compile web_portal/services/operation.py`. Status: open. Depends on T003 to T007.
- [ ] T013 [P] Update `scripts/generate_menu_wiki.py`, `scripts/menu_api_map/reference/curated.json`, and the example paths in three `scripts/menu_api_map/` files (FR-008). Files: `scripts/generate_menu_wiki.py`, `scripts/menu_api_map/reference/curated.json`, `scripts/menu_api_map/analysis/source_index.py`, `scripts/menu_api_map/render/markdown.py`, `scripts/menu_api_map/render/pages.py`. Acceptance: each import and path string names a new path. Verify: `python -m py_compile scripts/generate_menu_wiki.py`. Status: open. Depends on T003 to T007.

## Phase 3: Test updates

- [ ] T014 Update the 55 export test files in `plan.md` section E, under `tests/unit/export/` and `tests/unit/export/site_insights/` (FR-008, FR-011). Files: the 55 paths in `plan.md` section E. Acceptance: each import and patch target names a new dotted path. Verify: `python -m pytest tests/unit/export -q`. Status: open. Depends on T001, T008 to T013.
- [ ] T015 [P] Update the 30 unit test files outside `tests/unit/export/` listed in `plan.md` section E (FR-008). Files: the 30 paths under `tests/unit/` in `plan.md` section E, excluding `tests/unit/export/`. Acceptance: each import and patch target names a new dotted path. Verify: `python -m pytest tests/unit/juniper_rma tests/unit/prod_readiness tests/unit/web_portal -q`. Status: open. Depends on T008 to T013.
- [ ] T016 [P] Update the 6 files under `tests/e2e/`, `tests/fixtures/`, `tests/guardrails/`, and `tests/integration/` listed in `plan.md` section E (FR-008). Files: `tests/e2e/web_portal/juniper_browser_harness.py`, `tests/fixtures/next5_parity_baseline.py`, `tests/guardrails/test_endpoint_backlog_safety.py`, `tests/guardrails/test_endpoint_catalog.py`, `tests/integration/export/test_org_webhook_native_refusals.py`, `tests/integration/export/test_wifi_clients_native_response_failures.py`. Acceptance: each import and string names a new dotted path. Verify: `python -m pytest tests/guardrails/test_endpoint_catalog.py tests/guardrails/test_endpoint_backlog_safety.py -q`. Status: open. Depends on T008 to T013.
- [ ] T017 [P] Remove the three baseline objects from `tests/guardrails/nested_package_baseline.json` (FR-001). Files: `tests/guardrails/nested_package_baseline.json`, remote lines 156 to 170. Acceptance: the file holds 30 objects, valid JSON, and sorted paths. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py -q`. Status: open. Depends on T001.
- [ ] T018 Update the expected message and add the old-path test in `tests/guardrails/test_nested_package_structure.py` (FR-015, FR-016). Files: `tests/guardrails/test_nested_package_structure.py`, remote line 177. Acceptance: the expected message names 30 violations and 190 total excess, and the new test asserts that no file exists at each old module path. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py -q`. Status: open. Depends on T003 to T007.
- [ ] T019 [P] Add 46 approved moves to `_HISTORICAL_PATH_MOVES` in `tests/guardrails/test_performance_hook_catalog.py` (FR-008). Files: `tests/guardrails/test_performance_hook_catalog.py`, remote lines 28 to 38. Acceptance: each old path that `hook-catalog.csv` names maps to its new path, and `data_exporter.py` is absent from the map. Verify: `python -m pytest tests/guardrails/test_performance_hook_catalog.py -q`. Status: open. Depends on T003 to T007.

## Phase 4: Documents and generated references

- [ ] T020 [P] Update the 49 hand-edited documents in `plan.md` section E, plus `documentation/architecture.md` lines 263 and 284 (FR-008). Files: `.github/copilot-handoff.md`, `junk/refactor_candidates.md`, `documentation/diagrams/class-hierarchy/exporters.md`, `documentation/architecture.md`, and the 46 files under `documentation/api/`. Acceptance: each path names a new dotted or slash path. Verify: the `Old paths` row of the Move a module table in `.github/copilot-instructions.md`, run as in `design/quickstart.md`, step 3. Status: open. Depends on T003 to T007.
- [ ] T021 Regenerate the 14 generated references in `plan.md` section E (FR-008, SC-006). Files: `documentation/menu_reference.md`, `documentation/menu-api/*.md`, `documentation/wiki/Menu-API-Endpoints-*.md`, `documentation/wiki/Menu-Reference.md`. Acceptance: a second run of each generator changes no file. Verify: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`, each run twice. Status: open. Depends on T008 to T013.
- [ ] T022 [P] Add `changelog.d/issue-4168-split-rma-and-export-packages.md` (FR-013). Files: `changelog.d/issue-4168-split-rma-and-export-packages.md`. Acceptance: the fragment names issue #4168 and the three moved packages. Verify: the naming rule in `changelog.d/README.md`. Status: open. Depends on T001.

## Phase 5: Verification

- [ ] T023 Run the old-path search and the old logger name search (FR-008, SC-003). Files: none. Acceptance: the old-path search returns no hit in a live file, and the logger search returns no hit in a live file. Verify: the commands in `design/quickstart.md`, steps 3 and 4. Status: open. Depends on T014 to T021.
- [ ] T024 Measure the guard after the change (FR-002, SC-001). Files: `tests/guardrails/test_nested_package_structure.py`. Acceptance: the guard reports 206 directories examined, 30 violations, and 190 total excess. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py -k ratchet -s`. Status: open. Depends on T017, T018, T003 to T007.
- [ ] T025 Import each moved module at its new path (FR-009). Files: the 59 modules in `plan.md` section A. Acceptance: each new dotted path imports, and each old dotted path raises `ModuleNotFoundError`. Verify: the `Import smoke` row of the Move a module table, run as in `design/quickstart.md`, step 5. Status: open. Depends on T003 to T007.

## Final gate tasks

- [ ] T-LOCAL-GATES Run every local gate that applies to the changed files (FR-009, SC-002, SC-004, SC-005, SC-007). Files: the changed files from T003 to T025. Acceptance: each applicable gate in `.github/copilot-instructions.md` passes, and the result of each gate is recorded. Verify: the gate commands in `design/quickstart.md`, step 8. Status: open. Depends on T017 to T025.
- [ ] T-PR Commit, push, and open the pull request (FR-013). Files: the changed files from T003 to T025. Acceptance: the commit subject is `refactor(exporting): split juniper rma and export packages`, the body names `Closes #4168`, the branch is `chore/4168-split-rma-and-export-packages`, and the body lists each gate result. Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body,headRefName`. Status: open. Depends on T-LOCAL-GATES.
- [ ] T-REMOTE-CI Watch the remote CI run (SC-002, SC-004). Files: none. Acceptance: each required check reports success. Verify: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`. Status: open. Depends on T-PR.
- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge (FR-014). Files: none. Acceptance: after the squash merge, `.github/workflows/container-build.yml` completes on the merged SHA, the image revision label equals the merged SHA, and the deploy health checks pass. Verify: `gh run list -R jmorrison-juniper/MistHelper --workflow container-build.yml --limit 1`. Status: open. Depends on T-REMOTE-CI.

## Dependencies and execution order

- T000 has no dependency. T001 has no dependency.
- T002 depends on T001. T003 to T007 depend on T001 and T002.
- T008 to T013 depend on T003 to T007.
- T014 depends on T001 and T008 to T013. T015 and T016 depend on T008 to T013.
- T017 depends on T001. T018 depends on T003 to T007. T019 depends on T003 to T007.
- T020 depends on T003 to T007. T021 depends on T008 to T013. T022 depends on T001.
- T023 depends on T014 to T021. T024 depends on T017, T018, and T003 to T007. T025 depends on T003 to T007.
- T-LOCAL-GATES depends on T017 to T025. T-PR depends on T-LOCAL-GATES. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI.
