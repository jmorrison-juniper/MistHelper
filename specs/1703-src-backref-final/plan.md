# Implementation Plan: Source Back-Reference Removal

**Branch**: `refactor/1703-src-backref-final` | **Date**: 2026-09-16 | **Spec**: `specs/1703-src-backref-final/spec.md`

**Input**: Feature specification from `specs/1703-src-backref-final/spec.md`

## Summary

Remove the remaining source package back-references to the root `MistHelper` module. Keep the root alias for issue #2670. Add a guard that rejects new source back-references and proves its scan count.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Standard library, mistapi 0.64.0, pytest, ruff, black, mypy, radon

**Storage**: N/A

**Testing**: pytest guardrails, full non-e2e pytest suite, import smoke tests, static grep proof

**Target Platform**: Windows local development and Linux continuous integration

**Project Type**: Python CLI and web entrypoint

**Performance Goals**: No user-visible runtime delay beyond existing lazy import cost

**Constraints**: No deletion of the root `sys.modules` alias. No edits to generated Mist API documentation.

**Scale/Scope**: 26 source files with executable `import MistHelper`, 366 double-quoted `import_module` calls, and one new guard file.

## Constitution Check

- Five-Item Rule: The change adds one module in the existing `src/config/` package and one guard in the existing `tests/guardrails/` package. It does not add a new direct child under `src`.
- Class-Based Architecture: The source dependency seam uses a named class, not standalone wrapper functions.
- Safety-First: No destructive operation changes occur.
- Full Deployment Pipeline: Local gates, commit, pull request, CI, and merge are planned.
- Observability: New executable lines include inline comments and action logging where they perform work.

## Project Structure

### Documentation (this feature)

```text
specs/1703-src-backref-final/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
src/config/source_dependency_resolver.py
tests/guardrails/test_source_misthelper_backrefs.py
changelog.d/issue-1703-src-backref.md
```

Existing source files that contain a back-reference will change only to use the new source seam and to remove stale text.

**Structure Decision**: Use `src/config/` because it already owns source runtime settings and does not create a new top-level source package.

## Files Changed

The implementation will change `MistHelper.py`, `src/config/source_dependency_resolver.py`, source files that currently contain executable back-references, `tests/guardrails/test_source_misthelper_backrefs.py`, `specs/1703-src-backref-final/*`, and `changelog.d/issue-1703-src-backref.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing packages exceed five children | The repository already has this debt | A full package split is outside issue #1703 |
