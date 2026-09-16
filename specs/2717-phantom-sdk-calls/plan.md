# Implementation Plan: Phantom Mist SDK Calls

**Branch**: `fix/2717-phantom-sdk-calls` | **Date**: 2026-09-15 | **Spec**: `specs\2717-phantom-sdk-calls\spec.md`

**Input**: Feature specification from `specs\2717-phantom-sdk-calls\spec.md`

## Summary

Replace five nonexistent Mist SDK site lookups with the installed `getSiteInfo` route. Adjust each caller for a single-site response. Replace silent fallback handlers with error logs for API faults and SDK drift.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: `mistapi` 0.64.0, pytest, ruff, black, mypy, radon

**Storage**: Not applicable. The change reads mocked API responses only.

**Testing**: Unit tests with mocked Mist sessions and no live Mist API calls.

**Target Platform**: Windows local development and the existing MistHelper runtime targets.

**Project Type**: Python CLI and library code.

**Performance Goals**: Use one direct site lookup per caller. Do not page all organization sites.

**Constraints**: Do not import `MistHelper` from `src`. Do not edit vendor API records.

**Scale/Scope**: Five call sites, their unit tests, SpecKit artifacts, and one release-note fragment.

## Constitution Check

- Five-Item Rule: This is a surgical edit to existing files. It does not add a new child to a noncompliant parent.
- Class-Based Architecture: The change edits methods that already live inside semantic classes.
- Safety-First: No live API request occurs during tests. No destructive operation changes.
- Full Deployment Pipeline: Local gates, pull request checks, and merge verification apply.
- Observability & Logging: Each repaired handler logs before lookup, logs after lookup, and logs fault context.

## Project Structure

### Documentation

```text
specs\2717-phantom-sdk-calls\
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src\
├── device\virtual_chassis.py
├── export\site_anomaly_exporter.py
├── export\site_insights\device_metric_operation.py
├── export\site_insights\site_metric_operation.py
└── refactors\serial_cc\site_client_insights.py

tests\
└── unit\
    ├── test_virtual_chassis.py
    ├── export\test_site_anomaly_exporter.py
    ├── export\site_insights\test_device_metric_operation_wave3.py
    ├── export\site_insights\test_site_metric_operation_wave9.py
    └── serial_cc\test_site_client_insights.py

changelog.d\
└── issue-2717-phantom-sdk-calls.md
```

**Structure Decision**: Use the existing modules and tests because the defect is isolated to existing methods.

## Changed Files

- `src\device\virtual_chassis.py`: Replace `sites.getSite` with `sites.sites.getSiteInfo`.
- `src\export\site_anomaly_exporter.py`: Replace `sites.listSites` with `sites.sites.getSiteInfo`.
- `src\export\site_insights\device_metric_operation.py`: Replace `sites.listSites` with `sites.sites.getSiteInfo`.
- `src\export\site_insights\site_metric_operation.py`: Replace `sites.listSites` with `sites.sites.getSiteInfo`.
- `src\refactors\serial_cc\site_client_insights.py`: Replace `sites.listSites` with `sites.sites.getSiteInfo`.
- `tests\unit\test_virtual_chassis.py`: Prove the virtual chassis path returns the known site name.
- `tests\unit\export\test_site_anomaly_exporter.py`: Prove the anomaly path returns the known site name.
- `tests\unit\export\site_insights\test_device_metric_operation_wave3.py`: Prove the device metric path returns the known site name.
- `tests\unit\export\site_insights\test_site_metric_operation_wave9.py`: Prove the site metric path returns the known site name and reports a fault.
- `tests\unit\serial_cc\test_site_client_insights.py`: Prove the serial client insights path returns the known site name.
- `changelog.d\issue-2717-phantom-sdk-calls.md`: Record the user-visible fix.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing broad modules remain large | The issue requires a surgical repair | A module split would exceed the issue scope |
