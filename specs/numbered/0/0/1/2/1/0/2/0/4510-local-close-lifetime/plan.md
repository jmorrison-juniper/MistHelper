# Implementation Plan: Local close lifetime

**Branch**: `jmorrison-juniper-shell-local-close-investigation` | **Date**: 2026-10-30 | **Spec**: [Specification](spec.md)

## Summary

Give each connection one shared `SocketRuntime`.
That runtime owns a receive lock and a local-close event.
Close sets the event and aborts the connection before it waits for the receive lock.
It closes the descriptor only after the active receive exits.
Reads inspect the event under the lock before socket readiness or receive.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Existing websocket-client 1.9.2.
**Storage**: No persistent data change.
**Testing**: pytest, controlled thread schedules, and the session-only native poll reproduction.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Existing terminal transport.
**Performance Goals**: Preserve existing stop test bounds.
**Constraints**: No timeout increase, reader join, external request, or publication.
**Scale/Scope**: Shell, screen, and event-stream socket lifetime.

## Constitution Check

The change preserves public contracts and uses existing transport collaborators.
New tests enter a bounded child package.
Existing `ShellConnection` and `StreamConnection` exceed five members. Narrow lifetime wiring does not add a new public method.
The existing runtime test module exceeds five top-level names. Caller updates remain narrow.
Future structural remediation should divide those existing connection and test responsibilities separately.
The unique changelog fragment enters the established process folder.
Existing process-folder debt remains unchanged. Managed specification routes prevent additional root debt.
No new SDK transport, endpoint, credential, or product output is introduced.
The native diagnostic proves the failure before implementation.
Optional commit hooks remain deferred until validation. The app-managed branch remains active.

## Project Structure

### Documentation

The feature root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory holds research, data model, quickstart, and checklists.
No external contract changes require a contracts directory.

### Source Code

- `src/mist/realtime/websocket_streams/live/transport/runtime/reader/socket_runtime.py`
- `src/mist/realtime/websocket_streams/live/transport/runtime/reader/frame_reader.py`
- `src/mist/realtime/websocket_streams/live/transport/shell_client.py`
- `src/mist/realtime/websocket_streams/live/transport/stream_client.py`
- `tests/unit/websocket_streams/live/transport/runtime/test_frame_reader.py`
- `tests/unit/websocket_streams/live/transport/runtime/lifetime/`
- `changelog.d/issue-4510-local-close-lifetime.md`

## Complexity Tracking

The runtime remains a small collaborator with five methods or fewer.
No compatibility alias, socket-method override, native test dependency, or production scheduling hook is added.
