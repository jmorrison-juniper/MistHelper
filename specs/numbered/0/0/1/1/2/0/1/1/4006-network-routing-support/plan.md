# Implementation Plan: Isolate Network Routing Support Modules

**Branch**: `chore/4006-network-routing-support` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs\numbered\0\0\1\1\2\0\1\1\4006-network-routing-support\spec.md`.

## Summary

Move three routing support modules into `src/mist/networking/network/support/`. Update active imports, mock targets, guard maps, and generated menu pages. Add one structure guard and one changelog fragment. Rebuild the change from current `main`, because the preserved candidate is stale.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: `mistapi` 0.64.1, which satisfies the pin `>=0.64.0,<0.65`. The installed metadata is `mistapi-0.64.1.dist-info`. Gate tools come from `requirements-dev.txt`.

**Storage**: Not applicable. The change moves code and edits tests and documentation.

**Testing**: Focused pytest files, guard tests, `symbol-diff`, the menu generator, the STE linter, and the local gates table.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container.

**Project Type**: Command-line tool with a Python package under `src/`.

**Performance Goals**: Not applicable. The change keeps runtime behavior and SDK calls.

**Constraints**: No compatibility shims. No behavior change. At most five children at each structural level. Canonical paths only in active files.

**Scale/Scope**: Three moved modules with 1,388 lines in total (539, 461, and 388 lines). Eleven modified files. One new package initializer, one new guard, and one new changelog fragment.

## Constitution Check

Each rule has one result: PASS, PASS WITH TASK, RECORDED, PLANNED, or HOLD.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | PASS | After the change, the network root holds five structural children and the support package holds three (FR-003, FR-004). Before the change, the root holds seven. The nested baseline grandfathers it under #3824 until T012 removes the entry. |
| I. Managed record root | PASS | The record uses `specs/numbered/` and the fixed base-5 route. The route `0/0/1/1/2/0/1/1` equals base 5 of 4006, from `spec-route.ps1` lines 4 and 17. |
| I. Touched violations | RECORDED | The section "Existing violations touched by this change" lists each one and its remediation. |
| I. Function limits for new code | PASS WITH TASK | The candidate guard had one 27-line function. T013 keeps every new function at 25 lines or fewer. |
| II. Class-based architecture | PASS | No wrapper, alias, or delegating function is added. Class bodies stay unchanged. |
| III. Safety-first | PASS | No input handling, confirmation, or destructive operation changes. |
| IV. Full deployment pipeline | PLANNED | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 run after merge in T-MERGE. |
| V. Observability | PASS | No product log line changes. Logger names follow `__name__` (FR-009). Output stays ASCII. |
| VI. Inline comments | PASS WITH TASK | Each added line in the guard and map edits needs an inline comment (T010 to T013). |
| VII. Action logging | PASS | The moved modules keep their logging. The guard performs no product action. |
| Mist Cloud transport | PASS WITH DEBT | The change adds no REST call. The existing raw `requests.post` in `_routing_utils_payload.py` line 250 remains. Its debt is recorded below. |
| Packages, container, data | PASS | No dependency change. No container starts. No product output path changes. |
| Documentation | PASS | Generated pages regenerate (T014). `README.md` names no moved module (local search). |
| Release notes | PASS | One fragment (T015). |
| Multi-agent git | HOLD | The issue exists. The branch name follows `AGENTS.md`. Open draft PR #4208 overlaps one file, so publication waits (D-13). |
| Spec Kit layout | PASS | The feature root holds five children. The `design` folder holds five children. |

## Existing Violations Touched by This Change

Measured with the method in `design/research.md` section R5. Parameter counts exclude `self` and `cls`.

| File | Item | Measure | Action |
| - | - | - | - |
| `src/mist/networking/network/_routing_utils_parsing.py` | `_finalize_dest_transition` at line 212 | 5 parameters (6 with `self`) | Record only. Remediation: separate issue. |
| `src/mist/networking/network/_routing_utils_payload.py` | `_post_device_command` at line 234 | 5 parameters (6 with `self`) | Record only. Remediation: separate issue. |
| `src/mist/resources/device/_utility_commands_selection.py` | `_select_site_and_device` at line 64 | 26 lines | Record only. Remediation: separate issue. |
| `tests/unit/test_routing_utils.py` | Functions at lines 1476, 1550, 1769, 1829, 1865, and 1902 | 27 to 34 lines each | Record only. Remediation: separate issue. |
| `tests/guardrails/test_src_public_symbol_preservation.py` | Functions at lines 218, 348, and 403 | 29 to 53 lines each | Record only. Remediation: separate issue. |
| `src/mist/networking/network/routing_utils.py` | Dataclass `SsrRouteQuery` has eight fields | Generated initializer has eight arguments | Record only. Generated code is not a source function. |

## Architecture

The network root holds seven structural children on `main` today. The target shape holds five.

```text
src/mist/networking/network/
├── _routing_utils_forwarding.py
├── _routing_utils_routing.py
├── _routing_utils_ssr.py
├── routing_utils.py
└── support/
    ├── __init__.py
    ├── _routing_utils_display.py
    ├── _routing_utils_parsing.py
    └── _routing_utils_payload.py
```

- Facade: `routing_utils.py` defines `RoutingUtils` at line 113 on `main`. It binds six clusters in its constructor and exposes the public entry points.
- Orchestrators: `_routing_utils_forwarding.py`, `_routing_utils_routing.py`, and `_routing_utils_ssr.py`. Each handles one routing table type: forwarding, routing, or SSR and SRX.
- Support: `_routing_utils_display.py` (renderers), `_routing_utils_parsing.py` (parsers), and `_routing_utils_payload.py` (request payloads and REST calls).

## File-by-File Change Map

| Action | Path | Change |
| - | - | - |
| Add | `src/mist/networking/network/support/__init__.py` | Module docstring only. The preserved candidate text is acceptable. |
| Move | `src/mist/networking/network/_routing_utils_display.py` to `src/mist/networking/network/support/_routing_utils_display.py` | No content change. Blob `81619905f517792de24025d65b267bc540c158b8`. |
| Move | `src/mist/networking/network/_routing_utils_parsing.py` to `src/mist/networking/network/support/_routing_utils_parsing.py` | No content change. Blob `50cd37ff14e40e0b8f1ddda896ac3a9c1ab82f86`. |
| Move | `src/mist/networking/network/_routing_utils_payload.py` to `src/mist/networking/network/support/_routing_utils_payload.py` | Content from current `main`. Blob `38c2458ff14370be660d956ca30c252dc4fd291c`. The candidate blob `8e0229b79a05cbd1fab0af56c82608ba991cf28f` is not used. |
| Modify | `src/mist/networking/network/routing_utils.py` | Lines 22, 26, and 27 use canonical paths. The import block follows the Ruff order. |
| Modify | `src/mist/networking/network/_routing_utils_routing.py` | Line 25 uses the canonical payload path. |
| Modify | `src/mist/resources/device/_utility_commands_selection.py` | Line 15 docstring uses the canonical payload path. |
| Modify | `tests/unit/test_routing_utils.py` | 23 mock and logger targets, lines 839 to 1992, use canonical paths. |
| Modify | `tests/unit/test_unparseable_response_guards.py` | Line 16 import and line 82 logger string use canonical paths. |
| Modify | `tests/guardrails/test_src_public_symbol_preservation.py` | Add three `MODULE_PATHS` entries after line 43. Each entry has an inline comment. |
| Modify | `tests/guardrails/test_performance_hook_catalog.py` | Add three `_HISTORICAL_PATH_MOVES` entries after line 37. Each entry has an inline comment. |
| Modify | `tests/guardrails/nested_package_baseline.json` | Remove the object for `src/mist/networking/network` at lines 106 to 110. |
| Modify | `tests/guardrails/test_nested_package_structure.py` | Change the literal at line 177 to `32 violations` and `234 total excess`. |
| Modify (generated) | `documentation/menu-api/websocket.md` | Regenerate. Lines 77, 100, and 123 use canonical paths. |
| Modify (generated) | `documentation/wiki/Menu-API-Endpoints-Websocket.md` | Regenerate. Lines 77, 100, and 123 use canonical paths. |
| Add | `tests/guardrails/test_network_routing_support_structure.py` | Structure guard refreshed from the candidate. Functions have 25 lines or fewer. Each line has an inline comment. The active-path scan excludes the catalog move map. |
| Add | `changelog.d/issue-4006-network-routing-support.md` | One `###` heading and one `Changed` bullet that names issue #4006. |
| Add | `specs\numbered\0\0\1\1\2\0\1\1\4006-network-routing-support\` | This record. Added at T-PR. |
| Delete | None | The old paths disappear through the move. |
| Unchanged | `src/mist/networking/network/_routing_utils_forwarding.py`, `_routing_utils_ssr.py`, and `__init__.py` | Not named by the issue. They import no moved module. |
| Unchanged | `MistHelper.py` | Line 500 imports the facade, which does not move. |
| Unchanged | Any file under `specs/` | Historical records and CSV artifacts (FR-013). |

## Dependencies

- No new Python package.
- Gate tools come from `requirements-dev.txt` (`misthelper-devtools`).
- Open draft pull request #4208 changes `tests/guardrails/test_src_public_symbol_preservation.py`.
- Open issue #4728 reports an order-dependent failure in `tests/unit/test_routing_utils.py`.
- Retained branches for issues #2711 and #2861 share `tests/unit/test_routing_utils.py` in committed history.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| R1: The stale payload module reverts security change `5e890ed6` (PR #4317). | Rebuild from current `main`. Compare the blob after the move (TC-11). |
| R2: The nested ratchet fails on a stale baseline entry. | Remove the entry (T012). Check the report literal (TC-06). |
| R3: The performance catalog fails on hook rows 0281, 0283, and 0284. | Add map entries (T011). Run TC-05. |
| R4: Open draft PR #4208 overlaps the symbol guard file. | Keep publication closed until D-13 condition 1 is met (TC-13). |
| R5: Issue #4728 holds `tests/unit/test_routing_utils.py`. | Obtain the handoff before publication (D-13 condition 2). Run TC-02 alone and in the full suite. |
| R6: Generated pages drift from the generator output. | Regenerate with the generator (T014). Run TC-10. |
| R7: The import block fails Ruff ordering rules. | Sort the block and run the Lint gate (T005). |
| R8: Black or Mypy changes the parenthesized map values. | Run the Format and Types gates in T-LOCAL-GATES. |
| R9: A tracked file names an old path. | Run the old-path scan (TC-09). |
| R10: The symbol guard lacks history in a shallow CI clone. | The guard fetches more history. T-REMOTE-CI checks the run. |
| R11: The candidate guard's 27-line function breaks the 25-line limit. | Split the function during the refresh (T013). |
| R12: The `Old paths` gate in `copilot-instructions.md` reports the approved catalog move map. | Exclude that file from the structure guard scan and record the exception in the pull request body (D-7, D-10). |

## Rollback Steps

1. Before merge, close the pull request. Delete the remote branch `chore/4006-network-routing-support`. Remove the worktree. The archive branches keep the candidate.
2. After merge, create a branch from `main`. Run `git revert` on the squash commit. Open a pull request that closes #4006 again.
3. After the revert, run TC-01 to TC-10 again. Run the container build workflow on `main`.

Caution: a revert restores the old paths and removes the new guard and the changelog fragment.

Warning: never force-push `main`. A force-push removes commits that other agents pushed.

## Complexity Tracking

No new violation is added. The table in "Existing Violations Touched by This Change" lists the grandfathered debt. The refresh removes the candidate's new 27-line function.

## Process Folder Debt

The route uses base-5 digits from 0 to 4 at each level. Each folder therefore holds at most five children. This change adds one leaf folder and no debt.
