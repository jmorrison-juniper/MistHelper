# Contract: Selected Definition Refresh

**Feature**: [spec.md](../spec.md)

**Data records**: [data-model.md](../data-model.md)

The session retains its configured regional Mist host.
This feature does not select a host or create a session.
Validation uses an offline session only.
The existing SDK function sends `GET /api/v1/const/insight_metrics` with `query={}`.
Do not replace it with a new HTTP client.

## Selected exporter entry

**Planned interface**: `ConstDefinitionsExporter.export_endpoint(endpoint_name: str) -> DefinitionRefreshResult`.

Accept one public ASCII SDK module name.
Reject empty, private, dotted, path-like, non-string, or otherwise invalid names before import.
Do not normalize invalid names into a different selection.

The entry owns these responsibilities:

1. Validate the name and capture the existing counter values.
2. Inspect only the selected SDK module through existing discovery methods.
3. Process only its registered `EndpointConfig` through the existing cache and export path.
4. Build the result from counter differences and the first error.
5. Emit an accurate selected summary.

Do not enumerate unrelated SDK modules or use a full-export fallback.
Do not read another definition file or inspect its timestamp.
Do not process an old registration after selected discovery fails.
An invalid or unavailable selection makes zero API requests and zero file writes.

The result fields and count invariants appear in the [data model](../data-model.md#4-selected-refresh-result).
Secondary errors appear as distinct log records. They do not replace `first_error` or `http_status`.

## Cache and output contract

| Input state | Required selected behavior |
| --- | --- |
| File age below 86,400 seconds. | Return `fresh`, with zero requests and writes. Preserve bytes and modification time. |
| File age exactly 86,400 seconds. | Fetch once and attempt the primary definition write once. |
| Expired or missing file. | Fetch once and attempt the primary definition write once. |
| Timestamp cannot be read. | Retain the existing refresh behavior. |
| Successful refresh followed by another entry call. | Reuse the fresh cache without another request or write. |
| Unrelated files with any cache age. | Perform no discovery, reads, timestamp checks, requests, or writes for them. |

For a successful non-empty response, preserve `ConstInsightMetrics.csv` and these ordered fields:

```text
description,intervals,metric_name,report_intervals,report_scopes,scopes,type,unit
```

Retain existing normalization, interval text, multiline escaping, and output metadata.
Call `DataExporter.write_with_format_selection` with `api_function_name="listInsightMetrics"`.
Do not change configured backend selection.
A successful empty response retains the existing empty write attempt.
The CSV writer creates no file for empty data.
It leaves an existing stale file unchanged.
Do not invent a header or metric row for that case.

## Failure contract

| Failure | First evidence | Required outcome |
| --- | --- | --- |
| HTTP `4xx` or HTTP `5xx`, with or without a body. | Original HTTP status, response, and first available safe error text. | Return `failed`, record zero updates, and retain the existing empty fallback attempt. |
| SDK response with `status_code=None`. | No HTTP response, including an SDK proxy-error result. | Report a transport failure, not successful empty data. |
| Connection failure or timeout. | Original expected transport exception. | Return `failed` and retain the existing empty fallback attempt. |
| Selected import or function discovery failure. | Original caught discovery exception or a specific unavailable-definition error. | Return `failed` without another definition's discovery or output. |
| Primary writer returns `False`. | Failed Boolean boundary plus any preceding writer error log. | Return `failed`, record zero updates, and attempt the existing empty fallback. |
| Primary writer raises an expected exception. | Original output exception. | Return `failed`, record zero updates, and attempt the existing empty fallback. |
| Empty fallback returns `False` or raises an expected exception. | Separate secondary output evidence. | Keep the first error, original status, and one failed count. |

Validate HTTP status before treating `.data` as definition data.
A successful fallback does not repair the refresh result.
File existence does not repair the refresh result.
Do not add retries or catch unrelated programming faults.
Do not claim that a Boolean writer result exposes an exception that the writer did not return.

Keep first-error identity and status inside the local result.
Use the existing redaction boundary for visible error text.
Do not print a raw response, token, session object, request header, or credential-bearing URL.
Check formatted logs and traceback text with synthetic secret values.

## Shared helper contract

**Existing interface**: `InsightMetricsUtils.export_const_insight_metrics() -> None`.

Construct the existing exporter with the active session.
Request `insight_metrics` through `export_endpoint`.
Retain the `Export Available Insight Metrics:` banner.
Replace notices that falsely describe comprehensive export.
Keep the public return value as `None`.

Report `failed` before any file-availability test.
Do not emit `ConstInsightMetrics.csv is available` after a failed attempt.
If the result is `fresh` or `updated`, check only the selected CSV before an availability notice.
A successful configured backend write does not itself prove that a CSV exists.
A successful empty response does not prove that any scope has metrics or that a CSV exists.

Do not change `get_by_scope`, its exclusions, or its ordered return value.
Do not add shared last-result state.

## Caller compatibility

| Caller | Actual refresh entry | Retained return and behavior |
| --- | --- | --- |
| Site, Menu 74. | `SiteMetricOperation._refresh_const_metrics` | `None`, existing banner and site-scope loading. |
| Client, Menu 75. | `SiteClientInsightsService._print_intro_and_refresh` | `None`, existing banner and client workflow. |
| Device, Menu 76. | `DeviceMetricOperation._refresh_const_metrics` | `None`, existing banner and device-scope loading. |
| Organization. | `OrgExportUtils._insight_setup_or_empty` | Ordered org metrics, or `None` with the existing no-metrics outputs. |

The client calls `deps.InsightMetricsUtils.export_const_insight_metrics`.
Its resolver removes the unused `ConstDefinitionsExporter` dependency.
The other three caller files remain unchanged.

Retain prompts, selections, filenames, metric collection, error handling, and existing empty outputs.
The organization no-metrics path retains these four files:

- `OrgMetricsSummary.csv`.
- `OrgMetricsTimeSeries.csv`.
- `OrgMetricsResults.csv`.
- `OrgSitesData.csv`.

That path does not attempt a write to `OrgInsightMetrics_Legacy.csv`.
The four empty write attempts do not create CSV files.
Count these insight-output writes separately from definition writes.
If a failed output leaves an old definition CSV, retain existing caller reading behavior.
Do not report that failed refresh as successful.

## Full export compatibility

**Existing interface**: `ConstDefinitionsExporter.export_all() -> None`.

Keep SDK package enumeration, function selection, cache skips, output names, and full coverage.
Retain all 28 controlled baseline definitions.
Do not install a production list limited to those names.
Keep `all_models`, `all_countries`, and `all_countries_channels`, including their existing fallback lists.
Keep the skip behavior for unsupported required parameters.

Shared HTTP and write checks must improve truthful results without reducing definition coverage.
Do not alter model, country, or channel aggregation policy as part of this repair.
Full export may ignore new private error return values and continue processing its remaining definitions.

## Logging contract

Use ASCII messages and `%s`-style logging.
Log before and after selected discovery, cache inspection, API fetch, normalization, primary write, and fallback write.
An error record supplies the after-action evidence when an action fails.
Retain traceback context through the existing safe logging boundary.

A selected summary identifies the name, outcome, and current `processed`, `skipped_fresh`, `updated`, and `failed` counts.
A fetch summary identifies the known HTTP status.
A write summary identifies the Boolean result and distinguishes primary output from empty fallback.
Do not describe the selected operation as a comprehensive export.

See [quickstart.md](../quickstart.md) for the offline evidence procedure.
