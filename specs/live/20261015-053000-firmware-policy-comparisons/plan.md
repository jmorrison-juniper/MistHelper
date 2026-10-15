# Implementation Plan: Firmware policy comparisons

**Branch**: `jmorrison-juniper-firmware-policy-comparisons`
**Date**: 2026-10-15
**Spec**: [Specification](spec.md)

## Summary

Add one-scope comparisons to the existing authenticated settings routes.
Keep complete settings in private worker contexts and verified files.
Add historical inspection to recovery without restoration preparation.

## Technical Context

**Language/Version**: Python 3.13 and existing browser JavaScript.
**Primary Dependencies**: Flask, mistapi 0.64.0, existing JSON Schema validation.
**Storage**: Existing private bundles and sanitized job records.
**Testing**: pytest and Playwright with synthetic SDK transport.
**Target Platform**: Windows, macOS, Linux, and existing product container.
**Project Type**: Protected web portal.
**Performance Goals**: One requested scope per comparison, including 4,001 targets.
**Constraints**: No production access, complete immutable backups, no proof consumption.
**Scale/Scope**: Existing menus 305 and 306 only.

## Constitution Check

- Existing package debt remains unchanged. New modules enter the compliant
  `web_portal/routes/firmware_policy/restore/` package.
- Existing long manager and browser methods need narrow edits, not a broad rewrite.
  Extract comparison behavior into focused classes.
- Process folders have existing debt. Only unique feature records enter them.
  Incremental remediation remains the existing process-folder baseline ratchet.
- Product output remains under the configured data directory. Synthetic evidence
  uses ignored `test-artifacts/`.
- Every REST request uses mistapi and shared request admission.
- No new credential, environment variable, menu, write, or execution endpoint appears.
- Tests cover failed reads, pagination, privacy, ownership, immutability, and proof reuse.
- Draft PR uses Conventional Commits and preserves the repository template.
- Parent performs deployment and live acceptance. This child stops at a verified draft.

## Project Structure

```text
web_portal/routes/firmware_policy/restore/
  policies.py          firmware-only projection and field differences
  inspection.py        read-only historical and prepared-plan comparisons
  __init__.py          protected inspection routes
web_portal/routes/firmware_policy/jobs/
  manager.py           owner-checked local/remote comparison dispatch
web_portal/static/js/firmware-policy.js
web_portal/routes/firmware_policy/templates/firmware_policy.html
web_portal/routes/firmware_policy/restore/templates/firmware_restore.html
src/operations/execution/firmware_policy/sdk.py
tests/unit/firmware_policy_jobs/comparisons/
tests/integration/firmware_policy/recovery/comparisons/
tests/e2e/web_portal/test_firmware_policy.py
tests/e2e/web_portal/firmware_restore/evidence.py
.github/workflows/ci.yml
documentation/org-auto-upgrade-policy.md
documentation/backup-restoration.md
changelog.d/issue-4229-firmware-policy-comparisons.md
```

## Design

Prepared inspection resolves one row from a live owner-checked ready job.
It verifies the recovery bundle without consuming `BackupProof`, checks cloud
and current membership, then reads one complete current settings object.
It projects saved, current, and proposed effects through the supported schema.
Proposed values apply the already prepared body to a copy, including deletions.
Restoration also retains the source snapshot time and normalization notices.

Historical inspection validates an opaque bundle token and one record key.
It checks authenticated organization access and current membership before
returning saved firmware values. Current reads occur only on explicit comparison.
It rechecks source identity after reads. No plan, proof, or backup is created.

Rows report presence separately from values. Missing site policies say inherited.
Absent fields never receive invented defaults. Restoration defaults appear only
in proposed policy and explicit normalization notices.
Field cards repeat source labels and wrap paths and values at narrow widths.
The fixed-layout scope table does not acquire horizontal comparison scrolling.

The browser locks preparation on submission, ready status, and uncertain status.
It permits retry after a definite preparation-stage failure. Selection changes
explicitly invalidate the old plan. Application failures never trigger retries.
Phase-aware progress retains workflow phase through admission callbacks.
Browser evidence includes comparison screenshots and failed-flow traces in a dedicated artifact.
A live-workflow contract test rejects missing paths or capture arguments.

## Complexity Tracking

Existing manager and JavaScript classes exceed structural limits. This change
adds focused helpers and does not add direct children to their full packages.
Spec Kit's PowerShell setup command is unavailable on this host. The Bash setup
script is absent. Design artifacts therefore use the resolved local template directly.
The same host limitation applies to the analysis prerequisite command.
Analysis checked the feature JSON and read all three required artifacts directly.
