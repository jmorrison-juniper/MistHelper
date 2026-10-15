# Quickstart: Count Catalog Completeness

## Prerequisites

Use the bootstrapped repository environment. The environment must contain mistapi 0.64.1.

## Validation

Run the focused count exporter tests:

```sh
.venv/bin/python -m pytest -q tests/unit/export/test_count_exporter.py
```

The SDK catalog test must pass. The operation resolution and signature tests must include both added organization counts. The persistence strategy test must preserve the fingerprint composite key and verify the variable count strategy.
