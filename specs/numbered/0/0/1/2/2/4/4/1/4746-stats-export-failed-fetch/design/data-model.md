# Data Model: Statistics Export Processed Count After Failed Fetch

This change adds no stored data. The model below describes the values that one statistics export run passes through. Each entity names its source and its natural key.

## ProgressContext

- Source: `src\foundation\models\dataclasses\progress_event.py` (frozen dataclass, RC-23).
- Fields: `menu_option` (string or integer, used as the progress label), `operation_name` (string), and `total` (integer).
- Natural key: the pair of `menu_option` and `operation_name`. The two keys in this change are `("13", "device_stats")` and `("15", "vpn_peer_stats")`.
- Constraint: The labels, operation names, and totals stay unchanged (FR-005). The total is 1 for both exports.

## Completion Event

- Source: the `progress_complete` event that `emit_progress_complete` builds (RC-20).
- Fields: `event_type`, `timestamp`, `menu_option`, `operation_name`, `total_items`, `items_processed`, `was_stopped`, and `duration_seconds`.
- Natural key: the `timestamp` with `menu_option` and `operation_name`.
- Constraint: `items_processed` holds 1 when the fetch result is True. It holds 0 when the fetch result is False (FR-001, FR-002).
- Constraint: `was_stopped` holds False for both exports (FR-004). The field records user interruption (RC-22).
- Constraint: The field names and types stay unchanged (FR-006, RC-21).

## Fetch Result

- Source: the boolean that `APIDataFetcher.execute()` returns (RC-08 to RC-13).
- Values: True when the rows were exported (RC-10). False for an HTTP failure (RC-12, RC-13), an unparsed body, an empty response (RC-09), or a rate-limit stop (RC-16).
- Exceptions: An unexpected error re-raises and produces no value (RC-11).
- Natural key: none. The fetch result has one value for each call.

## State Transitions

One statistics export run moves through these states:

1. Idle to Cache hit. This transition applies in fast mode when a fresh file exists. The run emits no event (FR-007).
2. Idle to Started. The run emits a progress start event when a progress emitter exists.
3. Started to Fetching. The run calls `APIDataFetcher.execute()`.
4. Fetching to Succeeded. The fetch result is True. The run emits a completion event with processed count 1.
5. Fetching to Failed. The fetch result is False. The run emits a completion event with processed count 0.
6. Fetching to Raised. The fetcher re-raises an error. The run emits no completion event. This transition is out of scope (D-8).

## Relationships

- One statistics export run holds one `ProgressContext`.
- One statistics export run makes one fetch call and holds one fetch result.
- One statistics export run emits at most one completion event (FR-004).
- Each completion event copies the `menu_option` and `operation_name` of its `ProgressContext`.
