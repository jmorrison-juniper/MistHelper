# Offline verification

Use the existing locked local environment.
Do not run bootstrap, load credential files, or use a production database.

The session `issue4718/offline_checks.py` runner blocks socket, DNS, and SQLite calls.
It reports every attempt, including exceptions caught by the exporter.

```text
.venv/bin/python <session-files>/issue4718/offline_checks.py tests/unit/export/test_org_webhook_deliveries_exporter.py -q
```

Add `--previous` to load source from the preserved #4715 commit.
The new rejection cases must fail against that source.
The repaired source must pass both the repository tests and the independent coordinator cases.

The session evidence contains exact commands, outputs, committed bytes, and hashes.
