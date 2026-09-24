# Feature Specification: Menu 74 site insight path and refusals

**Issue**: #3266
**Branch**: `fix/3266-site-insight-path`
**Status**: Implemented in the pull request that closes #3266.

## Problem

Menu 74 exports the insight metrics of one site. It calls the SDK function `getSiteInsightMetrics`. mistapi 0.63.3 and 0.64.0 build this URL:

```text
/api/v1/sites/{site_id}/insights?metrics=<metric>
```

The live Mist cloud answers that URL with HTTP 404 and the body `{}`. The comma list form gets the same answer. mistapi does not raise an exception for an HTTP 404. `_fetch_one_metric` reads the empty body as "no data". Menu 74 therefore exports no data, and it reports `! 0 insight metrics exported to <file> (no data available)`. The operator cannot see that the Mist API refused each request.

The live cloud serves the path form:

```text
/api/v1/sites/{site_id}/insights/{metric}
```

A probe on 2026-09-23 sent GET requests only. It sent the path form for the 64 site-scope metrics of one site. 55 metrics returned HTTP 200 with data. 9 metrics returned HTTP 400:

| Metric | Error body |
| - | - |
| `noise` | The reason "valid band is required" |
| `time-to-connect`, `successful-connect`, `client-coverage-band5`, `client-coverage-band24`, `client-capacity-band5`, `client-capacity-band24` | The reason "data temporary unavailable" |
| `switch-metrics`, `gateway-metrics` | `{"details": "unknown"}` |

The 64 requests took 12.4 seconds in total, with a mean of 0.19 seconds.

`MetricRefusalLog` reads the reason from the keys `detail`, `error`, and `message`. It does not read `details`. For the last two metrics, the operator line therefore states that the body holds no reason, but the body holds one.

## User story

As a NOC engineer, I export the insight metrics of one site. I want the export to hold the data that the Mist API holds. If the API refuses a metric, I want to read the metric, the HTTP status, and the reason.

### Acceptance scenarios

1. If the site has data for a metric, menu 74 exports one record for that metric. The summary states the count of the records.
2. If the API refuses a metric with an HTTP status of 400 or more, the export holds no record for that metric. The operator reads one line with the metric, the status, and the reason.
3. If the API refuses every metric, the empty export summary shows. The refusal report follows it.

## Functional requirements

- **FR-001**: Menu 74 requests each site metric from the path form through the session `mist_get`. The path holds the metric name in URL-encoded form.
- **FR-002**: An answer with an HTTP status of 400 or more does not become a record.
- **FR-003**: The summary count holds only the metrics that returned data.
- **FR-004**: After the export, the operator reads each refused metric with its HTTP status and its reason. A run without a refusal adds no refusal line.
- **FR-005**: Each run starts with no refusal.
- **FR-006**: An answer without an integer HTTP status keeps the current behavior.
- **FR-007**: The file name, the record tags, and the `api_function_name` of the write stay the same.
- **FR-008**: `MetricRefusalLog` also reads the reason from the key `details`. The keys `detail`, `error`, and `message` keep their current order.

## Out of scope

- A change to the SDK. The SDK defect belongs to the upstream project `tmunzer/mistapi_python`.
- A fallback to the query form. If the cloud retires the path form, the refusal report shows HTTP 404 for each metric.
- The refresh of the constant definitions before the export. Issue #3300 covers that cost.
- A band parameter for the metric `noise`. The export sends no query parameter today, and this repair does not add one.

## Success criteria

- **SC-001**: A replay of the probe exports 55 records, and the summary states 55.
- **SC-002**: The same replay reports the 9 refusals. Each line states the reason that the probe recorded.
- **SC-003**: A run where the API refuses every metric shows the empty summary and the refusal report.
