# Implementation Plan: Refactor: isolate audit renderer modules

**Branch**: `chore/4011-audit-rendering` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Move the five helper modules of the audit renderer into a new helpers package under the rendering package. Remove the `clusters` package, which holds two of the five modules today. Keep `renderer.py` at its current canonical path. Update the active imports of the moved modules. Replace the six flat-keyed rows of the symbol guard with six baseline-keyed rows. Update seven rows of the hook catalog and the expected rows of the hook guard. Add a structure guard with exact counts, a retired-path scan, and three failure proofs. Add one changelog fragment. The change does not alter the renderer behavior, the report output, or any Mist API call.

## Technical Context

**Language/Version**: Python 3.15 or newer (row RC-57).

**Primary Dependencies**: The pinned `mistapi` package, version 0.64.1, for the audit log call (row RC-52). Pytest for tests and guards. The standard library `pathlib` and `subprocess` for the structure guard.

**Storage**: None. The change moves Python modules and edits test artifacts.

**Testing**: Pytest unit tests, the guards under `tests/guardrails/`, and the local gates in `design/checklists/gates.md`.

**Target Platform**: Windows 11, macOS, and Linux, as the repository instructions state in section "What this repository is".

**Project Type**: Python command-line tool with a web portal. The change touches one package under `src/`.

**Performance Goals**: No runtime change. The rendering code runs the same statements in the same order.

**Constraints**: Line length 120 (row RC-44). Five children or fewer for each structural directory (row RC-59). Five parameters or fewer for each function and 25 lines or fewer. No compatibility shim (row RC-53).

**Scale/Scope**: Five modules move. Two modules change their imports. Four tests and guards change. One guard is new. One changelog fragment is new. One record folder is new. No file outside `src/mist/access/audit/rendering/`, `tests/`, `specs/2448-misthelper-performance-monitoring/artifacts/`, and `changelog.d/` changes.

## Constitution Check

The constitution is at `.specify/memory/constitution.md` (row RC-55 for Principle I). The gate is passed before research and rechecked after design.

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-Item Rule | Pass | After the change, the audit root holds 5 children, rendering holds 2, and helpers holds 5 (FR-001 to FR-003). No new direct child enters a noncompliant parent. The nested baseline keeps its 33 violations, and none is in the audit package (row RC-30). |
| I. Function limits | Pass | Each moved function keeps its size. The structure guard uses one class and methods under 25 lines and five parameters. |
| II. Class-Based Architecture | Pass | The moved symbols keep their classes. The structure guard defines one class named `AuditLayoutInspector`. No wrapper module is added (FR-007). |
| III. Safety-First | Pass | The change adds no keyboard input, no destructive operation, and no secret. The structure guard reads tracked files only. |
| IV. Full Deployment Pipeline | Pass | Tasks T001 to T028 and the final tasks run the local gates, commit, rebase, push, open the pull request, wait for remote CI, and merge only with authorization. |
| V. Observability and Logging | Pass | The change adds no non-ASCII output. The structure guard prints ASCII only. Each new action in the guard logs an info line before it and a debug line after it. |
| VI. Inline Comments | Pass | Each changed import line keeps or receives an inline comment (T011 to T013). The new helpers `__init__.py` and the new guard carry inline comments on each executable line (T009, T023). |
| VII. Action Logging | Pass | The structure guard logs before and after each git call and each file read (T023). The moved modules have no logger, so no logger name changes (FR-013). |
| Mist transport | Pass | No REST or WebSocket call changes. The audit log call stays at `audit_analysis_ops.py` line 55 (row RC-15). |
| Output backends | Pass | The change does not alter any export. |
| Database keys | Pass | No endpoint strategy changes. |
| Data directory | Pass | The change writes no product output. |
| Container runtime | Pass | The change starts no container and changes no image. |
| File paths | Pass | The new guard builds paths with `pathlib`. Git receives list arguments, not joined strings. |
| Documentation | Pass | The renderer docstring names the new paths (T011). The changelog fragment names issue #4011 (T025). No other document names the moved modules (row RC-51 names only the audit operation). |
| Complexity-driven escalation | Pass | The change touches more than three files and moves modules, so this record is required. |
| Multi-agent git workflow | Pass | The work uses a worktree and explicit staging. Pull request #4208 overlaps one file, and the rebase handles it (row RC-25). |
| Test containers | Pass | No test container starts. The gates run on the worktree. |

## Project Structure

### Documentation (this feature)

The record folder is `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/`. It holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. The `design/` folder holds `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, and `checklists/`.

### Target layout of the audit package

```text
src/mist/access/audit/
    __init__.py
    analyzer.py
    audit_analysis_ops.py
    filter.py
    rendering/
        __init__.py
        renderer.py
        helpers/
            __init__.py
            _renderer_delta.py
            _renderer_format.py
            _renderer_html.py
            _renderer_mermaid.py
            _renderer_time.py
    time_parser.py
```

### File change map

| Action | Repository path | Requirement | Task |
|--------|-----------------|-------------|------|
| Move | `src/mist/access/audit/rendering/_renderer_delta.py` to `src/mist/access/audit/rendering/helpers/_renderer_delta.py` | FR-003, FR-004 | T004 |
| Move | `src/mist/access/audit/rendering/_renderer_format.py` to `src/mist/access/audit/rendering/helpers/_renderer_format.py` | FR-003, FR-004 | T005 |
| Move | `src/mist/access/audit/rendering/_renderer_time.py` to `src/mist/access/audit/rendering/helpers/_renderer_time.py` | FR-003, FR-004 | T006 |
| Move | `src/mist/access/audit/rendering/clusters/_renderer_html.py` to `src/mist/access/audit/rendering/helpers/_renderer_html.py` | FR-003, FR-004 | T007 |
| Move | `src/mist/access/audit/rendering/clusters/_renderer_mermaid.py` to `src/mist/access/audit/rendering/helpers/_renderer_mermaid.py` | FR-003, FR-004 | T008 |
| Add | `src/mist/access/audit/rendering/helpers/__init__.py` | FR-003, FR-019 | T009 |
| Delete | `src/mist/access/audit/rendering/clusters/__init__.py` and the empty `clusters/` folder | FR-004 | T010 |
| Modify | `src/mist/access/audit/rendering/renderer.py` (imports, docstring, and one stale comment) | FR-005, FR-006, FR-019 | T011 |
| Modify | `src/mist/access/audit/rendering/helpers/_renderer_html.py` (three imports) | FR-006 | T012 |
| Modify | `src/mist/access/audit/rendering/helpers/_renderer_mermaid.py` (two imports) | FR-006 | T013 |
| Modify | `tests/test_audit_renderer.py` (one import) | FR-006 | T014 |
| Modify | `tests/unit/marvis/mist/access/audit/test_renderer_format_wave9.py` (docstring and import) | FR-006 | T015 |
| Modify | `tests/unit/marvis/mist/access/audit/test_renderer_time_wave9.py` (docstring and import) | FR-006 | T016 |
| Modify | `tests/guardrails/test_src_public_symbol_preservation.py` (six rows, lines 82 to 87) | FR-008, FR-012 | T018 |
| Modify | `tests/guardrails/test_performance_hook_catalog.py` (expected rows, lines 277 to 288) | FR-009 | T019 |
| Modify | `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` (file path column, lines 80 to 84, 559, and 560) | FR-009 | T020 |
| Modify | `tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py` (two lists, lines 8 to 13 and 17 to 22) | FR-010 | T022 |
| Add | `tests/guardrails/test_audit_rendering_structure.py` | FR-011 | T023 |
| Add | `changelog.d/issue-4011-audit-rendering.md` | FR-014 | T025 |
| Add | `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/` (the record folder) | FR-021 | T026 |

No other repository path changes. The change leaves these files unchanged (checks in T017, T021, and T027):

- `src/mist/access/audit/audit_analysis_ops.py`, `junk/diag_rbo.py`, `tests/run_audit_integration.py`, and `tests/unit/marvis/mist/access/audit/test_audit_analysis_ops.py` (row RC-14 to row RC-23).
- `tests/guardrails/nested_package_baseline.json` and `tests/guardrails/test_nested_package_structure.py` (rows RC-30 and RC-31).
- `specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv` and the two summary JSON files (row RC-29).
- The historical records listed in FR-015 (rows RC-40, RC-46, RC-47, RC-48, and RC-49).

### Dependencies

- No new package. The pinned `mistapi` range stays `>=0.64.0,<0.65`.
- No new environment variable.
- No change to `requirements.txt` or `requirements-dev.txt`.

## Implementation Outline

1. Verify the 3824 layout and the three counts (T001).
2. Create the worktree and record the collected test counts (T002, T003).
3. Move the five helper modules and create the helpers package. Remove the `clusters` package (T004 to T010).
4. Update the active imports and docstrings (T011 to T017).
5. Update the symbol guard, the hook guard, the hook catalog, and the #3824 structure test (T018 to T022).
6. Add the structure guard and confirm the nested guard (T023, T024).
7. Add the changelog fragment and the record folder. Confirm the scope of the change (T025 to T027).
8. Run the focused tests, the guards, and the local gates (T028 and T-LOCAL-GATES).
9. Commit, rebase, push, open the pull request, watch the remote CI, and merge after authorization (T-PR, T-REMOTE-CI, T-MERGE).

## Complexity Tracking

**Existing debt that the change touches**: None. The audit package holds 5 children, the rendering package holds 5 children, and the `clusters` package holds 2 children. The nested baseline has no entry for these directories (row RC-30). The change moves the helper modules and does not add a child to any noncompliant parent.

**Existing debt that the change does not touch**: The nested baseline holds 33 violations with 236 total excess (row RC-31). This count is grandfathered. Issue #3824 tracks its remediation, and the change does not add to it.

**New design that needs a reason**:

| Item | Why it is needed | Simpler alternative rejected because |
|------|------------------|--------------------------------------|
| The helpers package | The issue requires a package with five helper modules. | Keeping the helper modules in `rendering/` leaves the rendering package at five children. The issue requires two. |
| The structure guard | The issue requires exact counts, and a guard must prove that it can fail. | The nested guard enforces only the limit of five (row RC-31). It cannot enforce the exact counts of the issue. |
| The renderer self row of the symbol guard mapping | The issue requires six rows. | Five rows break the issue count. The renderer self row adds symbol coverage for the renderer, and it costs no runtime. |

## Risks and Mitigations

- **Risk**: A caller imports a retired path, and the import fails at run time. **Mitigation**: The retired-path scan (TS-02) and the import checks (T028) name each caller before the commit.
- **Risk**: A helper symbol is lost in a move. **Mitigation**: The symbol guard (TS-09) compares each baseline module with its final module. A lost name fails the guard.
- **Risk**: The hook catalog rows do not resolve. **Mitigation**: The hook guard (TS-08) resolves each active row against the current AST. The seven rows change in the same commit as the moves.
- **Risk**: The nested guard reports a different examined count. **Mitigation**: The count stays the same, because one directory is removed and one is added (row RC-31). Task T024 confirms the count.
- **Risk**: A helper class reports a new `__module__` value. **Mitigation**: No code or test reads the `__module__` of a helper symbol (search result in `analysis.md`). The renderer `__module__` is unchanged, and an existing test checks it (TS-11).
- **Risk**: Pull request #4208 changes the same symbol guard file. **Mitigation**: Rebase the branch before the serial slot. Resolve only the `MODULE_PATHS` block. Rerun the symbol guard after the rebase (U-7).
- **Risk**: A stale `clusters/` cache folder remains on a developer machine. **Mitigation**: The structure guard counts tracked files only (contract `design/contracts/structure-guard.md`). Task T010 removes the exact folder path.
- **Risk**: The shared working tree contains unrelated edits. **Mitigation**: Use a worktree. Stage explicit paths only. Leave the five unrelated files untouched.

## Rollback Steps

1. Before the merge, close the pull request or revert the branch commit in the worktree. No data changes.
2. After the squash merge, open a new pull request that reverts the squash commit on a new branch from `main`.

Warning: Do not force-push `main` to remove the change. A force-push rewrites history for every other agent.
Caution: A revert restores the 3824 layout. The helper imports return to their previous paths, and the symbol guard rows return to their previous values.
