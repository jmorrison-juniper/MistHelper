# Quickstart: Mist Organization Licensing Comparison

**Date**: 2026-10-13
**Feature**: [spec.md](spec.md)

This guide defines validation for the planned integration. It does not start or deploy the feature.

## Prerequisites

- Use Python 3.13 or newer and the repository virtual environment.
- Use synthetic Mist responses. Do not use a production credential.
- Read the route and data shapes in [the interface contract](contracts/licensing-comparison.md).

## Validate the Service

Run the planned focused tests:

```bash
python -m pytest tests/integration/web_portal/licensing_comparison/test_service.py tests/integration/web_portal/licensing_comparison/test_routes.py tests/integration/web_portal/licensing_comparison/test_export.py
```

Expected result: the tests pass for authorized organizations, manual values, purchased values, SUB-AI components, request failures, and CSV output.

## Validate Mist SDK Calls

Run the existing SDK contract test:

```bash
python -m pytest tests/unit/web_portal/test_portal_sdk_calls.py
```

Expected result: each new Mist SDK call resolves in the installed `mistapi` package. Add 4xx and 5xx cases to the focused route tests.

## Validate the Portal Page

Run the existing Flask end-to-end smoke tests:

```bash
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

Expected result: the feature page returns a success response, its controls have stable selectors, and its navigation link appears.

## Validate the Export

Use synthetic comparison rows that include a manual organization, a SUB-AI component, a missing value, and a formula-like cell.

Expected result: the downloaded CSV matches the displayed rows, preserves unavailable values, and neutralizes formula-like text.

## Deployment Boundary

Do not start a new server, database, Redis service, or public port for this feature. Use the existing MistHelper Flask portal and compose group after implementation.
