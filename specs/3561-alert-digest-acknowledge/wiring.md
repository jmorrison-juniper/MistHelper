# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 280 | Export the alert digest handover report | src.reports.alert_digest.operation | AlertDigestOperation.run_digest | safe |  | False | False |
| 281 | Acknowledge recent unacknowledged alarms | src.reports.alert_digest.operation | AlertDigestOperation.run_acknowledge | destructive | Requires typed `ACK <count>` confirmation and supports `--dry-run`. | True | False |

## OperationRegistry comment

`# WHY:` Menu 280 reads recent alarms and writes a shift handover digest without changing Mist cloud state. Menu 281 changes alarm acknowledgement state, so it stays in the destructive category, requires the operator to type `ACK <count>`, and supports `--dry-run` for a no-change preview.

## Primary key strategies

```python
"alertDigest": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["category", "alarm_type", "site", "first_seen", "last_seen"],
    "indexes": ["category", "severity", "alarm_type", "site", "acknowledged_state"],
},
"alertAcknowledgeLog": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["alarm_id", "outcome", "run_time"],
    "indexes": ["alarm_id", "alarm_type", "site", "outcome", "http_status"],
},
```

## copilot-instructions category table

Add menu `280` to the `safe` category row. Add menu `281` to the `destructive` category row and state that it needs human review because it changes Mist alarm state.

## Import line for MistHelper.py

`from src.reports.alert_digest.operation import AlertDigestOperation  # Menu 280 and 281 (issue #3561) -- alert digest and alarm acknowledgement`

## Deferred integration notes

- Register menu 280 to call `AlertDigestOperation.run_digest`.
- Register menu 281 to call `AlertDigestOperation.run_acknowledge`.
- Keep menu 281 destructive in `src/utils/operation_registry.py`.
- Keep generated menu documentation and menu API map changes in the integration pull request.
