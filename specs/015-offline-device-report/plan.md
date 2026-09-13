# Implementation Plan: Offline Device Report

**Branch**: `015-offline-device-report` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-offline-device-report/spec.md`

## Summary

Add menu operation 158 that scans the entire Mist org inventory via `listOrgDevicesStats` (type="all", status="all"), filters to devices offline beyond a user-configurable threshold (default 48h), resolves site names via `listOrgSites` lookup dict, displays a summary + PrettyTable on screen, and saves a human-readable CSV with timestamped filename to `data/`. The feature is a new class `OfflineDeviceReporter` following the class-based architecture pattern, registered as `safe` in `OperationRegistry`.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `mistapi` 0.59+ (API access), `PrettyTable` (screen display), `csv` (stdlib, CSV output)
**Storage**: CSV to `data/OfflineDeviceReport_YYYYMMDD_HHMMSS.csv`; SQLite via `DataExporter.write_with_format_selection()` (dual output)
**Testing**: `pytest` (unit tests in `tests/unit/`), `python MistHelper.py --test` (integration)
**Target Platform**: Windows 11 (local dev), Linux containers (production)
**Project Type**: CLI menu operation within monolithic `MistHelper.py`
**Performance Goals**: Complete scan + display in <60s for 10,000 devices (SC-001)
**Constraints**: Single `listOrgDevicesStats` call + single `listOrgSites` call (2 API calls total). Screen display capped at 50 rows.
**Scale/Scope**: Orgs up to 10,000+ devices. Single new class (~150 lines), menu wiring, OperationRegistry entry.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | New class `OfflineDeviceReporter` with ~5 methods (each <25 lines, <5 params). No new packages/directories. |
| II. Class-Based Architecture | PASS | All logic in `OfflineDeviceReporter` class. No standalone wrappers. Full-word naming throughout. |
| III. Safety-First | PASS | Read-only operation. Threshold input uses `safe_input()` with validation (1-8760 hours). No destructive actions. No secrets logged. |
| IV. Full Deployment Pipeline | PASS | Standard workflow: py_compile, commit, push, CI build, pull, restart. |
| V. Observability & Logging | PASS | ASCII-only logging at debug/info/error levels. Progress messages for user feedback. |
| Tech Constraints: mistapi | PASS | Uses `mistapi.api.v1.orgs.stats.listOrgDevicesStats()` -- no direct HTTP. |
| Tech Constraints: Dual Output | PASS | Uses `DataExporter.write_with_format_selection()` for CSV/SQLite. |
| Tech Constraints: PK Strategy | PASS | Existing `listOrgDevicesStats` PK strategy already defined (composite: `device_id`, `timestamp`). |
| Tech Constraints: Data Directory | PASS | CSV output to `data/` via `FilePathUtils.get_csv_path()`. |
| Dev Workflow: Menu Operation | PASS | Follows 7-step menu op workflow. PK strategy exists. README + changelog updated. |

**Gate result: ALL PASS** -- no violations, no Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/015-offline-device-report/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
MistHelper.py            # New class OfflineDeviceReporter + menu entry "158" + OperationRegistry entry
tests/unit/              # Unit tests for OfflineDeviceReporter
README.md                # Updated menu table + operation count + changelog
```

**Structure Decision**: This feature adds a single class to the monolithic `MistHelper.py` file, consistent with all other menu operations. No new packages, modules, or directories. Menu dispatch dict gets entry `"158"`, OperationRegistry gets `safe` classification.
