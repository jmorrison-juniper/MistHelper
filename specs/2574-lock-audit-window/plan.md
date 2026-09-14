# Plan: Lock audit read cost

## Objective
Measured: Reduce peak traced Python memory for `read_audit_rows()` on growing audit trails.

## Method
1. Read the writer code and match its JSONL row shape.
2. Build local fixtures with 1,000, 10,000, and 50,000 rows.
3. Measure the baseline before code changes.
4. Profile the 10,000 row case with `cProfile`.
5. Remove the measured extra work without changing public behavior.
6. Measure the candidate with the same harness.
7. Run focused tests and quality gates.

## Risk
Measured: Expiry inference depends on old rows. A windowed read can return a wrong inferred row. The fix must process the whole trail in order and keep only the newest inferred rows.

## Rollback
Rejected: No rollback was needed. The retained change passed the memory objective.
