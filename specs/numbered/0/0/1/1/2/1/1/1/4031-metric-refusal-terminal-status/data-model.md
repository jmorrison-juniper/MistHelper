# Data Model: Metric Refusal Terminal Status

This feature adds no persistent entity and changes no export schema. It adds
one transient decision to each independent metric operation.

## Existing transient entities

### SiteRunContext

- **Owner**: `SiteMetricOperation`
- **Fields**: `site_id`, `site_name`
- **Use**: Supplies the site scope for requests, row annotations, file names,
  refusal reports, and the terminal failure marker.
- **Persistence**: None.

### DeviceRunContext

- **Owner**: `DeviceMetricOperation`
- **Fields**: `site_id`, `site_name`, `device_id`, `device_name`,
  `device_mac`, `device_model`
- **Use**: Supplies the device scope for requests, row annotations, file
  names, refusal reports, and the terminal failure marker.
- **Persistence**: None.

### MetricRefusal

- **Owner**: Existing `MetricRefusalLog` helper.
- **Fields**: `metric`, `status_code`, `reason`
- **Validation**: The helper records only integer HTTP status values at or
  above 400. It keeps the reason ASCII, single-line, and at most 200
  characters.
- **Persistence**: None. The list lives for one operation run.
- **Scope rule**: The shared helper is read-only for this feature.

## New transient state condition

### Refusal terminal condition

- **Definition**: `MetricRefusalLog.refusals` contains one or more records after
  the operation collects all requested metrics.
- **Transition**:
  1. `_collect_metrics()` clears the prior run's refusal list.
  2. Each refused response adds one record and returns no export row.
  3. Later metrics continue to run.
  4. `_finalize()` writes successful rows or the existing empty result.
  5. `report()` writes each refusal detail.
  6. The operation writes one `Failed to` handled-error marker.
- **No-refusal state**: The existing success path remains unchanged and emits
  no refusal failure marker.

## Export row rules

- A valid non-empty response becomes one existing annotated row.
- An empty response remains excluded.
- A refused response body remains excluded.
- A transport exception remains excluded and keeps its current per-metric
  behavior.
- Partial rows remain written before the terminal marker is emitted.

## Compatibility rules

- No new database key or persistent storage is needed.
- No endpoint, request path, response shape, or export format changes.
- No portal response schema changes.
