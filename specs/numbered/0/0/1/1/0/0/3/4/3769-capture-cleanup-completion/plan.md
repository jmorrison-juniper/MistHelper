# Implementation Plan: Capture cleanup completion

**Branch**: `jmorrison-juniper-fix-3769-capture-cleanup-completion`

**Date**: 2026-10-26

**Spec**: [Capture cleanup completion](spec.md)

## Summary

Keep execution results private until stream closure and capture cleanup return.
Report cleanup exceptions as failed results before normal execution classification can run.
Change only `UtilityExecution` in production.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Existing Mist SDK session and WebSocket transport.

**Storage**: No change.

**Testing**: pytest, threading events, controlled API responses, and existing loopback runner tests.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Internal utility lifecycle.

**Performance Goals**: Add no delay, polling, worker, or timeout.

**Constraints**: Preserve capture identity checks and all existing live assertions.

**Scale/Scope**: One production class and one new test module.

## Constitution Check

- The existing worktree branch remains app-managed. The branch hook must not create another branch.
- The managed route uses eight base-5 segments, resolved through `create-new-feature.ps1`.
- The active feature selector stays command-scoped. No tracked feature pointer changes.
- The new test enters `transport/clients`, which has three existing children.
- The feature root has at most five children. Supporting records enter `design/`.
- The release note is one unique process record. Existing changelog directory debt remains outside this repair.
- Separate remediation: migrate existing process-folder debt through the established structural program.
- The existing execution module has five top-level classes. This repair adds no top-level class.
- Existing collaborators exceed five fields or methods in places. The repair does not expand those declarations.
- Separate remediation: divide those existing declarations in a dedicated structural change.
- No transport, SDK call, output format, credential, or duration policy changes.
- No new external interface requires SDK insufficiency evidence.
- Tests mock external responses and retain the existing loopback integration coverage.
- Commit and pull request titles use Conventional Commits.

## Project Structure

Production:
`src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`

Regression:
`tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`

Read-only integration coverage:
`tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`

Documentation:
This feature directory and `changelog.d/issue-3769-capture-cleanup-completion.md`.

## Design

Record a possible execution exception without notifying the sink.
Run the existing `_close()` exactly once.
If cleanup raises, log the exception type and publish one explicit failed result.
Otherwise, apply the existing execution-error or normal-result classification.
Do not change `CaptureCleanup`, `CaptureStopper`, or `UtilityFinisher`.

## Validation

First run the barrier test against unchanged source and retain its failure output.
Then run focused unit tests and the unchanged loopback utility suite.
Measure execution-module coverage and apply compile, lint, format, type, complexity, security, symbol, and documentation gates.
Commit the intended tests before the required test-quality comparison.

## Complexity Tracking

No new structural exception is required.
Keep `run()` within 25 lines and cyclomatic complexity 10.
Preserve the existing module-level symbol set.
