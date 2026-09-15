# Implementation Plan: Isolated AppContext State

**Branch**: `fix/2667-appcontext-state` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/2667-appcontext-state/spec.md`

## Summary

`ApplicationBootstrap.__init__()` reads `MainEntrypoint.context`, which is a shared class attribute. Two bootstrap objects therefore share the session, organization, MSP grants, output format, progress emitter, and fast-mode flag. The repair makes each bootstrap create its own `AppContext` by default, while still allowing an explicit context. The bootstrap activates its context before startup side effects, so legacy module views continue to read the active invocation state.

## Technical Context

**Language/Version**: Python 3.13+.

**Primary Dependencies**: Standard library only for this change. Existing pytest, ruff, black, and mypy gates validate it.

**Storage**: N/A. No data schema changes.

**Testing**: pytest unit tests in `tests/unit/refactors/test_app_context_session_state.py` and `tests/unit/refactors/test_main_entrypoint.py`.

**Target Platform**: Windows PowerShell and Linux container hosts through existing Python code.

**Project Type**: Single Python CLI and web entry point.

**Performance Goals**: N/A. The change creates one small dataclass object per invocation.

**Constraints**: Do not change Mist API behavior. Keep legacy module views for session state. Keep functions within the 5-item rule limits.

**Scale/Scope**: One source file, two focused test files, one release-note fragment, and three SpecKit artifacts.

## Constitution Check

| Principle | Gate evaluation |
|---|---|
| Five-Item Rule | PASS. The new constructor parameter count is three, and each changed method stays under 25 lines. |
| Class-Based Architecture | PASS. The change extends `ApplicationBootstrap` and `MainEntrypoint`; it adds no standalone wrapper. |
| Safety-First | PASS. The change prevents state leakage between invocations. |
| Observability | PASS. The activation step logs before and after context changes. |
| Compatibility | PASS. Legacy module attribute views continue to use the active context. |

## Project Structure

### Documentation (this feature)

```text
specs/2667-appcontext-state/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
src/refactors/main_entrypoint.py
tests/unit/refactors/test_app_context_session_state.py
tests/unit/refactors/test_main_entrypoint.py
changelog.d/issue-2667-appcontext-state.md
```

**Structure Decision**: This is a surgical entry-point repair. No new package is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Existing `MistHelper.py` has many references to `MainEntrypoint.context`. | The branch must keep legacy module views working. | Rewriting every reader is outside issue #2667 and would increase risk. |
