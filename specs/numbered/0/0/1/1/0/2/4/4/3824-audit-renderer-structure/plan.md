# Implementation Plan: Audit Renderer Structure

**Branch**: `jmorrison-juniper-3824-audit-renderer-structure` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/spec.md`.

## Summary

Move the audit renderer and its helpers into bounded packages. Keep report behavior and renderer methods unchanged. Update active imports, remove old module paths, and remove the resolved audit violation from the nested-package baseline.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: pytest for tests; no new runtime dependency

**Storage**: None

**Testing**: pytest, import smoke checks, Ruff, Black, mypy, nested-package guard, and test-quality ratchet

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python library and command-line application

**Performance Goals**: No change to report generation time or output size

**Constraints**: Each source directory has five structural children or fewer. Do not keep old-path aliases. Keep Mist API calls and report content unchanged.

**Scale/Scope**: Six renderer modules, two package directories, active imports, renderer tests, and one nested-package baseline entry

## Constitution Check

### Pre-design gate

- **Five-Item Rule**: The current audit directory has 10 structural children and is recorded in the baseline for issue #3824. Moving the six renderer modules leaves five children in `audit/`, five in `rendering/`, and two in `rendering/clusters/`.
- **Existing debt**: The repository measures 35 nested source violations and 242 total excess children. This slice resolves the audit violation and targets 34 violations and 237 total excess children.
- **Incremental remediation**: Issue #3824 tracks the remaining baseline violations. This change removes only the resolved audit entry.
- **Class-based architecture**: Keep behavior in `AuditReportRenderer`, `_HtmlCluster`, and `_MermaidCluster`. Do not add a wrapper or alias.
- **Safety**: No Mist Cloud operation, destructive action, or production data change is in scope.
- **Process records**: Add this issue-specific specification under the managed numeric route and add one issue-specific changelog fragment.
- **Deployment pipeline**: Run each applicable test and quality gate. Stage only the explicit manifest. Commit with a Conventional Commit subject and the required co-author trailer. Rebase and rerun affected gates. Push the branch and open a pull request with exact results. Keep it unmerged and disable auto-merge until the coordinator verifies all required checks, CodeQL, review, base freshness, and no active holds.

**Gate result**: Pass. The planned move reduces the measured violation count and does not increase a source directory count.

### Post-design gate

- The interface contract records the one intended module-path change.
- The test plan covers reports, helper behavior, imports, and structural debt.
- No Mist Cloud or data-model contract is required.

**Gate result**: Pass.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── checklists/
    ├── contracts/
    ├── data-model.md
    ├── quickstart.md
    └── research.md
```

### Source Code

```text
src/mist/access/audit/
├── __init__.py
├── analyzer.py
├── audit_analysis_ops.py
├── filter.py
├── time_parser.py
└── rendering/
    ├── __init__.py
    ├── renderer.py
    ├── _renderer_delta.py
    ├── _renderer_format.py
    ├── _renderer_time.py
    └── clusters/
        ├── __init__.py
        ├── _renderer_html.py
        └── _renderer_mermaid.py

tests/test_audit_renderer.py
tests/unit/audit/test_renderer_format_wave9.py
tests/unit/audit/test_renderer_time_wave9.py
tests/guardrails/nested_package_baseline.json
tests/guardrails/test_nested_package_structure.py
```

Active callers in `audit_analysis_ops.py`, `tests/run_audit_integration.py`, and `junk/diag_rbo.py` will use `src.mist.access.audit.rendering.renderer`. Historical inventory and analysis records remain unchanged.

**Structure Decision**: Keep the renderer entry point and three shared helpers in `rendering/`. Put the HTML and Mermaid clusters in `rendering/clusters/`. This gives the audit and rendering directories five structural children or fewer.

## Implementation Notes

- The renderer class moves from `src.mist.access.audit.renderer` to `src.mist.access.audit.rendering.renderer`. Its `__module__` value changes accordingly.
- Update active imports, test imports, and module docstrings. Remove the old module files.
- Remove the `src/mist/access/audit` baseline entry after the measured count reaches five.
- Update the guard's explicit repository-wide count from 35 violations and 242 excess to 34 violations and 237 excess.
- Do not rewrite the tracked `.specify/feature.json` pointer. It selects another feature and is not part of this change.
- Stop this slice after pull request creation. The coordinator owns merge and production deployment after all required checks and review pass.

## Complexity Tracking

No constitution exception is required.
