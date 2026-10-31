# Tasks: Nested Source Package Remediation

**Input**: `specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), and supporting documents in `design/`.

## Phase 1: Setup

No dependency or project setup is required for this source-only refactor.

## Phase 2: Foundational

No shared infrastructure blocks the user stories.

## Phase 3: User Story 1 - Generate audit reports (Priority: P1)

**Goal**: Keep the existing audit report behavior while moving renderer modules.

**Independent Test**: Render sample and empty audit results, and check existing Mermaid, HTML, and delta behavior.

- [x] T001 [US1] Add import-path tests for the new renderer modules and absent legacy modules in `tests/unit/audit/test_renderer_structure_issue_3824.py`.
- [x] T002 [US1] Move `renderer.py`, `_renderer_delta.py`, `_renderer_format.py`, and `_renderer_time.py` into `src/mist/access/audit/rendering/`; move `_renderer_html.py` and `_renderer_mermaid.py` into `src/mist/access/audit/rendering/clusters/`; add package markers.
- [x] T003 [P] [US1] Update renderer imports and module references in `src/mist/access/audit/audit_analysis_ops.py`, `tests/test_audit_renderer.py`, `tests/run_audit_integration.py`, `tests/unit/audit/test_renderer_format_wave9.py`, `tests/unit/audit/test_renderer_time_wave9.py`, and `junk/diag_rbo.py`.

## Phase 4: User Story 2 - Maintain the audit package (Priority: P2)

**Goal**: Remove the audit source violation without adding a new violation or a compatibility path.

**Independent Test**: Run the nested source structure guard and confirm the audit tree has five or fewer structural children per directory.

- [x] T004 [US2] Remove the resolved `src/mist/access/audit` entry from `tests/guardrails/nested_package_baseline.json`, set measured counts in `tests/guardrails/test_nested_package_structure.py` to 34 violations and 237 excess, and map all six moved files in `tests/guardrails/test_src_public_symbol_preservation.py`.
- [x] T005 [P] [US2] Add the issue-specific release note in `changelog.d/issue-3824-audit-renderer-structure.md`.

## Phase 5: Polish and Cross-Cutting Concerns

- [x] T006 Run renderer and structure tests. Check new imports, removed imports, old-path references, and moved symbols. Run Ruff, Black, mypy, the test-quality preflight, Markdown links, and STE.
- [x] T007 Commit the audit renderer slice, rebase it onto current `main`, run exact-head checks, and merge it as PR #4552.

## Phase 6: Foundational Updates

- [x] T008 Extend `spec.md`, `plan.md`, `design/research.md`, `design/contracts/python-imports.md`, `design/quickstart.md`, and `design/checklists/requirements.md` for the WebSocket utility text move.

## Phase 7: User Story 3 - Maintain the WebSocket utility catalog (Priority: P2)

**Goal**: Keep utility text unchanged while moving its module into the existing utility package.

**Independent Test**: Run the utility text tests and confirm that the new module path resolves and the old module path does not.

- [x] T009 [US3] Add an import-path regression test in `tests/unit/websocket_streams/catalog/test_ws_utility_text.py`.
- [x] T010 [P] [US3] Move `utility_text.py` into `src/mist/realtime/websocket_streams/catalog/utilities/metadata/utility_text.py`.
- [x] T011 [P] [US3] Update the remaining source and test imports in `src/mist/realtime/websocket_streams/catalog/utilities/utility_fields.py`, `src/mist/realtime/websocket_streams/catalog/utilities/utility_discovery.py`, and `tests/unit/websocket_streams/catalog/test_ws_utility_text_3890.py`.
- [x] T012 [US3] Remove the resolved catalog violation and map the moved module in `tests/guardrails/nested_package_baseline.json`, `tests/guardrails/test_nested_package_structure.py`, and `tests/guardrails/test_src_public_symbol_preservation.py`.
- [x] T015 [US3] Exclude `__init__.py` markers and generated `__pycache__` directories from the WebSocket feature structure guard. Update measured totals and prove that a real source violation still fails.
- [x] T016 [US3] Move `utility_profile.py` and `utility_text.py` into `utilities/metadata/`. Keep the parent package at five direct entries and test that old module paths are absent.

## Phase 8: Polish and Cross-Cutting Concerns

- [x] T013 Run focused tests, import checks, the nested-package and symbol-preservation guards, the WebSocket feature structure guard, old-path search, compile, Ruff, Black, mypy, Markdown links, STE, and the test-quality preflight. Record exact outcomes.
- [ ] T014 Commit only the feature files, rebase onto `origin/main`, rerun affected gates, run the required test-quality analyzer before push, and open a pull request with the repository template. State why no release note applies. Keep the pull request open and leave auto-merge disabled until current-head checks, review, and hold status are verified.

## Dependencies and Execution Order

- **T001** precedes **T002** so the renderer import contract fails before the move.
- **T002** and **T003** can proceed in parallel after **T001**.
- **T004** depends on **T002**.
- **T005** is independent of the renderer move.
- **T006** depends on **T002**, **T003**, **T004**, and **T005**.
- **T007** depends on **T006** and records the completed PR #4552 slice.
- **T008** precedes all implementation tasks in User Story 3.
- **T009** precedes **T010** and **T011** so the import contract is tested before the move.
- **T010** and **T011** can proceed in parallel after **T009** because they change separate files.
- **T012** depends on **T010**.
- **T015** depends on **T012**.
- **T016** depends on **T010** through **T012** and **T015**.
- **T013** depends on **T009** through **T012**, **T015**, and **T016**.
- **T014** depends on **T013**.

## Parallel Opportunities

After **T009**, run **T010** and **T011** in parallel because they change separate files.

## Implementation Strategy

1. Add the import-path regression test and confirm it fails before the move.
2. Move the module and update active callers.
3. Update the structural baseline and symbol-preservation map.
4. Exclude package markers and generated cache directories from the WebSocket structure guard.
5. Group the utility metadata modules and keep the parent package within five direct entries.
6. Run the focused tests and all applicable move-module gates.
