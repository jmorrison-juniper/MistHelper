# Offline validation

Run `.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q`.

The environment already exists from #1794.
Tests block DNS and sockets and replace the HTTP session and writer.
Use real SDK response objects, not a response double with an invented status.
Verify initial 403 and 503, later empty-body 503, complete pagination, and valid empty results.
Use [the menu contract](contracts/menu.md) for all expected outcomes.
