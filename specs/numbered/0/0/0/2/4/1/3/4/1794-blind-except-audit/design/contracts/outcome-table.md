# Contract: outcome table in each slice pull request body

Each slice pull request body holds one outcome table. The table has one row for each audited site (FR-018). A reviewer uses this table to check each outcome in one sitting (User Story 4).

## Columns

| Column | Rule |
| - | - |
| Site | Repository path, enclosing symbol, and ordinal. This value is the natural key. |
| Line at main | Line number of the handler at the slice base commit. |
| Outcome | One of `delete`, `narrow`, or `keep`. |
| Exception types after | Operational exception types only, for `narrow`. Empty for `delete`. Never `TypeError`, `AttributeError`, `NameError`, or `AssertionError` (FR-010). |
| Log call | `error` with the exception type and the operation name for each continued handler. `none` for `delete`. |
| Caller evidence | Caller file and line for `delete` and `narrow` (FR-009). |
| Test name | Name of the test that covers the site (FR-021). |
| Reason | Required for `keep`. States why the breadth is correct (FR-012). |

## Rules

- Each audited site has one row. A blank cell fails the review (SC-003).
- The table holds at most 40 rows (FR-017).
- The implementer tests the outcomes in this order: `delete`, then `narrow`, then `keep` (FR-008).
- A `keep` row has a reason in the table and a reason comment in the code (FR-012, FR-014).
- A review step by a second person checks each `keep` reason. The agent cannot run this step (SC-004).
