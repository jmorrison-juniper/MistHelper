# Data Model: Alert Digest Acknowledge

## AlarmDefinition

Represents one row from `listAlarmDefinitions`.

| Field | Type | Rule |
| - | - | - |
| `key` | `str` | Required. Matches `AlarmRecord.alarm_type`. |
| `group` | `str` | Required. Maps to the digest category. |
| `severity` | `str` | Required. Maps to the portal severity label. |
| `display` | `str` | Optional in code. Used as a friendly alarm type when present. |
| `fields` | `tuple[str, ...]` | Optional in code. Helps future field-specific samples. |

## AlarmRecord

Represents one raw alarm row from `searchOrgAlarms`.

| Field | Type | Rule |
| - | - | - |
| `alarm_id` | `str` | Required for acknowledgement. Blank rows cannot be acknowledged. |
| `alarm_type` | `str` | Required for grouping. Unknown values are still included. |
| `site_id` | `str` | Optional. Blank site uses `unknown`. |
| `site_name` | `str` | Optional. Falls back to `site_id` or `unknown`. |
| `severity` | `str` | Optional. Definition severity wins when present. |
| `category` | `str` | Optional raw value. Definition group wins when present. |
| `count` | `int` | Optional. Defaults to `1` when missing or invalid. |
| `timestamp` | `float | None` | Optional first seen source. |
| `last_seen` | `float | None` | Optional last seen source. |
| `sample` | `str` | Optional device or client sample from known entity fields. |
| `acked` | `bool | None` | Optional acknowledgement state. |
| `acked_time` | `float | None` | Optional acknowledgement time. |

## AlarmGroup

Represents one CSV digest row for one alarm type and one site.

| Field | Type | Rule |
| - | - | - |
| `category` | `str` | From `AlarmDefinition.group`, or `unknown`. |
| `severity` | `str` | From definition or row, normalized to `Critical`, `Warning`, or `Informational` when possible. |
| `alarm_type` | `str` | Raw alarm type key. |
| `site` | `str` | Site name, site ID, or `unknown`. |
| `recurrence` | `int` | Sum of source `count` values for grouped rows. |
| `first_seen` | `str` | Earliest timestamp as UTC ISO text, or blank. |
| `last_seen` | `str` | Latest last seen value as UTC ISO text, or blank. |
| `sample_device_or_client` | `str` | First useful entity value from the group. |
| `acknowledged_state` | `str` | `acknowledged`, `unacknowledged`, `mixed`, or `unknown`. |

## AcknowledgementCandidate

Represents one alarm that menu 281 can acknowledge.

| Field | Type | Rule |
| - | - | - |
| `alarm_id` | `str` | Required. Candidate is invalid without it. |
| `alarm_type` | `str` | Required for display. |
| `site` | `str` | Site name, site ID, or `unknown`. |
| `severity` | `str` | Display severity. |
| `last_seen` | `str` | Display timestamp. |

## AcknowledgementResult

Represents one row in `AlertAcknowledgeLog.csv`.

| Field | Type | Rule |
| - | - | - |
| `alarm_id` | `str` | One row per attempted alarm ID. |
| `alarm_type` | `str` | Candidate type. |
| `site` | `str` | Candidate site. |
| `outcome` | `str` | `acknowledged`, `dry_run`, `cancelled`, or `error`. |
| `http_status` | `int | None` | HTTP status for confirmed sends. |
| `message` | `str` | Operator-readable result text. |
| `run_time` | `str` | UTC ISO timestamp for the run. |

## State Transitions

1. A raw alarm with `acked` false becomes an acknowledgement candidate.
2. A candidate remains unchanged during `--dry-run`.
3. A candidate remains unchanged when confirmation does not match `ACK <count>`.
4. A confirmed candidate receives one bulk acknowledgement request.
5. Each confirmed candidate receives one result row, even if the bulk request fails.
