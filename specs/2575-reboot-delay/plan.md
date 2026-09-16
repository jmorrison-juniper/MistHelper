# Implementation Plan: Multi-Site Reboot Delay

**Issue**: #2575
**Branch**: `fix/2575-reboot-delay`
**Date**: 2026-09-16
**Spec**: [spec.md](./spec.md)

## Summary

The multi-site upgrade options page adds the same reboot delay control that the
single-site page already has. The route reads `reboot_at`, validates it with the
single-site option mapper, and stores the operator duration. The aggregate
service stores the converted epoch seconds on every selected switch and gateway
site child.

## Technical Context

**Language**: Python 3.13, Jinja, HTML.

**Dependencies**: Flask, Flask-WTF, mistapi 0.64.0, pytest, Ruff, Black, mypy,
and Radon. No new dependency is added.

**Storage**: Existing signed Flask session for options and existing run store
for aggregate operations. No schema changes.

**Testing**: Pytest unit tests and contract tests under `tests/unit` and
`tests/contract`.

**Target Platform**: Windows development and the existing Linux container.

**Project Type**: Flask web portal inside the MistHelper Python project.

**Performance Goal**: The new validation runs during option save and adds no
cloud call.

**Safety Constraints**: Invalid and past delay values fail closed. Empty delay
keeps current behavior. The service sends no AP reboot delay.

**Scale**: The aggregate operation can include many selected sites. The delay
must apply to each selected site child.

## Constitution Check

| Principle | Design result |
| - | - |
| I. Five-Item Rule | The change is a surgical edit to existing noncompliant route, service, and template files. It adds no new child directory. |
| II. Class-Based Architecture | `OrgUpgradeScheduleReader` owns the new route validation logic. |
| III. Safety-First | The route validates the delay before confirmation and before any cloud write. |
| IV. Full Deployment Pipeline | The branch uses a worktree, local gates, a pull request, and required checks. |
| V. Observability | The route logs before and after schedule validation. |
| VI. Inline Comments | New Python lines carry inline comments. |
| VII. Action Logging | New route actions have before and after logs. |

## File Plan

| File | Change |
| - | - |
| `src/upgrade_portal/app/assets/templates/upgrade/org_options.html` | Add the `reboot_at` form control with a stable `data-testid`. |
| `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html` | Show the reboot delay when the operator set it. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | Read, validate, store, and display `reboot_at`. |
| `src/firmware/aggregate_upgrade_service.py` | Store the converted `reboot_at` epoch seconds on each non-AP site child. |
| `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | Add offline route, form, confirmation, validation, and aggregate service tests. |
| `changelog.d/issue-2575-reboot-delay.md` | Add the release note fragment. |

## Architecture

The route keeps the form value as the operator wrote it. The existing
single-site option mapper converts that value into epoch seconds during the
aggregate option build. The aggregate service then uses the existing site
planner, which already puts `reboot_at` into switch and gateway request bodies.

The aggregate service copies the converted field onto each site child. This
makes the durable record explicit and keeps the same field name and units as the
cloud request body.

## Interaction With Issue #2644

This change does not repair the site lock lifetime mismatch. A long multi-site
reboot delay can still outlive the twelve hour site lock. The issue #2644 fix
must add the lock-aware ceiling or stop rule after this change.

## Validation Plan

Run these commands in the issue worktree:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m radon cc src/ MistHelper.py wsgi.py starlink_dashboard.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -nc
python -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -q
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Surgical edit to existing large route module | The defect lives in the current route contract. | A new route would duplicate the existing workflow. |
| Surgical edit to existing aggregate service | The durable child record belongs to the current aggregate planner. | A second service would create two reboot scheduling mechanisms. |
