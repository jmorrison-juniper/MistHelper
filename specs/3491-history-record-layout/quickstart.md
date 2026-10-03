# Verification: Compact history records

Use the owned Python 3.13 environment.
Set `UPGRADE_PORTAL_E2E_STRICT=1`.
Set `UPGRADE_PORTAL_E2E_PORTS` to available ports from 9600 through 9699.
Keep browser tracing, screenshots, and video off for functional execution.

```bash
rtk proxy .venv/bin/python -B -m pytest \
  tests/e2e/upgrade_portal/test_history_record_layout_journey.py \
  tests/contract/upgrade_portal/test_history_record_layout_assets.py \
  --tracing=off --screenshot=off --video=off -p no:cacheprovider
```

For a separate controlled screenshot run, set `HISTORY_RECORD_LAYOUT_EVIDENCE` to an owned absolute artifact directory.
The new journey saves browser measurements there.
It saves screenshots only when `HISTORY_RECORD_LAYOUT_SCREENSHOTS=1`.
Inspect every required image after capture.
Do not publish screenshots or server logs.

Run the unchanged adjacent history tests and current source gates.
Compare all original browser identifiers, markers, fixture lifetimes, and baseline skips.
Verify the actual wheel, source distribution, and native asset response.
Prepare the complete pull request template offline.
Stop after the clean unpublished commit and local-only handoff.
