# Credential default resolution tasks

## Ordered tasks

1. **Confirm the candidate inventory**

   Record the 64 candidates, 40 files, zero parse failures, and 10
   wrong-identity sites from the current-tree review.

2. **Create the AST credential guard**

   Add the scanner, stable count line, parse-failure handling, zero-input
   failure, and negative fixture proof.

3. **Create the credential baseline**

   Record the current candidate kinds and paths without recording any secret
   value.

4. **Define the typed refusal contract**

   Choose the refusal type, message fields, logging fields, and caller behavior.
   Do not include credential values in any output.

5. **Repair Mist session fallbacks**

   Remove the process-wide and legacy token fallbacks from the four Mist
   request paths. Add missing, conflicting, and valid-token tests.

6. **Repair organization token resolution**

   Reject a global token after organization-scoped providers miss. Preserve
   valid cache and Vault behavior inside the organization boundary.

7. **Repair database configuration**

   Remove direct-construction Arango and Redis credential defaults. Add tests
   for missing credentials and validated standalone configuration.

8. **Repair portal database identity**

   Remove the default Arango username. Add a test that the portal refuses a
   missing username before database client construction.

9. **Review the remaining candidate set**

   Classify the other 54 candidates. Preserve intentional optional defaults and
   repair each required credential path.

10. **Reduce the baseline**

    Remove each repaired finding from the baseline. Reject any new finding.

11. **Run focused validation**

    Run the smallest test boundary in `spec.md`. Do not run the full suite.

12. **Obtain owner decisions**

    Record the decision for typed refusal, token precedence, standalone mode,
    baseline scope, and issue closure.

## Dependencies

* Task 2 depends on Task 1.
* Task 3 depends on Task 2.
* Tasks 4 through 8 depend on Task 3.
* Task 9 depends on Tasks 5 through 8.
* Task 10 depends on Task 9.
* Task 11 depends on Task 10.
* Task 12 must complete before implementation batches merge.

## Completion conditions

* No required credential uses a wider identity as a fallback.
* The guard reports a nonzero scan and zero parse failures.
* The negative fixture fails the guard.
* Each repaired path has a focused test.
* No credential value appears in source, tests, logs, documents, or reports.
