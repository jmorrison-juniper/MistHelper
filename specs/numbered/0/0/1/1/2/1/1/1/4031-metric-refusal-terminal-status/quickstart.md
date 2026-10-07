# Quickstart: Validate Metric Refusal Terminal Status

## Prerequisites

- Use Python 3.13 or newer.
- Install the project development dependencies.
- Run commands from the repository root.
- Do not use live Mist credentials for these focused unit tests.

## Focused validation

Run the site metric tests:

```text
python -m pytest tests/unit/export/site_insights/test_site_insight_path.py -q
```

Run the device metric tests:

```text
python -m pytest tests/unit/export/site_insights/test_device_metric_refusals.py -q
```

Expected result: both modules pass. The tests must prove mixed responses,
repeated refusals, preserved successful rows, refusal details, the handled-error
marker, and the no-refusal success path.

## Static validation

Compile the changed Python modules:

```text
python -m py_compile src/operations/exporting/export/site_insights/site_metric_operation.py src/operations/exporting/export/site_insights/device_metric_operation.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/export/site_insights/test_device_metric_refusals.py
```

Check formatting and lint for the changed Python files:

```text
python -m black --check src/operations/exporting/export/site_insights/site_metric_operation.py src/operations/exporting/export/site_insights/device_metric_operation.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/export/site_insights/test_device_metric_refusals.py
python -m ruff check src/operations/exporting/export/site_insights/site_metric_operation.py src/operations/exporting/export/site_insights/device_metric_operation.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/export/site_insights/test_device_metric_refusals.py
```

Check the implementation scope:

```text
git diff --name-only
```

Expected result: implementation work names only the two metric operation
modules, the two focused test modules, and one issue-4031 changelog fragment.
Plan artifacts are allowed only under this feature directory. The portal
service, shared refusal helper, and unrelated product or test files must not
appear.

## Behavior checks

For each operation, inspect the focused test output and log assertions:

1. A successful response remains in the writer input.
2. A refused response does not become a writer row.
3. Every refused metric appears in the existing refusal report.
4. One `Failed to` marker appears after the batch finishes.
5. The portal handled-error classifier can therefore mark the run failed.
6. A batch without refusals has no refusal failure marker.

See [data-model.md](data-model.md) for state transitions and
[research.md](research.md) for the marker decision.
