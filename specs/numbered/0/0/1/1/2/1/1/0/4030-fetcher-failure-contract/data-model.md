# Data Model: Fetcher Failure Contract

This feature changes no database or file schema. The model describes transient
objects that cross the fetcher, display, and portal boundaries.

## Entity: Device Fetch Configuration

**Owner**: `DeviceFetchConfig`

**Fields used by Menu 95**:

- `fetch_function`: The Mist synthetic-test endpoint callable.
- `filename`: `DeviceTestResults.csv`.
- `description`: `Fetching synthetic test stats`.
- `device_type`: `gateway`.
- `site_id`: Initially `None`.
- `device_id`: Initially `None`.

**Validation rule**: A site ID must exist before device selection starts.

## Entity: Device Fetch Outcome

**Owner**: `DeviceDataFetcher.fetch()`

**States**:

- `success-or-empty`: Return `None` after a valid fetch path.
- `explicit-failure`: Return `False` after a failure that must suppress
  completion.

**Issue #4030 transition**:

```text
site_id unresolved
    -> log exact operator error
    -> return False
    -> stop before device selection
```

**Invariants**:

- An unresolved site does not call device selection.
- An unresolved site does not call the Mist endpoint.
- An unresolved site does not transform data.
- An unresolved site does not render data.
- An unresolved site does not write a requested result.

## Entity: Captured Failure Evidence

**Owner**: The existing portal run log

**Required message**:

```text
! Error fetching device data: site ID could not be resolved.
```

**Classification**: `HANDLED_ERROR_MARKERS` matches `error fetching`
case-insensitively.

**Dependency**: Issue #3168 owns replacement of this prose coupling with a
typed outcome.

## Entity: Unrelated Output Evidence

**Owner**: `OutputFileScanner`

**Test representation**: One unrelated file created in `tmp_path` during site
selection.

**Purpose**: Reproduce concurrent output contamination without editing the run
record directly.

**Invariant**: The file can appear in `output_files`, but it cannot override a
handled error.

## Entity: Portal Run Verdict

**Owner**: `OperationExecutor`

**Fields inspected**:

- `status`
- `error_message`
- `completion_message`
- `output_files`
- `log_messages`

**Pre-repair transition**:

```text
site_id unresolved
    -> fetcher returns None
    -> display logs completion
    -> scanner finds unrelated output
    -> portal status becomes completed
```

**Post-repair transition**:

```text
site_id unresolved
    -> fetcher logs exact error
    -> fetcher returns False
    -> display suppresses completion
    -> scanner finds unrelated output
    -> handled error wins
    -> portal status becomes failed
```

## Unchanged Transitions

- A supplied site ID continues to device resolution.
- A missing device ID keeps its current return behavior.
- An empty successful Mist response keeps its no-data behavior.
- A successful response keeps its transform, export, and render behavior.
