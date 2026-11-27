# Data Model: Admission state and natural keys

The repair adds one in-memory attribute to the hardware CLI workflow. This model describes that attribute, the natural keys that the service supplies, and the transitions that the CLI uses.

## Entities

| Entity | Holder | Key | Values |
| - | - | - | - |
| Admission state | `HardwareCliWorkflow.admission` (branch copy) | None. The value lives in memory for one collection. | `not_started`, `uncertain`, `admitted` |
| Admitted parent | The parent that the start reply names | `session_id`, a natural key from the Mist-side service | A non-empty string |
| Durable output | The artifact directory that the artifact service verifies | `run_id`, the artifact identifier, and `directory`, the verified path | `run_id` is a string. `directory` is a path or none. |

## State Transitions

| From | Event | To | Result status | Caution |
| - | - | - | - | - |
| `not_started` | Selection, confirmation, or a prompt fails | `not_started` | `incomplete` | None |
| `not_started` | The operator interrupts before the start request | `not_started` | `cancelled` | None |
| `not_started` | The start request is sent | `uncertain` | Continues | None |
| `uncertain` | The start reply is a mapping with a non-empty `session_id` | `admitted` | Continues | None |
| `uncertain` | The start reply is invalid | `uncertain` | `incomplete` | Uncertain |
| `uncertain` | The start request raises an operational failure | `uncertain` | `incomplete` | Uncertain |
| `uncertain` | The operator interrupts during the start request | `uncertain` | `cancelled` | Uncertain |
| `admitted` | The batch reaches a terminal status with verified metadata | `admitted` | The batch status | None |
| `admitted` | Polling raises an operational failure | `admitted` | `incomplete` | Admitted |
| `admitted` | The operator interrupts during the wait | `admitted` | The cancel result | Admitted when the cancel result is incomplete |

## Rules

- The CLI sends the start request once for each collection. No transition leaves `uncertain` for a second start request (FR-004).
- The CLI sets `session_id` only after a verified start reply (FR-008).
- The CLI prints a durable directory only after verified completion (FR-005 and the Key Entities section of the spec).
- Each incomplete result in the `uncertain` or `admitted` state prints the matching caution (FR-005).

## Natural Keys

The Mist-side service supplies `session_id` and `run_id`. The repair creates no artificial key. This follows the constitution rule for database keys.
