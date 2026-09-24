# Implementation Plan: Report refused device insight metrics

## Design

A new module `src/export/site_insights/metric_refusals.py` holds two types.

- `MetricRefusal` is a frozen record of one refused request. It holds the metric name, the HTTP status, and the reason.
- `MetricRefusalLog` collects the refusals of one export run. `record(metric, response)` reads the HTTP status of the response. If the status is an integer of 400 or more, the method stores a refusal, logs a warning, and returns True. `report(target_name)` writes one operator line for each refusal.

`DeviceMetricOperation` holds one `MetricRefusalLog` for each run. `_collect_metrics` clears the log before the first request. `_fetch_one_metric` returns None for a refused response, so the error body does not become a row. `_run_export` reports the refusals after `_finalize`, so the report follows each of the three export paths.

Menu 74 and menu 75 can use the same class in their own repairs.

## Files

- src/export/site_insights/metric_refusals.py (new)
- src/export/site_insights/device_metric_operation.py
- tests/unit/export/site_insights/test_device_metric_refusals.py (new)
- tests/unit/export/site_insights/test_metric_refusals.py (new)
- changelog.d/issue-3267-device-insight-refusals.md (new)

## Risks

- A test double can hold a status that is not an integer. The check reads the status only when it is an integer, so those tests keep the current behavior.
- An error body can hold text that is not ASCII. The reason keeps ASCII characters only, so the log stays ASCII.
- The existing tests call the private helpers directly. The repair keeps each helper signature.

## Validation

- Record the red proof on the old code.
- Run the new tests and the existing menu 76 tests.
- Replay the five refusal bodies of the recorded run through the real menu 76 code.
- Run py_compile, Ruff, Black, mypy, symbol_diff, the STE linter, and the test ratchet.
