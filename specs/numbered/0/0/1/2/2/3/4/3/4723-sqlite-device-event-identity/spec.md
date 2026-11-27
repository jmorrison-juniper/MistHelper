# Feature Specification: SQLite Device Event Identity

**Issue**: #4723, "Runtime: SQLite device events overwrite records with the same timestamp"
**Feature Branch**: `fix/4723-sqlite-device-event-identity`
**Record**: `specs\numbered\0\0\1\2\2\3\4\3\4723-sqlite-device-event-identity`
**Created**: 2026-11-26
**Status**: Draft
**Input**: Issue #4723 reproduction on main commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a`. Main head checked on 2026-11-26 is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Clarifications

### Session 2026-11-26

- Q: Which SQLite writes does this fix cover? A: Every SQLite write that uses the endpoint name `searchOrgDeviceEvents`. Menu 97, menu 21, and menu 153 share the defect. (Decision D-2.)
- Q: Do the Redis and ArangoDB keys change? A: No. Issues #4724 and #4725 own those keys. (Decision D-3.)
- Q: Can the documented fields identify an event? A: No. The documented `device_event` schema requires only `org_id`, `timestamp`, and `type`. (Evidence R72 and R73.)
- Q: Can rows that were already lost come back? A: No. The migration keeps the rows that still exist. It does not rebuild lost rows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep each distinct device event (Priority: P1)

An operator runs menu 97, 21, or 153 with SQLite output. Two events share one timestamp and differ in content. The table keeps both rows.

**Why this priority**: The current key drops event records without an error. Every SQLite device event export is affected.

**Independent Test**: Write two events with the same timestamp and a different `type` into an empty table. Both rows exist, and the write returns True.

**Acceptance Scenarios**:

1. **Given** an empty identity table, **When** a batch holds two events with one timestamp and different content, **Then** two rows are stored.
2. **Given** a batch that holds two identical events, **When** the batch writes, **Then** the table holds one row and the log reports one merged row.
3. **Given** a verification failure, **When** the batch writes, **Then** the table is unchanged and the write returns False.

### User Story 2 - Migrate an existing database safely (Priority: P1)

An operator has a legacy table. The operator runs a dry run, reads the report, types `MIGRATE`, and runs the migration. Every surviving row moves to the identity table. The legacy table stays.

**Why this priority**: Existing databases keep the defect until they migrate. The migration must not lose surviving rows.

**Independent Test**: Create a legacy fixture with N distinct rows. The dry run changes nothing. The applied migration keeps N rows, and the backup and the legacy table each hold N rows.

**Acceptance Scenarios**:

1. **Given** a legacy table, **When** the operator runs a dry run, **Then** the report shows the key and counts, and no file changes.
2. **Given** a legacy table, **When** the operator applies the migration without the word `MIGRATE`, **Then** no file changes.
3. **Given** the word `MIGRATE`, **When** the migration applies, **Then** a checked backup exists before any change.
4. **Given** a count mismatch during the copy, **When** the migration applies, **Then** the transaction is discarded and the legacy table is unchanged.

### User Story 3 - Keep events from two organizations (Priority: P2)

Two organizations share one table. Both export an event with the same timestamp and the same content. The table keeps both rows.

**Why this priority**: Organizations share the table name. A collision between them hides one organization's data.

**Independent Test**: Write the same event for `org-a` and `org-b` into one table. Two rows exist.

**Acceptance Scenarios**:

1. **Given** one table, **When** two organizations write identical content, **Then** two rows exist.

### User Story 4 - Refuse writes to a legacy table (Priority: P2)

An operator starts an export before the migration. The writer sees the legacy key and stops.

**Why this priority**: A write to the legacy table overwrites rows. A refusal prevents further loss.

**Independent Test**: Point a device event write at a legacy table. No row changes, and the error names the migration command.

**Acceptance Scenarios**:

1. **Given** a legacy table, **When** menu 97 writes, **Then** no row changes and menu 97 stops with its existing error.
2. **Given** a legacy table, **When** menu 21 writes a non-empty batch, **Then** menu 21 logs an error and prints no completion line.

### User Story 5 - Rerun without duplicates (Priority: P3)

An operator reruns an export for the same window. The table keeps the same rows.

**Why this priority**: Operators rerun exports after a failure. Duplicate rows make reports wrong.

**Independent Test**: Write the same batch twice. The row count after the second write equals the count after the first.

**Acceptance Scenarios**:

1. **Given** stored rows, **When** the same batch writes again, **Then** the row count does not change.

### Edge Cases

- A field is missing in one event and empty in another event. Both produce the same fingerprint, and they merge. The stored data cannot tell them apart.
- A row has no `org_id`. The stored `org_id` is empty, and the row keeps its fingerprint.
- A batch holds more than 500 rows. The verification query runs in chunks of 500 keys.
- An export holds the database lock. The migration stops at `BEGIN IMMEDIATE` and changes no file.
- The backup copy fails or fails its integrity check. The migration stops before any change to the database.
- Free disk space is less than the database size plus the backup size. The migration stops before the backup starts.
- A legacy table has no key columns in its schema. The migration treats the table as legacy and copies its distinct rows.
- Mist adds a field to events. Events that carry the new field get a new fingerprint. Caution: one rerun can add a second row for an older event.
- Two different events have identical stored content. They merge into one row. Caution: the multiplicity of identical events is lost. The log reports each merged row.
- Warning: rows that the legacy key overwrote before this fix stay lost. The migration cannot restore them. Rerun the export to read data that the Mist API still returns.

### Non-Goals

- The Redis key and the ArangoDB key (issues #4724 and #4725).
- The OSPF key (issue #4726).
- CSV resume and checkpoint behavior (issues #4721 and #4722). Merged pull request #4834 added the exporter guard for menu 97.
- Result handling in the shared fetcher for menu 153. A follow-up issue owns that work.
- Composite keys of other endpoints, such as `searchSiteDeviceEvents`.
- Deleting a legacy table or a backup file.
- Changes to the strategy catalog entry or to any Mist API call.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The SQLite writer MUST store each distinct device event as one row for the endpoint `searchOrgDeviceEvents`.
- **FR-002**: Two events that differ in any non-empty stored field MUST both persist.
- **FR-003**: Rows from different organizations MUST NOT replace each other.
- **FR-004**: A batch write MUST return True only when verification finds every distinct submitted row in the table.
- **FR-005**: A failed verification MUST discard the whole batch and leave earlier rows unchanged.
- **FR-006**: Writing an identical batch again MUST NOT add a row.
- **FR-007**: Identical rows in one batch MUST store once, and the log MUST report the merged count.
- **FR-008**: The writer MUST refuse a write into a legacy table, write no row, and name the migration command in the error.
- **FR-009**: The migration MUST default to a dry run. The dry run MUST report the key, the row count, and the distinct count, and it MUST change no file.
- **FR-010**: The migration MUST make a backup and check the backup before any change to the database.
- **FR-011**: The migration MUST require the typed word `MIGRATE` before any change.
- **FR-012**: The migration MUST copy every distinct legacy row into the identity table.
- **FR-013**: The migration MUST run in one transaction. The migration MUST discard that transaction when a count check fails.
- **FR-014**: The migration MUST report an identity table as migrated and MUST change nothing.
- **FR-015**: The migration MUST NOT drop a legacy table and MUST NOT delete a backup file.
- **FR-016**: Menu 21 MUST log an error and print no completion line when a non-empty SQLite write returns False.
- **FR-017**: Menu 97 MUST keep its existing stop behavior when a SQLite batch write returns False.
- **FR-018**: The Redis writer, the ArangoDB writer, and the strategy catalog entry MUST NOT change.
- **FR-019**: Each new action MUST write an info log line before the action and a debug log line after it.
- **FR-020**: New log text MUST use ASCII only. New log text MUST NOT include a credential.
- **FR-021**: The operator guide, the strategy diagram, the instruction file, and the README MUST describe the identity and the migration.
- **FR-022**: The change MUST NOT add a direct child to a folder that already holds more than five children.
- **FR-023**: The fingerprint MUST return the same value for the same stored values on every run and on every supported Python version.

### Mist Cloud Transport Requirements

- The feature makes no new REST request.
- The existing method `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents` keeps its current arguments (evidence R74).
- The feature owns no WebSocket transport. No SDK insufficiency proof is needed.
- Secret redaction does not change. The feature adds no credential field.

### Key Entities

- **Legacy table**: A table written with the old composite key. Its primary key holds only the key columns that the first batch contained. For the documented shape, the key is `timestamp`.
- **Identity table**: A table with the primary key `org_id` and `misthelper_row_fingerprint`.
- **Device event row**: One stored event. It holds the source fields and two audit columns.
- **Row fingerprint**: A SHA-256 hex digest of the non-empty stored values of one row, in a fixed order.
- **Backup file**: A byte copy of the database. The migration writes it before any change. Its name holds a UTC timestamp.
- **Dry run report**: The text output of a migration dry run. It names the table, the key state, the row count, and the distinct count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The unit test for two events with one timestamp finds two rows and a True result.
- **SC-002**: The unit test for two organizations with identical content finds two rows.
- **SC-003**: Writing the same batch twice leaves the row count unchanged.
- **SC-004**: A write into a legacy table adds zero rows, and the legacy row count stays the same.
- **SC-005**: The migration test keeps every distinct legacy row. The backup and the legacy table each keep the original row count.
- **SC-006**: An injected verification failure leaves the row count unchanged and returns False.
- **SC-007**: The existing test for three SQLite rows and the existing test for the composite key builder pass without edits.
- **SC-008**: Each applicable local gate passes. The gate output reports the count of files, rows, or tests that it examined.

## Assumptions

- Live Mist responses can contain `id` or `device_id`. The documented schema does not require them (evidence R72 and R73).
- The Python `sqlite3` module supports `INSERT OR IGNORE`, `ALTER TABLE`, `BEGIN IMMEDIATE`, and `PRAGMA integrity_check`. SQLite documents the conflict behavior (research source S-5).
- Operators stop exports before a migration starts.
- The database path is `data/mist_data.db` (evidence R75).
- This record used no production data. No database was opened or changed.
