# Implementation Plan: Alert Digest Acknowledge

**Branch**: `feat/3561-alert-digest-acknowledge` | **Date**: 2026-09-29 | **Spec**: `specs/3561-alert-digest-acknowledge/spec.md`

**Input**: Feature specification from `specs/3561-alert-digest-acknowledge/spec.md`

## Summary

Add menu 280 as a safe alert digest and menu 281 as a destructive alarm acknowledgement path. The implementation uses a new `src/reports/alert_digest/` package with a Mist API client, pure model logic, and an operation class. The integration pull request wires the two menu entries from `specs/3561-alert-digest-acknowledge/wiring.md`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi>=0.64.0,<0.65`, `SourceDependencyResolver`, `DataExporter`, and standard-library modules.

**Storage**: CSV files under `data/` through `DataExporter`. `AlertDigest.md` is a handover document, so the writer creates it directly under `data/`.

**Testing**: `pytest`, `ruff`, `black`, `mypy`, `pydocstyle`, `vulture`, and `interrogate` through the assigned virtual environment.

**Target Platform**: Windows development worktree and the existing MistHelper runtime.

**Project Type**: MistHelper CLI menu operation package.

**Performance Goals**: Complete a normal 24-hour alert digest in under 60 seconds. Unit tests measure local grouping of 500 alarm rows in under 1 second.

**Constraints**: Menu 281 sends no destructive request without `ACK <count>`. `--dry-run` sends no request. All output uses ASCII text.

**Scale/Scope**: One organization, one lookback window, all alarm rows returned by paged `searchOrgAlarms`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Five-Item Rule: Pass. The new package adds at most five modules: `client.py`, `model.py`, `operation.py`, `prompts.py`, and `writer.py`.
- Class-Based Architecture: Pass. The entry point is `AlertDigestOperation`, and supporting logic lives in classes or dataclasses.
- Safety-First: Pass. Menu 281 requires typed `ACK <count>` and supports `--dry-run`.
- Full Deployment Pipeline: Pass for the fleet scope. The branch records integration changes in `wiring.md` and opens a draft pull request.
- Observability & Logging: Pass. The client and operation will log before and after API calls, prompts, transforms, and writes.
- Inline Comments: Pass. New Python code will include inline comments on executable lines.
- Action Logging: Pass. New Python code will log meaningful actions before and after execution.

## Project Structure

### Documentation (this feature)

```text
specs/3561-alert-digest-acknowledge/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── menu-contract.md
├── checklists/
│   └── requirements.md
├── tasks.md
└── wiring.md
```

### Source Code (repository root)

```text
src/reports/alert_digest/
├── __init__.py
├── client.py
├── model.py
├── operation.py
├── prompts.py
└── writer.py

tests/unit/reports/alert_digest/
├── __init__.py
├── test_alert_digest_client.py
├── test_alert_digest_model.py
└── test_alert_digest_operation.py
```

**Structure Decision**: Use one new nested package under `src/reports/alert_digest/` and one new matching test package. The fleet contract forbids this branch from editing integration-owned files. Menu registration, registry category changes, primary key strategies, generated menu reference changes, and README changes are deferred to the integration pull request and recorded in `wiring.md`.

## Phase 0 Research Summary

Research is recorded in `research.md`. The OpenAPI document confirms the four required operation IDs. The installed SDK exposes all four methods, so no fallback `mist_get` or `mist_post` path is needed. The AIOps skill pages define the alert dashboard categories, severity labels, list columns, alert type examples, templates, and pause rules.

## Phase 1 Design Summary

The data model is recorded in `data-model.md`. The menu contract is recorded in `contracts/menu-contract.md`. The quickstart gives validation steps for menu 280, menu 281 confirmation behavior, dry-run behavior, and local gates.

## Post-Design Constitution Check

- Five-Item Rule: Pass. Each new module has one responsibility, and the package contains five implementation modules.
- Safety-First: Pass. The destructive path is isolated in `AlertDigestOperation.run_acknowledge` and confirmation logic is testable without a network call.
- Output Backends: Pass. CSV exports use `DataExporter.write_with_format_selection`. Markdown output uses a direct file write because it is an operator handover document, not collected API data.
- Database Keys: Pass for the fleet branch. The required primary key strategies are listed in `wiring.md`, and the integration pull request applies them in `endpoint_primary_key_strategies.py`.
- README and menu references: Pass for the fleet branch. The exact integration work is listed in `wiring.md`, and the integration pull request owns the forbidden files.

## Complexity Tracking

No new constitution violation is introduced. Existing repository-wide folder fan-out is grandfathered technical debt. This feature adds a nested package and does not increase a noncompliant existing package level.
