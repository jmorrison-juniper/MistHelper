# Handler Outcome Contract

## Input

A portal handler may return the existing `OperationOutcome`. A handler may still return `None` or another legacy value.

## Result Mapping

| Handler result | Portal run state | Completion text |
|---|---|---|
| `no_output` | `completed` | The portal prefixes the supplied reason with its standard no-file message. |
| `completed` | `completed` | The portal uses the supplied message. |
| `failed` | `failed` | The portal uses the supplied message as the error. |
| `missing_input` | `failed` | The portal uses the supplied message as the error. |
| No `OperationOutcome` | Existing classification | The portal keeps the existing log and file checks. |

The portal keeps discovered output filenames for every outcome. The portal does not use log wording to override a typed outcome.

## Compatibility

The response shape and event names remain unchanged. Unmigrated handlers retain the current marker behavior.
