# Implementation Plan: Automated Testing Infrastructure

**Branch**: `012-automated-testing` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-automated-testing/spec.md`

## Summary

Add structured telemetry output (NDJSON), offline unit tests, live end-to-end testing of all non-destructive menu operations, and CI pipeline integration to MistHelper. The approach introduces a `TelemetryEmitter` class for best-effort event writing, an `OperationRegistry` class to centralize operation classification, refactors `run_systematic_test()` and `run_interactive_test()` to use `OperationRegistry` for non-interactive execution, extracts pure utility functions into importable modules for unit testing, and enhances the GitHub Actions workflow with a test gate before container build.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+, pytest (new — unit tests only)
**Storage**: NDJSON files in `data/` directory (`test_events.jsonl`, timestamped variants)
**Testing**: pytest (offline unit tests), `--test`/`--testinteractive` (live e2e with real APIs)
**Target Platform**: Windows 11 (local dev), Linux containers (production), GitHub Actions (CI)
**Project Type**: CLI tool (menu-driven)
**Performance Goals**: Unit tests complete in <30 seconds; telemetry writes add <1ms per event
**Constraints**: Zero import side effects for unit test modules; best-effort telemetry (never breaks primary operation); ASCII-only log output
**Scale/Scope**: ~28K line monolith (MistHelper.py), ~120 menu operations, ~60 currently tested by `--test`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Initial Assessment)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | New `tests/unit/` directory adds 1 child to project root. New classes (`TelemetryEmitter`, `TestHarness`) stay within limits. All new functions will observe max-5-params, max-25-lines. |
| II. Class-Based Architecture | PASS | All new functionality in named classes: `TelemetryEmitter`, `TestHarness`, `OperationRegistry`. No standalone wrappers. |
| III. Safety-First | PASS | No new destructive operations. Destructive ops explicitly excluded from automated test execution. Telemetry is best-effort (FR-008). |
| IV. Full Deployment Pipeline | PASS | CI enhancement adds test gate *before* existing build — strengthens the pipeline. |
| V. Observability & Logging | PASS | NDJSON telemetry is structured machine-parseable output — directly implements this principle. ASCII-only enforced. |

### Post-Design Gate (After Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | `tests/` has 2 children (`unit/`, `conftest.py`). `tests/unit/` has 4 test modules. Extracted modules have ≤5 public classes each. |
| II. Class-Based Architecture | PASS | `TelemetryEmitter`, `TestHarness`, `OperationRegistry`, `TestComparator` — all semantic classes, no wrappers. |
| III. Safety-First | PASS | `OperationRegistry` classifies destructive ops; `TestHarness` enforces skip-with-event for them. |
| IV. Full Deployment Pipeline | PASS | New `test` job gates `build-and-push` job in CI workflow. |
| V. Observability & Logging | PASS | All new modules use structured logging. Telemetry format is NDJSON per spec. |

**Gate Result**: PASS — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/012-automated-testing/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research findings
├── data-model.md        # Phase 1: Entity schemas and relationships
├── quickstart.md        # Phase 1: Getting started guide
├── contracts/           # Phase 1: Interface contracts
│   └── telemetry.md     # NDJSON event schemas
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
MistHelper.py                    # Modified: TelemetryEmitter class, OperationRegistry,
│                                #   TestHarness refactor, progress hooks in loops
├── tests/                       # NEW directory
│   ├── conftest.py              # pytest configuration, import helpers
│   └── unit/                    # Offline unit tests (no API needed)
│       ├── test_data_processing.py    # flatten_dict, escape_multiline, get_unique_keys
│       ├── test_config_utils.py       # check_stop_signal
│       ├── test_pk_strategies.py      # ENDPOINT_PRIMARY_KEY_STRATEGIES validation
│       └── test_telemetry.py          # TelemetryEmitter event format
├── scripts/
│   ├── test_stop_signal.py      # Existing (preserved)
│   └── compare_test_runs.py     # NEW: Test comparison utility (US5)
└── .github/workflows/
    └── container-build.yml      # Modified: add test job before build
```

**Structure Decision**: Single-project layout. MistHelper is a monolith CLI tool — no separate frontend/backend/API split. Tests live in a root-level `tests/` directory (standard Python convention). The `tests/unit/` subdirectory contains all offline unit tests. No `tests/integration/` for now — live e2e tests use the existing `--test` CLI mode.

## Complexity Tracking

> No constitution violations detected. Table left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
