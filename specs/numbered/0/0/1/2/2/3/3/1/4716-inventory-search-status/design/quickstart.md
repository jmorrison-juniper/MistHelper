# Local Validation

Use the restored offline environment. Do not run a live menu or read a credential file.
Use the session `run_offline_checks.py` runner to block sockets, DNS, and credential-file loading before collection.

```text
.venv/bin/python <session-files>/run_offline_checks.py tests/unit/export/test_org_inventory_search_exporter.py -q
.venv/bin/python <session-files>/run_offline_checks.py --original-source tests/unit/export/test_org_inventory_search_exporter.py -q
```

The repaired source must pass every case.
The original source must fail the new request-status and writer-result regressions.
Both runs must record zero socket and DNS attempts.
The session command report preserves the exact resolved commands and their results.
