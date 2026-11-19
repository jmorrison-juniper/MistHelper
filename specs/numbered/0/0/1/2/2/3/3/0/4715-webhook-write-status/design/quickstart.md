# Local validation

Use an offline environment from the locked dependency cache.
Do not execute the bootstrap script.

Run the focused tests through the session `offline_checks.py` runner.
The runner blocks socket and DNS requests and disables environment-file loading.

```text
.venv/bin/python <session-files>/offline_checks.py tests/unit/export/test_org_webhook_deliveries_exporter.py -q
```

Add `--original` to load the assigned original source without changing the working file.
The two failed-writer regression cases must fail against that source.
All cases must pass against the repair.

The session evidence contains the exact commands, outputs, and committed file hashes.
