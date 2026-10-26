# Validation guide

Use the worktree environment from `scripts/bootstrap_worktree.py`.
Run browser tests with screenshots, tracing, and video disabled.

```text
.venv/bin/python -m pytest tests/e2e/web_portal/result_truncation_notice --tracing off --screenshot off --video off
.venv/bin/python -m pytest tests/unit/web_portal/result_truncation_notice
node --check web_portal/static/js/operation_results.js
```

Before implementation, the clipped-cell notice assertion must fail against unchanged JavaScript.
After implementation, the same assertion and the short control must pass.
The tests must preserve complete values, native pagination, details, sorting, and downloads.
Run `tests/guardrails/test_e2e_shard_partition.py` to confirm that CI collects the browser tests.
