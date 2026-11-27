# Contract: Schema Context Detection and SQLite Write Outcome

This contract describes the internal Python interfaces between the endpoint detector, the SQLite writer, and the exporter dispatch boundary. The change adds no menu, CLI, output column, or Mist API request shape.

## Detector

`DatabaseSchemaUtils.determine_api_function_name_from_context()` in `src/foundation/persistence/db/database_schema_utils.py`.

- Input: none. The method reads the call stack of its caller.
- Output: `str`. The nearest frame name that contains one of `getOrg`, `listOrg`, `searchOrg`, `getSite`, `listSite`, or `searchSite`.
- Unknown output: `unknown` only after the walk completes with no matching frame.
- Errors: An exception from frame access or from the module logger propagates unchanged. The method returns no value after such an error.
- Side effects: One debug line after a match. The `finally` clause removes the local frame reference.

## SQLite writer

`SQLiteDatabaseWriter.write()` in `src/foundation/support/refactors/sqlite_database_writer.py`.

- Output: `bool`. `True` after a verified write. `False` for input validation and for failures that the writer handles itself.
- Detection failure: The detector exception propagates out of `write()`. No directory, connection, or table work starts.
- Named API function: The writer skips the detector when the API function name is not empty.

## Exporter dispatch boundary

`DataExporter._dispatch_format_write(data, filename_or_table, output_format, fieldnames, api_function_name)` in `src/operations/exporting/export/data_exporter.py`.

- Output: `bool`.
- Failure: Catches `Exception`. Logs at error level with the text `Failed to write data to <table> in <format> format: <error>`. Returns `False`.

## Invariants

- Only a completed walk with no matching frame returns `unknown`.
- A failed detection never selects an endpoint strategy or the default strategy.
- Named API function names bypass detection.
- The endpoint strategy table, the key rules, and the table DDL do not change.

## Evidence

- TST-1 covers the logging failure case.
- TST-2 covers the inspection failure case.
- TST-3 covers the exporter boundary case, with zero database connections.
- TST-4 updates the legacy expectation for the inspection failure case.
