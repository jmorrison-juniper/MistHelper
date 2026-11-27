# Tasks: Metrics Gateway Core Modules

**Input**: Routed design documents from `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/`. The plan is `plan.md`, and the requirements are in `spec.md`.

**Format**: Each task names its requirement IDs and exact file paths. It also gives an acceptance statement, one verification command from the local gates table, and a status. Add `[P]` when the task is safe in parallel.

**Status values**: `open` means the action has not started. `absent` means the target state is not on `main`. `verified-present` means `main` already has the target state. `partial` means some target items are present. The status reflects `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Repository root**: All paths are relative to the repository root. Run each command from the implementation worktree, which is `..\MistHelper-4009` after T003.

## Phase A: Baseline and Coordination

### T001 Confirm the baseline on main

- **Requirements**: FR-001, FR-002, FR-017
- **Depends on**: none
- **Files**: `src/interfaces/monitoring/metrics_gateway/cache.py`, `src/interfaces/monitoring/metrics_gateway/catalog.py`, `src/interfaces/monitoring/metrics_gateway/collector.py`, `src/interfaces/monitoring/metrics_gateway/samples.py`
- **Acceptance**: Each moved module exists at its old path. No `core/` path exists on `main`.
- **Verification**: `python -m pytest tests/guardrails -q`
- **Status**: verified-present

### T002 Confirm that PR #4208 releases the symbol guard file

- **Requirements**: FR-020
- **Depends on**: none
- **Files**: `tests/guardrails/test_src_public_symbol_preservation.py`
- **Acceptance**: The coordination check lists no open pull request that changes the file. The check uses `gh pr list --state open --json number,headRefName,files`. Without a release, T012 stays blocked.
- **Verification**: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py -q`
- **Status**: absent

### T003 Create the implementation worktree

- **Requirements**: FR-020
- **Depends on**: T001
- **Files**: none in the repository. The worktree path is `..\MistHelper-4009`.
- **Acceptance**: The worktree branch is `chore/4009-metrics-gateway-core`, created from `origin/main`. The bootstrap completes in the new worktree.
- **Verification**: `python -m py_compile MistHelper.py`
- **Status**: open

## Phase B: Package Move

### T004 Move the four modules with git mv

- **Requirements**: FR-001
- **Depends on**: T003
- **Files**: `src/interfaces/monitoring/metrics_gateway/core/cache.py`, `core/catalog.py`, `core/collector.py`, `core/samples.py`
- **Acceptance**: `git status` shows four renames into `core/`. Git stages each rename, so `git ls-files` lists each new path.
- **Verification**: `python -c "import src.interfaces.monitoring.metrics_gateway.core.catalog"`
- **Status**: absent

### T005 Add the core package initializer

- **Requirements**: FR-003, FR-022
- **Depends on**: T004
- **Files**: `src/interfaces/monitoring/metrics_gateway/core/__init__.py`
- **Acceptance**: The file holds one documentation string that gives the purpose and the five-child reason. It holds no re-export.
- **Verification**: `python -c "import src.interfaces.monitoring.metrics_gateway.core"`
- **Status**: absent

### T006 Rewrite the gateway imports

- **Requirements**: FR-002, FR-005, FR-006, FR-022
- **Depends on**: T005
- **Files**: `src/interfaces/monitoring/metrics_gateway/__init__.py`, `core/cache.py`, `core/collector.py`, `core/samples.py`, `prometheus.py`, `service.py`, `snmp.py`, `web.py`
- **Acceptance**: Each import names a core path, and no import names an old path. The root `__all__` list keeps its names. Each changed line has an inline comment.
- **Verification**: `python -c "import src.interfaces.monitoring.metrics_gateway"`
- **Status**: absent

## Phase C: Callers and Tests

### T007 [P] Rewrite the MIB generator imports and documentation

- **Requirements**: FR-005, FR-008, FR-022
- **Depends on**: T006
- **Files**: `src/operations/hardware/mib_generator/__init__.py`, `assignment.py`, `mib.py`, `runner.py`, `schema.py`
- **Acceptance**: Each import and the documentation path name the core catalog. The template at `mib.py` line 428 names the core path.
- **Verification**: `python -m pytest tests/unit/prod_readiness/operations/hardware/mib_generator/generator -q`
- **Status**: absent

### T008 [P] Update the contract test imports

- **Requirements**: FR-005
- **Depends on**: T006
- **Files**: `tests/contract/test_generated_mib_matches_agent.py`, `tests/contract/test_mib_matches_catalog.py`
- **Acceptance**: Each import names the core catalog path.
- **Verification**: `python -m pytest tests/contract/test_mib_matches_catalog.py -q`
- **Status**: absent

### T009 [P] Update the unit test imports and logger assertions

- **Requirements**: FR-005, FR-007
- **Depends on**: T006
- **Files**: `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_collector.py`, `test_prometheus_and_cache.py`, `test_snmp_and_service.py`, `test_snmp_integration.py`
- **Acceptance**: Each import names a core path. The five logger strings name the core logger, for example `src.interfaces.monitoring.metrics_gateway.core.collector`.
- **Verification**: `python -m pytest tests/unit/maps/interfaces/monitoring/metrics_gateway -q`
- **Status**: absent

### T010 [P] Update the MIB generator unit test imports

- **Requirements**: FR-005
- **Depends on**: T006
- **Files**: `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_mib_generator.py`, `test_properties.py`
- **Acceptance**: Each import names the core catalog path.
- **Verification**: `python -m pytest tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_properties.py -q`
- **Status**: absent

## Phase D: Guards

### T011 Add the gateway child guard test

- **Requirements**: FR-014, FR-022
- **Depends on**: T005
- **Files**: `tests/guardrails/test_src_domain_structure.py`
- **Acceptance**: The new test asserts the exact child set `core`, `prometheus.py`, `service.py`, `snmp.py`, and `web.py` for the gateway root. It asserts `cache.py`, `catalog.py`, `collector.py`, and `samples.py` for the core package.
- **Verification**: `python -m pytest tests/guardrails/test_src_domain_structure.py -q`
- **Status**: absent

### T012 Add the four MODULE_PATHS entries

- **Requirements**: FR-013, FR-022
- **Depends on**: T002, T004
- **Files**: `tests/guardrails/test_src_public_symbol_preservation.py`
- **Acceptance**: `MODULE_PATHS` holds four entries from each old path to each core path, relative to `src`. The entries follow the `constants.py` entry.
- **Verification**: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py -q`
- **Status**: absent

### T013 Update the nested baseline and totals

- **Requirements**: FR-015
- **Depends on**: T006
- **Files**: `tests/guardrails/nested_package_baseline.json`, `tests/guardrails/test_nested_package_structure.py`
- **Acceptance**: The JSON holds no entry for `src/interfaces/monitoring/metrics_gateway`, and it stays sorted by path. The test expects `32 violations, 233 total excess` at line 177.
- **Verification**: `python -m pytest tests/guardrails/test_nested_package_structure.py -q`
- **Status**: absent

## Phase E: Documents, Generated Pages, Script, and Hook Catalog

### T014 [P] Update the MIB guide

- **Requirements**: FR-009
- **Depends on**: T006
- **Files**: `documentation/mib_generator.md`
- **Acceptance**: Lines 13 and 108 name `src/interfaces/monitoring/metrics_gateway/core/catalog.py`.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/mib_generator.md`
- **Status**: absent

### T015 Regenerate the MIB and check it

- **Requirements**: FR-008
- **Depends on**: T007
- **Files**: `documentation/mibs/MISTHELPER-MIB.mib`
- **Acceptance**: `python MistHelper.py --mib-generate` changes only the header path lines. Then `python MistHelper.py --mib-check` exits with status 0. Stop and review any other changed line.
- **Verification**: `python -m pytest tests/contract/test_generated_mib_matches_agent.py -q`
- **Status**: absent

### T016 Regenerate the menu pages

- **Requirements**: FR-010
- **Depends on**: T006
- **Files**: `documentation/menu-api/interactive-safe.md`, `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md`
- **Acceptance**: Lines 1149 to 1151 of both pages link `core/collector.py`. Then `python -m scripts.menu_api_map --check` exits with status 0. Do not edit either page by hand.
- **Verification**: `python -m scripts.menu_api_map`
- **Status**: absent

### T017 Update the Observium script comment

- **Requirements**: FR-009
- **Depends on**: none
- **Files**: `container/observium/20-add-mist-static-sensors.sh`
- **Acceptance**: Line 120 names `src/interfaces/monitoring/metrics_gateway/core/catalog.py`.
- **Verification**: `git grep -n -E "metrics_gateway[./](cache|catalog|collector|samples)" -- ":!specs/1924-failure-evidence" ":!specs/2159-openapi-mib-generator" ":!specs/2448-misthelper-performance-monitoring/research.md" ":!specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv" ":!CHANGELOG.md" ":!changelog.d" ":!specs/numbered/0/0/1/1/2/0/1/4"`
- **Status**: absent

### T018 [P] Update the eight hook rows

- **Requirements**: FR-011
- **Depends on**: T004
- **Files**: `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv`
- **Acceptance**: Rows 266 to 271, 273, and 617 name the core paths. The row count, the hook IDs, and the symbols stay unchanged. The new files are staged before this task runs.
- **Verification**: `python -m pytest tests/guardrails/test_performance_hook_catalog.py -q`
- **Status**: absent

## Phase F: Historical Records, Changelog, and Record

### T019 Keep historical records unchanged

- **Requirements**: FR-012
- **Depends on**: none
- **Files**: `specs/1924-failure-evidence/inventory.md`, `specs/2159-openapi-mib-generator/plan.md`, `specs/2159-openapi-mib-generator/spec.md`, `specs/2159-openapi-mib-generator/tasks.md`, `specs/2448-misthelper-performance-monitoring/research.md`, `specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv`, `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog-summary.json`
- **Acceptance**: Each file keeps the blob SHA that `main` lists. The changed-file list contains none of these files.
- **Verification**: `python -m pytest tests/guardrails -q`
- **Status**: verified-present

### T020 [P] Add the changelog fragment

- **Requirements**: FR-018
- **Depends on**: none
- **Files**: `changelog.d/issue-4009-metrics-gateway-core.md`
- **Acceptance**: The fragment holds one `### Changed` heading and one bullet. The bullet names issue 4009.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: absent

### T021 Copy the reviewed record into the routed folder

- **Requirements**: FR-019
- **Depends on**: T020, and the final review in `analysis.md`
- **Files**: `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/module-paths.md`, `design/checklists/requirements.md`
- **Acceptance**: The routed folder holds the reviewed files. Each Markdown file scores 80 or above in the STE gate.
- **Verification**: `Get-ChildItem -LiteralPath specs\numbered\0\0\1\1\2\0\1\4\4009-metrics-gateway-core -Recurse -Filter *.md | ForEach-Object { ste-linter --config .ste-linter.toml --min-score 80 $_.FullName }`
- **Status**: absent

## Phase G: Local Gates

### T-LOCAL-GATES Run every applicable local gate

- **Requirements**: FR-016, FR-017, FR-022, SC-001 to SC-008
- **Depends on**: T004 to T021
- **Files**: every changed file in `plan.md`
- **Acceptance**: Each applicable gate in `design/quickstart.md` section 4 passes. The pull request body records each result. Each gate that does not apply names its reason.
- **Verification**: `python -m ruff check .`
- **Status**: open

## Phase H: Delivery

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-020, FR-021
- **Depends on**: T-LOCAL-GATES, T002
- **Files**: the explicit file list in `plan.md`. Do not stage a directory or a dot.
- **Acceptance**: The commit subject is `refactor(metrics-gateway): isolate core modules`. The body holds `Closes #4009` and the Copilot co-author trailer. The coordinator has assigned the serial slot before the push.
- **Verification**: `git grep -n -E "metrics_gateway[./](cache|catalog|collector|samples)" -- ":!specs/1924-failure-evidence" ":!specs/2159-openapi-mib-generator" ":!specs/2448-misthelper-performance-monitoring/research.md" ":!specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv" ":!CHANGELOG.md" ":!changelog.d" ":!specs/numbered/0/0/1/1/2/0/1/4"`
- **Status**: open

### T-REMOTE-CI Watch the remote checks

- **Requirements**: FR-020
- **Depends on**: T-PR
- **Files**: none
- **Acceptance**: Each required check passes on the latest commit. Run `gh pr checks --watch`. Do not add the `auto-merge` label yet.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- **Status**: open

### T-MERGE Enable auto-merge after authorization

- **Requirements**: FR-020, FR-021
- **Depends on**: T-REMOTE-CI and the orchestrator authorization
- **Files**: none
- **Acceptance**: The orchestrator authorizes the merge. Auto-merge runs only after every required check passes. The archive branch stays on the remote.
- **Verification**: `python -m scripts.menu_api_map --check` in a worktree of the updated `main`
- **Status**: open

## Dependencies and Execution Order

- T001 and T002 start first. T003 needs T001.
- T004 needs T003. T005 needs T004. T006 needs T005.
- T007 to T010, T013, T014, and T016 need T006. Each of them touches different files, so they run in parallel.
- T012 needs T002 and T004. The symbol guard waits for the PR #4208 release.
- T018 needs T004, and the renamed files must be staged.
- T-LOCAL-GATES needs every task from T004 to T021. T-PR needs T-LOCAL-GATES and T002.
- T-REMOTE-CI needs T-PR. T-MERGE needs T-REMOTE-CI and the orchestrator authorization.
