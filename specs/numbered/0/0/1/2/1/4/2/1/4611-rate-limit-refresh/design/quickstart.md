# Quickstart: Verify Rate Limit Refresh

**Feature**: [spec.md](../spec.md)

## Prerequisites

- Use Python 3.13 or newer.
- Bootstrap the worktree with `python3 scripts/bootstrap_worktree.py` if `.venv` is absent.

## Focused Validation

Run the rate-limit unit tests:

```shell
.venv/bin/python -m pytest tests/unit/test_rate_limiting.py -q
```

The command passes when failed 4xx and 5xx responses preserve the cache, successful responses update it, and all tests make no live Mist request.
