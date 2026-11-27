# Implementation Plan: Metrics Gateway Core Modules

**Branch**: `chore/4009-metrics-gateway-core` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/spec.md`. The route segments are the base-5 digits of 4009 (`112014`), padded to eight digits, as `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1` computes them.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Move four data-plane modules into `src/interfaces/monitoring/metrics_gateway/core/`. Rewrite each caller import, the logger assertions, and the generated references. Extend the symbol guard and the structure guard. Remove the gateway baseline entry, and update the eight active hook rows. Keep historical evidence unchanged.

## Technical Context

**Language/Version**: Python 3.15.2. `pyproject.toml` line 23 requires `>=3.15`.

**Primary Dependencies**: `mistapi` 0.64.1 (pin `>=0.64.0,<0.65`), Flask in the `web` module, pytest, Ruff, Black, Mypy, Bandit, pylint, radon, vulture, pydocstyle, interrogate, and the `misthelper-devtools` tools.

**Storage**: None changed. The MIB generator reads tracked inputs under `data/mib_generator/`. Product outputs stay under `data/`.

**Testing**: Targeted pytest modules, the guardrails folder, and the local gates table of `.github/copilot-instructions.md`. The targeted command in `design/quickstart.md` section 4 names 13 test modules. The `tests_planned` value in the status file counts those 13 modules.

**Target Platform**: Windows 11, macOS, and Linux. The gateway runs in the Podman compose group on port 8057, and that port does not change.

**Project Type**: Python package inside the MistHelper repository.

**Performance Goals**: No change. The move adds no module load and no loop.

**Constraints**: The five-item rule applies. No wrapper, alias, or fallback path is allowed. The spec phase runs no build, test, or repository script.

**Scale/Scope**: The change edits 32 existing paths. It also adds two new files and the record folder. The size is `L`, because the change spans two packages, the guards, the documents, and the generated pages.

## Constitution Check

*Gate: must pass before implementation. Re-check after the final gate run.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass after change | The gateway root holds four root modules and `core`, which is five children. The core package holds four modules. The baseline entry for the gateway root is removed. |
| II. Class-based architecture | Pass | The change adds no wrapper and no standalone function. The moves keep each existing class and function. |
| III. Safety-first | Pass | The change touches no input handling, no confirmation, and no destructive operation. |
| IV. Full deployment pipeline | Pass with steps | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. The container build runs after the merge on `main`. No push goes to `main`. |
| V. Observability and logging | Pass | Log messages and levels keep their text. Logger names change to the core names, and the five assertions follow. |
| VI. Inline comments | Pass after T004 to T010 | Each changed Python line gets an inline comment that gives the reason. |
| VII. Action logging | Pass with reason | The changed lines are imports and paths. They add no action. The moved code keeps its existing logging. Decision D-16 records the reason. |
| Python 3.15 | Pass | `pyproject.toml` line 23 requires `>=3.15`. The legacy plan named 3.13, and that value is stale. |
| mistapi only for Mist REST | Pass | The collector uses the pinned stats module at `collector.py` line 157. The change sends no direct HTTP request. |
| Owned WebSocket transport | Not applicable | The change edits no WebSocket code. |
| UV and requirements | Not applicable | The change edits no dependency file. |
| Podman runtime | Not applicable | The change edits one comment in a container script. It adds no image, volume, user, or port. |
| File paths | Pass | The change adds no path built by hand. The tests keep their existing path helpers. |
| Output backends | Not applicable | The change edits no export path. |
| Operational store | Not applicable | The change adds no coordination record. |
| Database keys | Not applicable | The change edits no endpoint and no primary key strategy. |
| Data directory | Pass | The change writes no product output. |
| Container security | Not applicable | The change edits no container user, volume, or port. |
| Zscaler and proxy | Pass | The change pushes no image from a local machine. |
| Security findings | Pass | The change adds no suppression. Bandit runs on the changed packages. |
| Documentation | Pass | The MIB guide and the generated menu pages are updated. The README does not change, because no operation or behavior changes. |
| Release notes | Pass | The change adds one fragment under `changelog.d/`. |
| Multi-agent git workflow | Pass with block | The branch uses the `chore` type. The issue needs the `in-progress` label before the branch exists. The symbol guard edit waits for PR #4208. |
| SpecKit escalation | Pass | This record exists, because the change touches more than three files and two packages. |
| Mist API documentation | Not applicable | The change edits no endpoint behavior. The coverage documents name no moved module. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      module-paths.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
src/interfaces/monitoring/metrics_gateway/
  __init__.py
  core/
    __init__.py
    cache.py
    catalog.py
    collector.py
    samples.py
  prometheus.py
  service.py
  snmp.py
  web.py
src/operations/hardware/mib_generator/
  __init__.py
  assignment.py
  mib.py
  runner.py
  schema.py
tests/contract/
tests/guardrails/
tests/unit/maps/interfaces/monitoring/metrics_gateway/
tests/unit/prod_readiness/operations/hardware/mib_generator/generator/
```

**Structure Decision**: The core package holds the four data-plane modules. The gateway root keeps the four root modules. No other package changes shape.

## File Change Map

Line numbers refer to `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

| Path | Action | Requirement | Change |
| - | - | - | - |
| `src/interfaces/monitoring/metrics_gateway/cache.py` | Move to `core/cache.py` | FR-001, FR-005 | Rewrite the three imports at lines 28 to 30. |
| `src/interfaces/monitoring/metrics_gateway/catalog.py` | Move to `core/catalog.py` | FR-001 | No internal import. The logger name changes. |
| `src/interfaces/monitoring/metrics_gateway/collector.py` | Move to `core/collector.py` | FR-001, FR-005 | Rewrite the two imports at lines 28 and 29. |
| `src/interfaces/monitoring/metrics_gateway/samples.py` | Move to `core/samples.py` | FR-001, FR-005 | Rewrite the import at line 19. |
| `src/interfaces/monitoring/metrics_gateway/core/__init__.py` | Add | FR-003 | Add a documentation string that names the purpose and the five-child reason. |
| `src/interfaces/monitoring/metrics_gateway/__init__.py` | Modify | FR-005, FR-006 | Rewrite the four imports at lines 26 to 30. Keep `__all__`. |
| `src/interfaces/monitoring/metrics_gateway/prometheus.py` | Modify | FR-002, FR-005 | Rewrite the imports at lines 25 and 26. |
| `src/interfaces/monitoring/metrics_gateway/service.py` | Modify | FR-002, FR-005 | Rewrite the imports at lines 22 and 23. |
| `src/interfaces/monitoring/metrics_gateway/snmp.py` | Modify | FR-002, FR-005 | Rewrite the imports at lines 39, 45, and 48. |
| `src/interfaces/monitoring/metrics_gateway/web.py` | Modify | FR-002, FR-005 | Rewrite the import at line 16. |
| `src/operations/hardware/mib_generator/__init__.py` | Modify | FR-008 | Rewrite the documentation path at line 14. |
| `src/operations/hardware/mib_generator/assignment.py` | Modify | FR-005 | Rewrite the import at line 24. |
| `src/operations/hardware/mib_generator/mib.py` | Modify | FR-005, FR-008 | Rewrite the import at line 22 and the header template path at line 428. |
| `src/operations/hardware/mib_generator/runner.py` | Modify | FR-005 | Rewrite the import at line 17. |
| `src/operations/hardware/mib_generator/schema.py` | Modify | FR-005 | Rewrite the import at line 22. |
| `tests/contract/test_generated_mib_matches_agent.py` | Modify | FR-005 | Rewrite the import at line 17. |
| `tests/contract/test_mib_matches_catalog.py` | Modify | FR-005 | Rewrite the import at line 26. |
| `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_collector.py` | Modify | FR-005, FR-007 | Rewrite the imports at lines 10 to 14. Rewrite the logger at line 221. |
| `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_prometheus_and_cache.py` | Modify | FR-005, FR-007 | Rewrite the imports at lines 9 to 18 and at line 341. Rewrite the loggers at lines 151 and 347. |
| `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_and_service.py` | Modify | FR-005, FR-007 | Rewrite the imports at lines 11 to 15 and at line 357. Rewrite the loggers at lines 59 and 70. |
| `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_integration.py` | Modify | FR-005 | Rewrite the imports at lines 45 and 46. |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_mib_generator.py` | Modify | FR-005 | Rewrite the import at line 16. |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_properties.py` | Modify | FR-005 | Rewrite the import at line 16. |
| `tests/guardrails/test_src_domain_structure.py` | Modify | FR-014 | Add the child-set test after the function at line 118. |
| `tests/guardrails/test_src_public_symbol_preservation.py` | Modify | FR-013 | Add four entries to `MODULE_PATHS` after line 37. |
| `tests/guardrails/nested_package_baseline.json` | Modify | FR-015 | Remove the gateway root object at lines 25 to 30. |
| `tests/guardrails/test_nested_package_structure.py` | Modify | FR-015 | Change the expected text at line 177 to `32 violations, 233 total excess`. |
| `documentation/mib_generator.md` | Modify | FR-009 | Rewrite the paths at lines 13 and 108. |
| `documentation/mibs/MISTHELPER-MIB.mib` | Modify (generated) | FR-008 | Regenerate the header path at line 20. |
| `documentation/menu-api/interactive-safe.md` | Modify (generated) | FR-010 | Regenerate the links at lines 1149 to 1151. |
| `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` | Modify (generated) | FR-010 | Regenerate the links at lines 1149 to 1151. |
| `container/observium/20-add-mist-static-sensors.sh` | Modify | FR-009 | Rewrite the comment path at line 120. |
| `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` | Modify | FR-011 | Rewrite the file path in rows 266 to 271, 273, and 617. |
| `changelog.d/issue-4009-metrics-gateway-core.md` | Add | FR-018 | One `### Changed` heading and one bullet that names issue 4009. |
| `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/` | Add | FR-019 | The reviewed record from the draft folder. |

The change touches 32 existing paths and adds 2 new files, plus the record folder. The four moved modules count as existing paths. `catalog.py` has no import edit, so it moves with no content change.

## Dependencies

- No package changes. No `requirements.txt` or `requirements-dev.txt` change.
- Issue #3824 is the parent. Its baseline debt is the reason for the gateway entry.
- Issue #4117 is closed. Its contract is in PR #4306, which merged on 2026-10-19. The contract makes the hook catalog active and keeps the inventory historical.
- PR #4208 is open. It changes `tests/guardrails/test_src_public_symbol_preservation.py`. The symbol guard edit waits for that file release.
- Gate tools come from `misthelper-devtools`. They include `symbol-diff`, `test-quality-analyzer`, `complexity-gate`, `ste-linter`, `check-citations`, and `markdown-link-check`.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| PR #4208 holds the symbol guard file | A merge conflict or a lost hunk | Task T012 waits for the release. FR-020 blocks publication until then. |
| The regenerated MIB changes lines outside the header | The MIB contract drifts | Review the diff after regeneration. Stop when other lines change. |
| A logger assertion keeps an old name | A test fails | Task T009 updates each assertion, and the targeted command confirms it. |
| New files are not staged | The hook guard reports unresolved rows | Stage each new file before T018 runs the hook guard. |
| The test-quality baseline stores line numbers | The gate reports a shifted finding | Run the gate. Never rewrite the baseline to hide a finding. |
| Five unrelated files are edited in the main checkout | A commit contains unrelated work | Use a fresh worktree. Stage explicit paths only. |
| An external caller imports an old path | An `ImportError` appears in that caller | The repository search lists 33 files that name a moved module. 27 active files change, and six historical files stay unchanged. No alias exists, by decision D-3. |
| The full test run takes a long time | The delivery slows | Run the targeted gates first. Run the full suite once before the push. |
| The archive branch is deleted | The candidate evidence is lost | FR-021 forbids the deletion. The spec warns about it. |

## Rollback Steps

1. Before the push, remove the worktree and delete the local branch `chore/4009-metrics-gateway-core`. Keep the archive branch.
2. After the squash merge, create the branch `chore/4009-revert-metrics-gateway-core` from `main`.
3. Run `git revert` on the squash commit in that branch. Open a pull request, and wait for the required checks.
4. Do not force-push `main`, and do not delete the archive branch.

## Implementation Outline

1. Phase A, tasks T001 to T003: confirm the baseline, confirm the guard file release, and create the worktree.
2. Phase B, tasks T004 to T006: move the modules, add the core initializer, and rewrite the gateway imports.
3. Phase C, tasks T007 to T010: rewrite the MIB generator imports, the contract tests, and the unit tests.
4. Phase D, tasks T011 to T013: add the guards and update the nested baseline.
5. Phase E, tasks T014 to T018: update the documents, regenerate the generated files, and update the hook rows.
6. Phase F, tasks T019 to T021: check the historical records, add the changelog fragment, and copy the record.
7. Phase G, task T-LOCAL-GATES: run every applicable local gate.
8. Phase H, tasks T-PR, T-REMOTE-CI, and T-MERGE: publish after the coordinator authorizes the slot.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The gateway root holds eight structural children under issue #3824. | This change removes the violation. The baseline entry is removed. | The move is the required fix, so no other option removes the violation. |
| The new record adds one child to the new route folder `4`. | The route folder holds only this record. | No existing folder is a valid home for the record. |

No other violation is added. The process folder `specs/` gets no new direct child.
