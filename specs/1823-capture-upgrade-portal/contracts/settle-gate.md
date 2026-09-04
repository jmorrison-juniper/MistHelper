# Settle Gate Contract: Capture Upgrade Portal (Issue #1823)

This document defines post-upgrade validation algorithm, timing, and recovery.

## Algorithm

Settle gate runs after UpgradeService completes. Runs 4 checks in parallel:

1. Reachability Check (ICMP ping)
   - Timeout: 5 seconds per attempt
   - Retry: Every 10 seconds for up to 5 minutes
   - Pass: Any response

2. API Responsiveness Check
   - Timeout: 10 seconds per attempt
   - Retry: Every 10 seconds for up to 5 minutes
   - Pass: HTTP 200 with valid response

3. Firmware Version Check
   - Expected: Matches target firmware from upgrade_runs
   - Timeout: 10 seconds per attempt
   - Retry: Every 10 seconds for up to 5 minutes

4. LLDP Neighbor Check
   - Expected: Same neighbors present (tolerates dynamic)
   - Timeout: 10 seconds per attempt
   - Retry: Every 10 seconds for up to 5 minutes

## Success Criteria
All four checks pass for all devices within 5 minutes.

## Failure Criteria
One or more checks fail after 5 minutes of retries.

## Comparison Validation
Settle gate success is prerequisite for ComparisonService.
