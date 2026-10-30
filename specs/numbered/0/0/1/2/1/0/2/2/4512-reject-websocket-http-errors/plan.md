# Implementation Plan: Discovery HTTP errors

**Branch**: `jmorrison-juniper-reject-websocket-http-errors` | **Date**: 2026-10-30 | **Spec**: [Specification](spec.md)

**Input**: Issue #4512 and the linked specification.

## Summary

Reject unsuccessful device responses before reading their data. Preserve nonfatal discovery and valid configuration when statistics fail.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Existing mistapi SDK.
**Storage**: Existing in-memory device caches.
**Testing**: pytest with injected SDK responses, without network access.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: CLI.
**Performance Goals**: No additional requests.
**Constraints**: No live Mist calls or new transport.
**Scale/Scope**: Two device response boundaries in one discovery mixin.

## Constitution Check

Use the existing app-managed branch. The branch hook must not create another checkout.
Use the command-scoped feature selector and leave the shared feature pointer unchanged.
Add no source module or class. Existing mixin member counts exceed the structural limit.
Keep this repair narrow. A separate future decomposition must reduce that existing debt.
The unique changelog fragment uses the process-folder exception. Existing fragments remain unchanged.
Future process-folder migration must retain these unique records.
All requests remain SDK requests. No owned transport changes.
The pre-design and post-design checks accept this scoped repair.

## Project Structure

### Documentation (this feature)

Keep `spec.md`, `plan.md`, and `tasks.md` at this feature root.
Keep supporting records under `design/`, with five children or fewer.
Attach the read-only specification analysis to issue #4512.

### Source Code (repository root)

- `src/mist/realtime/websocket/service_ping_discovery.py`: Validate device response statuses.
- `tests/unit/websocket/test_service_ping_discovery.py`: Cover failed and successful discovery.
- `changelog.d/issue-4512-reject-websocket-http-errors.md`: Describe the operator-visible repair.

**Structure Decision**: Edit existing source and test modules. Add no production abstraction for two small boundary checks.

## Complexity Tracking

| Existing debt | Scope decision | Incremental remediation |
|---|---|---|
| Discovery mixin exceeds five members | Edit existing methods only | Separate future discovery decomposition |
| Test module exceeds five names | Extend established test coverage | Separate future test grouping |
| Changelog folder exceeds five children | Add one required unique fragment | Preserve records during future folder migration |

## Validation

Run regression tests before the repair to prove failure.
Run focused discovery and manager tests after the repair.
Run compile, Ruff, Black, mypy, Bandit, complexity, docstrings, dead-code, and symbol checks on changed paths.
Run dependency audit and test-quality preflight.
After the commit, run the committed-diff test-quality gate against current `origin/main`.
Run required PR checks and CodeQL before standard auto-merge.
