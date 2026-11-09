# Offline validation

If dependencies are absent, run `uv sync --locked --extra dev` in this worktree.

Run `.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q`.

On Windows, use `.venv\Scripts\python.exe` instead.

The tests block DNS and sockets and replace the exporter and HTTP session.
Use [the menu contract](contracts/menu.md) for expected behavior.
Do not supply production credentials or start external services.
