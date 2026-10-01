# Quickstart: CSV imports

1. Create one CSV file under `data/` with the name that matches the import type.
2. Use the required column names from `specs/3572-csv-imports/research.md`.
3. Start menu 292 after the integration pull request wires it.
4. Select the import type.
5. Review the first ten rows and the total row count.
6. If this is a test, choose dry run mode.
7. To import, type `IMPORT <row_count>` exactly.
8. Read `data/CsvImportLog.csv` for the sanitized run result.

Warning: This operation creates or updates Mist cloud records. A human must review the destructive menu wiring before merge.
