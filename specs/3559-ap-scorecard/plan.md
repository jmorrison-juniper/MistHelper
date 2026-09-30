# Implementation Plan: Organization Access Point Scorecard

**Branch**: `feat/3559-ap-scorecard` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3559-ap-scorecard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Menu `278` exports an organization access point scorecard from `listOrgDevicesStats` with `type=ap`. The design adds `src/reports/ap_scorecard/` with a client module, a pure model module, and an operation module. The operation uses `APIDataFetcher` or the same `mistapi.get_all` seam as `src/export/org_device_stats_exporter.py`, then writes `ApScorecard.csv` and `ApScorecardBySite.csv` through `DataExporter.write_with_format_selection()`. Shared wiring stays deferred to [wiring.md](wiring.md).

## Technical Context

**Language/Version**: Python `3.13+`

**Primary Dependencies**: Existing `mistapi>=0.64.0,<0.65`, `DataExporter`, `APIDataFetcher`, `SourceDependencyResolver`, and standard library dataclasses.

**Storage**: CSV and configured MistHelper output backends under `data/` through `DataExporter.write_with_format_selection()`.

**Testing**: `pytest` unit tests under `tests/unit/reports/ap_scorecard/`, with no network calls.

**Target Platform**: Windows local development and the existing Linux container runtime.

**Project Type**: MistHelper CLI menu operation with CSV and database export.

**Performance Goals**: One organization-level paginated call for AP statistics, then linear in-memory aggregation by AP and site.

**Constraints**: Use `listOrgDevicesStats` with `type=ap`. Do not add a second custom pagination loop. Keep prompt-free behavior for `--test`. Edit shared integration files only through [wiring.md](wiring.md).

**Scale/Scope**: One AP detail row for each AP in the organization and one site summary row for each site with APs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
| - | - | - |
| Five-Item Rule | Pass | New code will live in `src/reports/ap_scorecard/`, a nested package. Planned modules are `client.py`, `model.py`, `operation.py`, and `__init__.py`. |
| Class-Based Architecture | Pass | The handler is `ApScorecard.run()` as a static method. The client and operation use classes. The model uses dataclasses and pure functions. |
| Safety-First | Pass | The operation is read-only and safe. It must not prompt in `--test`. It must use existing organization resolution helpers. |
| Output Backends | Pass | Both output files use `DataExporter.write_with_format_selection()` with registered endpoint names. |
| API Discovery | Pass | Research confirms `GET /api/v1/orgs/{org_id}/stats/devices`, `operationId=listOrgDevicesStats`, and the installed SDK symbol. |
| Logging and Comments | Pass | Implementation tasks must add `%s` logging before and after API fetches, transforms, and exports. New executable lines require inline comments. |
| Primary Key Strategy | Deferred | The exact primary key entries are in [wiring.md](wiring.md) for the integration pull request. |
| Shared File Updates | Deferred | `MistHelper.py`, registry, README, generated docs, and copilot instructions are deferred to [wiring.md](wiring.md). |

## Project Structure

### Documentation (this feature)

```text
specs/3559-ap-scorecard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── wiring.md            # Integration manifest for shared files
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── reports/
    └── ap_scorecard/
        ├── __init__.py
        ├── client.py
        ├── model.py
        └── operation.py

tests/
└── unit/
    └── reports/
        └── ap_scorecard/
            ├── __init__.py
            ├── test_ap_scorecard_client.py
            └── test_ap_scorecard_model.py
```

**Structure Decision**: Use one nested report package. Keep API access in `client.py`, pure calculations in `model.py`, and menu orchestration in `operation.py`. Keep tests in the matching unit path.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research

Research is complete in [research.md](research.md). It resolves the Mist API path, the SDK symbol, the pagination seam, the tile thresholds, and the AP statistics fields.

## Phase 1 Design

Design artifacts are complete:

- [data-model.md](data-model.md)
- [quickstart.md](quickstart.md)
- [contracts/export-contract.md](contracts/export-contract.md)
- [wiring.md](wiring.md)

## Post-Design Constitution Check

| Gate | Status | Evidence |
| - | - | - |
| Five-Item Rule | Pass | The source package plans four files, and the test package plans three files. |
| Class-Based Architecture | Pass | The operation handler is `ApScorecard.run()`. |
| Safety-First | Pass | The operation is read-only and uses no destructive confirmation. |
| Output Backends | Pass | The contract requires `DataExporter.write_with_format_selection()` for both files. |
| API Pagination | Pass | The contract requires `APIDataFetcher` or the same `mistapi.get_all` seam. |
| Shared File Ownership | Pass | Shared wiring is isolated in [wiring.md](wiring.md). |
