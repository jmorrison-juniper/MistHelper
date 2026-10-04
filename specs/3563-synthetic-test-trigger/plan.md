# Implementation Plan: Synthetic Test Trigger

**Branch**: `feat/3563-synthetic-test-trigger` | **Date**: 2026-09-29 | **Spec**: `specs/3563-synthetic-test-trigger/spec.md`

**Input**: Feature specification from `specs/3563-synthetic-test-trigger/spec.md`

## Summary

Menu `283` starts a Mist synthetic test on demand for a site, one device, or a switch RADIUS check. The implementation adds a new package under `src/mist/intelligence/troubleshooting/synthetic_test_trigger/`, unit tests under `tests/unit/troubleshooting/synthetic_test_trigger/`, and a wiring manifest for the integration pull request.

## Technical Context

**Language/Version**: Python `3.13+`.

**Primary Dependencies**: Existing `mistapi>=0.64.0,<0.65`, `DataExporter`, `PromptUtils`, and `InputUtils`.

**Storage**: Existing data export path writes `SyntheticTestTrigger.csv` under `data/`.

**Testing**: `pytest`, `ruff`, `black`, `mypy`, `pydocstyle`, `vulture`, and `interrogate`.

**Target Platform**: Windows development worktree and the existing MistHelper runtime.

**Project Type**: Interactive CLI menu operation.

**Performance Goals**: Poll until the result arrives or until `SYNTHETIC_TEST_TIMEOUT_SECONDS` expires.

**Constraints**: Do not edit menu wiring files. Record all integration values in `wiring.md`.

**Scale/Scope**: One site, optional one device, and one synthetic test request per run.

## Constitution Check

- Five-Item Rule: The new package uses four module files plus `__init__.py`.
- Class-Based Architecture: Client, model, and operation behavior live in named classes.
- Safety-First: The operation uses the shared EOF-safe input helper and requires `y` before a trigger.
- Observability: The client logs before and after every Mist API call with safe values only.
- Output Backends: The operation writes through `DataExporter.write_with_format_selection`.

## Project Structure

### Documentation (this feature)

```text
specs/3563-synthetic-test-trigger/
├── contracts/
│   └── cli.md
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
├── spec.md
├── tasks.md
└── wiring.md
```

### Source Code (repository root)

```text
src/mist/intelligence/troubleshooting/synthetic_test_trigger/
├── __init__.py
├── client.py
├── models.py
└── operation.py

tests/unit/troubleshooting/synthetic_test_trigger/
├── __init__.py
└── test_synthetic_test_trigger.py
```

**Structure Decision**: The feature uses one nested troubleshooting package, because the root `src/mist/intelligence/troubleshooting` directory already exists and the feature owns only its new child package.

## Complexity Tracking

No constitution violation is required.
