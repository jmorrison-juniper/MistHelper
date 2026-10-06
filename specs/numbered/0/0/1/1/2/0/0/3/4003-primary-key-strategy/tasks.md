# SLE trend primary key tasks

## Ordered tasks

1. **Confirm the implementation base**

   Confirm that pull request #4023 merged. Confirm exclusive ownership of each
   shared file.

2. **Measure the current table shapes**

   Record the old key, columns, indexes, and row count for each affected table.

3. **Create the backup service**

   Copy the database to the required timestamped path. Validate the copy before
   schema work starts.

4. **Create the migration detector**

   Detect an absent table, an old auto-increment table, and an already migrated
   table.

5. **Create the table rebuild**

   Build the replacement table and copy valid rows in one transaction.

6. **Create deterministic deduplication**

   Group by the complete composite key. Keep the newest update timestamp, then
   the highest old internal identifier.

7. **Create invalid-row refusal**

   Stop when any legacy row lacks a key value. Preserve the original table.

8. **Add request identifiers to trend rows**

   Add the request identifiers before the writer receives the normalized
   response object.

9. **Correct the two strategy entries**

   Apply the exact composite keys from `spec.md`.

10. **Replace the wrong strategy assertion**

    Change the assertion at lines 317 through 333. Do not change the line 592
    test.

11. **Add migration unit tests**

    Test detection, backup, rebuild, deduplication, validation, rollback, and
    operator messages.

12. **Add the migration integration test**

    Write different windows and a repeated window. Confirm accumulation and
    update behavior.

13. **Run focused validation**

    Run the test boundary from `spec.md`. Run each applicable repository gate.

14. **Publish the migration evidence**

    Record the measured counts, backup behavior, rollback proof, and exact gate
    results in the pull request.

15. **Release the hot file**

    Merge #4003 before #4012 starts its strategy-file change.

## Dependencies

* Task 2 depends on Task 1.
* Task 3 depends on Task 2.
* Task 4 depends on Task 2.
* Task 5 depends on Tasks 3 and 4.
* Task 6 depends on Task 5.
* Task 7 depends on Task 5.
* Task 8 depends on Task 1.
* Task 9 depends on Tasks 5 and 8.
* Task 10 depends on Task 9.
* Tasks 11 and 12 depend on Tasks 6 through 10.
* Task 13 depends on Tasks 11 and 12.
* Task 14 depends on Task 13.
* Task 15 depends on Task 14.

## Completion conditions

* Both endpoints use the specified composite keys.
* A new window preserves each prior window.
* A repeated window updates one row.
* The first affected write migrates an old table once.
* A verified backup exists before the table rebuild.
* An invalid row stops the migration without a table change.
* A failed rebuild leaves the original table active.
* Operator messages include the table, backup, counts, and status.
* The wrong current assertion no longer passes.
* The line 592 test remains unchanged by #4003.
* Issue #4012 starts only after the #4003 implementation merges.

