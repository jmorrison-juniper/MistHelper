# Quickstart: Capture Request Dependencies

**Feature**: [spec.md](../spec.md)

## Prerequisites

- Use the repository development environment.
- Keep Mist and database access blocked in the focused tests.

## Validate

Run the new regression test and the existing request-provider tests:

```bash
python -m pytest -q tests/integration/upgrade_portal/issue_4653 tests/integration/upgrade_portal/issue_3834 tests/integration/upgrade_portal/issue_3977 tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py
```

Expected result: all tests pass. The new test must prove that the normal factory binds the capture service to fake request resources and makes no live request.

Do not run a firmware upgrade or connect to a production store.
