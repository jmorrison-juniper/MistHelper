# Contract: test_skip event for an operator-only prompt

**Writer**: `OperatorPromptSkipRecorder.record` in `src/foundation/support/menu_testing/operator_prompt.py` (new). The recorder calls `emit_test_skip` in `src/mist/intelligence/analytics/telemetry_emitter.py` (RC-22).

## Fields

The payload order comes from the emitter at lines 167 to 175 (RC-22).

| Field | Value for option 247 | Type |
| - | - | - |
| `event_type` | `test_skip` | string |
| `timestamp` | UTC time in ISO 8601 form | string |
| `menu_option` | `247` | string |
| `status` | `skip` | string |
| `operation_name` | The registry title of option 247 (the menu 247 entry, lines 4916 to 4920 in `MistHelper.py`, RC-17) | string |
| `duration_seconds` | `0.0` | number |
| `skip_reason` | The registry skip reason of option 247 (RC-16) | string |
| `skip_category` | `operator_prompt` | string |
| `test_mode` | `interactive-operator-prompt` | string |

## Example

```json
{
  "event_type": "test_skip",
  "timestamp": "2026-11-26T20:06:19.257000+00:00",
  "menu_option": "247",
  "status": "skip",
  "operation_name": "Verify an email change token from the Mist email (verifySelfEmail)",
  "duration_seconds": 0.0,
  "skip_reason": "Requires an email change token from the Mist email",
  "skip_category": "operator_prompt",
  "test_mode": "interactive-operator-prompt"
}
```

## Summary Effect

- The summary event counts this skip in `skip_count` (RC-08 and RC-24).
- The summary `status` follows the rule in RC-23. A run with only skips reports `pass` while its verdict is failure. Analysis item A-3 records this defect.

## Compatibility

Existing categories and test modes keep their values. The new values appear only for an operator-only stop.
