# Implementation Plan: Required Device Identity for Inventory Failure Records

**Branch**: `jmorrison-juniper-audit-defaults-missing-inputs` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `/specs/numbered/0/0/0/4/2/0/0/3/2753-csv-device-id-validation/spec.md`.

## Summary

Require a valid device ID before the inventory comparator records either parse-failure row. Add a bounded scan and guard for the two defaults that hide a missing device ID.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Python standard library and pytest.

**Storage**: No schema change.

**Testing**: Focused pytest, repository Ruff, Black, mypy, Bandit, and test-quality ratchets.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Internal inventory comparison library.

**Performance Goals**: The scan reads one source file and adds no runtime work to normal comparisons.

**Constraints**: Do not call Mist, write production data, or change the shared test-quality baseline. Preserve valid failure-row output.

**Scale/Scope**: One source module, two failure-record paths, one scanner, one guard, and direct tests.

## Constitution Check

- **Five-Item Rule**: The new managed feature directory has four direct children at most. The `design/` directory holds the checklist, research, data model, and quickstart.
- **Existing structure**: The route parent already has two feature directories. The `changelog.d/` fragment is a required unique process record.
- **Existing debt**: The process folders hold many independent records. This slice does not add a shared index or restructure them. Track any process-folder migration in a separate issue if the guard or workflow changes.
- **Touched violations**: The two `device.get("id", "")` defaults in `csv_comparator.py` can write an unidentified failure row.
- **Class-based design**: Keep validation in the existing comparator class and scanning in a named scanner class.
- **Safety**: No cloud request or production-state change is required.
- **Logging**: Log the missing identity before raising a visible error. Do not log secrets.
- **Deployment pipeline**: Run the focused tests and each applicable local gate before publication.
- **Mist transport**: This feature uses no Mist Cloud transport.

## Project Structure

### Documentation

```text
specs/numbered/0/0/0/4/2/0/0/3/2753-csv-device-id-validation/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── checklists/requirements.md
    ├── data-model.md
    ├── quickstart.md
    └── research.md
```

### Source Code

```text
scripts/scan_2753.py
src/mist/resources/inventory/csv_comparator.py
tests/guardrails/test_issue_2753_csv_device_id_scan.py
tests/unit/test_csv_comparator.py
changelog.d/issue-2753-csv-device-id-validation.md
```

**Structure Decision**: Keep comparison behavior in its existing module. Put the scan command in `scripts/` and its guard in `tests/guardrails/`.

## Research Summary

- The issue manifest identifies two device ID defaults in failure-row creation.
- Mist device IDs are required identity values, not optional display labels.
- No external contract or live Mist test is needed for this internal validation boundary.

## Design Summary

- Read the device ID without an empty default.
- Reject absent, blank, or non-string values before appending a failure row.
- Keep valid device IDs unchanged.
- Scan only the selected source module and fail on unreadable or invalid source.
- Require the guard to report the examined file count and remaining candidate count.

## Complexity Tracking

No new module-level production name or hierarchy violation is planned. The two existing failure-record methods are touched because they own the defective defaults.
