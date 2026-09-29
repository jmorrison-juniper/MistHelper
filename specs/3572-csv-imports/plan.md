# Implementation Plan: CSV imports for PSKs, user MACs, and assets

**Branch**: `feat/3572-csv-imports`

**Date**: 2026-09-29

**Spec**: `specs/3572-csv-imports/spec.md`

## Summary

Menu 292 adds a destructive CSV import operation for organization PSKs, organization user MACs, organization assets, site PSKs, and site assets. The feature owns the new package `src/inventory/csv_imports/`, unit tests under `tests/unit/inventory/csv_imports/`, one release note fragment, and a wiring manifest for the integration pull request.

## Technical Context

**Language**: Python 3.13 or newer.

**Dependencies**: Existing standard library modules and the installed `mistapi` package. No new dependency is required.

**Input files**: `data/import_org_psks.csv`, `data/import_org_user_macs.csv`, `data/import_org_assets.csv`, `data/import_site_psks.csv`, and `data/import_site_assets.csv`.

**Output file**: `data/CsvImportLog.csv`.

**Menu registration**: Deferred to `specs/3572-csv-imports/wiring.md`, because the fleet contract forbids direct edits to `MistHelper.py`, `operation_registry.py`, and generated menu references.

## Architecture

1. `model.py` holds dataclasses and pure functions for import type metadata, CSV parsing, column validation, preview masking, confirmation parsing, and result rows.
2. `client.py` wraps the five `mistapi` import file functions and exposes one method that sends the selected import type.
3. `operation.py` resolves the shared Mist session, reads operator input, calls the model and client, supports dry run mode, and writes the result log.
4. Tests target the model and client without network access. Operation tests inject dependencies and use small CSV files inside the test path.

## Safety Rules

- The operation sends no request until the operator types `IMPORT <row_count>`.
- Dry run mode sends no request.
- PSK passphrases are masked in previews and never written to logs.
- The result log records the import type, row count, dry run flag, status, and summary only.
- Site imports require a site identifier before any request can run.

## Verification Plan

Run these commands before each implementation commit that changes code.

```powershell
C:\Users\jmorrison\mh-fleet\3572-csv-imports\.venv\Scripts\python.exe -m py_compile src\inventory\csv_imports\__init__.py src\inventory\csv_imports\model.py src\inventory\csv_imports\client.py src\inventory\csv_imports\operation.py
C:\Users\jmorrison\mh-fleet\3572-csv-imports\.venv\Scripts\python.exe -m ruff check src\inventory\csv_imports tests\unit\inventory\csv_imports
C:\Users\jmorrison\mh-fleet\3572-csv-imports\.venv\Scripts\python.exe -m black --check src\inventory\csv_imports tests\unit\inventory\csv_imports
C:\Users\jmorrison\mh-fleet\3572-csv-imports\.venv\Scripts\python.exe -m mypy src\inventory\csv_imports --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3572-csv-imports\.venv\Scripts\python.exe -m pydocstyle src\inventory\csv_imports
C:\Users\jmorrison\mh-fleet\3572-csv-imports\.venv\Scripts\python.exe -m pytest tests\unit\inventory\csv_imports -q --timeout=120
```

Before the final commit, also run `vulture` and `interrogate` against `src\inventory\csv_imports`.
