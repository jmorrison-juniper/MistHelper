# Implementation Plan: mistapi signature mismatch repair

**Branch**: `fix/2741-signature-mismatch` | **Date**: 2026-09-16 | **Spec**: `specs/2741-signature-mismatch/spec.md`

**Input**: Feature specification from `specs/2741-signature-mismatch/spec.md`

## Summary

Repair two call sites that do not match `mistapi` 0.64.0. Add tests that prove the SDK arguments and evidence output.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: `mistapi` 0.64.0, Flask, pytest, ruff, black, mypy.
**Storage**: No schema change. Reconciliation keeps existing safe evidence records.
**Testing**: Unit tests, integration SDK compatibility guard, and existing local gates.
**Target Platform**: Windows development. Runtime supports host and container use.
**Project Type**: Python CLI plus Flask portal.
**Performance Goals**: Keep call volume unchanged. One reconciliation read remains one paged site statistics request.
**Constraints**: Do not edit `MistHelper.py`. Do not edit vendor API documentation.
**Scale/Scope**: Two source files, two unit test files, one specification folder, and one release-note fragment.

## Constitution Check

- Five-Item Rule: This surgical repair edits existing files and adds one contained test file.
- Class-Based Architecture: New behavior stays inside `CLIShellManager` and `SiteStatsFirmwareEvidenceReader`.
- Safety-First: The repair makes no live Mist API request during tests.
- Full Deployment Pipeline: Local gates, pull request checks, and merge verification are required.
- Observability: The changed cloud reads log before and after their actions.

## Project Structure

### Documentation

```text
specs/2741-signature-mismatch/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src/
├── ssh/cli_shell_manager.py
└── upgrade_portal/api/run_controls/routes.py

tests/
├── unit/ssh/test_cli_shell_manager.py
├── unit/upgrade_portal/test_site_stats_evidence_reader.py
└── integration/test_mistapi_sdk_compatibility.py

changelog.d/
└── issue-2741-signature-mismatch.md
```

**Structure Decision**: Edit the existing feature owners. Do not add a wrapper, a shim, or a new package.

## Complexity Tracking

No constitution violation is required for this repair.

## Call-Site Audit

The installed `listSiteDevicesStats` signature is `mist_session, site_id, type=None, status=None, limit=None, page=None`.

| File | Verdict |
| - | - |
| `src/export/site_device_exporter.py` | Valid. It passes session, site ID, `type`, and `limit`. |
| `src/firmware/bulk_ap_upgrader.py` | Valid. It passes session, site ID, `type`, and `limit`. |
| `src/firmware/firmware_manager.py` line 682 | Valid. It passes session, site ID, `type`, and `limit`. |
| `src/firmware/firmware_manager.py` line 3519 | Valid. It passes session, site ID, `type`, and `limit`. |
| `src/gateway/gateway_ha_exporter.py` | Valid. It passes session, site ID, and `type`. |
| `src/maps/_maps_coverage.py` | Valid. It passes session, site ID, `type`, and `limit`. |
| `src/maps/launcher/_viewer_site_switch.py` | Valid. It passes session, site ID, and `limit`. |
| `src/maps/launcher/_viewer_url_switch.py` | Valid. It passes session, site ID, and `limit`. |
| `src/maps/maps_manager.py` | Valid. It passes session, site ID, and `limit`. |
| `src/upgrade_portal/api/run_controls/routes.py` | Repaired. It no longer passes `fields`. |
