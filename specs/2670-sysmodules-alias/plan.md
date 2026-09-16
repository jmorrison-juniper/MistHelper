# Implementation Plan: Remove the MistHelper sys.modules Alias

**Branch**: `refactor/2670-sysmodules-alias` | **Date**: 2026-09-16 | **Spec**: `specs/2670-sysmodules-alias/spec.md`

**Input**: Feature specification from `specs/2670-sysmodules-alias/spec.md`

## Summary

Remove the compatibility alias from the entry point after pull request #2730 removed source back-references. Keep the source guard active. Validate imports, guards, static gates, and the full test suite.

## Technical Context

**Language/Version**: Python 3.13 or newer. Local `mistapi` must be 0.64.0.

**Primary Dependencies**: Standard library, `mistapi`, pytest, Ruff, Black, mypy, Pylint, Radon.

**Storage**: No schema change. No persistent data change.

**Testing**: pytest guardrails, import commands, static gates, symbol diff, and the full non-e2e pytest suite.

**Target Platform**: Windows local development and the existing container deployment target.

**Project Type**: Python command line application with WSGI entry support.

**Performance Goals**: No runtime work added. Startup must not gain an extra import.

**Constraints**: Do not add a compatibility shim. Do not change destructive operations. Do not edit API documentation files.

**Scale/Scope**: Ten Python files, three SpecKit files, and one release-note fragment.

## Constitution Check

- **Five-Item Rule**: Pass. The change deletes an executable line and adds no Python structure.
- **Class-Based Architecture**: Pass. The change adds no wrapper, class, or compatibility alias.
- **Safety-First**: Pass. The change does not touch input handling or destructive operations.
- **Full Deployment Pipeline**: Pass. The plan includes local gates, a branch, a pull request, and CI checks.
- **Observability and Logging**: Pass. Existing startup logging remains in place.
- **Output Backends**: Pass. No exporter or storage path changes.
- **STE Writing**: Pass. New Markdown uses short direct sentences.

Touched existing violation: `MistHelper.py` remains a large entry point. This change reduces shim debt only. The separate remediation action is to continue extracting entry point responsibilities under existing refactor issues.

## Project Structure

### Documentation for this feature

```text
specs/2670-sysmodules-alias/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
MistHelper.py
changelog.d/issue-2670-sysmodules-alias.md
```

**Structure Decision**: Use a surgical edit. Adding a new module would add a wrapper or a shim, which this issue forbids.

## Files Changed

- `MistHelper.py`: Remove the `sys.modules["MistHelper"]` assignment and the comments that justified it.
- `src/firmware/firmware_manager.py`: Replace root-module proxy reads with `SourceDependencyResolver`.
- `src/refactors/serial_cc/site_client_insights.py`: Replace a constant-based root import with `SourceDependencyResolver`.
- `src/refactors/serial_cc/start_site_client_capture_wireless.py`: Replace a constant-based root import with `SourceDependencyResolver`.
- `src/refactors/serial_cc/start_site_scan_capture.py`: Replace a constant-based root import with `SourceDependencyResolver`.
- `src/export/org_inventory_exporter.py`: Remove stale prose that described the deleted root import path.
- `tests/guardrails/test_source_misthelper_backrefs.py`: Teach the guard to catch constant-based root imports and `sys.modules` reads.
- `tests/unit/firmware/test_firmware_manager_config.py`: Update module-global tests for the source resolver host.
- `tests/unit/firmware/test_firmware_manager_monitoring.py`: Update progress-bar tests for the source resolver host.
- `tests/unit/firmware/test_firmware_manager_proxy.py`: Replace removed proxy tests with resolver seam tests.
- `specs/2670-sysmodules-alias/spec.md`: Record requirements, risk, and the test plan.
- `specs/2670-sysmodules-alias/plan.md`: Record the implementation plan and changed files.
- `specs/2670-sysmodules-alias/tasks.md`: Record the ordered task list.
- `changelog.d/issue-2670-sysmodules-alias.md`: Add the release-note fragment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing `MistHelper.py` size | Issue #2670 targets one startup alias. | A startup move would increase conflict risk. |
