# Data Model: Nested Source Package Child Counts

## Entities

- **Directory measurement**: One directory under `src/` with tracked Python files. Its counted children are direct Python modules, except `__init__.py`, plus direct child directories with tracked Python files. The natural key is the repository path, for example `src/mist/access/api`.
- **Baseline entry**: One recorded violation in `tests/guardrails/nested_package_baseline.json`. Fields: `path`, `child_count`, and `remediation_issue`. The natural key is the path. Each entry has a count above five.
- **Inventory row**: One violating directory in `tasks.md`. Fields: task ID, owner issue, wave, slice, count, and holds. The natural key is the task ID.
- **Slice**: One bounded change. Fields: slice ID, wave, target directory, moved modules, and expected totals. The natural key is the slice ID, for example `W1-01`.
- **Hold**: One reservation on a path or a scope. Fields: hold ID, scope, reason, and release condition. The natural key is the hold ID, for example `H-3`.

## State Transitions

A directory moves through these states:

1. **Violation**: The directory holds more than five counted children. Its baseline entry records the current count.
2. **Reduced violation**: A slice lowers the count, and the count stays above five. The baseline entry changes to the new count. Total excess decreases.
3. **Resolved**: The count reaches five or fewer. The guard requires the baseline entry to be removed in the same change. A stale entry fails the guard.

A new directory that holds more than five counted children moves to a rejected state. The guard reports it as an unknown violation, and the change fails.

## Invariants

- The sum of `max(0, child_count - 5)` over the baseline entries equals the total excess that the guard computes for the same tree.
- The baseline paths sort in ascending order without duplicates.
- Each baseline entry names a directory that the guard measures as a violation.
