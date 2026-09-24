# Implementation Plan: Menu 74 site insight path and refusals

**Spec**: [spec.md](./spec.md)
**Issue**: #3266

## Summary

Replace the SDK call in `SiteMetricOperation._fetch_one_metric` with a GET of the path form through `self.apisession.mist_get`. Give the operation a `MetricRefusalLog`, as the device operation of menu 76 has. Report the refusals after the export. Teach `MetricRefusalLog` to read the key `details`.

## Technical context

- Python 3.13 and mistapi 0.64.0. The change adds no dependency.
- Pull request #3301 makes the same change for menu 75. `src/export/org_export_utils.py` already calls the path form `/api/v1/orgs/{org_id}/insights/{metric}` through `mist_get`.
- `DeviceMetricOperation` of menu 76 holds its `MetricRefusalLog` on the instance. It clears the log in `_collect_metrics`, and it reports the log after `_finalize`. This plan uses the same design.

## Design

1. The module constant `_SITE_METRIC_URI_TMPL` holds the path form.
2. `SiteMetricOperation.__init__` creates `self._refusal_log = MetricRefusalLog("site insight")`.
3. `_collect_metrics` clears the log before the first request, so each run starts empty.
4. `_fetch_one_metric` builds the URI with the URL-encoded metric name. It calls `self.apisession.mist_get(uri)`. Then it calls `self._refusal_log.record(metric, response)` before it reads the body as data.
5. `_run_export` calls `self._refusal_log.report(context.site_name)` after `_finalize`.
6. `MetricRefusalLog.REASON_KEYS` becomes `("detail", "details", "error", "message")`.

## Tests

- `tests/unit/export/site_insights/test_site_insight_path.py` (new): the path form, the encoded name, the SDK form, the probe replay, the refusal, the count, the report, the empty run, the start state, the old path for an answer without an integer status, and the tags.
- `tests/unit/export/site_insights/test_site_metric_operation_wave9.py`: four tests mock the SDK function. They change to mock `apisession.mist_get`.
- `tests/unit/export/site_insights/test_metric_refusals.py`: one new test reads the reason from the key `details`.

## Risks

- The cloud can retire the path form. Then the refusal report shows HTTP 404 for each metric, and the operator can see the failure.
- A metric name can hold a character that changes the path. The design URL-encodes the metric name, so the name stays one path segment.
- A body can hold both `detail` and `details`. The key `detail` stays first, so the menu 76 lines do not change.
