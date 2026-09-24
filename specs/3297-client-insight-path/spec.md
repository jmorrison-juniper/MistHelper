# Feature Specification: Menu 75 client insight path and refusals

**Issue**: #3297
**Branch**: `fix/3297-client-insight-refusals`
**Status**: Implemented in the pull request that closes #3297.

## Problem

Menu 75 exports the client insight metrics of one wireless client. It calls the SDK function `getSiteInsightMetricsForClient`. mistapi 0.63.3 and 0.64.0 build this URL:

```text
/api/v1/sites/{site_id}/insights/client/{client_mac}?metrics=<metric>
```

The live Mist cloud answers that URL with HTTP 404 and the body `{}` for every metric. mistapi does not raise an exception for an HTTP 404. `_fetch_single_metric` reads the empty body as "no data". Menu 75 therefore exports no data, and it reports `! 0 client insights exported to <file> (no data available)`. The operator cannot see that the Mist API refused each request.

The live cloud serves the path form:

```text
/api/v1/sites/{site_id}/insights/client/{client_mac}/{metric}
```

A probe on 2026-09-23 sent GET requests only. The path form returned HTTP 200 with data for all 12 client-scope metrics of one client. The probe tried the colon form and the bare form of the MAC. Each MAC form gave the same result on each URL form.

The two local API specifications disagree. `documentation/mist-api-openapi31yaml.yaml` names the query form. `documentation/mist-api-openapi3yaml.yaml` names the path form.

## User story

As a NOC engineer, I export the client insight metrics of one client. I want the export to hold the data that the Mist API holds. If the API refuses a metric, I want to read the metric, the HTTP status, and the reason.

### Acceptance scenarios

1. If the client has data for each metric, menu 75 exports one record for each metric. The summary states that count.
2. If the API refuses a metric with an HTTP status of 400 or more, the export holds no record for that metric. The operator reads one line with the metric, the status, and the reason.
3. If the API refuses every metric, the empty export summary shows. The refusal report follows it.

## Functional requirements

- **FR-001**: Menu 75 requests each client metric from the path form through the session `mist_get`. The path holds the metric name in URL-encoded form.
- **FR-002**: An answer with an HTTP status of 400 or more does not become a record.
- **FR-003**: The summary count holds only the metrics that returned data.
- **FR-004**: After the export, the operator reads each refused metric with its HTTP status and its reason. A run without a refusal adds no refusal line.
- **FR-005**: Each run starts with no refusal.
- **FR-006**: An answer without an integer HTTP status keeps the current behavior.
- **FR-007**: The MAC form, the file name, and the record tags stay the same.

## Out of scope

- A change to the SDK. The SDK defect belongs to the upstream project `tmunzer/mistapi_python`.
- A fallback to the query form. If the cloud retires the path form, the refusal report shows HTTP 404 for each metric.
- Menu 74 and menu 76. Issue #3266 and issue #3267 cover them.

## Success criteria

- **SC-001**: A replay of the probe exports 12 records, and the summary states 12.
- **SC-002**: A run where the API refuses every metric shows the empty summary and the refusal report.
