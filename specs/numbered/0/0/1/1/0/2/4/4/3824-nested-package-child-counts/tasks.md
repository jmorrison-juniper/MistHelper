# Tasks: Nested Source Package Child Counts

**Input**: `specs\numbered\0\0\1\1\0\2\4\4\3824-nested-package-child-counts\`

**Prerequisites**: `plan.md`, `spec.md`, and `design\research.md`.

## Format

`T###` is the task ID. `[FR-###]` names the requirement IDs. The status is one of `open`, `verified-present`, `partial`, or `absent`. The status shows the state on remote main at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

No task is safe in parallel. Each slice changes the shared guard files, so slices run one at a time under hold H-2.

## Requirement-to-Test Map

| Requirement | Test or gate |
| - | - |
| FR-001 | Guard totals in `tests/guardrails/test_nested_package_structure.py`, and the inventory rows T029 to T053 |
| FR-002 | `tests/guardrails/test_nested_package_structure.py`, through T001 |
| FR-003 | `tests/guardrails/test_nested_package_structure.py`, and each slice's import-path test |
| FR-004 | `tests/guardrails/test_nested_package_structure.py`, through each slice's guard task |
| FR-005 | `tests/guardrails/nested_package_baseline.json` through T002, and `tests/guardrails/test_src_public_symbol_preservation.py` through T003 |
| FR-006 | Each slice's import-path test `tests/unit/structure/test_nested_slice_w1_NN.py` |
| FR-007 | `python -m pytest tests/guardrails`, through each slice's consumer task |
| FR-008 | Each slice's import-path test, which asserts the new `__module__` value of each moved class |
| FR-009 | Manual hold check in `checklists\slice-gates.md`. No automated test applies. |
| FR-010 | T-LOCAL-GATES |
| FR-011 | Guard totals in SC-003, and tasks T052 and T053 |
| FR-012 | `tests/guardrails/test_move_module_guidance.py`, through T004 |
| FR-013 | `tests/guardrails/test_changelog_fragment_policy.py`, the changelog fragment guard |
| FR-014 | `tests/guardrails/test_nested_package_structure.py`, through T001 |

## Phase 1: Verified Baseline and Open Gaps

- **T001** [FR-002, FR-014] [verified-present] Confirm that `tests/guardrails/test_nested_package_structure.py` exists, measures direct children, and prints the examined count. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T002** [FR-005] [verified-present] Confirm that `tests/guardrails/nested_package_baseline.json` holds 33 entries that match the measured counts. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T003** [FR-005] [verified-present] Confirm that the symbol map in `tests/guardrails/test_src_public_symbol_preservation.py` names the audit renderer and utility text paths. Verify: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`.
- **T004** [FR-012] [partial] Add `python -m pytest tests/guardrails/test_nested_package_structure.py` to the local command of the Nested source package row in `.github/copilot-instructions.md`, line 259. This change ships in slice W1-01. Verify: `python -m pytest tests/guardrails/test_move_module_guidance.py`.

## Phase 2: Wave 1 Slices

Each slice has three tasks. Each task lists the exact paths. A slice must pass its three tasks in one pull request.

### W1-01: `src/mist/intelligence/marvis/actions`

- **T005** [FR-003, FR-004] [absent] Create `src/mist/intelligence/marvis/actions/alarm_actions/` with `__init__.py`. Move `acknowledgement.py` and `alarms.py` into it with `git mv`. Verify: `python -c "import src.mist.intelligence.marvis.actions.alarm_actions.alarms"`.
- **T006** [FR-006, FR-007, FR-008] [absent] Update each consumer of the two old module paths. Record each changed logger name in the pull request. Remove both old paths. Verify: `python -m pytest tests/guardrails`.
- **T007** [FR-005, FR-012, FR-013, FR-014] [absent] Set the expected totals to 32 violations and 235 excess. Remove the baseline entry for `src/mist/intelligence/marvis/actions`. Add `tests/unit/structure/test_nested_slice_w1_01.py` and `changelog.d/issue-3824-marvis-alarm-actions.md`. Apply T004. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-02: `src/mist/intelligence/troubleshooting/rf_diagnostics`

- **T008** [FR-003, FR-004] [absent] Create `output/` and `analysis/` under `src/mist/intelligence/troubleshooting/rf_diagnostics/`, each with `__init__.py`. Move `file_naming.py` and `recording.py` to `output/`. Move `audit.py` and `spectrum.py` to `analysis/`. Use `git mv`. Verify: `python -c "import src.mist.intelligence.troubleshooting.rf_diagnostics.output.recording"`.
- **T009** [FR-006, FR-007, FR-008] [absent] Update each consumer of the four old module paths. Record each changed logger name. Remove the four old paths. Verify: `python -m pytest tests/guardrails`.
- **T010** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 31 violations and 233 excess. Remove the baseline entry for `src/mist/intelligence/troubleshooting/rf_diagnostics`. Add `tests/unit/structure/test_nested_slice_w1_02.py` and `changelog.d/issue-3824-rf-diagnostics-packages.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-03: `src/mist/networking/network`

- **T011** [FR-003, FR-004] [absent] Create `src/mist/networking/network/routing_support/` with `__init__.py`. Move `_routing_utils_forwarding.py`, `_routing_utils_parsing.py`, `_routing_utils_payload.py`, and `_routing_utils_routing.py` into it. Use `git mv`. Verify: `python -c "import src.mist.networking.network.routing_support._routing_utils_parsing"`.
- **T012** [FR-006, FR-007, FR-008] [absent] Update each consumer of the four old module paths. Record each changed logger name. Remove the four old paths. Verify: `python -m pytest tests/guardrails`.
- **T013** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 30 violations and 231 excess. Remove the baseline entry for `src/mist/networking/network`. Add `tests/unit/structure/test_nested_slice_w1_03.py` and `changelog.d/issue-3824-network-routing-support.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-04: `src/mist/realtime/websocket`

- **T014** [FR-003, FR-004] [absent] Create `service_ping/` and `command_context/` under `src/mist/realtime/websocket/`, each with `__init__.py`. Move `service_ping_discovery.py` and `service_ping_manager.py` to `service_ping/`. Move `commands.py` and `context.py` to `command_context/`. Use `git mv`. Verify: `python -c "import src.mist.realtime.websocket.command_context.commands"`.
- **T015** [FR-006, FR-007, FR-008] [absent] Update each consumer of the four old module paths. Record each changed logger name. Remove the four old paths. Verify: `python -m pytest tests/guardrails`.
- **T016** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 29 violations and 229 excess. Remove the baseline entry for `src/mist/realtime/websocket`. Add `tests/unit/structure/test_nested_slice_w1_04.py` and `changelog.d/issue-3824-websocket-packages.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-05: `src/mist/access/api`

- **T017** [FR-003, FR-004] [absent] Confirm that `src/mist/resources/org` holds four counted children. Stop the slice if it holds five. Move `src/mist/access/api/response_integrity.py` to `src/mist/access/response_integrity.py`. Move `src/mist/access/api/client_fingerprint_operations.py` to `src/mist/resources/org/client_fingerprint_operations.py`. Verify: `python -c "import src.mist.access.response_integrity"`.
- **T018** [FR-006, FR-007, FR-008] [absent] Update each consumer found by `git grep -n "mist.access.api.response_integrity\|mist.access.api.client_fingerprint_operations"`. The known consumers are `api_data_fetcher.py`, `api_fetch_utils.py`, `tenant_fetch.py`, the AP warning client, `src/operations/exporting/export/wifi_clients_exporter.py`, `src/operations/exporting/export/simple_endpoint_exporter.py`, and two unit tests. Verify: `python -m pytest tests/guardrails`.
- **T019** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 28 violations and 227 excess. Remove the baseline entry for `src/mist/access/api`. Add `tests/unit/structure/test_nested_slice_w1_05.py` and `changelog.d/issue-3824-access-api-moves.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-06: `src/mist/resources/inventory`

- **T020** [FR-003, FR-004] [absent] Create `org_inventory/` under `src/mist/resources/inventory/` with `__init__.py`. Move `org_device_inventory_msp.py`, `org_device_inventory_summary.py`, and `org_device_inventory_summary_facade.py` into it. Use `git mv`. Verify: `python -c "import src.mist.resources.inventory.org_inventory.org_device_inventory_msp"`.
- **T021** [FR-006, FR-007, FR-008] [absent] Update each consumer of the three old module paths. Record each changed logger name. Remove the three old paths. Verify: `python -m pytest tests/guardrails`.
- **T022** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 27 violations and 225 excess. Remove the baseline entry for `src/mist/resources/inventory`. Add `tests/unit/structure/test_nested_slice_w1_06.py` and `changelog.d/issue-3824-inventory-org-package.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-07: `src/operations/execution/ssid_consolidation`

- **T023** [FR-003, FR-004] [absent] Create `phases/` under `src/operations/execution/ssid_consolidation/` with `__init__.py`. Move `_ssid_template_phase1.py`, `_ssid_template_phase2.py`, `_ssid_template_phase3.py`, and `_ssid_template_phase45.py` into it. Use `git mv`. Verify: `python -c "import src.operations.execution.ssid_consolidation.phases._ssid_template_phase1"`.
- **T024** [FR-006, FR-007, FR-008] [absent] Update each consumer of the four old module paths. Record each changed logger name. Remove the four old paths. Verify: `python -m pytest tests/guardrails`.
- **T025** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 26 violations and 223 excess. Remove the baseline entry for `src/operations/execution/ssid_consolidation`. Add `tests/unit/structure/test_nested_slice_w1_07.py` and `changelog.d/issue-3824-ssid-phases.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

### W1-08: `src/foundation/models/dataclasses`

- **T026** [FR-003, FR-004] [absent] Create `maps/`, `site/`, `export/`, and `runtime/` under `src/foundation/models/dataclasses/`, each with `__init__.py`. Move the 15 modules listed for W1-08 in `plan.md` to their packages. Use `git mv`. Verify: `python -c "import src.foundation.models.dataclasses.runtime.batch_worker"`.
- **T027** [FR-006, FR-007, FR-008] [absent] Update each consumer of the 15 old module paths. Find the consumers with `git grep -n "models.dataclasses"`. Record each changed logger name. Remove the 15 old paths. Verify: `python -m pytest tests/guardrails`.
- **T028** [FR-005, FR-013, FR-014] [absent] Set the expected totals to 25 violations and 213 excess. Remove the baseline entry for `src/foundation/models/dataclasses`. Add `tests/unit/structure/test_nested_slice_w1_08.py` and `changelog.d/issue-3824-dataclasses-packages.md`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

## Phase 3: Wave 2 Remediation

Each task ends when its directory holds five or fewer counted children. Each new package holds five or fewer counted children. The module groups are written in the change notes of each slice under D-9.

- **T029** [FR-001, FR-003, FR-004] [absent] W2-01: `src/mist/resources/device`, 14 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T030** [FR-001, FR-003, FR-004] [absent] W2-02: `src/mist/resources/gateway`, 16 counted children. Holds: none. Keep `overrides/` and `ssr_registration/` in place. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T031** [FR-001, FR-003, FR-004] [absent] W2-03: `src/mist/resources/site/address_audit`, 13 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T032** [FR-001, FR-003, FR-004] [absent] W2-04: `src/mist/intelligence/reports`, 18 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T033** [FR-001, FR-003, FR-004] [absent] W2-05: `src/operations/execution/firmware`, 11 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T034** [FR-001, FR-003, FR-004] [absent] W2-06: `src/operations/execution/capture`, 12 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T035** [FR-001, FR-003, FR-004] [absent] W2-07: `src/operations/execution/ssh`, 8 counted children. Holds: none. Do not add a child to `ssh/config`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T036** [FR-001, FR-003, FR-004] [absent] W2-08: `src/interfaces/visualization/ui`, 8 counted children. Holds: none. Do not add a child to `ui/execution`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T037** [FR-001, FR-003, FR-004, FR-009] [absent] W2-09: `src/interfaces/monitoring/metrics_gateway`, 8 counted children. Holds: H-6, issue 4009. Start only after issue 4009 closes or transfers the work. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

## Phase 4: Wave 3 Remediation

- **T038** [FR-001, FR-003, FR-004, FR-009] [absent] W3-01: `src/foundation/support/utils`, 18 counted children. Holds: H-1 for `operation_registry.py` and H-5 for `zscaler_catalogue.py`. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T039** [FR-001, FR-003, FR-004] [absent] W3-02: `src/foundation/support/refactors/serial_cc`, 9 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T040** [FR-001, FR-003, FR-004, FR-009] [absent] W3-03: `src/foundation/support/refactors`, 33 counted children. Holds: H-1 for `endpoint_primary_key_strategies.py` and H-3 for `initialize_mist_session.py`. Start after T039. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T041** [FR-001, FR-003, FR-004] [absent] W3-04: `src/interfaces/visualization/maps/launcher`, 8 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T042** [FR-001, FR-003, FR-004] [absent] W3-05: `src/interfaces/visualization/maps`, 19 counted children. Holds: none. Start after T041. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T043** [FR-001, FR-003, FR-004] [absent] W3-06: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade`, 6 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T044** [FR-001, FR-003, FR-004] [absent] W3-07: `src/interfaces/portals/upgrade_portal/compare`, 7 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T045** [FR-001, FR-003, FR-004] [absent] W3-08: `src/interfaces/portals/upgrade_portal/runtime`, 9 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T046** [FR-001, FR-003, FR-004] [absent] W3-09: `src/interfaces/portals/upgrade_portal/capture`, 9 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T047** [FR-001, FR-003, FR-004] [absent] W3-10: `src/interfaces/portals/upgrade_portal/app/routes`, 12 counted children. Holds: none. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T048** [FR-001, FR-003, FR-004] [absent] W3-11: `src/interfaces/portals/upgrade_portal/app`, 7 counted children. Holds: none. Start after T047. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T049** [FR-001, FR-003, FR-004] [absent] W3-12: `src/interfaces/portals/upgrade_portal/upgrade`, 21 counted children. Holds: none. Start after T043. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T050** [FR-001, FR-003, FR-004] [absent] W3-13: `src/interfaces/portals/upgrade_portal`, 11 counted children. Holds: none. Start after T044 to T049. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T051** [FR-001, FR-003, FR-004, FR-009] [absent] W3-14: `src/operations/exporting/export`, 48 counted children. Holds: H-4 for `data_exporter.py` and H-7 for issue 4168. Start after W1-05. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

## Phase 5: Violations Owned by Issue 4168

This record schedules no slice for these directories. Issue 4168 owns both.

- **T052** [FR-001, FR-011] [open] O-01: `src/operations/exporting/juniper_rma/model`, 6 counted children. Owner: issue 4168. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T053** [FR-001, FR-011] [open] O-02: `src/operations/exporting/juniper_rma/workflows`, 7 counted children. Owner: issue 4168. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

## Phase 6: Final Tasks

- **T-LOCAL-GATES** (T054) [FR-010] [open] Run each gate in the Local gates table that applies to the changed files. The gates are compile for `MistHelper.py` only, `python -m ruff check .`, `python -m black --check .`, `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, the changed test files, `python -m pytest tests/guardrails`, radon with complexity-gate, bandit, pylint, vulture, pydocstyle, interrogate, symbol-diff for each changed file, the test-quality procedure, and ste-linter for changed Markdown files. Verify: `python -m pytest tests/guardrails`.
- **T-PR** (T055) [FR-013] [open] Commit with a Conventional Commits subject, for example `refactor(mist): move marvis alarm actions into a package`. Add `Refs #3824` to the body. Do not use `Closes`. Push `refactor/3824-<slice-slug>` and open one pull request. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.
- **T-REMOTE-CI** (T056) [FR-010] [open] Wait for each required check with `gh pr checks <number> --watch`. Confirm that the `ci.yml` run passes on the exact pull request head. Verify: `python -m pytest tests/guardrails`.
- **T-MERGE** (T057) [FR-004] [open] Enable auto-merge only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Use a squash merge. Confirm that the guard totals on the merged head match the ratchet sequence. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`.

Caution: a failed guard check after a move leaves the import graph changed. Finish T005 to T007 in one pull request, and do not merge a partial slice.

## Completion Conditions

- Each task in Phases 2 to 4 has status `verified-present` on remote main.
- The guard reports 2 violations and 3 total excess. Both violations belong to issue 4168.
- Issue 3824 closes only after issue 4168 closes its two violations.
