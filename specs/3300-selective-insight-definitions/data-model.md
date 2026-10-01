# Data Model: Selective Insight Definitions

**Feature**: [spec.md](spec.md)

**Design contract**: [definition-refresh.md](contracts/definition-refresh.md)

This design adds no database entity, schema, primary key, or persistent status file.
All selected results belong to one refresh attempt.

## 1. Definition configuration

The existing `EndpointConfig` remains the discovery record.

| Field | Meaning |
| --- | --- |
| `endpoint_name` | The validated SDK module name, such as `insight_metrics`. |
| `module` | The imported module that contains the selected SDK function. |
| `function_name` | The existing discovered API function name. |
| `filename` | The existing generated definition filename. |
| `description` | The existing operator description. |
| `modname` | The full SDK module path. |
| `special_handling` | Existing standard, model, country, or channel dispatch. |

For insight refresh, discovery must retain these values:

- `endpoint_name`: `insight_metrics`.
- `function_name`: `listInsightMetrics`.
- `filename`: `ConstInsightMetrics.csv`.
- `modname`: `mistapi.api.v1.const.insight_metrics`.
- `special_handling`: `None`.

The selected entry consumes one configuration.
Full export retains its dynamic collection of configurations.
Do not change this existing data class.

## 2. Definition cache

| Field | Meaning |
| --- | --- |
| `path` | The existing `data/ConstInsightMetrics.csv` path. |
| `mtime` | The existing file modification time. |
| `age_seconds` | The cache clock minus `mtime`. |
| `fresh` | The existing strict comparison against 86,400 seconds. |

An age below 86,400 seconds is fresh.
An exact or greater age requires a refresh.
A missing file or an unreadable timestamp retains the existing refresh behavior.
Preserve the current behavior for future timestamps.
Do not add a second cache check or persistent failure marker.

Only the selected cache enters a selective refresh.
The validation harness takes unrelated-file snapshots outside the measured refresh.
Those snapshots must not count as accesses by the refresh operation.

## 3. Insight definition row

The existing normalizer determines row values and insertion order.
The real CSV writer sorts the eight column names.
Preserve that existing CSV order.

| Normalizer field | Existing value rule |
| --- | --- |
| `metric_name` | Preserve the SDK dictionary key and iteration order. |
| `description` | Preserve the description, with the existing empty default. |
| `type` | Preserve the type, with the existing empty default. |
| `unit` | Preserve the unit, with the existing empty default. |
| `scopes` | Join existing scope values with `, `. |
| `report_scopes` | Join existing report scope values with `, `. |
| `intervals` | Retain `_format_intervals`. |
| `report_intervals` | Retain `_format_report_intervals`. |

Retain `DataProcessingUtils.escape_multiline` before output.
Do not sort rows, fields, scopes, or interval names.
Retain existing defaults and handling for supported list or raw payloads.

The scope reader preserves CSV row order.
It normalizes the requested scope and parses existing comma or semicolon scope forms.
It excludes missing names, missing scopes, and names with `{` or `}`.
The result remains an ordered `list[str]`.

## 4. Selected refresh result

Place the small `DefinitionRefreshResult` data record in the existing exporter module.
Do not add a wrapper class or another source file.

| Field | Type | Rule |
| --- | --- | --- |
| `endpoint_name` | `str` | Identify the selected name without using it as an unvalidated path. |
| `outcome` | `fresh`, `updated`, or `failed` | Describe the current attempt, not file existence. |
| `counts` | Read-only mapping of four integer differences. | Snapshot the existing exporter counters for this attempt. |
| `http_status` | `int` or `None` | Retain the original known HTTP failure status. Fresh hits have no request status. |
| `first_error` | Exception or `None`. | Retain the first expected exception. Never replace it with a fallback error. |

The four count keys are `processed`, `skipped_fresh`, `updated`, and `failed`.
They correspond to the existing `endpoints_*` counters.
The result must not hold a live view of mutable counters.
Reuse of an exporter instance must not alter an earlier result.

### Count invariants

| Attempt | `processed` | `skipped_fresh` | `updated` | `failed` |
| --- | --- | --- | --- | --- |
| Registered definition, fresh cache. | 1 | 1 | 0 | 0 |
| Registered definition, successful primary write. | 1 | 0 | 1 | 0 |
| Registered definition, expected processing failure. | 1 | 0 | 0 | 1 |
| Invalid selection or discovery failure before registration. | 0 | 0 | 0 | 1 |

An empty successful response can produce `updated`.
A successful empty fallback cannot produce `updated`.
A secondary fallback failure cannot increase `failed` again.
Unexpected programming errors retain their existing propagation behavior.

The offline session and writer record actual I/O counts separately.
They distinguish request attempts, primary writes, fallback writes, and successful writes.
These measurements support acceptance evidence without duplicating exporter counters.

## 5. State transitions

```text
selected name
  -> invalid name -> failed
  -> selected SDK discovery
       -> discovery failure -> failed
       -> registered EndpointConfig
            -> existing cache decision
                 -> fresh -> fresh
                 -> missing, stale, or unreadable timestamp
                      -> fetch and existing normalization
                           -> successful primary write -> updated
                           -> first expected failure
                                -> existing empty fallback attempt
                                     -> success or secondary failure -> failed
```

Record the first failure before the fallback.
Retain the original HTTP response on an HTTP exception.
If no error text exists, retain the HTTP status as the first available error message.
A `False` writer result carries no original exception object.
Keep its original writer log and report the failed Boolean boundary accurately.

## 6. Caller relationships

All four refresh entries use `InsightMetricsUtils.export_const_insight_metrics`.
That helper constructs the existing exporter, selects `insight_metrics`, and reports its result.
The helper returns `None`, so caller return contracts remain unchanged.

Site, device, and client refresh entries return `None`.
Organization setup returns the ordered organization metric list or `None`.
Its no-metrics path attempts four empty normalized writes without the legacy combined file.
The CSV writer creates no file for empty data and leaves any existing file unchanged.
The shared helper does not add a new abort, retry, file-deletion, or stale-data policy.

See the [caller contract](contracts/definition-refresh.md#caller-compatibility) for the exact entries and output boundaries.
