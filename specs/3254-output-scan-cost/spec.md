# Feature Specification: Reduce Operations Portal Output Scan Cost

## Problem

After each operation, the portal scans the full data folder to find files that the operation wrote. The measured scan takes most of the run time on the Windows OneDrive bind mount.

## Evidence

- Full sweep median run time: 10.4 seconds.
- Full sweep median handler time: 1.5 seconds.
- Full sweep median scan time: 8.2 seconds.
- Full sweep maximum scan time: 33 seconds.
- Local probe on the shared container: 7.4 seconds cold and 6.0 seconds warm.
- Detailed probe: file `stat()` calls dominate the cost.

## Acceptance Criteria

1. The scanner finds files that are created during a run.
2. The scanner finds files that are overwritten in place during a run.
3. The scanner never prunes `per-host-logs`.
4. The scanner keeps runtime files out of the result panel.
5. The existing output scan tests stay green.
6. A guard test fails on the old full-stat scan and passes on the new scan.
7. The container probe shows a lower cold and warm scan time.

## Out of Scope

- Changes to `web_portal/services/operation.py`.
- Changes to destructive operations.
- Container deployment.
- Application concurrency changes.
