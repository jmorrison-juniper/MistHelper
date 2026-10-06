# SLE trend primary key strategy specification

**Feature Branch**: `4003-primary-key-strategy`  
**Feature Path**:
`specs/numbered/0/0/1/1/2/0/0/3/4003-primary-key-strategy/`  
**Issue**: #4003  
**Status**: Draft

## Summary

Two SLE trend endpoints use `auto_increment_with_unique`. The SQLite writer
clears each auto-increment table before it inserts a new batch.

The current behavior removes prior trend windows. It does not add duplicate
rows, as the issue body states.

Both endpoints need `composite_pk`. Each key must include the request
identifiers and the response window.

The route uses eight base-5 digits. Issue 4003 converts to `00112003`.
The route is `0/0/1/1/2/0/0/3`.

## Measured evidence

The review used this command for the hot strategy file:

```text
git show origin/main:src/foundation/support/refactors/endpoint_primary_key_strategies.py
```

The review did not open the working copy of the hot file.

The measured `origin/main` commit was
`f1505203d1d5ec845c94cb54f55118d613cf4e49`.

The runtime strategy table contains 568 entries. It contains 316
`auto_increment_with_unique` entries.

Line 3972 defines `getSiteSleClassifierSummaryTrend`. Line 3993 defines
`getSiteSleSummaryTrend`.

Both entries use this strategy:

```text
type: auto_increment_with_unique
primary_key: misthelper_internal_id
unique_constraints: none
```

The SQLite writer uses `INSERT OR REPLACE` for `natural_pk` and
`composite_pk`. It uses `DELETE` followed by `INSERT` for an auto-increment
strategy.

The OpenAPI schemas require `start` and `end` in both successful responses.
The classifier response also requires `metric`.

Pull request #4023 preserves these top-level response objects. The
implementation for #4003 must start after #4023 merges.

## Failure direction

### `getSiteSleSummaryTrend`

The current auto-increment strategy clears prior windows before each export.
The endpoint returns time-series trend data that must accumulate by window.

The defect silently overwrites data that must accumulate.

The correct strategy is `composite_pk`.

The required key is:

```text
site_id, scope, scope_id, metric, start, end
```

### `getSiteSleClassifierSummaryTrend`

The current auto-increment strategy clears prior windows before each export.
The endpoint returns classifier trend data that must accumulate by window.

The defect silently overwrites data that must accumulate.

The correct strategy is `composite_pk`.

The required key is:

```text
site_id, scope, scope_id, metric, classifier, start, end
```

## Row identity

The response supplies `start` and `end`. The exporter supplies the request
identifiers.

Before the write, the exporter must add each missing request identifier to the
normalized response row. The writer must receive every key field as a column.

The implementation must reject a row that lacks any key field. It must not
create a composite key from only the available fields.

The implementation must not derive an identifier from the export file name.
A display label is not a stable data key.

## Existing database migration

### First run after the change

On the first affected export, the writer must inspect the existing table
schema. A table with `misthelper_internal_id` as its key needs migration.

If no affected table exists, the writer must create the keyed table and
continue the export.

If the table already has the required composite key, the writer must skip the
migration and continue the export.

### Rebuild decision

SQLite cannot change an existing primary key with `ALTER TABLE`.
The migration must rebuild each affected table.

The implementation must not add only the new columns. That action leaves the
old auto-increment key and clear-before-insert behavior in place.

### Backup requirement

Before the rebuild, the implementation must copy `data/mist_data.db` to a
timestamped backup in the same directory.

The backup name must include a UTC timestamp and an issue-specific suffix.
The implementation must validate that the backup exists and is readable.

If backup validation fails, the implementation must stop before any schema
change.

### Transaction boundary

After backup validation, the migration must use one SQLite transaction.

The transaction must:

1. Read the source schema and row count.
2. Validate every required key column and value.
3. Create a replacement table with the target composite key.
4. Copy one retained row for each composite key.
5. Validate the copied row count and key uniqueness.
6. Replace the old table with the new table.
7. Create the configured indexes.
8. Commit only after every validation passes.

If a step fails, the transaction must roll back. The original table must
remain active.

### Deduplication

The migration must deduplicate by the complete target composite key.

If two rows have the same key, keep the row with the newest
`misthelper_updated_time`.

If the timestamps match, keep the row with the highest
`misthelper_internal_id`.

The migration must report the source row count, retained row count, and
removed duplicate count.

### Invalid legacy rows

An old row can lack a new request identifier. The migration must not invent
that value.

If any row lacks a required key value, the migration must stop. It must leave
the original table unchanged.

The operator message must include the table name and invalid row count. It
must not print row data.

### Operator messages

Before migration, show the table name and backup path.

During migration, show the source row count and the target key.

After migration, show the retained row count and removed duplicate count.

If migration fails, show that the original table remains active. Also show the
verified backup path.

The log must include the same counts. The log must not include response data.

### Reversibility

Warning: the migration is not automatically reversible. Deduplication removes
rows from the rebuilt table.

The operator must restore the verified backup to recover the exact prior
database.

## Test correction

The current test at
`tests/unit/export/test_endpoint_family_exporter.py:317-333` asserts the wrong
strategy.

The exact assertion is:

```python
assert ENDPOINT_PRIMARY_KEY_STRATEGIES[operation] == {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": list(required),
    "unique_constraints": [],
    "description": "Endpoint family export for " + operation,
}
```

The implementation must change this assertion. A repair that leaves this
assertion green has not repaired the strategy defect.

The full test search found no other test file that locks either strategy.
The same test file contains all other endpoint name references.

The test at line 592 belongs to #3699. The implementation for #4003 must not
change that test.

## Issue ordering

Issues #4003 and #4012 need two implementation pull requests.

Issue #4003 must merge first. It defines and proves the shared migration path
for a primary key change.

Issue #4012 must rebase after #4003. Its worker must measure the Cradlepoint
response and select its strategy independently.

This order gives one pull request exclusive ownership of the hot strategy file.
It also lets #4012 reuse the migration path when its table shape changes.

Pull request #4023 must merge before the #4003 implementation. It owns the
object-response test at line 592 and the response preservation code.

## Scope

### In scope

* The two measured strategy corrections.
* Request identifier enrichment for the two trend rows.
* Migration of existing SQLite tables.
* A verified database backup before the rebuild.
* Composite-key deduplication and validation.
* Operator messages for migration progress and failure.
* Focused unit and integration tests.

### Out of scope

* Source changes in this specification pull request.
* Test changes in this specification pull request.
* The object-response repair in #3699 and pull request #4023.
* The missing Cradlepoint strategy in #4012.
* Any other primary key strategy entry.
* ArangoDB and Redis schema changes.

## User scenarios and tests

### Scenario 1: Preserve prior trend windows

As an operator, I want a new trend export to preserve prior windows.

**Independent test**: Write two different windows and confirm that both rows
remain.

### Scenario 2: Update the same trend window

As an operator, I want a repeated window export to update one row.

**Independent test**: Write the same composite key twice and confirm that one
row holds the newest values.

### Scenario 3: Migrate an existing table

As an operator, I want the first keyed export to migrate the old table safely.

**Independent test**: Create an auto-increment table, run the migration, and
confirm the composite key and retained rows.

### Scenario 4: Stop before an unsafe migration

As an operator, I want migration to stop when a legacy row lacks a key value.

**Independent test**: Add one invalid legacy row and confirm that the original
table remains unchanged.

### Scenario 5: Recover from a migration failure

As an operator, I want a verified backup before a table rebuild.

**Independent test**: Force a failure after replacement table creation. Confirm
the rollback, original table, backup, and error message.

## Functional requirements

* **FR-001**: Both endpoint entries MUST use `composite_pk`.
* **FR-002**: Each primary key MUST match the key in this specification.
* **FR-003**: The exporter MUST add each request identifier before the write.
* **FR-004**: The writer MUST reject a row that lacks any key field.
* **FR-005**: The writer MUST detect the old auto-increment table shape.
* **FR-006**: The migration MUST rebuild the table.
* **FR-007**: The migration MUST create and validate a database backup first.
* **FR-008**: The rebuild MUST use one SQLite transaction.
* **FR-009**: The migration MUST deduplicate by the complete composite key.
* **FR-010**: The migration MUST use the defined row retention rule.
* **FR-011**: A failed migration MUST leave the original table active.
* **FR-012**: Messages MUST show the table, backup, counts, and status.
* **FR-013**: Messages MUST NOT print response data.
* **FR-014**: The implementation MUST change the wrong strategy assertion.
* **FR-015**: The implementation MUST NOT change the line 592 test.
* **FR-016**: The #4003 implementation MUST start after pull request #4023.
* **FR-017**: The #4012 implementation MUST rebase after #4003.
* **FR-018**: This pull request MUST change no source file or test file.

## Acceptance criteria

* The specification names both current entries and both correct strategies.
* The specification states the measured clear-before-insert behavior.
* The specification states that both defects overwrite accumulating data.
* The two complete composite keys are explicit.
* The migration rebuilds each affected table.
* A verified database backup exists before the rebuild.
* The migration stops on a missing key value.
* The transaction rollback preserves the original table after a failure.
* The deduplication rule is deterministic.
* The operator sees progress, counts, success, and failure information.
* The reversibility warning is explicit.
* The wrong current test assertion is quoted.
* The line 592 ownership limit is explicit.
* The #4003 and #4012 pull request order is explicit.
* The specification pull request changes only the four approved records.

## Smallest implementation test boundary

The implementation worker must run focused tests for:

```text
tests/unit/export/test_endpoint_family_exporter.py
tests/unit/refactors/test_sqlite_database_writer.py
tests/unit/db/test_database_schema_utils.py
tests/integration/test_sle_trend_sqlite_migration.py
```

The implementation must also run the compile, lint, format, type, security,
symbol, and test quality gates that apply to the changed files.

