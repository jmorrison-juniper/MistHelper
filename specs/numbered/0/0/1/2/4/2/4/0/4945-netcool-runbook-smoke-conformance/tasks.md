# Tasks: Netcool Runbook Smoke Package Conformance

**Input**: Design documents in `specs/numbered/0/0/1/2/4/2/4/0/4945-netcool-runbook-smoke-conformance/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/`.

**Tests**: The specification and the constitution require tests. Each guard test fails first on the untouched package. Each unit test for a new class fails first on a stub that raises `NotImplementedError`. The register of tests appears in the section "Test Register".

**Ownership**: Touch only the files that the change map in `plan.md` names. Do not modify `.specify/feature.json`, `README.md`, `CHANGELOG.md`, or `pyproject.toml`. Add files by explicit path. The structure guard reads tracked files only.

**Environment**: Run Python from the `.venv` at the repository root. Run each `gh` command after this line: `$env:GH_HOST='github.com'` and then `$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other [P] tasks of its phase, because it edits a different file.
- **[Story]**: The user story that the task serves. Stories US1 to US4 come from `spec.md`.
- Each task carries requirement IDs, exact paths, an acceptance statement, one verification command, and a status. A status is `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Baseline

**Purpose**: Record the facts that the change depends on, before the first edit.

- [ ] T001 Confirm the fourteen functions and their limits on `main`. FR-001, FR-002, FR-003, FR-007.
  - Files: `scripts/netcool_runbook_smoke/checks/scope.py`, `scripts/netcool_runbook_smoke/checks/searches.py`, `scripts/netcool_runbook_smoke/client.py`.
  - Acceptance: The remote rows R74 to R87 in `design/research.md` match the line numbers of the remote blobs.
  - Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate, after T006).
  - Status: verified-present.

- [ ] T002 Confirm the CI gate gap and the exclusions on `main`. FR-014.
  - Files: `.github/workflows/ci.yml`, `pyproject.toml`.
  - Acceptance: The rows R18 to R22 show that the five variables name no package path. The rows R27 to R29 show the three exclusions.
  - Verify: `python -m ruff check .` (Lint gate, to confirm the current state of the repository).
  - Status: verified-present.

- [ ] T003 Record the baseline on the untouched branch. FR-021, FR-022.
  - Files: `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py`, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py`, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py`, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py`.
  - Acceptance: The file `design/quickstart.md` step 3 records the collected count, the pass count, the console lines, and the evidence keys of the fixed fake run.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke` (Tests gate).
  - Status: open.

- [ ] T004 Measure the first results of each gate on the untouched package. FR-014, FR-019.
  - Files: `scripts/netcool_runbook_smoke/`.
  - Acceptance: The results of mypy strict, radon, Vulture, pydocstyle, Interrogate, the explicit Ruff run, and the explicit Bandit run are recorded in the working notes. The notes stay outside the repository.
  - Verify: `python -m mypy scripts/netcool_runbook_smoke/__init__.py --config-file pyproject.toml` (Types gate).
  - Status: open.

- [ ] T005 Measure the baseline coverage of the package. FR-020.
  - Files: `tests/unit/scripts/netcool_runbook_smoke/`.
  - Acceptance: The coverage value of the package is recorded before the first edit.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke --cov=scripts.netcool_runbook_smoke --cov-report=term` (Coverage gate, package target).
  - Status: open.

## Phase 2: Guards

**Purpose**: Build the guards first, so each later change meets a failing test.

- [ ] T006 Add the structure scanner to `tests/guardrails/test_nested_package_structure.py`. FR-001 to FR-006.
  - Files: `tests/guardrails/test_nested_package_structure.py`.
  - Acceptance: TEST-01 to TEST-04 pass on fixtures with known counts. The scanner prints the examined counts. On the untouched package, the scanner reports the fourteen functions.
  - Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate).
  - Status: open.

- [ ] T007 Add the gate guard tests to `tests/guardrails/test_ci_gate_triggers.py`. FR-014, FR-015, FR-016.
  - Files: `tests/guardrails/test_ci_gate_triggers.py`.
  - Acceptance: TEST-06 and TEST-07 fail on the untouched `ci.yml` and pass after Phase 5.
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py` (Tests gate).
  - Status: open.

- [ ] T008 Add the injected-violation tests to `tests/guardrails/test_ci_gate_triggers.py`. FR-017. Depends on T007.
  - Files: `tests/guardrails/test_ci_gate_triggers.py`.
  - Acceptance: TEST-08 and TEST-09 prove that at least two steps fail on an injected violation. Each test uses a temporary copy and writes no file to the repository.
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py` (Tests gate).
  - Status: open.

## Phase 3: User Story 1, sub-package layout

**Purpose**: Move the modules into the sub-packages of `plan.md`. Keep the function bodies unchanged in this phase.

- [ ] T009 [US1] Create `settings/` and move `SmokeSettings`, `SettingsLoader`, `EnvFileReader`, and `IdentityRules`. FR-008, FR-009.
  - Files: `scripts/netcool_runbook_smoke/settings/__init__.py`, `scripts/netcool_runbook_smoke/settings/smoke_settings.py`, `scripts/netcool_runbook_smoke/settings/settings_loader.py`, `scripts/netcool_runbook_smoke/settings/identity_rules.py`, `scripts/netcool_runbook_smoke/__main__.py`, `scripts/netcool_runbook_smoke/command.py`.
  - Acceptance: Each new module imports. The old names leave `__main__.py` and `command.py`.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.settings.settings_loader"` (Import smoke gate).
  - Status: open.

- [ ] T010 [US1] Create `transport/` with `call_record.py`, `pages.py`, `call_governor.py`, `timed_call.py`, and `read_client.py`. FR-008, FR-009. Depends on T009.
  - Files: `scripts/netcool_runbook_smoke/transport/__init__.py`, `scripts/netcool_runbook_smoke/transport/call_record.py`, `scripts/netcool_runbook_smoke/transport/pages.py`, `scripts/netcool_runbook_smoke/transport/call_governor.py`, `scripts/netcool_runbook_smoke/transport/timed_call.py`, `scripts/netcool_runbook_smoke/transport/read_client.py`, `scripts/netcool_runbook_smoke/client.py`.
  - Acceptance: `CallGovernor._run_with_timeout` moves into the module `timed_call.py` with its body unchanged. The file `client.py` is deleted at the end of T016.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.transport.read_client"` (Import smoke gate).
  - Status: open.

- [ ] T011 [US1] Create `reporting/` with `sources.py`, `redaction.py`, `evidence.py`, and `logging_setup.py`. FR-008, FR-009.
  - Files: `scripts/netcool_runbook_smoke/reporting/__init__.py`, `scripts/netcool_runbook_smoke/reporting/sources.py`, `scripts/netcool_runbook_smoke/reporting/redaction.py`, `scripts/netcool_runbook_smoke/reporting/evidence.py`, `scripts/netcool_runbook_smoke/reporting/logging_setup.py`, `scripts/netcool_runbook_smoke/documents.py`, `scripts/netcool_runbook_smoke/command.py`.
  - Acceptance: Each class keeps its name and its body. The `LogSetup.PACKAGE_LOGGERS` tuple keeps its value.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.reporting.evidence"` (Import smoke gate).
  - Status: open.

- [ ] T012 [US1] Create `checks/core/` with `results.py`, `context.py`, and `support.py`. Empty `checks/__init__.py`. FR-008, FR-009.
  - Files: `scripts/netcool_runbook_smoke/checks/__init__.py`, `scripts/netcool_runbook_smoke/checks/core/__init__.py`, `scripts/netcool_runbook_smoke/checks/core/results.py`, `scripts/netcool_runbook_smoke/checks/core/context.py`, `scripts/netcool_runbook_smoke/checks/core/support.py`, `scripts/netcool_runbook_smoke/checks/support.py`.
  - Acceptance: `checks/__init__.py` holds no class and no re-export. `checks/support.py` is deleted.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.checks.core.context"` (Import smoke gate).
  - Status: open.

- [ ] T013 [US1] Create `checks/identity/` with `loading.py`, `privilege.py`, `usage.py`, and `identity_checks.py`. Delete `checks/identity.py`. FR-008, FR-009.
  - Files: `scripts/netcool_runbook_smoke/checks/identity/__init__.py`, `scripts/netcool_runbook_smoke/checks/identity/loading.py`, `scripts/netcool_runbook_smoke/checks/identity/privilege.py`, `scripts/netcool_runbook_smoke/checks/identity/usage.py`, `scripts/netcool_runbook_smoke/checks/identity/identity_checks.py`, `scripts/netcool_runbook_smoke/checks/identity.py`.
  - Acceptance: Each class keeps its name and its body.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.checks.identity.identity_checks"` (Import smoke gate).
  - Status: open.

- [ ] T014 [US1] Create `checks/scope/` with `filters.py`, `sites.py`, and `inventory.py`. Delete `checks/scope.py`. FR-008, FR-009.
  - Files: `scripts/netcool_runbook_smoke/checks/scope/__init__.py`, `scripts/netcool_runbook_smoke/checks/scope/filters.py`, `scripts/netcool_runbook_smoke/checks/scope/sites.py`, `scripts/netcool_runbook_smoke/checks/scope/inventory.py`, `scripts/netcool_runbook_smoke/checks/scope.py`.
  - Acceptance: The existing ten functions move with their bodies unchanged in this task. The split happens in Phase 4.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.checks.scope.inventory"` (Import smoke gate).
  - Status: open.

- [ ] T015 [US1] Create `checks/searches/` with `observations.py`, `families.py`, `counts.py`, and `search_checks.py`. Delete `checks/searches.py`. FR-008, FR-009.
  - Files: `scripts/netcool_runbook_smoke/checks/searches/__init__.py`, `scripts/netcool_runbook_smoke/checks/searches/observations.py`, `scripts/netcool_runbook_smoke/checks/searches/families.py`, `scripts/netcool_runbook_smoke/checks/searches/counts.py`, `scripts/netcool_runbook_smoke/checks/searches/search_checks.py`, `scripts/netcool_runbook_smoke/checks/searches.py`.
  - Acceptance: Each class keeps its name and its body.
  - Verify: `python -c "import scripts.netcool_runbook_smoke.checks.searches.search_checks"` (Import smoke gate).
  - Status: open.

- [ ] T016 [US1] Move `RunReport` into `__main__.py`, delete `client.py`, `command.py`, and `documents.py`. FR-010. Depends on T009 to T015.
  - Files: `scripts/netcool_runbook_smoke/__main__.py`, `scripts/netcool_runbook_smoke/client.py`, `scripts/netcool_runbook_smoke/command.py`, `scripts/netcool_runbook_smoke/documents.py`.
  - Acceptance: `__main__.py` holds `CheckSequence`, `SmokeCommand`, and `RunReport`. Its entry point block stays at its last line. No old module file remains.
  - Verify: `python -m scripts.netcool_runbook_smoke --help` (Safe sweep gate, read-only option output).
  - Status: open.

- [ ] T017 [P] [US1] Update the import paths in `test_netcool_smoke_client.py`. FR-009. Depends on T010.
  - Files: `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py`.
  - Acceptance: Every import names a new module. No alias is added.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` (Tests gate).
  - Status: open.

- [ ] T018 [P] [US1] Update the import paths in `test_netcool_smoke_checks.py`. FR-009. Depends on T012 to T015.
  - Files: `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py`.
  - Acceptance: Every import names a new module. No alias is added.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` (Tests gate).
  - Status: open.

- [ ] T019 [P] [US1] Update the import paths in `test_netcool_smoke_command.py`, `test_netcool_smoke_documents.py`, and `test_netcool_runbook_document.py`. FR-009. Depends on T011 and T016.
  - Files: `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py`, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py`.
  - Acceptance: Every import names a new module. No alias is added.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke` (Full tests gate for the package).
  - Status: open.

- [ ] T020 [US1] Add TEST-10 and TEST-17 to `tests/guardrails/test_nested_package_structure.py`. FR-010, FR-023. Depends on T016 and T019.
  - Files: `tests/guardrails/test_nested_package_structure.py`.
  - Acceptance: TEST-10 imports every new module, proves that each removed module path fails, and proves the logger prefix rule. TEST-17 proves that no package module imports an HTTP library.
  - Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate).
  - Status: open.

## Phase 4: User Story 1, function limits

**Purpose**: Split the fourteen functions. Each task edits one module family, so the tasks run in parallel.

- [ ] T021 [P] [US1] Split `filter_verdict`, `record`, and the request list of `smk_09` in `checks/scope/filters.py`. FR-001 to FR-004, FR-007. Depends on T014.
  - Files: `scripts/netcool_runbook_smoke/checks/scope/filters.py`, `scripts/netcool_runbook_smoke/checks/scope/sites.py`.
  - Acceptance: `TypeFilterVerdict`, `ProbeRecorder`, and `FilterRequests` exist. Each body holds five statements or fewer per block.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` (Tests gate).
  - Status: open.

- [ ] T022 [P] [US1] Split `smk_08`, `_site_part`, and `first_site` in `checks/scope/sites.py`. FR-001 to FR-004, FR-007. Depends on T021.
  - Files: `scripts/netcool_runbook_smoke/checks/scope/sites.py`.
  - Acceptance: `SiteSearchRoll`, `SiteSearchJudge`, and the helpers of `SiteListing` exist.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` (Tests gate).
  - Status: open.

- [ ] T023 [P] [US1] Split `count_sum`, `webhook_part`, `smk_10`, and `_judge` in `checks/scope/inventory.py`. FR-001 to FR-004, FR-007. Depends on T014.
  - Files: `scripts/netcool_runbook_smoke/checks/scope/inventory.py`.
  - Acceptance: `InventorySummaries` and `InventoryJudge` exist. `InventoryChecks` holds five methods or fewer.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` (Tests gate).
  - Status: open.

- [ ] T024 [P] [US1] Split `smk_06` and `smk_07` in `checks/searches/search_checks.py`. FR-001 to FR-004, FR-007. Depends on T015.
  - Files: `scripts/netcool_runbook_smoke/checks/searches/search_checks.py`.
  - Acceptance: `SearchChecks` holds four methods, and `SearchRollup` holds the roll-up methods.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` (Tests gate).
  - Status: open.

- [ ] T025 [P] [US1] Split `_attempt` and `_run_with_timeout` across `transport/call_governor.py` and `transport/timed_call.py`. FR-001 to FR-004, FR-007. Depends on T010.
  - Files: `scripts/netcool_runbook_smoke/transport/call_governor.py`, `scripts/netcool_runbook_smoke/transport/timed_call.py`.
  - Acceptance: `CallGovernor` holds five methods or fewer. `TimedCall.run` holds the timeout rules, and the fault re-raises in the caller.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` (Tests gate).
  - Status: open.

- [ ] T026 [US1] Run the structure scanner on the restructured package. FR-001 to FR-006. Depends on T020 to T025.
  - Files: `tests/guardrails/test_nested_package_structure.py`.
  - Acceptance: The scanner reports zero violations for the package.
  - Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate).
  - Status: open.

## Phase 5: User Story 2, CI gates

**Purpose**: Add the package path to each gate. Repair each finding that the gate reports.

- [ ] T027 [US2] Add the package path to the five gate variables in `ci.yml`. FR-014. Depends on T004.
  - Files: `.github/workflows/ci.yml`.
  - Acceptance: `MYPY_PATHS`, `RADON_PATHS`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` name `scripts/netcool_runbook_smoke`. `MYPY_PATHS` names `scripts/netcool_runbook_smoke/__init__.py` (decision D-13).
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py` (Tests gate).
  - Status: open.

- [ ] T028 [US2] Add an explicit Ruff step and an explicit Bandit step to `ci.yml`. FR-014, FR-015. Depends on T004.
  - Files: `.github/workflows/ci.yml`.
  - Acceptance: The Ruff step runs `ruff check scripts/netcool_runbook_smoke`. The Bandit step runs `bandit -c pyproject.toml -r scripts/netcool_runbook_smoke -q`. Each step has a count step.
  - Verify: `python -m ruff check scripts/netcool_runbook_smoke` (Lint gate, package target).
  - Status: open.

- [ ] T029 [US2] Add one count step to each of the seven gate jobs in `ci.yml`. FR-015. Depends on T027 and T028.
  - Files: `.github/workflows/ci.yml`.
  - Acceptance: Each count step prints the number of Python files of the package and fails at zero. The job count stays unchanged (FR-018).
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py` (Tests gate).
  - Status: open.

- [ ] T030 [US2] Repair each mypy strict finding in the package. FR-019. Depends on T026.
  - Files: the modules under `scripts/netcool_runbook_smoke/`.
  - Acceptance: `mypy` reports `Success` on the package. No `# type: ignore` line is added.
  - Verify: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py scripts/netcool_runbook_smoke/__init__.py --config-file pyproject.toml` (Types gate).
  - Status: open.

- [ ] T031 [US2] Repair each radon, Vulture, pydocstyle, and Interrogate finding in the package. FR-014. Depends on T026.
  - Files: the modules under `scripts/netcool_runbook_smoke/`.
  - Acceptance: Each gate reports zero findings for the package, and Interrogate reports 90 percent or above.
  - Verify: `pydocstyle scripts/netcool_runbook_smoke` and `interrogate scripts/netcool_runbook_smoke --fail-under 90` (Docstrings gate, package target).
  - Status: open.

- [ ] T032 [US2] Confirm that the CI job count is unchanged. FR-018. Depends on T029.
  - Files: `.github/workflows/ci.yml`.
  - Acceptance: The count of jobs under `jobs:` equals the count on `main`.
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py` (Tests gate).
  - Status: open.

## Phase 6: User Story 3, comments and logging

**Purpose**: Rewrite the comments that only restate the code. Add the logs that Principle VII requires.

- [ ] T033 [US3] Add a comment on the first physical line of each executable statement. FR-011. Depends on T026.
  - Files: each module under `scripts/netcool_runbook_smoke/`.
  - Acceptance: The test TEST-05 passes. Each comment states a cause and a purpose.
  - Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate).
  - Status: open.

- [ ] T034 [US3] Add the info log before and the debug log after each touched action. FR-013. Depends on T026.
  - Files: each module under `scripts/netcool_runbook_smoke/`.
  - Acceptance: Each new or touched action has the two log lines. Each log line uses `%s` formatting and ASCII text.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke` (Full tests gate for the package).
  - Status: open.

- [ ] T035 [US3] Run the seeded sample audit and repair each failing line. FR-012. Depends on T033 and T034.
  - Files: each module under `scripts/netcool_runbook_smoke/`.
  - Acceptance: At least 36 of the 40 sampled comment lines pass (decision D-24).
  - Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate).
  - Status: open.

## Phase 7: User Story 4, behavior and documentation

**Purpose**: Prove that the operator sees the same result. Add the changelog fragment.

- [ ] T036 [US4] Compare the console lines and the evidence keys with the T003 baseline. FR-022. Depends on T026.
  - Files: `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`.
  - Acceptance: The lines and the keys match. A difference stops the task and the change returns to the owner of the difference.
  - Verify: `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py` (Tests gate).
  - Status: open.

- [ ] T037 [US4] Confirm that the runbook command starts the package. FR-010. Depends on T016.
  - Files: `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`.
  - Acceptance: The command `python -m scripts.netcool_runbook_smoke --help` prints the option list. The runbook text does not change.
  - Verify: `python -m scripts.netcool_runbook_smoke --help` (Safe sweep gate, read-only option output).
  - Status: open.

- [ ] T038 [P] [US4] Add the changelog fragment. FR-024.
  - Files: `changelog.d/issue-4945-netcool-runbook-smoke-conformance.md`.
  - Acceptance: The fragment has one `### Changed` heading and one bullet that names issue 4945.
  - Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests gate).
  - Status: open.

## Phase 8: Final gates and delivery

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files. FR-020, FR-021, FR-025. Depends on T026 to T038.
  - Files: each changed file in the change map.
  - Acceptance: Ruff, Black, mypy strict, the package tests, and the guard tests all pass. The package coverage is 95 percent or above.
  - Acceptance: The test quality gate, radon, Bandit, Vulture, pydocstyle, Interrogate, symbol-diff for each changed file, the old-path search, the import smoke, and the count steps all pass.
  - Acceptance: The results go into the pull request body.
  - Verify: `python -m ruff check .` (Lint gate), `python -m black --check .` (Format gate), and `python -m pytest tests/unit/scripts/netcool_runbook_smoke` (Tests gate).
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request. FR-025. Depends on T-LOCAL-GATES.
  - Files: the changed files of the change map only.
  - Acceptance: The commit subject is `refactor(netcool-smoke): conform the package to the constitution and CI gates`. The branch is `chore/4945-netcool-runbook-smoke-conformance`. The body contains `Closes #4945`, the gate results, the coverage value, the symbol-diff results, and the count of removed non-comment lines.
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py` (Tests gate).
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote CI run. SC-003, SC-008. Depends on T-PR.
  - Files: `.github/workflows/ci.yml`.
  - Acceptance: Every required check passes. The seven gates print a count above zero. The job count is unchanged.
  - Verify: `gh pr checks <number> --watch` (Tests gate, remote).
  - Status: open.

- [ ] T-MERGE Merge the approved pull request. Principle IV steps 9 to 11. Depends on T-REMOTE-CI.
  - Files: `.github/workflows/container-build.yml`.
  - Acceptance: The merge uses one squash commit. The orchestrator authorizes the merge. After the merge, the workflow `container-build.yml` completes on the merged revision, and its image revision label equals the merged commit SHA. Step 12 does not apply (decision D-22).
  - Verify: `gh run list --workflow container-build.yml --branch main --limit 1` (Safe sweep gate, read-only status).
  - Status: open.

## Test Register

| ID | Test | File | Kind | Requirement |
| - | - | - | - | - |
| TEST-01 | Function limits: code lines, parameters, body blocks, and statements | `tests/guardrails/test_nested_package_structure.py` | Guard fixture | FR-001 to FR-003 |
| TEST-02 | Module top-level names limit, logger included | `tests/guardrails/test_nested_package_structure.py` | Guard fixture | FR-005 |
| TEST-03 | Directory children limit, `__init__.py` excluded | `tests/guardrails/test_nested_package_structure.py` | Guard fixture | FR-006 |
| TEST-04 | Class methods limit | `tests/guardrails/test_nested_package_structure.py` | Guard fixture | FR-004 |
| TEST-05 | Each statement carries a comment on its first physical line. Each function with a Mist call, a file write, or a file read holds an info log before that action | `tests/guardrails/test_nested_package_structure.py` | Guard | FR-011, FR-013 |
| TEST-06 | Seven gates name the package path in `ci.yml`, and the count of job keys equals the recorded count | `tests/guardrails/test_ci_gate_triggers.py` | Guard | FR-014, FR-016, FR-018 |
| TEST-07 | Each gate step prints a count and fails at zero | `tests/guardrails/test_ci_gate_triggers.py` | Guard | FR-015, FR-016 |
| TEST-08 | Injected Ruff violation fails the explicit Ruff step | `tests/guardrails/test_ci_gate_triggers.py` | Injected | FR-017 |
| TEST-09 | Injected Vulture violation fails the Vulture step | `tests/guardrails/test_ci_gate_triggers.py` | Injected | FR-017 |
| TEST-10 | Import smoke, removed paths fail, and the logger prefix rule holds | `tests/guardrails/test_nested_package_structure.py` | Guard | FR-008, FR-010 |
| TEST-11 | `TimedCall.run` returns the response, a timeout, or the re-raised fault | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` | Unit | FR-021 |
| TEST-12 | `TypeFilterVerdict` and `ProbeRecorder` return FAIL, WARN, and PASS outcomes | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` | Unit | FR-021 |
| TEST-13 | `SiteSearchRoll` and `SiteSearchJudge` return the site outcomes | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` | Unit | FR-021 |
| TEST-14 | `InventorySummaries.count_sum` and `webhook_part` return the counts and the text | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` | Unit | FR-021 |
| TEST-15 | `SearchRollup` returns the roll-up status and text | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` | Unit | FR-021 |
| TEST-16 | `CallGovernor` refuses an attempt when the budget is spent | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` | Unit | FR-021 |
| TEST-17 | No package module imports an HTTP library, and the Mist REST call is `APISession.mist_get` only | `tests/guardrails/test_nested_package_structure.py` | Guard | FR-023 |

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Baseline)**: No dependency. T001 and T002 are verified. T003 to T005 run before the first edit.
- **Phase 2 (Guards)**: Depends on Phase 1. T006 must fail on the untouched package.
- **Phase 3 (Sub-package layout)**: Depends on Phase 2. T009 to T015 run in order, because each move changes the import paths of the next move. T017 to T019 follow the moves they update.
- **Phase 4 (Function limits)**: Depends on Phase 3. T021 to T025 edit different module families, so they run in parallel.
- **Phase 5 (CI gates)**: T027 and T028 depend on T004. T029 depends on T027 and T028. T030 and T031 depend on T026.
- **Phase 6 (Comments and logging)**: Depends on T026. T035 depends on T033 and T034.
- **Phase 7 (Behavior)**: Depends on T026. T037 depends on T016.
- **Phase 8 (Final gates)**: Depends on every earlier phase.

### Parallel Opportunities

- T021, T022, T023, T024, and T025 run in parallel after their dependencies.
- T017, T018, and T019 run in parallel after their dependencies.
- T038 runs in parallel with the Phase 5 and Phase 6 tasks.

## Guard Rules

- Warning: a guard that cannot read its input must fail. A guard that reports zero examined files passes silently, so each guard prints its examined count.
- Caution: a new test file in `tests/guardrails/` adds a child to a folder that holds 79 children. Put each guard into the existing file that the plan names.
- Caution: a new test file in `tests/unit/scripts/netcool_runbook_smoke/` adds a sixth child to a folder that holds five children. Put each new test into the existing module that the plan names.
- Caution: the test-quality analyzer compares file paths with its baseline. Do not rewrite the baseline to hide a new finding.

## Notes

- A task finishes only after its verification command passes on the changed files.
- A task that finds a conflict stops, and it reports the conflict to the orchestrator.
- The working notes of T003 to T005 stay outside the repository.
