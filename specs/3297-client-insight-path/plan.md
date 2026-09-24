# Implementation Plan: Menu 75 client insight path and refusals

**Spec**: [spec.md](./spec.md)
**Issue**: #3297

## Summary

Replace the SDK call in `SiteClientInsightsService._fetch_single_metric` with a GET of the path form through `deps.apisession.mist_get`. Give `_ExportContext` a `MetricRefusalLog`, which the repair of #3267 adds. Report the refusals after the export.

## Technical context

- Python 3.13 and mistapi 0.64.0. The change adds no dependency.
- `src/export/org_export_utils.py` already calls `session.mist_get(uri=uri, query=query)` where the SDK cannot build the request. This plan uses the same pattern.
- `MetricRefusalLog` lives in `src/export/site_insights/metric_refusals.py`. Pull request #3298 adds it, so this branch rebases onto `main` after that merge.

## Design

1. The module constant `_CLIENT_METRIC_URI_TMPL` holds the path form.
2. `_ExportContext` gets the field `refusals`. A default factory creates a new `MetricRefusalLog("client insight")` for each context. `execute` builds a new context for each run, so each run starts empty.
3. `_fetch_single_metric` builds the URI with the URL-encoded metric name. It calls `deps.apisession.mist_get(uri)`. Then it calls `context.refusals.record(metric, response)` before it reads the body.
4. `_run_collect_and_export` calls `context.refusals.report(context.client_mac)` after the export. The call follows the `try` block, so the report also shows after an export fault.

## Tests

- `tests/unit/serial_cc/test_site_client_insight_path.py` (new): the path form, the SDK form, the probe replay, the refusal, the count, the report, the empty path, the start state, the old path for an answer without an integer status, and the tags.
- `tests/unit/test_exports.py`: `test_client_insights_uses_metrics_keyword` asserts the SDK query form, which the live cloud refuses. The test changes to assert the path form.
- `tests/unit/serial_cc/test_site_client_insights.py`: the happy path test mocks the SDK function. It changes to mock `apisession.mist_get`.

## Risks

- The cloud can retire the path form. Then the refusal report shows HTTP 404 for each metric, and the operator can see the failure.
- A metric name can hold a character that changes the path. The design URL-encodes the metric name, so the name stays one path segment.
