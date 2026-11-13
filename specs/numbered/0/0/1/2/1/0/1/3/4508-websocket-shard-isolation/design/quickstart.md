# Validation Instructions

If the environment is absent, run `python3 scripts/bootstrap_worktree.py`.
Use the worktree interpreter for each command.

Run the focused journey:

```text
.venv/bin/python -m pytest tests/e2e/websockets_tab/test_websockets_terminal.py::test_review_18_session_switch_drops_pending_paste -q --browser chromium
```

Expect both the normal and controlled cases to pass.

Run the offline shard:

```text
.venv/bin/python -m pytest tests/e2e/websockets_tab -q --browser chromium --tracing retain-on-failure --screenshot only-on-failure
```

Expect every test to pass without a retry.
Keep failure evidence in `test-artifacts/`.
Follow the repository test-quality procedure after the scoped commit and before the push.
