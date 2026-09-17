# Implementation Plan: Masking Default Audit

**Branch**: `2753-masking-defaults` | **Date**: 2026-09-17 | **Spec**: `specs\2753-masking-defaults\spec.md`

**Input**: Feature specification from `specs\2753-masking-defaults\spec.md`

## Summary

Repair the destructive upgrade start route so it refuses missing input at the point of absence. Add unit tests that assert the visible refusal and the log message.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Flask, pytest, and the existing upgrade portal modules.

**Storage**: No schema change.

**Testing**: pytest, ruff, black, mypy, bandit, pylint, symbol_diff, and guard_proof_audit.

**Target Platform**: Windows development and Linux container runtime.

**Project Type**: Web route inside the MistHelper upgrade portal.

**Performance Goals**: Validation runs before any cloud call and adds no network work.

**Constraints**: Do not touch the work for exception handlers in issue #1794. Do not log secrets.

**Scale/Scope**: Triage the 235 visible priority candidates and repair four defaults in one route.

## Constitution Check

- Five-Item Rule: Each method of the validator stays under 25 lines and five parameters.
- Class-Based Architecture: The validation lives in `UpgradeStartInputValidator`.
- Safety-First: The destructive route refuses missing device, version, and strategy input.
- Observability: The validator logs before validation and logs the exact missing field.
- Deployment Pipeline: The branch uses a worktree, a pull request, and local gates.

## Project Structure

### Documentation

```text
specs\2753-masking-defaults\
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src\upgrade_portal\app\routes\upgrade.py
tests\unit\upgrade_portal\test_upgrade_start_input_validator.py
changelog.d\issue-2753-masking-defaults.md
```

**Structure Decision**: Use the existing route module because the defect is local to the route boundary.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Existing large route module touched | The unsafe defaults live at this boundary. | A new wrapper module would hide the route ownership. |
