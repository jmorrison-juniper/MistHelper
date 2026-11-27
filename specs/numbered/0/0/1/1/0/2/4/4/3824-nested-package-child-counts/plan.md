# Implementation Plan: Nested Source Package Child Counts

**Branch**: `refactor/3824-<slice-slug>` for each slice

**Date**: 2026-11-26

**Spec**: `specs\numbered\0\0\1\1\0\2\4\4\3824-nested-package-child-counts\spec.md`

## Summary

This plan orders 33 violations into three waves. Wave 1 has eight slices with exact module moves. Waves 2 and 3 list each violation with its owner, its holds, and its end state. Each slice lowers total excess and keeps the guard green.

## Technical Context

- **Language and version**: Python 3.15 or newer. Source: C-11.
- **Gate tools**: pytest, Ruff, Black, mypy, radon, bandit, pylint, vulture, pydocstyle, interrogate, ste-linter, and symbol-diff. Source: the Local gates table in `.github/copilot-instructions.md`.
- **Storage**: None. Each slice moves source modules only.
- **Targets**: Windows 11, macOS, and Linux.
- **Constraints**: Five counted children for each directory. No compatibility path. Hot files and holds as listed in the hold register.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | Each slice lowers total excess and adds no violation. Each new package holds five or fewer counted children. |
| II. Class-Based Architecture | Pass | Moves keep each class in place under a new path. No wrapper is added. |
| III. Safety-First | Pass | No input handling, destructive operation, or Mist Cloud call changes. |
| IV. Full Deployment Pipeline | Pass | Each slice runs T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. |
| V. Observability and Logging | Pass | Each slice records changed logger names. No new log output is added. |
| VI. Inline Comments | Pass | Moved code keeps its comments. Each new `__init__.py` holds a docstring that gives its purpose. |
| VII. Action Logging | Pass | Moved code keeps its logging statements. No new action is added. |
| Python 3.15 | Pass | Each slice targets Python 3.15. Source: C-11. |
| mistapi as the only Mist interface | Not applicable | Moves change no Mist REST call. |
| Podman container runtime | Not applicable | No container file changes. |
| Output backends and operational store | Not applicable | No export or persistence behavior changes. |
| Menu operations | Not applicable | A slice that moves a menu-registered module runs the menu reference gate. |
| Security findings | Pass | No finding is suppressed. |
| Documentation | Pass | Each slice updates each document that names a moved path. |
| SpecKit escalation | Pass | This record is the specification for the wave 1 slices. |
| Multi-agent git workflow | Pass | Each slice uses one branch, one pull request, and one hold check. |
| Governance | Pass | No constitution amendment is needed. |

## Ratchet Sequence

Each wave 1 slice runs after the previous slice merges. The totals below use the guard arithmetic in C-04 and C-09.

| Step | Slice | Violations after | Total excess after |
| - | - | - | - |
| 0 | Measured base | 33 | 236 |
| 1 | W1-01 | 32 | 235 |
| 2 | W1-02 | 31 | 233 |
| 3 | W1-03 | 30 | 231 |
| 4 | W1-04 | 29 | 229 |
| 5 | W1-05 | 28 | 227 |
| 6 | W1-06 | 27 | 225 |
| 7 | W1-07 | 26 | 223 |
| 8 | W1-08 | 25 | 213 |

## Wave 1 Change Map

Each row lists the exact modules that move. Each move uses `git mv`. Each new package holds an `__init__.py` file. The directory names below are relative to `src/`.

| Slice | Violating directory | Count before | Modules moved (from the directory) | New package | Count after |
| - | - | - | - | - | - |
| W1-01 | `mist/intelligence/marvis/actions` | 6 | `acknowledgement.py`, `alarms.py` | `alarm_actions/` | 5 |
| W1-02 | `mist/intelligence/troubleshooting/rf_diagnostics` | 7 | `file_naming.py` and `recording.py` to `output/`. `audit.py` and `spectrum.py` to `analysis/`. | `output/`, `analysis/` | 5 |
| W1-03 | `mist/networking/network` | 7 | `_routing_utils_forwarding.py`, `_routing_utils_parsing.py`, `_routing_utils_payload.py`, `_routing_utils_routing.py` | `routing_support/` | 4 |
| W1-04 | `mist/realtime/websocket` | 7 | `service_ping_discovery.py` and `service_ping_manager.py` to `service_ping/`. `commands.py` and `context.py` to `command_context/`. | `service_ping/`, `command_context/` | 5 |
| W1-05 | `mist/access/api` | 7 | `response_integrity.py` to `mist/access/`. `client_fingerprint_operations.py` to `mist/resources/org/`. | none new. `mist/resources/org` gains one module | 5 |
| W1-06 | `mist/resources/inventory` | 7 | `org_device_inventory_msp.py`, `org_device_inventory_summary.py`, `org_device_inventory_summary_facade.py` | `org_inventory/` | 5 |
| W1-07 | `operations/execution/ssid_consolidation` | 7 | `_ssid_template_phase1.py`, `_ssid_template_phase2.py`, `_ssid_template_phase3.py`, `_ssid_template_phase45.py` | `phases/` | 4 |
| W1-08 | `foundation/models/dataclasses` | 15 | Five `map_*_deps.py` modules to `maps/`. Three site modules to `site/`. Two export modules to `export/`. Five runtime modules to `runtime/`. | `maps/`, `site/`, `export/`, `runtime/` | 4 |

Wave 1 module names for W1-08:

- `maps/`: `map_clone_deps.py`, `map_marker_deps.py`, `map_scaling_deps.py`, `map_viewer_deps.py`, `map_wizard_deps.py`.
- `site/`: `family_selection_context.py`, `msp_org_context.py`, `site_auto_upgrade_deps.py`.
- `export/`: `export_backend_options.py`, `polyglot_write_outcome.py`.
- `runtime/`: `batch_worker.py`, `endpoint_config.py`, `progress_event.py`, `systematic_test_option.py`, `websocket_stream_target.py`.

## Shared Change Set for Each Slice

Each slice changes these files in the same pull request:

- `tests/guardrails/nested_package_baseline.json`. Remove the entry for a directory that reaches five counted children. Keep the entries sorted by path.
- `tests/guardrails/test_nested_package_structure.py`, lines 176 and 177. Replace the expected violation count and total excess with the values in the ratchet sequence.
- `tests/guardrails/test_src_public_symbol_preservation.py`. Add the old and new path of each moved module to the map. The map begins near line 82. Source: C-16.
- `tests/unit/structure/test_nested_slice_w1_NN.py`. Add one import-path test. It proves that the new path imports, that the old path fails, and that each moved class reports the new `__module__` value.
- `changelog.d/issue-3824-<slug>.md`. Add one fragment. Source: the repository rule in `.github/copilot-instructions.md`.
- Each consumer that imports a moved module. Find each consumer with `git grep -n "<old dotted path>"` before the move.

## Hold Register

| Hold | Path or scope | Reason | Release condition |
| - | - | - | - |
| H-1 | `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `README.md`, `documentation/menu_reference.md` | Hot files in the repository rule. One open pull request may touch them at a time. Sources: C-17, C-18, C-19. | The open pull request that touches the file merges or closes. |
| H-2 | `tests/guardrails/nested_package_baseline.json`, `tests/guardrails/test_nested_package_structure.py`, `tests/guardrails/test_src_public_symbol_preservation.py` | Every slice edits these files. | The previous slice merges. |
| H-3 | `src/foundation/support/refactors/initialize_mist_session.py` and new `src/interfaces/wan_performance/` packages | Open pull request 4208 changes this file and adds packages. Source: C-21. | Pull request 4208 merges or closes. |
| H-4 | `src/operations/exporting/export/data_exporter.py` | Open pull request 4813 changes this file. Source: C-22. | Pull request 4813 merges or closes. |
| H-5 | `src/foundation/support/utils/zscaler_catalogue.py` | Issue 1794 reserves the file for an audit. Source: C-20. | Issue 1794 integrates the audit or transfers the file in writing. |
| H-6 | `src/interfaces/monitoring/metrics_gateway/` | Issue 4009 is open and covers the same core modules. Source: C-49. | Issue 4009 closes or transfers the work in writing. |
| H-7 | `src/operations/exporting/export/` | Issue 4168 names the export folder in its title. The baseline assigns the folder to issue 3824. Source: C-48 and the baseline. | The owner of issue 4168 confirms that no export slice overlaps its work. |

## At-Limit Directories

The guard counts 29 directories at exactly five counted children on remote main. Source: C-09. A change must not add a child to these directories.

- `src/foundation`, `src/foundation/persistence/db`, `src/foundation/runtime`
- `src/interfaces/portals`, `src/interfaces/portals/licensing_comparison`, `src/interfaces/visualization/ui/execution`
- `src/mist`, `src/mist/access/audit`, `src/mist/access/audit/rendering`
- `src/mist/intelligence`, `src/mist/intelligence/juniper_docs`, `src/mist/intelligence/juniper_docs/acquire`, `src/mist/intelligence/juniper_docs/classify`, `src/mist/intelligence/juniper_docs/harvest`
- `src/mist/intelligence/reports/org_security_posture/checks`, `src/mist/realtime/websocket_streams/catalog`, `src/mist/realtime/websocket_streams/web/services/operations`
- `src/mist/resources`, `src/mist/resources/gateway/overrides`, `src/mist/resources/site/rrm_reset`
- `src/operations`, `src/operations/execution`, `src/operations/execution/firmware_policy`, `src/operations/execution/firmware_policy/recovery`, `src/operations/execution/ssh/config`
- `src/operations/exporting/ex_hardware_inventory`, `src/operations/exporting/ex_hardware_inventory/report`, `src/operations/exporting/ex_hardware_inventory/run`, `src/operations/hardware/mib_generator`

Caution: a new child in an at-limit directory creates a violation. The guard fails the change, and the pull request must repair the change before it merges.

## Waves 2 and 3

Waves 2 and 3 use the rules in `D-9` of `design\research.md`. Each slice in these waves writes its module groups in its own change notes. Each slice uses the end state in `tasks.md`.

## Dependencies and Execution Order

1. Wave 1 runs first, one slice at a time, in the order of the ratchet sequence.
2. Wave 2 starts after W1-08 merges. Each wave 2 slice holds H-2.
3. Wave 3 starts after wave 2 except for the upgrade portal parent and the export folder. Each parent starts after its children.
4. W3-03 starts after W3-02, because the `serial_cc` child must leave the refactors directory first.
5. W3-14 starts after W1-05, because W1-05 changes an import in a WiFi exporter module. Source: the W1-05 consumer list in `tasks.md`.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A new child lands in an at-limit directory | Check the at-limit list before each change. The guard fails the change if it adds a violation. |
| A module move breaks an import | Run the import smoke command and the guardrail tests in the same pull request. |
| A logger name or `__module__` value changes without a record | Record each change in the pull request, as FR-008 requires. |
| A test path moves during issue 4142 | Re-derive the test list with `git grep` at each slice start. |
| Open pull requests 4208 and 4813 conflict with a slice | Hold H-3 and H-4 block the affected paths. |
| Issue 4168 overlaps the export folder | Hold H-7 blocks wave 3 slice W3-14 until issue 4168 confirms. |
| A slice rebases over a newer baseline and changes the expected totals | Measure the guard again after the rebase. Update the expected totals before the push. |

## Rollback

1. Open a new pull request that reverts the slice merge commit on `main`.
2. Restore the previous baseline and the previous expected totals in the same pull request.
3. Run `python -m pytest tests/guardrails/test_nested_package_structure.py` on the reverted tree.

Warning: a force push to `main` removes shared commits for every user of the repository. Do not force-push `main`.

## Complexity Tracking

Grandfathered debt that each slice touches:

| Violation | Slice | Why it stays for now |
| - | - | - |
| 33 directories in the inventory | Waves 1 to 3 | The rule forbids new debt. It does not force one change to remove all debt. |

New design that needs an exception: none. Each new package holds five or fewer counted children.

## Project Structure

```text
specs/numbered/0/0/1/1/0/2/4/4/3824-nested-package-child-counts/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      ratchet-baseline.md
      guard-report.md
    checklists/
      requirements.md
      slice-gates.md
```
