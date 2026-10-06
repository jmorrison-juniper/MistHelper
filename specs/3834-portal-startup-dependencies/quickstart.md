# Quickstart: Verify portal startup dependencies

Run the focused tests:

```bash
python -m pytest -q tests/integration/upgrade_portal/issue_3834
```

Run related route and wiring tests:

```bash
python -m pytest -q \
  tests/unit/upgrade_portal/test_phase2_service_wiring.py \
  tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py \
  tests/unit/upgrade_portal/test_comparison_routes.py
```

Run the changed-file quality checks from `.github/copilot-instructions.md`.

Confirm the final path list:

```bash
git diff --name-only 92d2e25^
```

The list must contain only the approved production, test, specification,
documentation, and changelog paths.
