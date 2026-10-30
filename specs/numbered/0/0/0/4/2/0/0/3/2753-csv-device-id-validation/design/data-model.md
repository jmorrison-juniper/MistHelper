# Data Model: Inventory Failure Record

## Inventory Failure Record

| Field | Requirement |
| --- | --- |
| `device_id` | Nonblank string supplied by the device record. |
| `device_serial` | Existing serial value used to describe the comparison. |
| `failure_reason` | Existing parse or processing failure description. |
| `timestamp` | Existing UTC timestamp for the record. |

## Validation Rules

- Reject a missing, blank, or non-string `device_id`.
- Do not append a failure record when validation fails.
- Preserve the original `device_id` when it passes validation.
- Keep all other record fields unchanged.
