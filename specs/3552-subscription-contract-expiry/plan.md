# Implementation Plan: Subscription Contract Expiry Report

**Branch**: `3552-subscription-contract-expiry` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3552-subscription-contract-expiry/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Menu 271 will produce two scored renewal reports for one selected Mist
organization. `SubscriptionExpiry.csv` will show one row per subscription type.
`ContractExpiry.csv` will show one row per device contract. The implementation
will keep API access in `client.py`, pure scoring in `model.py`, and menu
orchestration in `operation.py`. Integration changes for the menu, the registry,
the README, generated references, and primary key strategy are deferred to
[wiring.md](wiring.md).

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, `DataExporter`,
`SourceDependencyResolver`, and the Python standard library.

**Storage**: CSV output through existing exporter behavior. No new persistent
store is introduced by this feature branch.

**Testing**: `pytest` unit tests under
`tests/unit/reports/subscription_expiry/` during implementation.

**Target Platform**: MistHelper CLI and menu operation on Windows and Linux.

**Project Type**: Python CLI report operation.

**Performance Goals**: One report run completes after one license summary call,
one license usage call, and one paginated JSI inventory search.

**Constraints**: Do not mutate Mist cloud data. Do not implement integration
wiring in this branch. Preserve one row per output grain. Keep missing values
visible. Use Simplified Technical English in user-facing text.

**Scale/Scope**: One organization at a time. Output grain is one subscription
type and one device contract row.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gate status**: PASS for the planning step.

- **Five-Item Rule**: PASS. The future feature package is
  `src/mist/intelligence/reports/subscription_expiry/`, and tests are in
  `tests/unit/reports/subscription_expiry/`.
- **Class-Based Architecture**: PASS. `client.py`, `model.py`, and
  `operation.py` hold named classes with clear ownership. No wrapper-only module
  is planned.
- **Safety-First**: PASS. The report is read-only. It does not change Mist
  subscription, contract, or organization state.
- **Full Deployment Pipeline**: PASS for planning. Implementation and wiring
  tasks will carry local gates and pull request evidence.
- **Observability and Logging**: PASS. `operation.py` will log before and after
  API calls, scoring, export, and summary output.
- **Inline Comments**: PASS. Implementation tasks must comment each generated
  executable line.
- **Action Logging**: PASS. Implementation tasks must log each meaningful
  action before and after it runs.
- **Technology Constraints**: PASS. Existing `mistapi` SDK methods are planned.
  Direct HTTP calls are not planned.

## Project Structure

### Documentation (this feature)

```text
specs/3552-subscription-contract-expiry/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── wiring.md            # Deferred integration work for a later branch
└── contracts/           # Phase 1 output (/speckit.plan command)
    └── subscription-expiry-report.md
```

### Source Code (repository root)

```text
src/
└── reports/
    └── subscription_expiry/
        ├── __init__.py
        ├── client.py
        ├── model.py
        └── operation.py

tests/
└── unit/
    └── reports/
        └── subscription_expiry/
            ├── test_client.py
            ├── test_model.py
            └── test_operation.py
```

**Structure Decision**: Use a new nested report package so the feature does not
add direct children to crowded existing packages. Keep SDK calls in `client.py`.
Keep dataclasses and scoring in `model.py`. Keep prompting, context resolution,
report execution, export, and console summary in `operation.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research

Research is complete in [research.md](research.md). All technical context
unknowns are resolved.

## Phase 1 Design

Design artifacts are complete:

- [data-model.md](data-model.md)
- [contracts/subscription-expiry-report.md](contracts/subscription-expiry-report.md)
- [quickstart.md](quickstart.md)
- [wiring.md](wiring.md)

## Post-Design Constitution Check

**Gate status**: PASS for the planned design.

- The planned source package respects the Five-Item Rule.
- The planned classes keep SDK access, pure scoring, and orchestration separate.
- The report is read-only and uses existing Mist SDK methods.
- The feature branch defers menu, registry, README, generated reference, and
  primary key wiring to [wiring.md](wiring.md).
- Implementation tasks must add logs, inline comments, and unit tests before a
  pull request can pass review.
