# Implementation Plan: Status Fallback for Quiet Operation Streams

**Branch**: `fix/3183-status-fallback` | **Date**: 2026-09-23 | **Spec**: specs/3183-status-fallback/spec.md

## Summary

The Operations page must recover when the event stream closes or stays quiet without a terminal event. The browser will arm a bounded fallback timer and ask the existing status route for the active run.

## Technical Context

**Language/Version**: JavaScript in the existing browser bundle, plus Python 3.13 tests.

**Primary Dependencies**: Existing portal JavaScript, pytest, and the status route at `/api/operations/status/<run_id>`.

**Storage**: No persistent storage change.

**Testing**: Static unit guard for the stream fallback and local portal verification on port 9602.

**Target Platform**: MistHelper Operations portal in a desktop browser.

**Project Type**: Web portal frontend repair.

**Performance Goals**: Ask the status route within 20 seconds after stream silence starts.

**Constraints**: Do not edit `web_portal/services/operation.py`. Do not increase Mist API load.

**Scale/Scope**: One static JavaScript file, one unit test, one release-note fragment, and SpecKit artifacts.

## Constitution Check

The change touches an existing large JavaScript file. It adds no new direct child to a noncompliant hierarchy. New helper functions stay below 25 lines and use no parameters or one parameter.

## Project Structure

```text
specs/3183-status-fallback/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui.md
└── tasks.md

web_portal/static/js/operations.js
tests/unit/web_portal/test_operation_stream_fallback.py
```

**Structure Decision**: Use the existing operations controller and portal unit tests.

## Complexity Tracking

No new complexity violation exists.
