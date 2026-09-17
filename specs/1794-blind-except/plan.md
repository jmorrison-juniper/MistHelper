# Implementation Plan: Blind Exception Handler Cleanup Slice

**Branch**: `refactor/1794-blind-except` | **Date**: 2026-09-16 | **Spec**: `specs\1794-blind-except\spec.md`

**Input**: Feature specification from `specs\1794-blind-except\spec.md`

## Summary

Repair one high-risk firmware handler first. Replace the broad catch around the `listSiteDevicesStats` call with a `RuntimeError` catch, so malformed SDK calls raise.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: `mistapi` 0.64.0, pytest, ruff, black, mypy, Bandit.

**Storage**: No schema change.

**Testing**: pytest unit tests and repository quality gates.

**Target Platform**: Windows development worktree and GitHub Actions.

**Project Type**: Python CLI and web service repository.

**Performance Goals**: No extra Mist API calls.

**Constraints**: Do not edit issue #1793 root logger calls or issue #1766 warning text.

**Scale/Scope**: Baseline is 813 handlers. This slice repairs one handler and leaves 812.

## Constitution Check

- Five-Item Rule: No new source module and no new class.
- Class-Based Architecture: The change stays inside `RunningFirmwareVersionResolver`.
- Safety-First: Programming errors now raise on a firmware evidence path.
- Observability: The operational failure path keeps the existing error log.
- Quality Gates: Targeted pytest, ruff, black, Bandit, and other requested gates run before final report.

## Project Structure

### Documentation (this feature)

```text
specs\1794-blind-except\
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src\firmware\running_version.py
tests\unit\firmware\test_running_version.py
changelog.d\issue-1794-blind-except.md
```

**Structure Decision**: Use the existing firmware resolver and unit test file.

## Complexity Tracking

No constitution violation is added.

## Changed Files

- `src\firmware\running_version.py`: Narrow the catch in `fetch_site_running_versions`.
- `tests\unit\firmware\test_running_version.py`: Add the runtime-failure and programming-error proofs.
- `tests\unit\firmware\test_firmware_manager_ssr.py`: Patch SSR flow tests so they do not call a live stats endpoint.
- `specs\1794-blind-except\spec.md`: Record requirements and acceptance criteria.
- `specs\1794-blind-except\plan.md`: Record the implementation plan.
- `specs\1794-blind-except\tasks.md`: Record the execution order.
- `changelog.d\issue-1794-blind-except.md`: Add the release-note fragment.

## Deferred Work

- #2833 repairs the remaining firmware and upgrade portal handlers. Count: 216.
- #2834 repairs the API, authentication, input, and inventory handlers. Count: 42.
- #2835 repairs the database, export, data, and file persistence handlers. Count: 139.
- #2836 repairs the display, report, UI, and miscellaneous handlers. Count: 415.
