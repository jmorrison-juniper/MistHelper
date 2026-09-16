# Implementation Plan: Browser upgrade start journey

**Branch**: `fix/2632-browser-upgrade` | **Date**: 2026-09-16 | **Spec**: `specs/2632-browser-upgrade/spec.md`

**Input**: Feature specification from `specs/2632-browser-upgrade/spec.md`

## Summary

Repair issue #2632 by adding measured browser coverage for the site upgrade start path. Keep the default test operator on a reserved address. Use the existing firmware-operator fixture for the write path. Keep the existing 120-second E2E timeout guard as the hang boundary.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: pytest, pytest-playwright, pytest-timeout, Flask, Waitress on Windows.

**Storage**: Process-owned E2E record stores under the browser fixture. No persistent schema changes.

**Testing**: pytest E2E, unit tests, contract tests, ruff, black, and mypy.

**Target Platform**: Windows development worktree and GitHub Actions runners.

**Project Type**: Python CLI with a Flask upgrade capture portal.

**Performance Goals**: The full browser suite must finish in the same time class as the issue baseline.

**Constraints**: No production credential. No live Mist call. No default reachable operator address.

**Scale/Scope**: One issue, two browser fixture files, one release-note fragment, and one specification set.

## Constitution Check

- Five-Item Rule: The change edits existing test files only and adds no new production package child.
- Class-Based Architecture: The new browser assertion lives in `TestUpgradeStart`.
- Safety-First: The reachable address stays in a test-only fixture. The default address stays reserved.
- Full Deployment Pipeline: Local gates, commit, pull request, CI, and merge are required.
- Observability: New test steps log before and after meaningful browser actions.

## Project Structure

### Documentation (this feature)

```text
specs/2632-browser-upgrade/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
tests/
└── e2e/
    ├── conftest.py
    └── upgrade_portal/
        ├── conftest.py
        └── test_upgrade.py

changelog.d/
└── issue-2632-browser-upgrade.md
```

## Changed Files

- `tests/e2e/upgrade_portal/conftest.py`: Add a start-ready seeded run that only the start test mutates.
- `tests/e2e/upgrade_portal/test_upgrade.py`: Add `TestUpgradeStart` with a measured start journey.
- `tests/e2e/conftest.py`: Keep the existing 120-second E2E timeout guard unchanged.
- `specs/2632-browser-upgrade/spec.md`: Record the behavior contract.
- `specs/2632-browser-upgrade/plan.md`: Record the implementation plan.
- `specs/2632-browser-upgrade/tasks.md`: Record the task order and evidence.
- `changelog.d/issue-2632-browser-upgrade.md`: Add the release note.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing E2E fixture exceeds five constructs | The fixture already holds the browser server seam and seeded records | Moving records to a new module would be unrelated risk for this bug fix |
