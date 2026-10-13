# WAN Dashboard Validation Guide

Use synthetic Mist responses for local checks. Do not use a production token in a test.

## Prerequisites

- Python 3.13 or newer.
- The MistHelper test environment and dependencies.
- The MistHelper repository root as the current directory.
- No live Mist, Snowflake, or additional Redis service.

## Prepare the Local Environment

```bash
python3 scripts/bootstrap_worktree.py
source .venv/bin/activate
```

The bootstrap installs the project requirements and downloads the browser used by end-to-end tests.

## Validate the Dashboard

Run the dashboard integration tests:

```bash
python -m pytest tests/integration/web_portal/wan_dashboard
```

Run the portal end-to-end test that includes the dashboard journey:

```bash
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

Run the portal and SDK regression tests:

```bash
python -m pytest tests/e2e tests/integration/test_mistapi_sdk_compatibility.py
```

## Expected Results

- The dashboard appears in the current portal navigation.
- Synthetic gateway, port, peer-path, traffic, and SLE data appear in the correct views.
- The filters cover the complete paginated test fixture.
- Each supported traffic and insight range uses its expected time window.
- The hourly CSV has the documented 12-column header and matches the selected rows.
- Rate limits and API errors show clear status. A prior successful result remains visible when available.
- No new service, database, or published port appears in the compose configuration.

See [the interface contract](contracts/wan-dashboard.md) and [the data model](data-model.md) for test assertions and record fields.
