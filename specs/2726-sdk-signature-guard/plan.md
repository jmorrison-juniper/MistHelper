# Implementation Plan: mistapi SDK signature guard

**Branch**: `chore/2726-sdk-signature-guard` | **Date**: 2026-09-16 | **Spec**: `specs/2726-sdk-signature-guard/spec.md`

**Input**: Feature specification from `specs/2726-sdk-signature-guard/spec.md`

## Summary

Extend the existing SDK name guard so it also compares each static call against the installed `mistapi` signature. Count dynamic calls as unverifiable, keep them visible, and fail when the count grows beyond the baseline.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard library `ast`, `importlib.util`, `logging`, `dataclasses`, and `pathlib`. Installed `mistapi` 0.64.0 supplies the checked SDK surface.

**Storage**: Not applicable. The guard reads files and writes no persistent runtime data.

**Testing**: `pytest`, `ruff`, `black`, `mypy`, `radon`, and `tools.guard_proof_audit`.

**Target Platform**: Windows local development and Linux CI.

**Project Type**: Python CLI and test suite.

**Performance Goals**: Complete the focused integration guard in less than one minute locally.

**Constraints**: Do not edit `src/`. Do not edit API documentation. Keep the guard offline and deterministic.

**Scale/Scope**: Scan `MistHelper.py`, 360 Python files under `src/`, and the installed `mistapi` package.

## Constitution Check

- Five-Item Rule: The change edits one existing test module and adds one spec folder. The existing test module is above 25 lines before this change, so this is grandfathered debt.
- Class-Based Architecture: The guard logic stays inside named classes. The fixture helper builds data and does not wrap a class method.
- Safety-First: The guard makes no live Mist API request and reads no secrets.
- Full Deployment Pipeline: Local gates, a branch, a pull request, CI, and auto-merge are required.
- Observability: The guard logs before and after source, SDK, and signature checks.

## Project Structure

### Documentation (this feature)

```text
specs/2726-sdk-signature-guard/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
tests/
└── integration/
    └── test_mistapi_sdk_compatibility.py

changelog.d/
└── issue-2726-sdk-signature-guard.md
```

**Structure Decision**: Keep all guard code in the existing integration test file so issue #2689 behavior extends rather than duplicates.

## Changed Files

- `tests/integration/test_mistapi_sdk_compatibility.py`
- `specs/2726-sdk-signature-guard/spec.md`
- `specs/2726-sdk-signature-guard/plan.md`
- `specs/2726-sdk-signature-guard/tasks.md`
- `changelog.d/issue-2726-sdk-signature-guard.md`

## Dynamic-call decision

The guard reports dynamic `*args`, `**kwargs`, and registry-only calls loudly. It fails only when the recorded baseline grows. This keeps the guard useful now and blocks new unmeasured SDK calls.

## Keyword and positional handling

The guard maps positional arguments to installed parameter positions. A rename does not fail a positional call when the argument count still satisfies the required positions. The guard checks keyword arguments by name. A removed or renamed keyword fails because the SDK no longer accepts that name.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing test module exceeds 25 lines | The guard already lived in this file from issue #2689 | Moving it now would mix a signature guard with a broad test refactor |
