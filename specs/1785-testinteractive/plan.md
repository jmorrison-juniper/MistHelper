# Implementation Plan: Unattended Interactive-Safe Test Run

**Branch**: `feat/1785-testinteractive` | **Date**: 2026-09-16 | **Spec**: `specs/1785-testinteractive/spec.md`

**Input**: Feature specification from `specs/1785-testinteractive/spec.md`

## Summary

Add an input-provider seam to the interactive-safe test runner. The seam replaces `InputUtils.safe_input` only during one option run. It restores the EOF-safe prompt after the handler returns. Add a second safety check that refuses any candidate outside `interactive_safe`.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard library, pytest, existing MistHelper modules.

**Storage**: Existing telemetry JSONL under `data/`.

**Testing**: pytest unit tests, local lint, format, type, and guard checks.

**Target Platform**: Windows development shell and GitHub Actions.

**Project Type**: Python CLI.

**Performance Goals**: Add no network calls before the existing site resolution step.

**Constraints**: Do not weaken EOF handling. Do not run destructive, websocket, continuous-loop, or resource-intensive operations.

**Scale/Scope**: Current registry contains 268 reachable menu entries and 92 `interactive_safe` entries.

## Constitution Check

- Five-Item Rule: The edited runner module is an existing file. New methods stay small.
- Class-Based Architecture: New behavior lives in `UnattendedInteractiveInputProvider` and `InteractiveTestRunner`.
- Safety-First: The normal `InputUtils.safe_input` implementation is restored after each option.
- Observability: New actions have before and after logging.
- Testing: Unit tests cover prompt generation, destructive refusal, zero-count failure, and skip reasons.

## Project Structure

### Documentation

```text
specs/1785-testinteractive/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src/troubleshooting/interactive_test_runner.py
MistHelper.py
tests/unit/troubleshooting/test_interactive_test_runner.py
changelog.d/issue-1785-testinteractive.md
```

**Structure Decision**: Use the existing interactive test runner module. Do not add a new package for this narrow change.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing module exceeds small-file ideals | The runner already owns this workflow | Moving it would create an unrelated refactor |
