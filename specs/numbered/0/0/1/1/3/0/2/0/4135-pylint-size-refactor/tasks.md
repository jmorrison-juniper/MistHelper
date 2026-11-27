# Tasks: Function and module size for Pylint limits

**Input**: Numeric record `specs/numbered/0/0/1/1/3/0/2/0/4135-pylint-size-refactor/`. Plan: `plan.md`. Spec: `spec.md`. Research: `design/research.md`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md` (required), `design/data-model.md`, `design/quickstart.md`.

**Tests**: Tests are required by the constitution. Each new test function appears in the task that adds it.

**Organization**: Tasks run in phases. A phase depends on the phases before it, except where a task marks `[P]`.

## Format

`[ID] [P?] Title`. Each task lists requirements, files, acceptance, verification, and status.

- `[P]`: Safe in parallel. The task touches files that no other parallel task touches.
- Status values: open, verified-present, partial, or absent.
- Verification uses one command from the local gates table in `.github/copilot-instructions.md`. The acceptance line names any extra check from the issue.

## Phase A: Baseline and confirmation

**Purpose**: Capture the values that tests compare, and confirm the findings before any edit.

- [ ] T001 Capture parity constants on `main`

  - Requirements: FR-002, FR-007, FR-008
  - Files: `tests/unit/web_portal/test_portal_required_controls.py`, `tests/guardrails/test_endpoint_catalog.py`, `tests/guardrails/test_operation_registry_menu_coverage.py`
  - Acceptance: Three SHA-256 constants are computed on `main` before any edit. Test `test_registry_matches_baseline` and test `test_menu_key_order_matches_baseline` each compare one constant. The endpoint constant gets its test in Task T032. Each test passes on `main`.
  - Verification: `python -m pytest tests/unit/web_portal/test_portal_required_controls.py` (Tests row)
  - Status: open. Depends on none.

- [ ] T002 [P] Confirm the findings with Pylint on `main`

  - Requirements: FR-015
  - Files: none changed. Read-only run of Pylint on the four named paths.
  - Acceptance: The run reports R0911 at `_is_user_facing`, R0914 and R0915 at `_build_registry`, C0302 for three modules, and R0801 for the Juniper pair. R0913 and R0917 appear only if the parser missed a signature. Record any surprise in `analysis.md` before code changes.
  - Verification: `pylint src/ --fail-under=9.5` (Code quality row). The issue command also runs on the four named paths.
  - Status: partial. Reading confirmed the findings. Pylint has not run.

- [ ] T003 [P] Record the nested-package ratchet before any edit

  - Requirements: FR-013
  - Files: `tests/guardrails/test_nested_package_structure.py` (read only)
  - Acceptance: The ratchet reports 190 directories, 33 violations, and 236 total excess on `main`.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests row)
  - Status: verified-present. The recomputed counts match the test string at line 177.

## Phase B: Web portal operation module (R0911, R0914, R0915, C0302)

**Purpose**: Split the registry, the parameter builders, the run-log handler, and the context helpers out of `operation.py`.

- [ ] T010 [P] Create the parameter package

  - Requirements: FR-002, FR-009, FR-012, FR-016
  - Files: add `src/foundation/support/portal_operations/__init__.py` and `src/foundation/support/portal_operations/parameters.py`. Source lines are 174 to 327 of `web_portal/services/operation.py`.
  - Acceptance: Class `PortalParameters` holds each builder as a static method. The module imports no `MistHelper`. Each changed line carries an inline comment.
  - Verification: `python -m py_compile src/foundation/support/portal_operations/parameters.py` (Compile row)
  - Status: verified-present. The source lines exist on `main`.

- [ ] T011 Create the group builders

  - Requirements: FR-002, FR-016
  - Files: add `src/foundation/support/portal_operations/groups/__init__.py`, `site.py`, `client.py`, `cli_endpoint.py`, and `juniper.py`. Source lines are 410 to 603, 604 to 749, 750 to 910, and 328 to 405.
  - Acceptance: Classes `SiteMenuGroups`, `ClientMenuGroups`, `CliEndpointMenuGroups`, and `JuniperRmaMenuGroups` each hold static `rows()` methods. Each method holds at most 15 locals and 50 statements.
  - Verification: `radon cc src/foundation/support/portal_operations/groups -j | complexity-gate --max 10` (Complexity row)
  - Status: verified-present. The six group markers exist at lines 410, 548, 556, 604, 750, and 780 of `main`.

- [ ] T012 Create the registry builder

  - Requirements: FR-002
  - Files: add `src/foundation/support/portal_operations/registry.py`
  - Acceptance: Class `PortalRegistryBuilder` has a static `build()` that merges the group rows in the original order. The hash test from T001 passes.
  - Verification: `python -m pytest tests/unit/web_portal/test_portal_required_controls.py` (Tests row)
  - Status: verified-present. Depends on T010 and T011.

- [ ] T013 Move the run-log handler and split the classifier

  - Requirements: FR-001, FR-016
  - Files: add `src/foundation/support/portal_operations/run_log_handler.py` and modify `tests/unit/web_portal/test_portal_log_routing.py`. Source lines are 1732 to 1952 of `web_portal/services/operation.py`.
  - Acceptance: Class `_RunLogHandler` keeps its name and behavior. Method `_is_user_facing` returns at most six times. Helper `_is_plumbing_record` holds the plumbing checks in the original order. Test `test_user_facing_classification_branches` passes for each of the eight outcomes.
  - Verification: `python -m pytest tests/unit/web_portal/test_portal_log_routing.py` (Tests row)
  - Status: verified-present. The method returns eight times from line 1894 to line 1908.

- [ ] T014 Move the context-answer helpers

  - Requirements: FR-004, FR-016
  - Files: add `src/foundation/support/portal_operations/context_answers.py`. Source lines are 1120 to 1243 of `web_portal/services/operation.py`.
  - Acceptance: Class `ContextAnswers` holds the helpers as static methods. The call sites in `OperationExecutor` use the class.
  - Verification: `python -m pytest tests/unit/web_portal/test_issue_4053_runtime_answers.py` (Tests row)
  - Status: verified-present. Depends on T015 for the call sites.

- [ ] T015 Reduce `operation.py` to the public module

  - Requirements: FR-004, FR-010, FR-011
  - Files: modify `web_portal/services/operation.py`
  - Acceptance: The module keeps `OperationExecutor`, the constants, `_read_positive_int_env`, and `PARAMETER_REGISTRY = PortalRegistryBuilder.build()`. It imports `_RunLogHandler`, `ContextAnswers`, and the registry. It holds 1,000 lines or fewer, counted by LF.
  - Verification: `python -m pytest tests/unit/web_portal/test_operation_destructive_gate.py` (Tests row)
  - Status: verified-present. The module holds 1,952 LF lines on `main`.

## Phase C: Juniper row writer (R0801)

**Purpose**: Keep one write body for the two Juniper workflows.

- [ ] T020 [P] Add the row writer to the Juniper export module

  - Requirements: FR-003, FR-009, FR-016
  - Files: modify `src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py`. The body comes from `_write` at line 113 of `asset_lookup.py` and at line 471 of `correlation.py`.
  - Acceptance: Class `JuniperRowWriter` takes the exporter in its constructor. Method `write()` logs before and after each export. The module imports no `MistHelper`. The module docstring names the Juniper export scope.
  - Verification: `python -m py_compile src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py` (Compile row)
  - Status: verified-present. The duplicate method exists on `main`.

- [ ] T021 Replace both `_write` methods

  - Requirements: FR-003
  - Files: modify `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` and `src/operations/exporting/juniper_rma/workflows/correlation.py`
  - Acceptance: Each workflow builds `JuniperRowWriter(exporter)` in its constructor. Each `_write` method is removed. The constructor signatures keep the `exporter` argument.
  - Verification: `python -m pytest tests/unit/juniper_rma/workflows/test_lookups.py` (Tests row)
  - Status: verified-present. Depends on T020.

- [ ] T022 Add the two writer tests

  - Requirements: FR-003
  - Files: modify `tests/unit/juniper_rma/workflows/test_lookups.py` and `tests/unit/juniper_rma/workflows/test_correlation.py`
  - Acceptance: `test_writer_skips_empty_rows` proves that empty rows write no file. `test_writer_forwards_api_name_and_fields` proves the API name and the field list reach the exporter. Neither test uses a bare `assert`.
  - Verification: `python -m pytest tests/unit/juniper_rma/workflows/test_correlation.py` (Tests row)
  - Status: open. Depends on T021.

## Phase D: Endpoint dictionary (C0302)

**Purpose**: Split the 612-entry dictionary into six contiguous blocks, keep the order, and keep the public names.

- [ ] T030 [P] Create the six endpoint blocks

  - Requirements: FR-006, FR-007, FR-012
  - Files: add `src/foundation/persistence/db/endpoint_strategies/__init__.py`, `entries_first/__init__.py`, `entries_first/block_1.py`, `entries_first/block_2.py`, `entries_first/block_3.py`, `entries_second/__init__.py`, `entries_second/block_4.py`, `entries_second/block_5.py`, `entries_second/block_6.py`
  - Acceptance: Block `n` holds the entries from position `(n - 1) * 102 + 1` to `n * 102` in file order. Dictionaries are named `ENDPOINT_BLOCK_1` to `ENDPOINT_BLOCK_6`. The six blocks hold 612 keys with no duplicate.
  - Verification: `python -m py_compile src/foundation/persistence/db/endpoint_strategies/entries_first/block_1.py src/foundation/persistence/db/endpoint_strategies/entries_first/block_2.py src/foundation/persistence/db/endpoint_strategies/entries_first/block_3.py src/foundation/persistence/db/endpoint_strategies/entries_second/block_4.py src/foundation/persistence/db/endpoint_strategies/entries_second/block_5.py src/foundation/persistence/db/endpoint_strategies/entries_second/block_6.py` (Compile row)
  - Status: verified-present. The file holds 612 keys from line 144 to line 4527.

- [ ] T031 Compose the public endpoint dictionary

  - Requirements: FR-006, FR-007
  - Files: modify `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
  - Acceptance: The module keeps the docstring, the classes `SleTrendIdentity` and `SleWindowIdentity`, and `ENDPOINT_PRIMARY_KEY_STRATEGIES = {**ENDPOINT_BLOCK_1, **ENDPOINT_BLOCK_2, **ENDPOINT_BLOCK_3, **ENDPOINT_BLOCK_4, **ENDPOINT_BLOCK_5, **ENDPOINT_BLOCK_6}`. Each block is listed in the merge in file order. The module holds 1,000 lines or fewer, counted by LF.
  - Verification: `python -m pytest tests/guardrails/test_endpoint_catalog.py` (Tests row)
  - Status: verified-present. The file holds 4,537 LF lines on `main`. Depends on T030.

## Phase E: MistHelper module (C0302)

  - Requirements: FR-007
  - Files: modify `tests/guardrails/test_endpoint_catalog.py`
  - Acceptance: `test_endpoint_strategy_order_and_values_match_baseline` compares the SHA-256 of the ordered items with the constant from T001.
  - Verification: `python -m pytest tests/guardrails/test_endpoint_catalog.py` (Tests row)
  - Status: open. Depends on T031.

## Phase E: MistHelper module (C0302)

**Purpose**: Move the menu, the context, the runtime, and the bootstrap classes out of `MistHelper.py`. Keep the host contract in place.

- [ ] T040 [P] Create the CLI package skeleton

  - Requirements: FR-012
  - Files: add `src/interfaces/cli/__init__.py`, `bootstrap/__init__.py`, `context/__init__.py`, `menu/__init__.py`, and `runtime/__init__.py`
  - Acceptance: The `cli/` directory holds four subdirectories and no module. Each package docstring names the package subject.
  - Verification: `python -m py_compile src/interfaces/cli/__init__.py src/interfaces/cli/bootstrap/__init__.py src/interfaces/cli/context/__init__.py src/interfaces/cli/menu/__init__.py src/interfaces/cli/runtime/__init__.py` (Compile row)
  - Status: open.

- [ ] T041 Move `LogRotationSettings`

  - Requirements: FR-005
  - Files: add `src/interfaces/cli/bootstrap/log_rotation.py`. Source lines are 109 to 185 of `MistHelper.py`.
  - Acceptance: The class keeps its name and fields. `MistHelper.py` imports it from the new module.
  - Verification: `python -m py_compile src/interfaces/cli/bootstrap/log_rotation.py` (Compile row)
  - Status: verified-present. Depends on T040.

- [ ] T042 Split `GlobalImportManager`

  - Requirements: FR-005, FR-010, FR-016
  - Files: add `src/interfaces/cli/bootstrap/factories.py`, `dependency_installer.py`, and `import_initializer.py`. Source lines are 1207 to 2441 of `MistHelper.py`, grouped as in `design/research.md`.
  - Acceptance: Every method name from the split map appears once. The initializer may call the installer. The installer never calls the initializer. Each module holds 1,000 lines or fewer.
  - Verification: `python -m py_compile src/interfaces/cli/bootstrap/factories.py src/interfaces/cli/bootstrap/dependency_installer.py src/interfaces/cli/bootstrap/import_initializer.py` (Compile row)
  - Status: verified-present. Depends on T041.

- [ ] T043 Move the context helpers and wiring

  - Requirements: FR-005, FR-016
  - Files: add `src/interfaces/cli/context/login.py`, `strategies.py`, and `wiring.py`. Source lines are 2596 to 2808, 2809 to 3377, and 3378 to 3651 of `MistHelper.py`.
  - Acceptance: Each function keeps its body. Each module imports no `MistHelper`. The session and credential tests keep passing.
  - Verification: `python -m pytest tests/unit/test_credential_preflight.py` (Tests row)
  - Status: verified-present. Depends on T040.

- [ ] T044 Split the menu literal into four blocks

  - Requirements: FR-008, FR-012
  - Files: add `src/interfaces/cli/menu/entries_a.py`, `entries_b.py`, `entries_c.py`, and `entries_d.py`. Source lines are 3658 to 6501 of `MistHelper.py`. Update `tests/guardrails/test_operation_registry_menu_coverage.py`.
  - Acceptance: Blocks hold menu entries 1 to 78, 79 to 155, 156 to 232, and 233 to 309. Each block keeps file order. `menu/__init__.py` defines `MENU_ACTIONS` as the ordered union. The menu key order test from T001 passes. Each block holds 1,000 lines or fewer.
  - Verification: `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py` (Tests row)
  - Status: verified-present. The literal holds 309 menu entries on `main`. The location of `GlobalImportManager.MenuEntry` is confirmed in this task.

- [ ] T045 Move the runtime helpers

  - Requirements: FR-005, FR-016
  - Files: add `src/interfaces/cli/runtime/systematic.py`, `launchers.py`, `cli_flags.py`, and `dispatch.py`. Source lines are 6502 to 6855, 6856 to 7330, 7331 to 7827, and 7828 to 8268 of `MistHelper.py`.
  - Acceptance: Each function keeps its body. Each module holds 1,000 lines or fewer and imports no `MistHelper`.
  - Verification: `python -m pytest tests/unit/refactors/test_tui_launcher.py` (Tests row)
  - Status: verified-present. Depends on T040.

- [ ] T046 Reduce `MistHelper.py` to the host block

  - Requirements: FR-005, FR-009, FR-010
  - Files: modify `MistHelper.py`
  - Acceptance: The module keeps the header and the host binding at line 712. It keeps the bootstrap block at lines 938 to 1206. It keeps the globals at lines 2442 to 2558, the context module at lines 2559 to 2595, and the entry guard at line 8276. It binds `menu_actions = MENU_ACTIONS`. `__all__` lists only names that the module still defines. The module holds 1,000 lines or fewer, counted by LF.
  - Verification: `python MistHelper.py --test` (Safe sweep row)
  - Status: verified-present. The module holds 8,372 LF lines on `main`. Depends on T041 to T045.

- [ ] T047 Update the source dependency resolver

  - Requirements: FR-011
  - Files: modify `src/foundation/runtime/config/source_dependency_resolver.py`
  - Acceptance: Each moved name that the resolver reads by name maps to its new module in `_module_symbols`. No entry names `MistHelper` as a source module.
  - Verification: `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` (Tests row)
  - Status: verified-present. The `_module_symbols` map starts at line 40 of `main`. Depends on T046.

- [ ] T048 Migrate test references to the new owners

  - Requirements: FR-011, FR-014
  - Files: every test file that names a moved `MistHelper` attribute. The inventory search covers 805 matches in 108 files. Also modify `tests/guardrails/test_endpoint_catalog.py` lines 521 to 574 to read `src/interfaces/cli/menu/` instead of `MistHelper.py`.
  - Acceptance: No test patches or reads a moved name on `MistHelper`. The full shards pass.
  - Verification: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and the second command in `.github/copilot-instructions.md` (Full tests row)
  - Status: verified-present. Depends on T046 and T047.

- [ ] T049 Add the import-cycle and import-order guard

  - Requirements: FR-009
  - Files: modify `tests/guardrails/test_move_module_guidance.py`
  - Acceptance: `test_new_source_modules_do_not_import_misthelper` fails on any new module that imports `MistHelper`. It also imports `src.interfaces.cli.bootstrap.import_initializer` in a fresh process and confirms no network call.
  - Verification: `python -m pytest tests/guardrails/test_move_module_guidance.py` (Tests row)
  - Status: absent. No such guard exists on `main`.

## Phase F: Documents and the changelog fragment

**Purpose**: Update the counts and paths that the documents name, and add the release note.

- [ ] T050 [P] Update the three documents

  - Requirements: FR-017
  - Files: modify `documentation/architecture.md` (lines 164 and 196), `documentation/CONTRIBUTING-MistHelper.md` (the symbol map at line 31), and `.github/copilot-instructions.md` (the key file row at line 580)
  - Acceptance: Each count matches the measured LF count after the change. Each new package appears in the contributor map. The copilot instructions remain STE compliant.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` (STE row)
  - Status: verified-present. The row at line 196 states 8,071 lines, and the row at line 580 states 8,382 lines.

- [ ] T051 [P] Add the changelog fragment

  - Requirements: FR-018
  - Files: add `changelog.d/issue-4135-pylint-size-refactor.md`
  - Acceptance: The file holds one `###` heading and one `Changed` bullet that names issue 4135.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests row)
  - Status: open.

- [ ] T052 File the remediation issue

  - Requirements: FR-016
  - Files: none changed. Create one GitHub issue for the touched violations named in `plan.md`, Complexity Tracking.
  - Acceptance: The issue lists each touched function over 25 lines, each moved module-level function, and each grandfathered directory touched by this change. Its number appears in the pull request body.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests row), to confirm the grandfathered entries the issue names.
  - Status: open.

- [ ] T053 File the menu gate repair issue

  - Requirements: FR-013
  - Files: none changed. Create one GitHub issue that names the absent module `scripts/menu_api_map`.
  - Acceptance: The issue quotes the failing command output. The CI job `menu_reference_drift` at line 732 of `.github/workflows/ci.yml` runs the same command. Its number appears in the pull request body.
  - Verification: `python -m scripts.menu_api_map --check` (Menu reference row). The command fails on `main` because the module is absent. The failure is the expected result for this task.
  - Status: open.

## Final tasks

- [ ] T-LOCAL-GATES Run every applicable local gate

  - Requirements: FR-001 to FR-018
  - Files: none changed. Run each gate from the table in `.github/copilot-instructions.md` that applies to the changed files. Add the diagram gate `diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt` and the citation gate `check-citations src tests`.
  - Acceptance: Each gate reports its expected result. The symbol gate reports only the removed names that `plan.md` lists. The menu gate reports the blocked module. The ratchet reports 190 directories, 33 violations, and 236 total excess. Each command output is saved in the pull request body. A gate that did not run is named as not run.
  - Verification: The table rows named in each phase above, plus the four rows named here.
  - Status: open. Depends on T001 to T053.

- [ ] T-PR Commit, push, and open the pull request

  - Requirements: FR-018
  - Files: the changed files named in `plan.md`
  - Acceptance: One commit uses the message `refactor(lint): reduce function and module size for pylint limits` with the body line `Closes #4135`. The branch is `chore/4135-pylint-size-refactor`. The pull request title matches the commit subject. The body lists the gate results, the removed names, the stale-reference notes, and the issue numbers from T052 and T053.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests row), and the pull request title check.
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI Watch the remote checks

  - Requirements: FR-015
  - Files: none changed
  - Acceptance: Each required check reports success on the latest commit. A failed job is read, repaired, and pushed as a new commit.
  - Verification: `gh pr checks` lists each required check with success on the latest commit.
  - Status: open. Depends on T-PR.

- [ ] T-MERGE Squash merge after authorization

  - Requirements: FR-018
  - Files: none changed
  - Acceptance: The orchestrator authorizes the merge. The `auto-merge` label is added only after every check passes. The squash merge creates one commit on `main`. The branch and the worktree are removed after the merge.
  - Verification: `gh pr view` shows the merged state and the squash commit.
  - Status: open. Depends on T-REMOTE-CI.
