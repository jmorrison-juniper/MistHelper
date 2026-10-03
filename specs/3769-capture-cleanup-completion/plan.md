# Implementation Plan: Capture Cleanup Completion

**Branch**: `jmorrison-juniper-capture-cleanup-completion`

**Date**: 2026-10-03

**Spec**: `specs/3769-capture-cleanup-completion/spec.md`

## Summary

Make utility completion wait for stream close and required capture cleanup.
Preserve runtime error mapping when cleanup succeeds.
Report cleanup errors as one failed result, including after an operator stop.
Require successful Mist API responses. Preserve existing capture lookup data selection.

## Technical Context

**Language**: Python 3.13 or newer.

**Dependencies**: Existing `mistapi` API session protocol, `pytest`, and `pytest-cov`.

**Storage**: None. The change adds no persistent state.

**Testing**: Focused utility runner tests with the existing fake Mist API session.

**Target platform**: Existing MistHelper host and container platforms.

**Project type**: Python utility runner inside the MistHelper application.

**Performance goals**: Add no waits, retries, or timeouts to runtime cleanup.

**Constraints**: Keep the existing utility test file read-only. Add no transport, endpoint, dependency, or fixture. Keep the release note in its own `changelog.d/` file.

**Scale and scope**: One utility run, one stream client, and at most one capture cleanup request.

## Technical Approach

1. Keep runtime work separate from terminal reporting. `UtilityExecution` records any runtime exception, then continues to cleanup.
2. Detach and close the stream client in its own guarded step. Attempt the real `CaptureCleanup` in a second guarded step, even if close fails.
3. Finalize once after both cleanup steps resolve. If cleanup fails, call `UtilityFinisher.failure`. If cleanup succeeds and a runtime exception exists, call `UtilityFinisher.error` to preserve the current operator-stop mapping. Otherwise call `UtilityFinisher.finish`.
4. Log cleanup traceback frames through the existing structured logging boundary. Do not log exception text, API payloads, capture IDs, credentials, or local variables.
5. In `CaptureStopper`, require integer HTTP status 200 for lookup and deletion. Reject missing or malformed status. Preserve existing data selection.
6. Preserve the scope selected by the trigger channel. Use the request's original organization or site ID and the capture ID from the trigger answer.
7. Treat cancellation as the existing cooperative stop event. Do not interrupt cleanup. Normal completion closes the stream without cloud stop.
8. Pass the monitor completion timestamp into `UtilityFinisher.finish`. Cleanup duration must not change a normal completion reason.
9. Add an issue-owned release-note fragment at `changelog.d/issue-3769-capture-cleanup-completion.md`. Do not edit `CHANGELOG.md`.

## Constitution Check

| Gate | Result | Evidence |
| --- | --- | --- |
| Five-Item Rule | Pass | The coordinator approved the existing `transport/clients/` test directory. The new file changes its child count from three to four. |
| Class-based architecture | Pass | The design uses the existing `UtilityExecution`, `CaptureCleanup`, `CaptureStopper`, and `UtilityFinisher` classes. |
| Safety and input validation | Pass | Cleanup preserves capture identity and scope. Missing or malformed HTTP status fails visibly. |
| Observability and secret handling | Pass with implementation constraint | Use the existing structured logger. Log traceback frames without exception text, request data, identifiers, credentials, or locals. |
| Mist Cloud transport | Pass | Keep `mist_get` and `mist_delete`. Add no endpoint or direct HTTP request. |
| Product data and persistence | Pass | Add no product output or persistent state. |
| Release note | Pass | The feature owns one issue-named fragment. `changelog.d/` currently has 79 entries. The constitution permits unique required records there. Track a separate process-folder debt review. |

**Resolved gate decision**: The coordinator approved the replacement test path before its creation. No existing file moves or changes.

## Design Decisions

- Keep terminal reporting in `UtilityExecution` after cleanup, rather than reporting in `_execute`.
- Run stream close and capture cleanup independently. Record both cleanup failures, then report one final `FAILED` result.
- Give cleanup failures precedence over runtime errors. This ensures an operator stop cannot hide cleanup failure.
- Call `UtilityFinisher.error` only when cleanup succeeds. This retains the existing stopped result for a runtime error while stopping.
- Treat a valid lookup with no matching capture as success. Do not send DELETE in that case.
- Require status 200 for both REST operations. A successful lookup alone does not prove that DELETE succeeded.
- Treat a stop request during cleanup as a state change, not as permission to interrupt cleanup.
- Use deterministic `threading.Event` barriers for the completion-order test. Do not use sleeps or increase existing timeouts.

## Project Structure

```text
specs/3769-capture-cleanup-completion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── capture-cleanup.md

src/websocket_streams/live/runners/utility/runner/
├── execution.py
├── capture.py
└── monitoring.py

tests/unit/websocket_streams/live/transport/clients/
└── test_capture_cleanup_completion_3769.py

changelog.d/
└── issue-3769-capture-cleanup-completion.md
```

**Structure decision**: Reuse the current runner classes and API protocol. Add no production module. Keep four direct specification children.
The user holds remote delivery. Local completion does not claim release, merge, or deployment completion.

## Verification Plan

1. Add the controlled DELETE-barrier test to the new owned test file. Run that test once against the unmodified production source. Record the expected red result: the sink reaches a terminal state while DELETE remains blocked.
2. Implement the source changes only after the red result. Run the same barrier test. It must pass, and the sink must record exactly one terminal result after the barrier releases.
3. Run the owned tests for successful cleanup, no match, GET failure, DELETE failure, close failure, operator stop, stop during trigger, normal completion, and cancellation.
4. Confirm both scope paths and matching-ID selection. Confirm malformed status never permits successful cleanup.
5. Measure branch coverage for changed branches. Require at least 80 percent.
6. Run syntax, lint, format, type, and the focused test checks for changed files. Do not run a full deployment pipeline as part of planning.

## Complexity Tracking

| Violation or debt | Required action |
| --- | --- |
| The original utility test directory has five children. | Use the coordinator-approved existing `transport/clients/` directory. |
| `changelog.d/` has 79 direct entries. | Add only the issue-owned fragment during implementation. Track process-folder cleanup as a separate action. |
