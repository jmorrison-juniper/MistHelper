# Implementation Plan: E911 BSSID Compliance Report

**Branch**: `182-e911-bssid-report` | **Date**: 2026-04-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/182-e911-bssid-report/spec.md`

## Summary

New Menu 160 operation: generates a CSV/SQLite report mapping every AP BSSID to its physical location (site name, site address, floor/map name, AP name) across the entire Mist organization for E911 compliance. Uses the purpose-built `listOrgApsMacs` endpoint to retrieve radio base MACs, derives 16 BSSIDs per radio by enumerating the last nibble, and joins with site/device/map data via in-memory lookup dictionaries. Follows the `OfflineDeviceReporter` (Menu 158) class pattern.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (Mist API SDK)
**Storage**: CSV (primary) + SQLite (`data/mist_data.db`) via `DataExporter`
**Testing**: pytest + `--test` mode (safe category, fully automated)
**Target Platform**: Windows 11 (dev), Linux containers (prod)
**Project Type**: CLI menu operation within monolithic `MistHelper.py`
**Performance Goals**: Complete report for 10,000 APs in under 2 minutes
**Constraints**: Rate-limited API calls via adaptive delay; all output to `data/` directory
**Scale/Scope**: Single class (~150 lines), 4 API lookups, single file edit + README update

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | Class has 5 static methods: `execute`, `_fetch_lookups`, `_build_bssid_rows`, `_display_summary`, `_format_bssid`. All under 25 lines. |
| II. Class-Based (No Wrappers) | PASS | All logic in `E911BSSIDReportGenerator` class. No standalone wrapper functions. |
| III. Safety-First | PASS | Read-only operation. No user input required. No destructive actions. No secrets logged. |
| IV. Full Deployment Pipeline | PASS | Will execute complete pipeline after implementation. |
| V. Observability & Logging | PASS | ASCII-only logging at info (progress) and debug (API response counts) levels. |
| Technology Constraints | PASS | Uses mistapi SDK, dual output via DataExporter, natural PK in ENDPOINT_PRIMARY_KEY_STRATEGIES. |
| New Menu Operation Workflow | PASS | All 7 steps followed: API discovery, PK strategy, flatten, dual output, README, changelog, pipeline. |

**Post-Design Re-Check**: All gates still PASS. No clarifications remain.

## Project Structure

### Documentation (this feature)

```text
specs/182-e911-bssid-report/
├── plan.md              # This file
├── research.md          # Phase 0: API research and decision log
├── data-model.md        # Phase 1: Entity model and lookup dictionaries
├── quickstart.md        # Phase 1: Usage guide
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # Add E911BSSIDReportGenerator class, menu_actions entry,
                         # OperationRegistry entry, ENDPOINT_PRIMARY_KEY_STRATEGIES entry
README.md                # Update menu table and operation count
```

**Structure Decision**: Single-file modification pattern. MistHelper is a monolithic ~28K line Python file. The new class is added inline following existing conventions (near other org-level exporters). No new files or directories needed beyond the spec artifacts.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
