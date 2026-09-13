# Performance monitoring data model

## PerformanceEvent

`PerformanceEvent` is one bounded measurement record.
The JSON contract is `contracts/performance-event.schema.json`.

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Use `1.0.0`. |
| `event_type` | enum | Use operation, HTTP, database, file, serialization, cache, startup, or diagnostic. |
| `timestamp_utc` | date-time string | Use UTC for event order. Do not use it for elapsed time. |
| `monitor_type` | string | Name the measurement method. |
| `source` | object | Name the repository file and exact qualified symbol. |
| `status` | enum | Use `ok`, `error`, `cancelled`, or `timeout`. |
| `sample_rate` | number | Use a value above zero and not above one. |
| `run_id` | string | Use a random run-local correlation identifier. |
| `parent_run_id` | string or null | Link a child event to its parent. |
| `dimensions` | object | Use no more than 16 allowlisted dimensions. |
| `measurements` | object | Use no more than 32 nonnegative numeric values. |

## SourceRef

`SourceRef` identifies a code boundary.

| Field | Required | Description |
| --- | --- | --- |
| `file` | Yes | Repository-relative path from the inventory. |
| `symbol` | Yes | Exact qualified AST symbol. |
| `class` | No | Owning class when a report needs a separate class field. |

## MeasurementRun

`MeasurementRun` groups equivalent events and raw artifacts.

| Field | Description |
| --- | --- |
| `run_id` | Correlation identifier. |
| `source_revision` | Commit plus dirty-state description. |
| `python` | Executable, implementation, version, and build. |
| `environment` | OS, architecture, CPU, dependencies, power mode, and logging state. |
| `workload` | Workload identifier and fixture identity. |
| `state` | Cold, warm, cache hit, cache miss, or sustained. |
| `tools` | Tool names, versions, options, and limits. |
| `artifacts` | Raw timing, profile, memory, I/O, startup, and sampler files. |

## WorkloadDefinition

`WorkloadDefinition` makes a comparison repeatable.

| Field | Description |
| --- | --- |
| `name` | Stable workload name. |
| `entrypoint` | Exact command or callable. |
| `size` | Small, medium, or large. |
| `distribution` | Typical or worst-case. |
| `state` | Cold or warm. |
| `fixture_source` | Sanitized fixture source and revision. |
| `expected_output` | Digest or explicit invariant. |
| `limits` | Duration, repetitions, memory, requests, and artifact size. |

## Metric names

Use a subsystem prefix and a unit suffix when a unit applies.

- `perf.wall_ns`
- `perf.process_cpu_ns`
- `http.requests_total`
- `http.retries_total`
- `http.pages_total`
- `http.request_bytes`
- `http.response_bytes`
- `db.query_wall_ns`
- `db.queries_total`
- `file.operations_total`
- `file.read_bytes`
- `file.write_bytes`
- `serialize.input_bytes`
- `serialize.output_bytes`
- `cache.hits_total`
- `cache.misses_total`
- `cache.evictions_total`
- `diagnostic.traced_peak_bytes`
- `diagnostic.rss_bytes`

## Cardinality rules

Use only stable enums, booleans, and coarse numeric buckets.
Do not use raw organization, site, device, user, path, URL, query, or payload values.
Limit symbol values to entries in the hook catalog or inventory.

## Privacy rules

Do not store credentials, tokens, headers, cookies, payloads, SQL text, file paths, MAC addresses, or IP addresses.
Do not store error messages that can contain private input.
Store an allowlisted error class instead.

## Retention rules

Bound the sink queue and the local artifact directory.
Set a documented age and size limit.
Delete the oldest diagnostic artifacts first.
Do not delete the active baseline or candidate for an open performance decision.
