# Implementation Plan: Terminal Session Replay Isolation

**Branch**: `jmorrison-juniper-fix-4508-websocket-shard-isolation`

**Date**: 2026-11-08

**Spec**: [Specification](spec.md)

## Summary

The CI replay response contains the complete 44-byte banner and prompt.
The new xterm instance has blank rows while the page remains above the terminal.
Its native visibility observer pauses rendering outside the viewport.

The test waits for rendered text before it ensures that the terminal enters the viewport.
This ordering can stop the test although the stored bytes arrive correctly.
A controlled offline experiment reproduces the blank rows.
Scrolling the terminal into view renders the same stored bytes.

Repair the test precondition, not the server or timeout.
Add a controlled browser case that holds the replay until the native visibility observer pauses rendering.
Run the existing paste isolation assertions in both normal and controlled cases.

## Technical Context

**Language/Version**: Python 3.13 and browser JavaScript.

**Primary Dependencies**: Existing pytest, Playwright, Chromium, Flask, and vendored xterm.

**Storage**: Fake shell buffers only.

**Testing**: Focused browser regression, full offline WebSockets shard, and applicable test gates.

**Target Platform**: Existing browser tests on macOS and Linux.

**Project Type**: Test reliability repair.

**Performance Goals**: Preserve the existing 15-second wait boundary.

**Constraints**: No live Mist request, timeout increase, production change, or CI retry.

**Scale/Scope**: One existing browser test module, its specification, and one release fragment.

## Constitution Check

The production protocol and transport remain unchanged.
All external connections use the existing fake cloud and loopback portal.
The new control uses the browser's native visibility observer.
It must not replace xterm output with simulated text.

The test module already exceeds the five-name limit.
The selected test already exceeds the 25-line limit.
Keep the repair narrow and document this existing debt.
An incremental follow-up can divide browser journeys by behavior without changing their test identifiers.
The release-fragment folder has existing process-folder debt.
Add only the unique issue fragment. A separate folder migration can reduce this debt.

The specification uses the route returned by the repository PowerShell resolver.
Keep the active feature selector command-scoped.
Do not change `.specify/feature.json`.
Use Conventional Commits and the repository PR template.

## Project Structure

The feature root holds `spec.md`, `plan.md`, `tasks.md`, and `design/`.
The design folder holds research, data model, validation instructions, contracts, and checklists.

The implementation changes `tests/e2e/websockets_tab/test_websockets_terminal.py`.
It adds `changelog.d/issue-4508-terminal-replay-visibility.md`.
It does not change `tests/e2e/conftest.py` or a production file.

## Complexity Tracking

| Existing debt | Bounded decision | Incremental action |
| - | - | - |
| Large terminal test module | Keep the replay journey in its existing module | Divide browser journeys in a separate change |
| Large selected journey | Extract the replay selection into a small test helper class | Keep later test helpers within 25 lines |
| Release-fragment folder debt | Add one issue-specific fragment | Migrate process records separately |
