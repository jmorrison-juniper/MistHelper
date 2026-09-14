# Feature Specification: Top-20 Compliance Violations Remediation

**Status**: Superseded on 2026-09-14.

Issue #1003 used an old top-20 list. The current analyzer output supersedes it. Evidence: `rtk python tools/check_compliance.py src\maps\maps_manager.py` reports 100.0 A+, while this plan listed that file as 54.0 F. Use `specs\1009-compliance-backlog-remediation` for the active backlog.

## Current disposition

This specification closes as reconciled. Remaining structural debt moves to the follow-up issue created from the 1009 analysis.
