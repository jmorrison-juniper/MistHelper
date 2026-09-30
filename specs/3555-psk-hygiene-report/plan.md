# Implementation Plan: PSK Hygiene Report

**Branch**: `feat/3555-psk-hygiene-report` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/3555-psk-hygiene-report/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add menu `274` as a safe PSK hygiene report that produces `data/PskHygiene.csv` without prompts. The feature is implemented as `PskHygieneReport.run()` in `src/reports/psk_hygiene/`, with separate client, model, and operation modules. The client reads organization PSKs, organization WLANs, and organization templates through `mistapi`. The model scores each PSK through `PskHygieneScorer` and dataclasses. The operation resolves the Mist session and organization ID, calls the client and model, logs only summary counts, and exports through `DataExporter.write_with_format_selection`.

## Technical Context

**Language/Version**: Python `3.13` or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, existing `SourceDependencyResolver`, existing `ConfigUtils`, existing `DataExporter`, and standard-library dataclasses and date parsing.

**Storage**: No new persistent store. The report exports through the existing output backend path and writes `PskHygiene.csv` under `data/` by default.

**Testing**: `pytest` unit tests under `tests/unit/reports/psk_hygiene/`. Tests use fakes and must not call the network.

**Target Platform**: MistHelper CLI on Windows and Linux, including container and SSH runs.

**Project Type**: CLI menu operation and report exporter.

**Performance Goals**: Process one organization-wide PSK set in memory. Complete the model step in linear time relative to PSK and WLAN record count.

**Constraints**: `run()` must not prompt. If no organization ID is configured, the operation fails closed and logs a clear message. The operation must be safe for `--test`. Secrets must never reach logs, console output, or report rows. The report must record only `old_passphrase_present`.

**Scale/Scope**: One new safe menu operation, one new report package, and one unit test directory. Generated menu documentation is deferred to the integration pull request.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
| - | - | - |
| Five-Item Rule | Pass | New code enters `src/reports/psk_hygiene/`, a nested feature package. The planned package has at most five modules: `__init__`, `client`, `model`, `operation`, and optional package metadata. |
| Class-Based Architecture | Pass | The public entry point is the class `PskHygieneReport` with static `run()`. Helper behavior belongs to feature classes or pure model functions where specified by this issue. No wrapper function is planned. |
| Safety-First | Pass | `run()` has no prompt. The operation uses existing session and organization resolvers and exports only sanitized rows. |
| Full Deployment Pipeline | Deferred | This plan step edits only `specs/3555-psk-hygiene-report/**`. Implementation must add the release note, run local gates, open the pull request, and pass CI. |
| Observability and Logging | Pass | The operation logs before and after fetch, model, and export actions. It logs counts only and never logs PSK values. |
| Inline Comments | Pass | Implementation tasks must add inline comments to all AI-generated executable lines in touched blocks. |
| Action Logging | Pass | Implementation tasks must add `info` before and `debug` after each meaningful action. |
| Output Backends | Pass | The operation exports with `DataExporter.write_with_format_selection(data, filename, api_function_name=...)`. |
| Mist API Access | Pass | The client uses installed `mistapi` methods where they exist. No direct HTTP call is planned. |
| Primary Key Strategy | Deferred | The integration pull request must add `psk_hygiene_report` before non-CSV backends are release-ready. |

## Project Structure

### Documentation (this feature)

```text
specs/3555-psk-hygiene-report/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── operation-contract.md
│   └── report-schema.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── reports/
    └── psk_hygiene/
        ├── __init__.py
        ├── client.py
        ├── model.py
        └── operation.py

tests/
└── unit/
    └── reports/
        └── psk_hygiene/
            ├── test_client.py
            ├── test_model.py
            ├── test_operation.py
            └── test_traceability.py

changelog.d/
└── issue-3555-psk-hygiene-report.md
```

**Structure Decision**: Use a nested package under `src/reports/psk_hygiene/` so the feature has a clear boundary and does not add new root-level children. Create `tests/unit/reports/psk_hygiene/` with fake client data and no network calls. Create the release note during implementation, not during this plan step, because this request allows edits only under `specs/3555-psk-hygiene-report/**`.

## Phase 0 Research

Research is complete in [research.md](./research.md). All API, security, rotation, and scope questions have a recorded decision. No unresolved clarification remains.

## Phase 1 Design

Design artifacts are complete:

- [data-model.md](./data-model.md)
- [quickstart.md](./quickstart.md)
- [contracts/report-schema.md](./contracts/report-schema.md)
- [contracts/operation-contract.md](./contracts/operation-contract.md)

## Post-Design Constitution Check

| Gate | Status | Evidence |
| - | - | - |
| Five-Item Rule | Pass | The design keeps the new package to four planned modules and keeps the public class in `operation.py`. |
| Class-Based Architecture | Pass | `PskHygieneReport.run()` owns operation orchestration. Pure model functions stay in `model.py` because the required architecture explicitly asks for pure functions and dataclasses. |
| Safety-First | Pass | Contracts prohibit prompts, direct network access in tests, and secret fields in rows. |
| Output Backends | Pass | The operation contract requires `DataExporter.write_with_format_selection`. |
| Observability | Pass | The operation contract requires sanitized summary logging only. |
| Release Process | Deferred | The release note and generated references are implementation tasks because they are outside the allowed plan-step edit boundary. |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| None | Not applicable | Not applicable |
