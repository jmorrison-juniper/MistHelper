# Data Model: Explicit Portal Run Outcomes

## OperationOutcome

The existing immutable `OperationOutcome` carries:

| Field | Type | Purpose |
|---|---|---|
| `state` | `completed`, `no_output`, `missing_input`, or `failed` | Names the handler result. |
| `message` | Nonblank string | Gives the operator the result reason. |
| `detail` | Optional nonblank string | Carries additional handler detail. |

The portal stores the returned outcome in the run record until it classifies the run. It does not serialize a new public field.

## Legacy Fallback Count

The executor keeps one integer count. It increments when a handler without an explicit outcome uses a recognized empty-result log marker. A lock protects updates from concurrent runs. Each increment logs the menu number and new count.
