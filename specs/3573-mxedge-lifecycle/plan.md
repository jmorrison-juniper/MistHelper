# Implementation Plan: Mist Edge Lifecycle Operation

**Branch**: `feat/3573-mxedge-lifecycle` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/3573-mxedge-lifecycle/spec.md`

## Summary

Add package `src/org/mxedge_lifecycle/` for menu `293`. The operation presents one destructive sub-menu with claim, assign, unassign, bounce data ports, and upgrade. Each step builds an OpenAPI-shaped request body, asks for the exact typed confirmation word, supports dry-run, calls the matching `mistapi.api.v1.orgs.mxedges` SDK function, and writes `data/MxEdgeLifecycleLog.csv`. The upgrade step polls `getOrgMxEdgeUpgrade` until a terminal status or `UPGRADE_POLL_TIMEOUT_SECONDS`.

## Technical Context

**Language/Version**: Python 3.13+.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65` and standard library modules only.

**Storage**: CSV file under `data/`. No schema change.

**Testing**: `pytest` unit tests under `tests/unit/org/mxedge_lifecycle/`. Tests use fake clients and fake sessions only.

**Target Platform**: MistHelper CLI on Windows, macOS, Linux, and container runtime.

**Project Type**: Single-project Python CLI.

**Performance Goals**: Poll upgrade status with a bounded interval and timeout. No loop runs without a timeout.

**Constraints**: Category is destructive. The feature branch may edit only the assigned package, assigned tests, spec files, and release note fragment. Menu wiring, registry wiring, primary key strategy records, README, and generated references are deferred to the integration pull request through `wiring.md`.

**Scale/Scope**: One new package, one new unit test directory, one release note fragment, and one spec directory.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
| - | - | - |
| Five-Item Rule | PASS | The package has client, models, operation, and init modules. Each function stays focused on one step. |
| Class-Based Architecture | PASS | `MxEdgeLifecycleOperation` is the menu entry point. `MxEdgeLifecycleClient` owns API calls. Model classes own request body construction and polling decisions. |
| Safety-First | PASS | Every step uses a typed word and supports dry-run before a Mist request. |
| Observability | PASS | The client logs before and after every API call and does not log claim codes. |
| Inline Comments | PASS | New executable lines include inline comments that state intent. |
| Documentation Coverage | PASS | Public modules, classes, and functions include docstrings. |
| Local-First Validation | PASS | Contract validation uses fake clients with no network. |

## Project Structure

### Documentation

```text
specs/3573-mxedge-lifecycle/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── tasks.md
└── contracts/
    └── request-bodies.md
```

### Source Code

```text
src/org/mxedge_lifecycle/
├── __init__.py
├── client.py
├── models.py
└── operation.py

tests/unit/org/mxedge_lifecycle/
├── __init__.py
├── test_mxedge_lifecycle_client.py
├── test_mxedge_lifecycle_models.py
└── test_mxedge_lifecycle_operation.py
```

**Structure Decision**: Use the required package path. Keep pure request-body logic in `models.py`, Mist SDK calls in `client.py`, and prompts plus export orchestration in `operation.py`.

## Complexity Tracking

No constitution violation is planned.
