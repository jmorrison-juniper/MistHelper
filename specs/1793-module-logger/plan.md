# Implementation Plan: Module logger sweep for firmware manager

**Branch**: `refactor/1793-module-logger` | **Date**: 2026-09-16 |
**Spec**: `specs/1793-module-logger/spec.md`

**Input**: Feature specification from
`specs/1793-module-logger/spec.md`

## Summary

Replace the root logger calls in `src/firmware/firmware_manager.py` with a
module logger. Keep the sweep reviewable by changing one file and 236 call
sites.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Standard library `logging`, existing MistHelper code

**Storage**: Not applicable

**Testing**: py_compile, ruff, black, mypy, pylint, radon, guard proof audit,
symbol diff, and pytest shards

**Target Platform**: Windows and Linux

**Project Type**: Python CLI and web service repository

**Performance Goals**: No runtime behavior change

**Constraints**: Preserve message text, log level, `%s` formatting, and
exception handlers

**Scale/Scope**: 236 call sites in one file out of 5793 measured root logger
calls

## Constitution Check

- Five-Item Rule: No new function, class, or package is added.
- Class-based architecture: No wrapper is added.
- Safety-first: No input handling changes are made.
- Full deployment pipeline: Local gates and test shards must run before the
  pull request.
- Observability: The change improves logger source attribution.
- Automated sweep safety: The pull request reports counts, string patch search,
  symbol diff, and shard results.

## Project Structure

### Documentation for this feature

```text
specs/1793-module-logger/
├── plan.md
├── spec.md
└── tasks.md
```

### Source Code

```text
src/
└── firmware/
    └── firmware_manager.py

changelog.d/
└── issue-1793-module-logger.md
```

**Structure Decision**: The change edits one existing firmware module and one
release note fragment. It does not add a new package.

## Files Changed

- `src/firmware/firmware_manager.py`
- `specs/1793-module-logger/spec.md`
- `specs/1793-module-logger/plan.md`
- `specs/1793-module-logger/tasks.md`
- `changelog.d/issue-1793-module-logger.md`

## Complexity Tracking

No constitution violation is introduced.
