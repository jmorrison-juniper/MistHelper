# Validation guide

Use the isolated worktree.

```text
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
```

Run the strict command from [the plan](../plan.md).
Require three analyzed files with zero errors and zero warnings.
Run focused tests with `.venv/bin/python -m pytest`.
Run applicable standard gates against the explicit changed-file manifest.
Read [the entry-point contract](contracts/entrypoint.md) before interpreting results.
Do not run production menus.
