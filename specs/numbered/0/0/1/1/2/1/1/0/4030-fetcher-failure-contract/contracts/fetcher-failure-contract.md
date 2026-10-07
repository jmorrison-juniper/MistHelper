# Contract: Unresolved Site Fetch Failure

## Scope

This contract applies to `DeviceDataFetcher.fetch()` when no site ID is
supplied and site selection cannot resolve one.

## Inputs

- `DeviceFetchConfig.site_id` is `None` or empty.
- `PromptUtils.select_site_id_from_csv()` returns no usable site ID.
- The remaining fetch configuration can contain any valid filename,
  description, device type, or endpoint callable.

## Required Output

The fetcher must emit this exact operator-visible error:

```text
! Error fetching device data: site ID could not be resolved.
```

The fetcher must return explicit `False`.

## Required Stops

After site resolution fails, the fetcher must not:

- Call `select_device_id_from_inventory`.
- Call the Mist endpoint.
- Flatten or escape response data.
- Call the data exporter.
- Render a table.
- Create the requested result file.

## Display Contract

`InteractiveDisplayUtils.device_tests()` must remain unchanged.

When the fetcher returns explicit `False`, the display must return before it
logs:

```text
Completed device_tests execution.
```

## Portal Contract

`OperationExecutor` must remain unchanged.

The portal must scan the captured error before it accepts output evidence. The
existing `error fetching` marker must return the exact error as the failure
reason.

Unrelated output can remain in the run record. The final status must still be
`failed`.

## Red-Green Regression Contract

The portal regression must use:

- The real `InteractiveDisplayUtils.device_tests`.
- The real `DeviceDataFetcher`.
- The real `OperationExecutor` execution path.
- The real `OutputFileScanner` against `tmp_path`.

The test can replace external boundaries only:

- Site selection.
- The Mist endpoint.
- The API session.
- Data export and display sinks.
- The scanner root.

The test must not fake the fetcher result or prepare portal log entries.

## Before-Repair Evidence

Run the new portal regression before the production edit.

The run must contain unrelated output evidence. The observed portal status must
be `completed`, so the new expected-failure assertion fails.

## After-Repair Evidence

Run the same portal regression after the production edit.

The run must:

- Have status `failed`.
- Keep the unrelated output evidence.
- Contain the exact fetcher error in `error_message`.
- Omit the display completion log.
- Make no Mist request.

## Dependency

Issue #3168 owns the broader removal of log-marker coupling. This feature uses
the established marker contract and does not expand it.
