# Contract: Ratchet guard output

**Scope**: `tests/guardrails/test_nested_package_structure.py` and `tests/guardrails/nested_package_baseline.json`.

## Printed message

The guard test prints one message in this format.

`nested_package_scope: <N> directories examined, <V> violations, <E> total excess`

Expected value before the change: N = 190, V = 33, E = 236.

Expected value after the change: N = 206, V = 30, E = 190.

## Baseline file rules

- The file holds one JSON object.
- The object holds `version` with the value 1, `source_root` with the value `src`, and `max_children` with the value 5.
- The object holds `violations`, a nonempty list.
- Each entry holds `path`, `child_count`, and `remediation_issue`.
- Each `path` starts with `src/`, uses forward slashes, and has no `..` segment.
- Each `child_count` is greater than 5. Each `remediation_issue` is a positive integer.
- The entries are sorted by `path`, and no `path` repeats.

## Failure messages

The guard assertion names one of these conditions.

- `Unknown violations`: a directory with more than five children has no baseline entry.
- `Stale baseline entries`: a baseline entry has no matching violation.
- `Increased child count`: a baseline entry has a larger child count than measured.
- `Stale baseline entry reached five children`: a baseline entry names a directory with five children or fewer.
- `Total excess increased`: the measured total excess is larger than the baseline total excess.

## Verification

Run `design/quickstart.md`, steps 1 and 2.
