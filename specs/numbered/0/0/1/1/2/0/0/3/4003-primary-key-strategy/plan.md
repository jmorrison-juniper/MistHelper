# SLE trend primary key implementation plan

**Issue**: #4003  
**Route**:
`specs/numbered/0/0/1/1/2/0/0/3/4003-primary-key-strategy/`  
**Dependency rule**: Merge pull request #4023 before implementation starts.

## Batch 0: reserve shared files

Confirm that no open pull request owns the strategy file, the SQLite writer, or
the selected tests.

Files:

* `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
* `src/foundation/support/refactors/sqlite_database_writer.py`
* `src/foundation/persistence/db/database_schema_utils.py`
* `src/operations/exporting/export/endpoint_family_exporter.py`
* Focused test files from this plan.

Dependency: pull request #4023.

## Batch 1: add migration detection and backup

Add a migration subject that detects the old table key and creates a verified
database backup.

The backup must use a UTC timestamp. It must remain beside
`data/mist_data.db`.

The migration must stop before schema work when backup validation fails.

Dependency: Batch 0.

## Batch 2: rebuild the affected table

Create the replacement table with the requested composite key.

Copy valid rows in one transaction. Apply the deterministic deduplication rule.
Validate row counts and key uniqueness before the table replacement.

Roll back every schema change when any validation fails.

Dependency: Batch 1.

## Batch 3: enrich the trend rows

Add the request identifiers to each normalized trend response before
persistence.

Do not derive values from the file name. Reject a row that lacks a response
window or a request identifier.

Dependency: pull request #4023 and Batch 1.

## Batch 4: correct the strategies

Change the two strategy entries to `composite_pk`.

Use this summary trend key:

```text
site_id, scope, scope_id, metric, start, end
```

Use this classifier trend key:

```text
site_id, scope, scope_id, metric, classifier, start, end
```

Keep useful indexes on the request identifiers and window fields.

Dependency: Batches 2 and 3.

## Batch 5: replace the wrong test contract

Change the assertion at
`tests/unit/export/test_endpoint_family_exporter.py:317-333`.

Add tests for identifier enrichment, missing key refusal, and both exact
strategy dictionaries.

Do not change the line 592 test. Pull request #4023 owns that behavior.

Dependency: Batch 4.

## Batch 6: prove migration behavior

Add focused tests for:

* A table with no prior schema.
* A prior auto-increment table.
* Two different windows.
* A repeated window.
* Duplicate legacy keys.
* A missing legacy key value.
* Backup failure.
* A failure during the rebuild transaction.
* A second run after a completed migration.

Each failure test must confirm that the original table remains active.

Dependency: Batches 2 through 5.

## Batch 7: publish the implementation evidence

Run the smallest test boundary and all applicable quality gates.

Record the backup path format, source rows, retained rows, removed rows, and
failure proof in the pull request.

Dependency: Batch 6.

## Issue 4012 sequence

Use a separate implementation pull request for #4012.

Merge #4003 first. Rebase #4012 after the merge. Reuse the reviewed migration
path if the Cradlepoint strategy changes its existing table shape.

Do not combine the response contract review for #4012 with the trend migration.

## Ownership controls

* One implementation pull request owns the hot strategy file.
* The #4003 worker must wait for pull request #4023.
* The #4012 worker must wait for the #4003 implementation.
* No batch may edit a file held by another open pull request.
* The migration tests must use a temporary database.
* No test may use `data/mist_data.db`.

