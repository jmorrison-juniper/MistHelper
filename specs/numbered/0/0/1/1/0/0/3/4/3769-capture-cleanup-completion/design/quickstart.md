# Cleanup-order verification

Use the worktree Python environment.

```bash
python3 scripts/bootstrap_worktree.py
source .venv/bin/activate
python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py
python -m pytest -q tests/unit/websocket_streams/live/runners/utility
```

Before the repair, the four barrier cases must fail because terminal state precedes DELETE.
After the repair, all barrier cases must pass.
The existing live utility test must remain unchanged.

See [the plan](../plan.md) for the remaining local gates.
No production credential or external cloud is required.
