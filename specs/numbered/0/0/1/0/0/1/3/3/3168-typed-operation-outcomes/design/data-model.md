# Data Model: OperationOutcome

The public model is
`src.foundation.models.operation_outcome.OperationOutcome`.

| Field | Type | Validation |
| - | - | - |
| `state` | Literal string | One of the four states in the handler contract. |
| `message` | String | Required and nonblank. Preserve the supplied text. |
| `detail` | String or `None` | Default `None`. If supplied, require nonblank text. |

The model is frozen and slotted. All fields are immutable values.
The record has no state transitions or external dependencies.

Wrong field types raise `TypeError`. Unsupported states and blank text raise
`ValueError`. Error messages name the field but do not include its supplied value.

Construction does not log a message, write a file, or perform an external action.
The caller remains responsible for logging operation actions and failures.

The model carries no output paths or row counts. A future caller must verify
output evidence separately. It must not infer that evidence from message text.
