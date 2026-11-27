# Contract: Evidence Register

## Location

The register is the table under the heading "Comparison Register" in the parity record file `design/research.md`. The audit reads only this table.

## Header

The refreshed register uses this header row exactly.

`| Row | Current state on main | Evidence | Acceptance check | Disposition | Owner decision | Parity task | Gate |`

The baseline table in this record uses the headers "Remote checks" and "Required check." The parity T005 refresh replaces those headers.

## Columns

| Column | Allowed value | Rule |
| --- | --- | --- |
| Row | `C01` to `C40` | One row for each ID, in order, with no gap. |
| Current state on main | Text that starts with Missing, Partial, Implemented, Unsupported, or Requires approval | Use the state words of the parity record. Cite the remote checks in the Evidence column. |
| Evidence | Path, blob SHA, and line for each item | Each item uses the form `path` blob `sha` line `n`. Separate items with a comma. |
| Acceptance check | A test path with a function name, or an explicit acceptance statement | Required for an accepted row. |
| Disposition | `accepted`, `unsupported-approved`, or `open` | Exactly one value for each row. |
| Owner decision | `none` or an OD number | Required for an unsupported-approved row. Use `none` for other rows. |
| Parity task | Parity task IDs, such as T007 and T008 | Required for an open row. |
| Gate | Gate IDs G1, G2, G3, G4, G5, GV, or `none` | Lists each gate that blocks the row. |

## Example

The example uses a synthetic row ID. Fixtures in the audit tests use the ID `X01` only.

| Row | Current state on main | Evidence | Acceptance check | Disposition | Owner decision | Parity task | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X01 | Example state only | `path/example.py` blob `0000000000000000000000000000000000000000` line 1 | `tests/example/test_example.py::test_example` | accepted | none | none | none |

## Validation Rules

1. The header row matches the contract exactly.
2. Each row ID from C01 to C40 appears exactly once.
3. Each disposition uses one allowed value.
4. An accepted row has at least one evidence item and an acceptance check.
5. An unsupported-approved row has an owner decision ID that exists in the gate decision record, and that record has limit text.
6. An open row has at least one parity task ID and at least one gate ID or `none`.
7. A blob SHA that differs from the working tree file makes the audit fail.
8. A secret-like value in any cell makes the audit fail.
