# Implementation Plan: Terminal Preference Readiness

**Branch**: `fix-3759-terminal-readiness` | **Date**: 2026-10-03 | **Spec**: `spec.md`

**Input**: Feature specification from `specs/3759-terminal-preference-readiness/spec.md`

## Summary

J9 currently snapshots an unchecked template control before deferred preference initialization can set the default.
Use Playwright's checked-state wait for the existing default, then preserve the current snapshot, screenshot, and assertion.
Add deterministic browser controls for delayed initialization and bounded failure.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing pytest, pytest-playwright, and Playwright dependencies.

**Storage**: None.

**Testing**: Browser tests with Playwright and the required repository checks.

**Target Platform**: Local development browser with the existing native pytest fixtures.

**Project Type**: Python tests.

**Performance Goals**: Keep every readiness wait within its supplied timeout.

**Constraints**: Do not change runtime, shared harness, fixtures, dependencies, policy files, baseline files, exclusions, or other journeys.

## Constitution Check

- The change remains in the unique directory for this issue and the authorized browser test scope.
- Generated screenshots remain under the existing ignored test-artifact path.
- No Mist Cloud transport or product behavior changes.
- No release fragment applies to this internal test repair.

## Project Structure

```text
specs/3759-terminal-preference-readiness/
├── plan.md
├── spec.md
└── tasks.md
tests/e2e/websockets_tab/
├── test_3759_terminal_preference_readiness.py
└── test_websockets_terminal.py
```

**Structure Decision**: Change only J9 in the existing file. Put readiness controls in a new test file.

## Verification Plan

1. Run the readiness controls alone with native Playwright.
2. Run the existing browser cases separately from the new controls.
3. Record collected, completed, failed, skipped, and unexecuted original memberships.
4. Run syntax, Ruff, Black, configured mypy, test-quality, and applicable security checks.
5. Record unavailable or pre-existing gates without suppressing them.
