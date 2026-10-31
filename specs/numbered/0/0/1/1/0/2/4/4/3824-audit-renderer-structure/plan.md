# Implementation Plan: Nested Source Package Remediation

**Branch**: `refactor/3824-websocket-catalog-structure` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/spec.md`.

## Summary

Move the audit renderer and its helpers into bounded packages. Keep report behavior and renderer methods unchanged. The next slice moves the WebSocket utility text module into the existing utility package and keeps its labels, descriptions, and hints unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: pytest for tests; no new runtime dependency

**Storage**: None

**Testing**: pytest, import smoke checks, Ruff, Black, mypy, nested-package guard, and test-quality ratchet

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python library and command-line application

**Performance Goals**: No change to report generation time or output size

**Constraints**: Each source directory has five structural children or fewer. Do not keep old-path aliases. Keep Mist API calls, report content, and utility text unchanged.

**Scale/Scope**: Six renderer modules, one utility text module, active imports, focused tests, and two nested-package baseline entries

## Constitution Check

### Pre-design gate

- **Five-Item Rule**: The audit move left each affected audit directory at five children or fewer. The current WebSocket catalog has six structural children. Moving `utility_text.py` into `utilities/` leaves five in `catalog/` and five in `utilities/`.
- **Existing debt**: The repository measures 34 nested source violations and 237 total excess children. This slice resolves the catalog violation and targets 33 violations and 236 total excess children.
- **Incremental remediation**: Issue #3824 tracks the remaining baseline violations. This slice removes only the resolved catalog entry.
- **Class-based architecture**: Keep behavior in `AuditReportRenderer` and `UtilityText`. Do not add a wrapper or alias.
- **Safety**: No Mist Cloud operation, destructive action, or production data change is in scope.
- **Process records**: Extend the existing issue specification under its managed numeric route. Do not change `.specify/feature.json`. Do not add a release note because this internal move changes no user-visible behavior.
- **Deployment pipeline**: Run each applicable test and quality gate. Stage only the explicit manifest. Commit with a Conventional Commit subject and the required co-author trailer. Rebase and rerun affected gates. Push the branch and open a pull request with exact results. Keep it unmerged and disable auto-merge until the coordinator verifies all required checks, CodeQL, review, base freshness, and no active holds.

**Gate result**: Pass. The planned move reduces the measured violation count and does not increase a source directory count.

### Post-design gate

- The interface contract records the renderer and utility text module-path changes.
- The test plan covers report behavior, utility text, imports, and structural debt.
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

The WebSocket catalog move uses this package layout:

```text
src/mist/realtime/websocket_streams/catalog/
├── model.py
├── sdk_annotation.py
├── utility_text.py  # Before this slice
├── utilities/
│   ├── utility_catalog.py
│   ├── utility_discovery.py
│   ├── utility_fields.py
│   └── utility_profile.py
```

After the move, `utility_text.py` resides in `utilities/`. Its two source callers and two test callers use the new path. The old path does not remain.

## Implementation Notes

- The renderer class moves from `src.mist.access.audit.renderer` to `src.mist.access.audit.rendering.renderer`. Its `__module__` value changes accordingly.
- Update active imports, test imports, and module docstrings. Remove the old module files.
- Remove the `src/mist/access/audit` baseline entry after the measured count reaches five.
- Update the guard's explicit repository-wide count from 35 violations and 242 excess to 34 violations and 237 excess.
- Move `utility_text.py` to `src/mist/realtime/websocket_streams/catalog/utilities/utility_text.py`.
- Update the utility text logger name and `UtilityText.__module__` path. Keep class methods and returned text unchanged.
- Update both source imports and both test imports. Remove the old module path without an alias.
- Remove the `src/mist/realtime/websocket_streams/catalog` baseline entry and update the measured count to 33 violations and 236 excess.
- Do not rewrite the tracked `.specify/feature.json` pointer. It selects another feature and is not part of this change.
- Stop this slice after pull request creation. The coordinator owns merge and production deployment after all required checks and review pass.

## Complexity Tracking

No constitution exception is required.
