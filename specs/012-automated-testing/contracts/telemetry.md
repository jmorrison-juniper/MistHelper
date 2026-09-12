# Telemetry Contract: NDJSON Event Format

**Feature**: 012-automated-testing | **Version**: 1.0

## Overview

MistHelper emits structured events to NDJSON files in the `data/` directory. Consumers (AI agents, CI pipelines, comparison utilities) read these files line-by-line. Each line is a self-contained JSON object.

## File Locations

| File Pattern | When Created | Content |
|-------------|-------------|---------|
| `data/test_events_YYYYMMDD_HHMMSS.jsonl` | `--test` or `--testinteractive` run | TestEvents for that run |
| `data/test_events.jsonl` | Any operation (always-on) | ProgressEvents from current session |

## Event Schemas

### test_start

Emitted when a menu operation begins execution during a test run.

```json
{
  "event_type": "test_start",
  "timestamp": "2026-03-11T14:30:00Z",
  "menu_option": "11",
  "operation_name": "List Site Devices",
  "test_mode": "systematic"
}
```

### test_pass

Emitted when a menu operation completes successfully.

```json
{
  "event_type": "test_pass",
  "timestamp": "2026-03-11T14:30:05Z",
  "menu_option": "11",
  "status": "pass",
  "operation_name": "List Site Devices",
  "duration_seconds": 5.23,
  "test_mode": "systematic"
}
```

### test_fail

Emitted when a menu operation raises an exception.

```json
{
  "event_type": "test_fail",
  "timestamp": "2026-03-11T14:30:05Z",
  "menu_option": "11",
  "status": "fail",
  "operation_name": "List Site Devices",
  "duration_seconds": 2.10,
  "error_type": "mistapi.exceptions.MistApiError",
  "error_message": "401 Unauthorized: Invalid API token (truncated at 500 chars)",
  "test_mode": "systematic"
}
```

### test_skip

Emitted for operations excluded from automated execution.

```json
{
  "event_type": "test_skip",
  "timestamp": "2026-03-11T14:30:05Z",
  "menu_option": "90",
  "status": "skip",
  "operation_name": "AP Firmware Upgrade",
  "duration_seconds": 0.0,
  "skip_reason": "Destructive operation - modifies device firmware",
  "skip_category": "destructive",
  "test_mode": "systematic"
}
```

### test_summary

Emitted once at the end of a test run.

```json
{
  "event_type": "test_summary",
  "timestamp": "2026-03-11T14:35:00Z",
  "menu_option": "0",
  "status": "pass",
  "total_operations": 120,
  "pass_count": 60,
  "fail_count": 2,
  "skip_count": 58,
  "total_elapsed_seconds": 300.5,
  "test_mode": "systematic"
}
```

### progress_start

Emitted before a site/device iteration loop begins.

```json
{
  "event_type": "progress_start",
  "timestamp": "2026-03-11T14:30:00Z",
  "menu_option": "11",
  "operation_name": "List Site Devices",
  "total_items": 45
}
```

### progress_tick

Emitted after each iteration completes.

```json
{
  "event_type": "progress_tick",
  "timestamp": "2026-03-11T14:30:01Z",
  "menu_option": "11",
  "operation_name": "List Site Devices",
  "total_items": 45,
  "current_item": "HQ-Building-A",
  "items_completed": 12,
  "items_remaining": 33
}
```

### progress_complete

Emitted when a loop finishes (naturally or via stop signal).

```json
{
  "event_type": "progress_complete",
  "timestamp": "2026-03-11T14:30:45Z",
  "menu_option": "11",
  "operation_name": "List Site Devices",
  "total_items": 45,
  "items_processed": 45,
  "was_stopped": false,
  "duration_seconds": 45.3
}
```

## Consumer Guide

### Reading Events (Python)

```python
import json

with open("data/test_events_20260311_143000.jsonl") as file:
    for line in file:
        event = json.loads(line)
        if event["event_type"] == "test_fail":
            print(f"FAILED: Menu {event['menu_option']} - {event['error_message']}")
```

### Reading Events (jq)

```bash
# All failures
jq 'select(.status == "fail")' data/test_events_20260311_143000.jsonl

# Summary only
jq 'select(.event_type == "test_summary")' data/test_events_20260311_143000.jsonl

# Progress for Menu 11
jq 'select(.menu_option == "11" and .event_type | startswith("progress"))' data/test_events.jsonl
```

## Compatibility

- **Format**: NDJSON (newline-delimited JSON, RFC 7464 compatible)
- **Encoding**: UTF-8 (ASCII-safe — no Unicode in event values per constitution)
- **Line terminator**: `\n` (LF)
- **Max line length**: No hard limit, but `error_message` capped at 500 characters
- **Versioning**: Schema version not embedded in events (v1 assumed). Future breaking changes will add a `schema_version` field.
