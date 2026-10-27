# Validation

Create the worktree environment with `python3 scripts/bootstrap_worktree.py`.
Activate it with `source .venv/bin/activate`.

Run the regression:

```sh
python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py -q
```

Run the existing behavior checks:

```sh
python -m pytest tests/unit/web_portal/test_event_bus_deadlock.py tests/unit/web_portal/test_portal_stream_thread_release.py tests/e2e/web_portal/test_portal_smoke.py -q
```

Expect one executor per application and unchanged HTTP responses.
Temporarily replace the helper with its original implementation in memory.
Confirm that the forced-race regression fails, then restore the helper.
