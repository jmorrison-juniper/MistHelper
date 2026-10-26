# Verify cleanup completion

Use the worktree environment. If it is absent, run `python3 scripts/bootstrap_worktree.py`.

Run the barrier cases before the repair:

```text
.venv/bin/python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py -k terminal_waits_for_matching_cleanup
```

Expect two assertion failures with unchanged source.
See [the evidence](research.md) for the measured baseline.

After the repair, run both the new module and the unchanged utility tests:

```text
.venv/bin/python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py
```

Expect no failure. The new module checks the ordering and outcomes described in [the lifecycle model](data-model.md).
All requests use the controlled loopback service.
