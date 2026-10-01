# Data Model: Mist Edge Lifecycle Operation

## `LifecycleRequest`

Represents one operator-selected step.

| Field | Type | Notes |
| - | - | - |
| `step` | `str` | One of `claim`, `assign`, `unassign`, `bounce`, or `upgrade`. |
| `confirmation_word` | `str` | One of `CLAIM`, `ASSIGN`, `UNASSIGN`, `BOUNCE`, or `UPGRADE`. |
| `body` | `dict[str, object]` | The OpenAPI request body. |
| `target_summary` | `str` | Redacted text for console and CSV evidence. |
| `dry_run` | `bool` | True when the system must not send a request. |

## `LifecycleLogRow`

Represents one row in `data/MxEdgeLifecycleLog.csv`.

| Field | Type | Notes |
| - | - | - |
| `timestamp_utc` | `str` | UTC ISO 8601 time with seconds. |
| `org_id` | `str` | Organization identifier. |
| `step` | `str` | Lifecycle step name. |
| `target` | `str` | Device, site, port, or upgrade target. Claim code is never stored. |
| `dry_run` | `bool` | True when no request was sent. |
| `status` | `str` | `sent`, `dry_run`, `cancelled`, `timeout`, or `error`. |
| `detail` | `str` | Short redacted result detail. |

## `UpgradePollResult`

Represents the final status of upgrade polling.

| Field | Type | Notes |
| - | - | - |
| `upgrade_id` | `str` | Upgrade identifier selected for polling. |
| `status` | `str` | Latest status string from Mist. |
| `terminal` | `bool` | True when the status is complete, failed, canceled, cancelled, success, or error. |
| `timed_out` | `bool` | True when polling reached the timeout. |
| `poll_count` | `int` | Number of status reads. |

## Validation Rules

- `mxedge_ids` must be a non-empty list of strings.
- `site_id` must be present for assignment only.
- `ports` must be a non-empty list of strings for bounce.
- The claim code can appear only in the API request body.
- Dry-run rows use `dry_run` status and do not call the client.
