# Data Model: SQLite Device Event Identity

## Legacy Table

- **Names**: `OrgDeviceEvents` (menu 21 and menu 153, through the filename rule in R20) and `OrgDeviceEvents_52w` (menu 97, R21).
- **Natural key**: None is stored. The primary key holds the key columns that the first batch contained (R8). For the documented event shape, the primary key is `timestamp`.
- **Columns**: Each source field as TEXT. Two audit columns, `misthelper_created_time` and `misthelper_updated_time`.
- **Who writes it**: The writer before this change (R10 and R11).

## Identity Table

- **Names**: The same names as the legacy tables. The migration renames the legacy table first.
- **Primary key**: `(org_id, misthelper_row_fingerprint)`.
- **Columns**: Each source field as TEXT, with a sanitized name. `org_id` is TEXT NOT NULL. It stores an empty string when the event has no `org_id`. `misthelper_row_fingerprint` is TEXT NOT NULL and holds 64 hexadecimal characters. Two audit columns.
- **Indexes**: One index for each field in the catalog index list that the table holds. The catalog list for `searchOrgDeviceEvents` is `device_id`, `timestamp`, `type`, `org_id`, and `site_id` (R5, line 268). Index names follow the existing `idx_<table>_<column>` rule (R80).
- **Who writes it**: The identity store in `src/foundation/persistence/device_events/store.py`.

## Device Event Row

- **Source**: One event from the Mist search response. `DataExporter.export_with_processing` flattens and escapes the rows before the write (R19, lines 504 and 505).
- **Stored value form**: The writer converts each value to a string. A None value and a missing field both become an empty string (R78).
- **Equality**: Two rows are equal when every non-empty stored value is equal. Empty values do not count (D-1).

## Row Fingerprint

- **Input**: Pairs of `(column name, stored string)`. The pairs exclude empty values, the audit columns, and the fingerprint column.
- **Order**: Sorted by column name in ASCII order.
- **Encoding**: A JSON array of two-item arrays, written with `ensure_ascii` set to True and with separators `,` and `:`. The text is then encoded as ASCII bytes.
- **Digest**: SHA-256 hexadecimal digest. The shape follows `SleTrendIdentity.key` (R7, lines 68 to 74).
- **Stability**: The same stored values give the same digest on every run and on every supported Python version (FR-023).
- Caution: A change to the input form, the order, or the encoding changes every fingerprint. Such a change needs its own migration.

## Backup File

- **Location**: The same folder as the database file.
- **Name**: The database file name, a dot, a UTC timestamp, and the suffix `.bak`.
- **Creation**: A byte copy made with `shutil.copy2` before any change.
- **Check**: `PRAGMA integrity_check` returns `ok` on the copy. The copy size equals the source size. The row count of each migrated table equals the source count.

## Dry Run Report

- **Fields**: Table name, key state (`identity`, `legacy`, or `absent`), primary key columns, row count, and distinct identity count.
- **Access**: The database opens with a read-only URI, built with `Path.as_uri()` and the mode `ro`.
- **Effect**: The report changes no file.

## Migration Run

- **Inputs**: Database path, one or more table names, and the `--apply` flag.
- **Stages**: Inspect the database. Confirm with the word `MIGRATE`. Make the backup. Open one `BEGIN IMMEDIATE` transaction. Rename the legacy table and create the identity table. Copy the rows and run the count checks. Commit or discard the transaction.
- **Exit codes**: 0 for a dry run, a migrated table, or an identity table. 1 for a refusal or a failure, with no change. 2 for a usage error.

## State Transitions

| From | Event | To | Notes |
| - | - | - | - |
| absent | Writer runs with the endpoint | identity | The writer creates the table with the identity key (FR-001). |
| identity | Writer runs with the endpoint | identity | Rows are added or ignored. Rerun adds no row (FR-006). |
| legacy | Writer runs with the endpoint | legacy | The writer refuses and names the migration command (FR-008). No row changes. |
| legacy | Migration applies | identity | The legacy table is renamed to `<table>_legacy_<UTC stamp>` and kept (FR-015). |
| legacy | Migration fails before commit | legacy | The transaction is discarded. The legacy table is unchanged (FR-013). |
| identity | Migration runs | identity | The report says already migrated. No change (FR-014). |
