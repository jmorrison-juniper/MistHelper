# Data Model: RRM optimize or reset plan capture

## Entity: RrmRunSettings

| Field | Type | Validation |
| - | - | - |
| `action` | string | Must be `OPTIMIZE` or `RESET`. |
| `dry_run` | boolean | True sends no Mist change request. |
| `settle_seconds` | integer | Must be greater than or equal to `0`. |
| `bands` | list[string] | Defaults to `["24", "5", "6"]`. |

## Entity: RrmRadioPlanRow

| Field | Type | Validation |
| - | - | - |
| `site_id` | string | Required. |
| `ap` | string | Required when present in the Mist payload. |
| `band` | string | Required for diff comparison. |
| `channel` | string | Optional. Uses `curr_channel` when present. |
| `width` | string | Optional. Uses `curr_bandwidth` when present. |
| `power` | string | Optional. Uses `curr_power` when present. |

## Entity: RrmPlanDiffRow

| Field | Type | Validation |
| - | - | - |
| `site_id` | string | Required. |
| `ap` | string | Required. |
| `band` | string | Required. |
| `change_type` | string | `changed`, `missing_before`, or `missing_after`. |
| `before_channel` | string | Optional. |
| `after_channel` | string | Optional. |
| `before_width` | string | Optional. |
| `after_width` | string | Optional. |
| `before_power` | string | Optional. |
| `after_power` | string | Optional. |

## State Transitions

```text
Prompted -> BeforeCaptured -> Confirmed -> RequestSent -> Settled -> AfterCaptured -> DiffWritten
Prompted -> BeforeCaptured -> DryRunComplete
Prompted -> BeforeCaptured -> Refused
```

## Validation Rules

- The operation must stop before a Mist change request when the before file write fails.
- The operation must stop before a Mist change request when the confirmation word does not match the action.
- The operation must write only changed, missing-before, or missing-after radios to the diff.
