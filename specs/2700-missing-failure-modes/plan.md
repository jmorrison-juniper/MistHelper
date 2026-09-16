# Implementation Plan: Missing failure mode triage

**Branch**: `chore/2700-missing-failure-modes` | **Date**: 2026-09-16 | **Spec**: `specs\2700-missing-failure-modes\spec.md`

**Input**: Feature specification from `specs\2700-missing-failure-modes\spec.md`

## Summary

Repair the failure-mode analyzer so it scopes tests by the imported source under test. Add targeted `MistEndpointService` failure-mode tests. Record the remaining rule debt in follow-up issues.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard library, pytest, requests exceptions, and existing mistapi SDK test seams.

**Storage**: Existing analyzer JSON report under `tools\test_quality_analyzer\output\report.json`.

**Testing**: pytest, Ruff, Black, mypy, radon, `tools.test_quality_analyzer`, and `tools.guard_proof_audit`.

**Target Platform**: Windows local worktree and GitHub Actions on `main` pull request checks.

**Project Type**: Python CLI with a nested `mist-ops-platform` Python service.

**Performance Goals**: Keep analyzer runtime in the same order as the existing full analyzer run.

**Constraints**: Do not edit generated Mist API documentation. Change fewer than 20 files.

**Scale/Scope**: Six rule groups and one high-risk Mist SDK service test file.

## Constitution Check

- Five-Item Rule: This change edits existing files and adds no new package child.
- Class-Based Architecture: New analyzer behavior lives in `FailureModeApplicabilityInferer` and data classes.
- Safety-First: No live Mist request occurs. All new tests use mocks.
- Full Deployment Pipeline: Local gates and pull request checks prove the change.
- Observability: The detector emits an inspected module metric. Empty body handling logs a warning.

## Project Structure

### Documentation (this feature)

```text
specs\2700-missing-failure-modes\
├── spec.md
├── plan.md
├── tasks.md
└── triage.md
```

### Source Code (repository root)

```text
tools\test_quality_analyzer\
├── __main__.py
└── detection\missing_failure_mode.py

tests\tools\test_quality_analyzer\
└── test_meta_fixtures.py

mist-ops-platform\
├── src\shared\mist\endpoints.py
└── tests\unit\mist\test_endpoint_retry.py

changelog.d\
└── issue-2700-missing-failure-modes.md
```

**Structure Decision**: Edit the existing analyzer, guard, and highest-risk Mist SDK service tests. Add only feature documentation and one release-note fragment.

## Touched Existing Violations

No new hierarchy violation is added. The repository already has more than five top-level children, so this feature uses existing directories only.

## Changed Files

1. `tools\test_quality_analyzer\detection\missing_failure_mode.py`.
2. `tools\test_quality_analyzer\__main__.py`.
3. `tests\tools\test_quality_analyzer\test_meta_fixtures.py`.
4. `mist-ops-platform\src\shared\mist\endpoints.py`.
5. `mist-ops-platform\tests\unit\mist\test_endpoint_retry.py`.
6. `specs\2700-missing-failure-modes\spec.md`.
7. `specs\2700-missing-failure-modes\plan.md`.
8. `specs\2700-missing-failure-modes\tasks.md`.
9. `specs\2700-missing-failure-modes\triage.md`.
10. `changelog.d\issue-2700-missing-failure-modes.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| None | Not applicable | Not applicable |
