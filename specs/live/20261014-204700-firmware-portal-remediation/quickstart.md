# Validation guide

Use the worktree environment. Do not use production credentials.

```text
.venv/bin/python -m pytest tests/unit/firmware_policy tests/contract/firmware_policy tests/integration/firmware_policy
.venv/bin/python -m pytest tests/e2e/web_portal/test_firmware_policy.py
```

Run the related restoration browser tests and changed portal integration tests.
Use a fixture server for screenshots and snapshots. Commit only the small sanitized evidence set.
Verify both desktop columns, dynamic version visibility, numerical ordering, defaults, and the backup-before-confirmation sequence.
Verify more than 4,000 targets and a backup above 17,402,805 bytes.
Check malformed, tampered, partial, foreign-session, stale-target, and private-access failures.

The parent performs connected acceptance. Do not claim Windows or human acceptance from fixture tests.
