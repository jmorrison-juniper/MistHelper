# Implementation Plan: Organization WAN Edge Scorecard

**Branch**: `3560-wan-edge-scorecard` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3560-wan-edge-scorecard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add menu `279` as a safe organization WAN edge scorecard. The later implementation will use `WanEdgeScorecard` with static `run()` in `src/reports/wan_edge_scorecard/`. It will reuse the existing gateway statistics fetch from menu `15` or menu `18`, with `listOrgDevicesStats` and `type=gateway`. It will write one gateway scorecard, one DHCP pool detail report, one site scorecard, and a console summary.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, existing `DataExporter`, and existing gateway statistics export helpers.

**Storage**: Output files under `data/` through the configured export behavior. No new database schema is planned.

**Testing**: `pytest` unit tests under `tests/unit/reports/wan_edge_scorecard/`, plus the existing local gates for changed implementation files.

**Target Platform**: Windows development worktree and Linux container runtime.

**Project Type**: MistHelper CLI menu operation and report package.

**Performance Goals**: Use one shared gateway statistics pagination path for all gateway statistics consumers.

**Constraints**: This planning step edits only `specs/3560-wan-edge-scorecard/**`. Later implementation must not create a second pagination loop.

**Scale/Scope**: One organization report for all gateways returned by `listOrgDevicesStats` with `type=gateway`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan evidence |
| - | - | - |
| Five-Item Rule | Pass | Later code enters `src/reports/wan_edge_scorecard/`, which is a nested feature package. |
| Class-Based Architecture | Pass | Later code uses `WanEdgeScorecard` with static `run()`. |
| Safety-First | Pass | Menu `279` is safe and must run in `--test` without a prompt. |
| Full Deployment Pipeline | Pass with fleet limit | This step creates planning artifacts only. Later code work must run the normal gates. |
| Observability and Logging | Pass | Later implementation must log before and after fetch, transform, and export actions. |
| Inline Comments | Pass | Later implementation must comment touched executable lines. |
| Action Logging | Pass | Later implementation must log all meaningful report steps. |
| Output Backends | Pass | Collected API data must use the configured export behavior. |
| Primary Keys | Not applicable | This feature writes reports. It does not add a persistent endpoint table. |

## Project Structure

### Documentation (this feature)

```text
specs/3560-wan-edge-scorecard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── wiring.md            # Implementation wiring contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── reports/
    └── wan_edge_scorecard/
        ├── __init__.py
        ├── client.py
        ├── scorecard.py
        ├── models.py
        └── scoring.py

tests/
└── unit/
    └── reports/
        └── wan_edge_scorecard/
            ├── test_scorecard.py
            └── test_scoring.py

changelog.d/
└── issue-3560-wan-edge-scorecard.md

MistHelper.py
src/utils/operation_registry.py
documentation/menu_reference.md
```

**Structure Decision**: Use one nested report package and one matching unit test package. This planning step does not edit source, tests, changelog, documentation, or `.specify/feature.json`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

| Principle | Status | Post-design evidence |
| - | - | - |
| Five-Item Rule | Pass | Design keeps the feature in one nested report package. |
| Class-Based Architecture | Pass | The handler contract names `WanEdgeScorecard.run()`. |
| Safety-First | Pass | No destructive behavior is designed. No operator prompt is required. |
| Output Backends | Pass | The output contract requires configured export behavior for report files. |
| Observability | Pass | The wiring contract requires fetch, transform, and export logging. |
| Testability | Pass | The quickstart defines deterministic fixture-based validation. |
