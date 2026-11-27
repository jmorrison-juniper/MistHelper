# Contract: Gate and Owner Decision Records

## Gate Table

The gate table uses this header row exactly.

`| Gate | Scope | Status | Owner | Decision ID | Decision date | Evidence | Blocked work |`

The table holds six rows: G1, G2, G3, G4, G5, and GV.

| Column | Allowed value | Rule |
| --- | --- | --- |
| Gate | G1, G2, G3, G4, G5, or GV | One row for each gate. |
| Status | `open` or `passed` | A gate passes only with a decision ID and a decision date. |
| Owner | An owner role | The role names the person or group that decides. |
| Decision ID | `none` or an OD number | Points to an owner decision record. |
| Decision date | UTC time in ISO 8601 form | Example form: 2026-12-01T09:00:00Z. |
| Evidence | Remote check IDs or paths with lines | Cites the evidence that the owner reviewed. |
| Blocked work | Short text | Names the work that stays blocked while the status is `open`. |

## Owner Decision Record

Each owner decision record has these fields.

| Field | Rule |
| --- | --- |
| Decision ID | The form `OD-` followed by a number. Each ID appears once. |
| Subject | A row ID such as C17, or a gate ID such as G4. |
| Owner role | The role that holds the decision. |
| Approver | The named person who approved the decision. |
| Date | UTC time in ISO 8601 form. |
| Outcome | `approved` or `refused`. |
| Limit text | Required for an approved unsupported disposition. Text that operators see in the converter. |
| Scope | The operation families, rows, or files that the decision covers. |

## Rules

1. Only a named owner writes an owner decision record. The agent writes no outcome.
2. A gate passes only when an approved record exists for its decision ID and its date is present.
3. Gate G5 passes only when the permission and typed-confirmation controls exist with tests. Each cloud write still needs its own operator approval at run time.
4. A refused record keeps the gate open. A refused record never changes the register disposition.
5. A record without a limit text does not support an unsupported-approved disposition.

## Example

The example uses a synthetic decision ID. It does not record a real decision.

| Decision ID | Subject | Owner role | Approver | Date | Outcome | Limit text | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OD-001 | C17 | Product owner | Example approver | 2026-12-01T09:00:00Z | approved | Flow export is display only. The converter does not generate device commands. | Row C17 only |
