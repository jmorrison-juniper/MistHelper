# Implementation Plan: Cache generator error reporting

**Branch**: `jmorrison-juniper-cache-error-reporting` | **Date**: 2026-11-09 | **Spec**: [Specification](spec.md)

**Input**: Issue #1794, cache generator slice.

## Summary

Use `logging.exception` for the existing error log in `CacheUtils._run_csv_generator`.
Preserve its root logger, message template, arguments, exception boundary, and boolean results.
Use mocked callbacks to test failures, success, keyboard interrupts, and process exits.
Test the public cache dispatcher with a missing cache and the same failure assertions.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Standard logging and unittest.mock.
**Storage**: No storage change.
**Testing**: pytest, Ruff, Black, mypy, Bandit, Radon, and repository guards.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Existing command-line tool.
**Performance Goals**: No change to successful generation.
**Constraints**: No live Mist calls, suppression, gate changes, or remote Git writes.
**Scale/Scope**: One existing source file and one existing test file.

## Constitution Check

The change adds no production declaration or public interface.
The existing `CacheUtils` class exceeds five members. This narrow change adds no member.
Separate remediation: divide cache responsibilities in a separately claimed issue, not this slice.
The release fragment uses the required unique process record exception.
Separate process-folder remediation remains outside this slice.
Each new specification directory has five children or fewer.
Tests use mocked generators and temporary paths. No production data changes.
The ordinary `Exception` boundary is necessary for caller-supplied callbacks.
Ruff requires `logging.exception` instead of `logging.error(..., exc_info=True)`.
`KeyboardInterrupt` and `SystemExit` remain outside that boundary.
No Mist transport, dependency, environment variable, or schema change is necessary.

The app owns the existing isolated branch, so the branch hook must not create another branch.
PowerShell was absent. A portable release supplies the repository route and setup commands.
The feature selector remains command-scoped to avoid changing the tracked shared selector.
Optional commit hooks are deferred to the single authorized local commit.
Disabled companion hooks do not execute.

## Project Structure

### Documentation (this feature)

The feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains research, data model, validation guide, and the specification checklist.

### Source Code (repository root)

- `src/foundation/persistence/cache/cache_utils.py`
- `tests/unit/cache/test_cache_utils.py`
- `changelog.d/issue-1794-cache-generator-errors.md`

## Validation

First demonstrate that the new failure test fails because the log record lacks exception information.
Then apply the single logging change and run the complete cache test module.
Run focused compile, lint, format, type, complexity, security, symbol, documentation, and specification checks.
Commit explicit paths once, then run the required test quality preflight and committed-difference gate.
Do not push or open a pull request. Report evidence and remaining blockers to the coordinator.

## Complexity Tracking

No new abstraction or exception handler is necessary.
Existing class and process-folder debt remain unchanged.
