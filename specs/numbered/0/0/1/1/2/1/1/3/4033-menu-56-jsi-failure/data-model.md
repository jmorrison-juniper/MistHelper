# Data Model: Delay Metrics History

## Delay History Destination

**Path**: `data/delay_metrics.json`

**Format**: UTF-8 JSON Lines

**Rules**:

- The file contains zero or more complete rows.
- Each nonblank line is one valid JSON object.
- The default retained row count is 100.
- A missing file represents empty history.
- A zero-byte file represents empty history.

## Delay History Row

| Field | Type | Rule |
| --- | --- | --- |
| `timestamp` | String | Use an ISO 8601 UTC value. |
| `delay_metrics` | Object | Preserve the current delay calculation payload. |
| `api_cache` | Object | Preserve the current API usage snapshot. |
| `tuning_data` | Object | Preserve the current PID tuning snapshot. |

The repair does not add, remove, or rename a row field.

## Process Lock

**Type**: One module-level `threading.Lock`

**State transitions**:

1. Unlocked
2. Locked before the destination read
3. Locked during row append and retention
4. Locked during temporary-file write
5. Locked during replacement or cleanup
6. Unlocked after the cycle ends

No second writer can read the destination during states 2 through 5.

## Temporary History File

**Location**: The destination directory

**Name**: A unique hidden or prefixed name with a temporary suffix

**Content**: The complete retained JSONL history

**State transitions**:

1. Absent
2. Created
3. Fully written and closed
4. Replaced into the destination
5. Absent after success

On failure, cleanup changes state 2 or 3 to absent.
The prior destination remains unchanged until state 4 succeeds.

## Validation Rules

- Reject no existing valid row.
- Skip blank lines during a read.
- Treat zero bytes as empty history.
- Keep each written row independently valid JSON.
- Replace only after the complete temporary content is closed.
- Remove the temporary file after each failed cycle.
- Keep the prior destination bytes after a failed replacement.
