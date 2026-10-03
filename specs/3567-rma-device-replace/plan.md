# Implementation Plan: RMA Device Replacement

**Branch**: `feat/3567-rma-device-replace` | **Date**: 2026-09-29 | **Spec**: `specs/3567-rma-device-replace/spec.md`

**Input**: Feature specification from `specs/3567-rma-device-replace/spec.md`

## Summary

Menu `287` adds a destructive RMA device replacement operation. The operation reads organization inventory, validates an old device and an unassigned replacement of the same type, backs up the old device configuration, requires the typed word `REPLACE`, calls `replaceOrgDevices`, and writes `DeviceReplaceLog.csv`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, standard-library `csv`, `json`, `logging`, `pathlib`, and `sys`.

**Storage**: Local files under `data/`, specifically `data/rma_backups/` and `data/DeviceReplaceLog.csv`.

**Testing**: `pytest`, `ruff`, `black`, `mypy`, `pydocstyle`, `vulture`, and `interrogate` through the worktree virtual environment.

**Target Platform**: MistHelper command-line and SSH container sessions on Windows-compatible paths.

**Project Type**: Python CLI operation package with a deferred menu registration.

**Performance Goals**: The operation reads inventory with a page size of `1000` and sends at most one replace request.

**Constraints**: The operation is destructive, requires typed `REPLACE`, supports `--dry-run`, logs before and after each Mist API call, and never logs secrets.

**Scale/Scope**: One organization, one old device, and one replacement device per run.

## Constitution Check

- Five-Item Rule: The new package has no more than five direct files, and each test directory has no more than five direct files.
- Class-Based Architecture: The feature uses classes for the client, model, persistence, and operation layers.
- Safety-First: The operation uses the shared safe input helper and typed `REPLACE` confirmation.
- Full Deployment Pipeline: The fleet contract controls commits, push milestones, and the draft pull request.
- Observability and Logging: The client, persistence, and operation log each significant action before and after it.
- Data Backends: This feature writes an operational log and backup files under `data/`, not a report table.

## Project Structure

### Documentation (this feature)

```text
specs/3567-rma-device-replace/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── contracts/
│   └── operation-contract.md
└── tasks.md
```

### Source Code

```text
src/mist/resources/inventory/device_replace/
├── __init__.py
├── client.py
├── models.py
├── operation.py
└── persistence.py

tests/unit/inventory/device_replace/
├── __init__.py
├── test_rma_device_replace_client.py
├── test_rma_device_replace_model.py
└── test_rma_device_replace_operation.py
```

**Structure Decision**: A new nested package keeps the inventory parent from gaining loose operation files. The model stays pure, the client wraps Mist calls, persistence owns files, and the operation owns prompts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
