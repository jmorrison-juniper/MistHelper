# Quickstart: WAN Probe Response Status

## Prerequisites

Build the worktree environment with `python3 scripts/bootstrap_worktree.py`.

## Validate

Run the focused tests:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/gateway/test_wan_probe_device_override_manager.py \
  tests/unit/gateway/test_wan_probe_override_pipeline.py \
  tests/unit/refactors/test_wan_probe_device_override_manager.py
```

The 403 test must report a failed result and no device update call. The HTTP 200 test must retain the successful update result.
