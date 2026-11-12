# Offline validation

Use the worktree environment created by `python3 scripts/bootstrap_worktree.py`.

```sh
.venv/bin/python -m pytest -q tests/guardrails/e2e_timeout_budget tests/guardrails/test_e2e_shard_partition.py tests/guardrails/test_ci_runtime_budgets.py tests/guardrails/test_ci_gate_triggers.py
.venv/bin/python -m ruff check tests/guardrails/e2e_timeout_budget/test_browser_installation.py
.venv/bin/python -m black --check tests/guardrails/e2e_timeout_budget/test_browser_installation.py
```

The setup tests execute the embedded workflow program against temporary files.
They require no administrator access, apt installation, network request, or production credential.
The tests must retain the original file on every rejected input or backup failure.
The mutation tests must reject removal of required browser installation.

Read [research.md](research.md) for measured failure evidence and the limits of local validation.
Do not retry CI to collect another timing sample.
