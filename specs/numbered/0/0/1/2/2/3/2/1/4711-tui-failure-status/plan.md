# Implementation Plan: TUI completion reporting

**Branch**: `jmorrison-juniper-tui-completion-reporting` | **Date**: 2026-11-09 | **Spec**: [Specification](spec.md)

## Summary

Track normal completion within each launch call.
Report success after console restoration only when the TUI returns normally.
Keep the common exit helper neutral and preserve its signature.

## Technical Context

**Language/Version**: Python 3.13 or newer. Local locked restoration selected Python 3.14.7.

**Primary Dependencies**: Standard logging, pytest, and unittest.mock. No new dependency.

**Storage**: No storage change or database access.

**Testing**: Offline mocked sessions and TUI behavior with sockets and DNS blocked.

**Target Platform**: Windows, macOS, and Linux. Local verification uses macOS.

**Project Type**: Existing CLI.

**Performance Goals**: No additional external request or event loop.

**Constraints**: One reserved production file. No change to another owner's existing test file.

**Scale/Scope**: Issue #4711 only.

## Constitution Check

- The change adds no production declaration or public interface.
- The new test path and release note are explicitly reserved by the coordinator.
- Existing source-class and test-folder size violations remain outside this repair.
- A separate future change must reduce that structural debt without this reservation.
- All new specification directories have five children or fewer.
- The numeric route uses the eight base-5 segments for 4711.
- PowerShell is unavailable. Equivalent integer arithmetic and parent checks validated the route.
- The explicit user instruction prohibits branch creation hooks, shared feature pointers, deployment, and remote writes.
- Optional commit hooks are deferred until the single verified local commit.
- The local environment uses `uv sync --locked --extra dev --offline`, without bootstrap or Git configuration changes.
- No Mist transport, production operation, or real TUI starts.
- The final commit uses `Refs #4711`, not an issue closure.

These checks apply before and after the design. No unresolved design question remains.

## Project Structure

- `src/foundation/support/refactors/tui_launcher.py`
- `tests/unit/config/foundation/support/refactors/runtime/console/test_tui_launcher_failure_status.py`
- `changelog.d/issue-4711-tui-failure-status.md`
- Issue-specific records in this feature directory.

## Complexity Tracking

A call-local completion flag avoids new persistent state and preserves repeated-launch behavior.
An unconditional exit helper cannot determine success.
A parameter change would unnecessarily affect existing helper callers.
