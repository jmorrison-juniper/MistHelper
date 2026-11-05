# Local close validation

Use the isolated worktree environment. No Mist credential is required.

Run the portable regression:

```text
.venv/bin/python -m pytest tests/unit/websocket_streams/live/transport/runtime/lifetime --no-cov -q
```

Run the existing live transport tests:

```text
.venv/bin/python -m pytest tests/unit/websocket_streams/live --no-cov -q
```

Both commands must pass without changes to existing test bounds or final-state assertions.
The session-only native reproduction provides additional macOS evidence.
It is not a repository test dependency.
