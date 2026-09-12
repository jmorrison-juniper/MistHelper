# Data Model: Automated Testing Infrastructure

**Feature**: 012-automated-testing | **Date**: 2026-03-11

## Entities

### TestEvent

A single structured record of a test action during `--test` or `--testinteractive` runs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | yes | One of: `test_start`, `test_pass`, `test_fail`, `test_skip`, `test_summary` |
| `timestamp` | string (ISO 8601) | yes | UTC timestamp, e.g. `2026-03-11T14:30:00Z` |
| `menu_option` | string | yes | Menu option number, e.g. `"11"` |
| `status` | string | conditional | One of: `pass`, `fail`, `skip`. Required for `test_pass`, `test_fail`, `test_skip`. Present with aggregate value for `test_summary`. Absent for `test_start`. |
| `duration_seconds` | float | yes | Wall-clock duration of this operation |
| `operation_name` | string | no | Human-readable operation description |
| `error_type` | string | no | Exception class name (present when `status: "fail"`) |
| `error_message` | string | no | First 500 chars of exception message (present when `status: "fail"`) |
| `skip_reason` | string | no | Why this operation was skipped (present when `status: "skip"`) |
| `skip_category` | string | no | Category: `destructive`, `interactive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop` |
| `test_mode` | string | no | `systematic` or `interactive` |
| `total_operations` | int | no | Total ops count (present in `test_summary`) |
| `pass_count` | int | no | Number passed (present in `test_summary`) |
| `fail_count` | int | no | Number failed (present in `test_summary`) |
| `skip_count` | int | no | Number skipped (present in `test_summary`) |
| `total_elapsed_seconds` | float | no | Full test run duration (present in `test_summary`) |

**Validation Rules**:
- `event_type` must be one of the 5 defined values
- `timestamp` must parse as valid ISO 8601
- `menu_option` must be a string representation of an integer (1-120)
- `duration_seconds` must be non-negative
- `error_message` must be truncated to 500 characters maximum

### ProgressEvent

A checkpoint record emitted during live operations for AI progress monitoring.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | yes | One of: `progress_start`, `progress_tick`, `progress_complete` |
| `timestamp` | string (ISO 8601) | yes | UTC timestamp |
| `menu_option` | string | yes | Menu option number |
| `operation_name` | string | yes | Human-readable description, e.g. `"List Site Devices"` |
| `total_items` | int | yes | Total items to process |
| `current_item` | string | no | Name/ID of current item (present in `progress_tick`) |
| `items_completed` | int | no | Count completed so far (present in `progress_tick`, `progress_complete`) |
| `items_remaining` | int | no | Count remaining (present in `progress_tick`) |
| `items_processed` | int | no | Final count processed (present in `progress_complete`) |
| `was_stopped` | bool | no | True if stopped via stop signal (present in `progress_complete`) |
| `duration_seconds` | float | no | Total operation duration (present in `progress_complete`) |

**Validation Rules**:
- `event_type` must be one of the 3 defined values
- `total_items` must be non-negative
- `items_completed` must not exceed `total_items`
- `was_stopped` defaults to `false` if absent

### OperationEntry

A registry entry classifying a menu operation for test execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `option` | string | yes | Menu option number, e.g. `"11"` |
| `category` | string | yes | One of: `safe`, `interactive_safe`, `destructive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop` |
| `skip_reason` | string | no | Human-readable reason for skipping (present when category is not `safe` or `interactive_safe`) |
| `requires_site_id` | bool | yes | Whether this operation requires a site_id parameter |
| `requires_device_id` | bool | yes | Whether this operation requires a device_id parameter |

**Validation Rules**:
- `category` must be one of the 7 defined values
- `option` must be unique within the registry
- Operations with `category: "safe"` or `category: "interactive_safe"` must NOT have a `skip_reason`

### TestComparison

A derived analysis comparing two sets of TestEvents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_a_file` | string | yes | Path to first test event file |
| `run_b_file` | string | yes | Path to second test event file |
| `run_a_timestamp` | string (ISO 8601) | yes | Timestamp of first run |
| `run_b_timestamp` | string (ISO 8601) | yes | Timestamp of second run |
| `new_failures` | list[ComparisonItem] | yes | Operations that passed in A but fail in B |
| `resolved_failures` | list[ComparisonItem] | yes | Operations that failed in A but pass in B |
| `timing_regressions` | list[ComparisonItem] | yes | Operations >2x slower in B vs A |
| `status_changes` | list[ComparisonItem] | yes | Any other status transitions |

### ComparisonItem

A single entry in a TestComparison list.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `menu_option` | string | yes | Menu option number |
| `operation_name` | string | no | Human-readable name |
| `run_a_status` | string | yes | Status in run A |
| `run_b_status` | string | yes | Status in run B |
| `run_a_duration` | float | no | Duration in run A (seconds) |
| `run_b_duration` | float | no | Duration in run B (seconds) |
| `ratio` | float | no | Duration ratio B/A (present for timing regressions) |
| `error_message` | string | no | Error details (present for failures) |

## Relationships

```text
TestEvent ──> written to ──> data/test_events_YYYYMMDD_HHMMSS.jsonl
ProgressEvent ──> written to ──> data/test_events.jsonl
OperationEntry ──> used by ──> run_systematic_test() / run_interactive_test() (determines run/skip/skip-with-event)
TestComparison ──> reads ──> two TestEvent files
ComparisonItem ──> references ──> TestEvent pairs by menu_option
```

## State Transitions

### TestEvent Lifecycle

```text
test_start ──> test_pass (operation succeeded)
test_start ──> test_fail (operation threw exception)
test_skip (operation not executed — emitted without test_start)
test_summary (emitted once at end of run)
```

### ProgressEvent Lifecycle

```text
progress_start ──> progress_tick (repeated N times) ──> progress_complete
progress_start ──> progress_complete (if stopped by stop signal with 0 ticks)
```

## Storage

- **Test events**: `data/test_events_YYYYMMDD_HHMMSS.jsonl` (timestamped per run)
- **Progress events**: `data/test_events.jsonl` (rolling, current run)
- **Retention**: Configurable limit (default 10 files). Oldest timestamped files deleted when limit exceeded.
- **Format**: NDJSON — one `json.dumps()` line per event, newline-terminated
- **No database storage**: Telemetry events are NOT written to `mist_data.db` — they are operational artifacts, not API data
