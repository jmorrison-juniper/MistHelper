# Tasks: Audit Report Rendering Packages

**Feature**: `4011-audit-rendering` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Each task names its files and its exact completion check. Run the tasks in order,
because a later task reads the result of an earlier task.

## Phase 1: Package creation

- [X] **T001** Create `src/mist/access/audit/rendering/__init__.py` with a package
  docstring. Check: the file exists and holds one docstring line.
- [X] **T002** Create `src/mist/access/audit/rendering/helpers/__init__.py` with a
  package docstring. Check: the file exists and holds one docstring line.

## Phase 2: Module moves

- [X] **T003** Move `src/mist/access/audit/renderer.py` to
  `src/mist/access/audit/rendering/renderer.py` with `git mv`. Check:
  `git status` reports one rename and no copy.
- [X] **T004** Move `_renderer_delta.py`, `_renderer_format.py`,
  `_renderer_html.py`, `_renderer_mermaid.py`, and `_renderer_time.py` to
  `src/mist/access/audit/rendering/helpers/` with `git mv`. Check: `git status`
  reports five renames, and the audit root holds no `_renderer_*` module.

## Phase 3: Import updates

- [X] **T005** Update each internal import and docstring reference inside the six
  moved modules to the canonical `audit.rendering` paths. Check: no moved module
  names an old path.
- [X] **T006** Update the consumer imports in
  `src/mist/access/audit/audit_analysis_ops.py` and `junk/diag_rbo.py`. Check:
  both files import `AuditReportRenderer` from `audit.rendering.renderer`.
- [X] **T007** Update the test imports in `tests/run_audit_integration.py`,
  `tests/test_audit_renderer.py`, `tests/unit/audit/test_renderer_format_wave9.py`,
  and `tests/unit/audit/test_renderer_time_wave9.py`. Check: each test file names
  only canonical paths.
- [X] **T008** Split each import line that exceeds 120 characters after the longer
  path. Check: `awk` reports no line above 120 characters in the changed modules.

## Phase 4: Guards

- [X] **T009** Add six exact old-to-new module paths to `MODULE_PATHS` in
  `tests/guardrails/test_src_public_symbol_preservation.py`. Check: the guard
  reports no lost symbol and no missing moved module.
- [X] **T010** Add `tests/guardrails/test_audit_rendering_structure.py` with one
  inspector class, the exact expected layout, and three direct failure proofs.
  Check: the guard passes and each failure proof raises the expected message.

## Phase 5: Records

- [X] **T011** Add `changelog.d/issue-4011-audit-rendering.md` with one `###`
  heading and one `Changed` bullet that names issue #4011. Check: the changelog
  fragment guard passes.
- [X] **T012** Add `spec.md`, `plan.md`, and `tasks.md` under
  `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/`. Check: the process
  folder structure guard passes, and no other spec record is added.

## Phase 6: Verification

- [X] **T013** Run the focused audit tests: `tests/test_audit_renderer.py`,
  `tests/unit/audit/`, and the new structure guard. Check: every test passes.
- [X] **T014** Run the domain structure, source import, symbol preservation,
  changelog, and Markdown link guards. Check: every guard passes.
- [X] **T015** Run compile, Ruff, Black, Mypy, Bandit, Radon complexity,
  pydocstyle, and Interrogate on the changed files. Check: each gate passes.
- [X] **T016** Commit locally with a Conventional Commit message, `Closes #4011`,
  and the Copilot co-author trailer. Then run the required post-commit
  test-quality procedure. Check: the gate reports zero new findings.
- [X] **T017** Keep the two `specs/2448` snapshot artifacts byte-identical to
  `origin/main`, and map the six removed paths to the moved modules inside
  `tests/guardrails/test_performance_hook_catalog.py`. Add tests that prove each
  mapping, an unknown path, and a lost symbol. Check: the catalog guard passes,
  and `git diff origin/main -- specs/2448-misthelper-performance-monitoring/artifacts/`
  reports no change.

## Out of scope

- Any wrapper, alias, or fallback import at an old module path.
- Any change to `analyzer.py`, `filter.py`, or `time_parser.py` behavior.
- Any change to a shared registry, a generated reference, a historical spec,
  `AGENTS.md`, or `CLAUDE.md`.
- Any push, pull request, issue state change, workflow run, or merge.
