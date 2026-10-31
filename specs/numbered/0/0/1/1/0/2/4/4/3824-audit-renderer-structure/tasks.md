# Tasks: Audit Renderer Structure

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
- [ ] T007 Stage only the feature manifest and commit. Rebase onto `origin/main` and rerun affected gates. Run the required test-quality analyzer before push. Push the branch and open a pull request with exact results. Keep it unmerged. Leave auto-merge disabled until the coordinator verifies required checks, CodeQL, review, base freshness, and no active holds.

## Dependencies and Execution Order

- **T001** precedes **T002** so the new import contract has a failing regression test before the move.
- **T002** and **T003** touch separate files and can proceed in parallel after **T001**.
- **T004** depends on the completed move in **T002**.
- **T005** is independent of the source move.
- **T006** depends on **T002**, **T003**, **T004**, and **T005**.
- **T007** depends on **T006**.

## Parallel Opportunities

After **T001**, run **T002** and **T003** in parallel because they change separate source and caller files. Run **T005** in parallel with **T002** or **T004**.

## Implementation Strategy

1. Add the import contract test and verify it fails before the move.
2. Move the modules and update active callers.
3. Update the structural baseline and add the issue release note.
4. Run the independent tests and all applicable move-module gates.
