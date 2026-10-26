# Implementation Plan: Capture cleanup completion

**Branch**: `jmorrison-juniper-fix-3769-capture-cleanup-order` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Issue #3769 and the managed specification in this directory.

## Summary

Retain the execution result until cleanup ends. Publish that result after successful cleanup.
Publish one explicit failed result if cleanup raises an exception.
Keep capture identity checks, trigger timing, transport behavior, and existing tests unchanged.

## Technical Context

**Language/Version**: Python 3.13.13.
**Primary Dependencies**: Existing mistapi session, websocket-client, pytest.
**Storage**: No change.
**Testing**: Event barriers, real controlled loopback stream, and the existing utility runner suite.
**Target Platform**: Windows, macOS, Linux.
**Project Type**: Existing utility runner.
**Performance Goals**: Preserve current stop and execution limits.
**Constraints**: No production request, timeout increase, assertion change, or #3575 change.
**Scale/Scope**: One source module and one new test module.

## Constitution Check

- Use the existing app-managed branch from current main, not a second branch.
- Keep the shared feature pointer unchanged.
- Add the test module under the compliant `transport/clients` directory.
- Add a managed specification with five root children or fewer.
- Existing source classes and import groups have structural debt. Do not add a production declaration or class.
- Existing `changelog.d` has process-folder debt. Add only this issue's unique required fragment.
- Incremental remediation: use managed routes for this record and leave unrelated process records unchanged.
- Make no new API or transport interface. Existing SDK session and transport contracts remain unchanged.
- Publish a PR only after focused local verification. Do not merge, deploy, or enable auto-merge.
- PowerShell setup scripts cannot run on this host. Use the inspected route algorithm and existing templates directly.
- Optional commit hooks remain deferred until local verification. Disabled companion hooks do not run.

## Project Structure

### Documentation (this feature)

This root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
Supporting records remain under `design/`.

### Source Code (repository root)

- `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`
- `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`
- `changelog.d/issue-3769-capture-cleanup-completion.md`

The existing `test_ws_utility_runner.py` remains read-only.

## Design

Store the execution exception, if present, without publishing it.
Use the existing `finally` cleanup boundary before choosing a terminal result.
Handle cleanup exceptions separately from execution errors.
Cleanup failure takes precedence over operator stop and execution errors.
Keep the existing finisher mappings for successful cleanup.
Log the cleanup exception type and action without its potentially sensitive message.

## Complexity Tracking

The repair uses nested exception handling in one existing lifecycle method.
This preserves unconditional cleanup without adding a helper, compatibility path, or new production type.
No dependency, schema, transport, or capture-selection change is necessary.
