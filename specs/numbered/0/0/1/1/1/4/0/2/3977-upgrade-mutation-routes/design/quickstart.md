# Quickstart: Upgrade Mutation Routes

## Prerequisites

Use the repository virtual environment. Do not set production credentials for these tests.

## Validate the change

Run the focused checks from the repository root:

```bash
python -m pytest tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py
python -m pytest tests/integration/upgrade_portal/issue_3834
python -m pytest tests/integration/upgrade_portal/issue_3977
```

Each test must use fake sessions, services, and stores. A passing result must show that missing dependencies and failed guards prevent every mutation call.
