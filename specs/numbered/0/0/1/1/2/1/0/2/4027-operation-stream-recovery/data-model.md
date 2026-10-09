# Data Model: Operation Stream Recovery

This feature adds no server entity and no stored schema.
The browser holds temporary state for the displayed operation.

## Operation Run View

**Purpose**: Identify the active browser run and reject stale asynchronous
work.

| Field | Type | Rules |
|---|---|---|
| `active_run_id` | string or null | Matches only the run that can receive active updates. |
| `terminal_run_id` | string or null | Names the run that reached `completed` or `failed`. |
| `stream` | `EventSource` or null | Belongs to `active_run_id`. Close it during replacement or finish. |
| `status_timer` | timeout handle or null | Holds one scheduled five-second check. |
| `status_request_run_id` | string or null | Names the one active status request. |

### Validation Rules

- A timer can exist only for the active run.
- A status request can exist for only one run.
- A response can change the page only when its run is active.
- A terminal run cannot return to `running`.
- A stream event can change the page only when its stream still owns the run.

### State Transitions

```text
idle
  -> running
  -> completed
  -> failed

running
  -> running after an authoritative running response
  -> completed after status or terminal stream data
  -> failed after status or terminal stream data

completed and failed
  -> no further state for the same run
```

Starting or reconnecting to another run replaces the active run state.
Replacement closes the old stream and clears the old timer.

## Authoritative Status Result

**Purpose**: Represent the existing status endpoint response.

| Field | Type | Rules |
|---|---|---|
| `run_id` | string | Must match the requested active run. |
| `status` | string | Relevant values are `running`, `completed`, and `failed`. |
| `completion_message` | string or null | Used for a completed presentation. |
| `error_message` | string or null | Used for a failed presentation. |
| `output_files` | list of strings | Each value is an exact server file path. |

The browser does not change this contract.

## Output Presentation

**Purpose**: Track the exact output set that the browser applied.

| Field | Type | Rules |
|---|---|---|
| `output_run_id` | string or null | Scopes every output identity to one run. |
| `ordered_paths` | list of strings | Holds each exact path once in first-delivery order. |
| `identity_signature` | string or null | Canonical comparison of `run_id` and exact paths. |
| `output_applied` | boolean | Distinguishes an unapplied state from an applied empty set. |

### Output Identity

An output identity is this pair:

```text
(run_id, exact_server_file_path)
```

Examples:

```text
("run-a", "site-a/result.csv")
("run-a", "site-b/result.csv")
("run-b", "site-a/result.csv")
```

All three examples are distinct identities.
The first two can share the base name `result.csv`.
The first and third can share the exact path.

### Output Set Rules

- Remove repeated exact paths within one delivery.
- Preserve the first input order for visible links.
- Compare identity sets without order differences.
- Replace links when the identity set changes.
- Skip links and preview work when the identity set is identical.
- Apply the first terminal empty set.
- Hide the link panel for an empty set.
- Reset the results preview for an empty set.
- Keep the terminal message during output cleanup.

## Status Check Measurement

The Playwright proof will record these values:

| Measurement | Meaning |
|---|---|
| `scheduled_delays` | Requested browser timeout values. |
| `status_checks` | Calls to the existing status endpoint. |
| `terminal_transitions` | Accepted completed or failed transitions. |
| `stream_error_calls` | Calls to the controlled stream error handler. |

## Output Replay Measurement

The Playwright proof will record these values:

| Measurement | Meaning |
|---|---|
| `replay_sources` | Status replay and terminal stream replay deliveries. |
| `exact_paths` | Distinct exact server paths sent to the browser. |
| `rendered_links` | Visible output links after replay. |
| `preview_loads` | Requests to the result preview endpoint. |
