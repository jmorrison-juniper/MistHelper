# Feature Specification: Reduce Operations Portal Output Scan Cost

## Problem

After each operation, the portal scans the full data folder. It finds files that the operation wrote. The scan takes most of the run time on the Windows OneDrive bind mount.

## Evidence

- Full scan median run time: 10.4 seconds.
- Full scan median handler time: 1.5 seconds.
- Full scan median scan time: 8.2 seconds.
- Full scan maximum scan time: 33 seconds.
- Local probe on the shared container: 7.4 seconds cold and 6.0 seconds warm.
- Detailed probe: file `stat()` calls dominate the cost.

## Acceptance Criteria

1. The scanner finds files that are created during a run.
2. The scanner finds files that are overwritten in place during a run.
3. The scanner finds existing files that untracked writers change.
4. The scanner never prunes `per-host-logs`.
5. The scanner keeps runtime files out of the result panel.
6. The existing output scan tests stay green.
7. A guard test fails on the old full-stat scan and passes on the new scan.
8. The container probe shows a lower cold and warm scan time.
9. A run with no fast-path result pays the old pruned full-scan cost.

## Out of Scope

- Changes to `web_portal/services/operation.py`.
- Changes to destructive operations.
- Container deployment.
- Application concurrency changes.
