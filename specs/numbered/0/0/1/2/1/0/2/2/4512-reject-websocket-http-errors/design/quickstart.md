# Validation guide

Run `python3 scripts/bootstrap_worktree.py` if the worktree has no environment.

Run `.venv/bin/python -m pytest tests/unit/websocket/test_service_ping_discovery.py tests/unit/websocket/test_service_ping_manager.py`.

Expect all tests to pass without network access.
The status matrix must reject client errors, server errors, redirects, and missing statuses.
Successful responses must preserve exact sorted cache contents.

See [the response model](data-model.md) for cache behavior.
