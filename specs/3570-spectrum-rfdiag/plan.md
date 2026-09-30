# Implementation Plan: Spectrum RF Diagnostics

**Branch**: `3570-spectrum-rfdiag` | **Date**: 2026-09-29 | **Spec**: `specs/3570-spectrum-rfdiag/spec.md`

**Input**: Feature specification from `specs/3570-spectrum-rfdiag/spec.md`

## Summary

Build a new RF diagnostics package at `src/troubleshooting/rf_diagnostics` with two guided modes. Spectrum mode starts AP spectrum analysis, polls the running state, and prints the final result. Recording mode starts a client RF diagnostic recording, waits for operator stop or duration, stops the recording, downloads the file under `data/rfdiags/`, and writes one audit row in `data/RfDiagnostics.csv`. Unit tests live under `tests/unit/troubleshooting/rf_diagnostics`. Menu 290 integration is deferred and tracked in `specs/3570-spectrum-rfdiag/wiring.md`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi` 0.59+; existing `InputUtils.safe_input`; standard `csv`, `datetime`, `pathlib`, `time`, and `logging` modules; pytest and test doubles for unit tests.

**Storage**: Fixed local outputs only. The audit file is `data/RfDiagnostics.csv`. Recording downloads are saved under `data/rfdiags/`. No database schema change is planned.

**Testing**: pytest unit tests under `tests/unit/troubleshooting/rf_diagnostics`. Tests use fake API sessions, fake SDK callables, fake waits, and temporary file paths.

**Target Platform**: Windows local development and Linux container runtime. Paths must use `pathlib.Path` or `os.path.join()`.

**Project Type**: Python CLI package inside the MistHelper application.

**Performance Goals**: Keep each happy path to no more than five required prompts after menu 290. Keep spectrum polling bounded by a configured poll limit and interval. Write one small audit row per run.

**Constraints**: Scope is limited to `src/troubleshooting/rf_diagnostics` and `tests/unit/troubleshooting/rf_diagnostics`. This planning step edits only `specs/3570-spectrum-rfdiag`. Use the Mist SDK when it has a method. Use `apisession.mist_get('/api/v1/sites/{site_id}/analyze_spectrum')` or an equivalent API-session call for the missing running-spectrum SDK method. Do not print secrets, tokens, or raw credentials. User prompts must use the safe input pattern. Generated source code must include inline comments and action logging.

**Scale/Scope**: One operator run at a time. One site and one AP or client per run. Audit growth is append-only and small for operator diagnostics.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Five-Item Rule**: Fleet-contract exception with a recorded implementation risk. `src/troubleshooting` has four visible direct children, so adding `rf_diagnostics` keeps that level at five. `tests/unit/troubleshooting` already has five visible test files. Adding `rf_diagnostics` there would make six direct children. This is required by the issue scope and is tracked in Complexity Tracking. Implementation must not add any other child at that level.
- **II. Class-Based Architecture**: Pass. The design uses semantically named classes. It avoids standalone wrapper functions.
- **III. Safety-First**: Pass. Confirmation defaults to no. All operator input uses safe input. File names are sanitized before write.
- **IV. Full Deployment Pipeline**: Pass for the fleet package boundary. The core package validates locally and records menu integration in `wiring.md`; the integration pull request applies the deferred menu files.
- **V. Observability & Logging**: Pass. Planned code logs before and after API calls, waits, file writes, and audit writes. Output text stays ASCII.
- **VI. Inline Comments**: Pass. Planned source code requires inline comments on generated code lines.
- **VII. Action Logging**: Pass. Planned classes include before and after logging for meaningful actions.

## Project Structure

### Documentation (this feature)

```text
specs/3570-spectrum-rfdiag/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── contracts/
│   └── rf-diagnostics.md
└── tasks.md             # Created by the tasks phase, not by this plan.
```

### Source Code (repository root)

```text
src/
└── troubleshooting/
    └── rf_diagnostics/
        ├── __init__.py
        ├── audit.py
        ├── client.py
        ├── file_naming.py
        ├── models.py
        ├── operation.py
        ├── recording.py
        └── spectrum.py

tests/
└── unit/
    └── troubleshooting/
        └── rf_diagnostics/
            ├── test_audit.py
            ├── test_client_requests.py
            ├── test_file_naming.py
            ├── test_recording_flow.py
            └── test_spectrum_flow.py
```

**Structure Decision**: Use one nested package under `src/troubleshooting` so the feature has clear ownership and stays below the five-child source limit. Use one matching unit-test package under `tests/unit/troubleshooting/rf_diagnostics` because the issue names that path. Menu, registry, endpoint catalog, changelog, and README integration remain deferred in `wiring.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Planned `tests/unit/troubleshooting/rf_diagnostics` creates a sixth direct child under `tests/unit/troubleshooting`. | The feature issue and user instructions require this test path. Keeping the tests together makes the RF flow testable and discoverable. | Adding flat test files directly under `tests/unit/troubleshooting` would still increase the child count and scatter the feature. Moving existing tests is out of scope for this issue. |

## Phase 0 Output

`research.md` resolves all technical choices. No open clarification items remain.

## Phase 1 Output

`data-model.md`, `contracts/rf-diagnostics.md`, and `quickstart.md` define the planned data, interface contracts, and validation guide.

## Post-Design Constitution Check

- **I. Five-Item Rule**: Same fleet-contract exception and same recorded test-path risk. No new source hierarchy violation is planned.
- **II. Class-Based Architecture**: Pass. Entities map to classes and dataclasses.
- **III. Safety-First**: Pass. Contracts require safe prompts, fail-closed downloads, and no secret output.
- **IV. Full Deployment Pipeline**: Pass for this package pull request after local validation. Menu wiring remains deferred by fleet contract and is recorded in `wiring.md`.
- **V. Observability & Logging**: Pass. Contracts require action logs around remote calls and file writes.
- **VI. Inline Comments**: Pass. Implementation tasks must enforce same-line comments for generated code.
- **VII. Action Logging**: Pass. Implementation tasks must enforce before and after logs for each action.

