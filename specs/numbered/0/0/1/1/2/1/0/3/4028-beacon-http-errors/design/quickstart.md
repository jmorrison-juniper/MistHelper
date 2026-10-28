# Validation guide

Use the bootstrapped worktree environment. No Mist credential is required.

Run `.venv/bin/python -m pytest tests/unit/export/test_site_client_exporter.py -q`.

All cases must pass. The returned-error cases must assert no exporter call and an explicit failure message.
The returned-success cases must assert the exact rows, filename, and endpoint metadata.
The retry cases must assert the request count and adaptive delay.

Run `.venv/bin/python -m ruff check src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py`.
Run `.venv/bin/python -m black --check src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py`.

Each command must exit zero. Use the [response contract](contracts/beacon-response.md) for expected behavior.
