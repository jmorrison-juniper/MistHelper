# Quickstart: SQLite Device Event Identity

## Prerequisites

- Open PowerShell in the repository root. Activate the environment with `.venv\Scripts\Activate.ps1`. The environment uses Python 3.15 (R44).
- Use the test files for reproduction. Do not open `data\mist_data.db` for reproduction. The rules keep production data out of this work.
- Copy the database before any migration test. Store the copy outside `data\`, for example in `test-artifacts\`.

## Scenario 1: Reproduce the defect with the new tests

The reproduction uses an empty temporary database and two events. Both events share one timestamp and differ in `type`.

1. Run the identity test for two events with one timestamp.

   ```powershell
   python -m pytest tests/unit/db/test_device_event_identity.py -k same_timestamp -q
   ```

2. Before the fix, the writer stores one row for the two events. The assertion that expects two rows fails.
3. After the fix, the writer stores two rows. The test passes.

## Scenario 2: Check identity behavior

1. Run the full identity test module.

   ```powershell
   python -m pytest tests/unit/db/test_device_event_identity.py -q
   ```

2. Expected result: 13 tests pass.

## Scenario 3: Check the migration without changes

Run the dry run against a copy of the legacy database.

```powershell
python -m src.foundation.persistence.device_events.legacy_migration --db "test-artifacts\mist_data_copy.db" --table OrgDeviceEvents_52w --table OrgDeviceEvents
```

Expected result: the report lists each table with its key state and counts. The exit code is 0. The file time of the copy does not change.

## Scenario 4: Apply the migration to the copy

1. Run the migration with `--apply`.

   ```powershell
   python -m src.foundation.persistence.device_events.legacy_migration --db "test-artifacts\mist_data_copy.db" --table OrgDeviceEvents_52w --apply
   ```

2. At the prompt, type `MIGRATE` and press Enter. Any other word stops the run with no change.
3. Expected result: a backup file appears in `test-artifacts\`. The identity table holds every distinct row. The legacy table keeps its original name with a UTC suffix.
4. Run the dry run again. The report says the table already uses the identity key.

## Scenario 5: Check menu 21 failure handling

```powershell
python -m pytest tests/unit/export/test_org_alarm_event_exporter.py -k device_events -q
```

Expected result: the new failure test passes. The zero-row test passes.

## Scenario 6: Check existing behavior

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py -q
python -m pytest tests/unit/test_device_events_52w_exporter.py tests/unit/test_device_events_52w_exporter_extended.py -q
python -m pytest tests/unit/db/test_database_schema_utils.py -q
python -m pytest tests/contract/test_arango_declared_indexes.py -q
python -m pytest tests/unit/config/foundation/persistence/storage/db/test_sqlite_database_writer_logging.py -q
```

Expected result: each command exits 0. The three-row test still stores three rows.

## Scenario 7: Run the gates for changed files

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/guardrails -q
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md documentation/operator-guide.md documentation/diagrams/core/database-strategy.md changelog.d/issue-4723-sqlite-device-event-identity.md
```

Expected result: ruff prints `All checks passed`. Black reports no file that needs a change. Mypy prints `Success`. Guardrails pass. Each STE score is 80 or above.
