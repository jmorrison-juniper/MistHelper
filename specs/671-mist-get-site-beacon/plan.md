# Implementation Plan: Mist API Read Operation -- getSiteBeacon

**Branch**: `671-mist-get-site-beacon` | **Date**: 2026-08-03 | **Spec**: `/specs/671-mist-get-site-beacon/spec.md`

**Input**: Feature specification from `/specs/671-mist-get-site-beacon/spec.md`

## Summary

Add a new MistHelper menu operation for `getSiteBeacon` (`GET /api/v1/sites/{site_id}/beacons/{beacon_id}`) that safely collects required IDs, executes the SDK call once per selected scope, and persists results via `DataExporter.write_with_format_selection(..., api_function_name='getSiteBeacon')` for CSV, SQLite, and ArangoDB/Redis workflows.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: `mistapi>=0.63.1`, `python-dotenv`, `PyYAML`, `structlog`, existing MistHelper utility modules (`InputUtils`, `DataExporter`)

**Storage**: CSV files under `data/`, SQLite (`data/mist_data.db`), optional ArangoDB + Redis through `DatabaseRouter`

**Testing**: `pytest` (unit + integration marker), `python -m py_compile MistHelper.py`, `python -m ruff check`, `python -m black --check`

**Target Platform**: Windows dev environment + Podman container runtime (Linux) + SSH/container interactive sessions

**Project Type**: Single-project Python CLI application with modular `src/` packages

**Performance Goals**: Single endpoint fetch completes within 5 seconds under normal API latency; retries and backoff honor existing adaptive rate-limit controls

**Constraints**:
- Must use `safe_input()` handling for all interactive prompts
- Must apply constitution-mandated inline comments and action logging patterns
- Must keep operation read-only and non-destructive
- Must update `ENDPOINT_PRIMARY_KEY_STRATEGIES`, README menu table, and CHANGELOG in same issue scope

**Scale/Scope**: One new GET menu operation, one new endpoint PK strategy entry, focused docs updates, and regression-safe export path reuse

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate Review

- **I. Five-Item Rule**: PASS — planned work is a small additive change with helper reuse, no large structural expansion.
- **II. Class-Based Architecture**: PASS — implementation will extend existing class/module pathways; no wrapper-only functions.
- **III. Safety-First**: PASS — prompt flow explicitly requires `safe_input()` and graceful EOF handling.
- **IV. Full Deployment Pipeline**: PASS (execution-phase gate) — validation commands and deployment pipeline remain required after coding.
- **V. Observability & Logging**: PASS — info-before/debug-after logging is included in handler design.
- **VI. Inline Comments**: PASS (execution-phase gate) — all generated executable lines will require same-line comments.
- **VII. Action Logging**: PASS — API call, transform, and export steps include before/after logging.

**Gate Result (Pre-Research)**: PASS

### Post-Design Gate Re-Check

- Data model preserves natural key semantics (`id`) for beacon entities.
- Contract design enforces safe input, bounded API invocation, and backend-consistent persistence.
- Quickstart validation includes lint/syntax/test gates and run-path verification.

**Gate Result (Post-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/671-mist-get-site-beacon/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── get-site-beacon-contract.md
│   └── get-site-beacon-response.schema.json
└── tasks.md                 # created in /speckit.tasks phase
```

### Source Code (repository root)

```text
MistHelper.py
src/
├── refactors/
│   └── endpoint_primary_key_strategies.py
├── utils/
│   └── input_utils.py
├── export/
│   └── data_exporter.py
└── db/
    └── arango_writer.py

documentation/
├── MIST_API_MISSING_ENDPOINTS.md
└── api/sites/

tests/
├── unit/
└── integration/
```

**Structure Decision**: Use the existing single-project CLI structure. Implement `getSiteBeacon` by extending current menu/endpoint dispatch flow, reusing `InputUtils.safe_input`, exporter plumbing, and endpoint strategy configuration without introducing new top-level packages.

## Phase 0: Research Plan

1. Confirm request/response semantics for `getSiteBeacon` (required path params, non-paginated response, 404/429 behavior).
2. Select primary key strategy for `getSiteBeacon` aligned with existing beacon endpoint conventions.
3. Validate integration pattern for menu prompt -> SDK call -> data export -> backend routing.

**Output**: `research.md`

## Phase 1: Design Plan

1. Define request/result/export entities and validation rules in `data-model.md`.
2. Define user-facing operation contract and response schema in `contracts/`.
3. Define operator validation workflow in `quickstart.md`.
4. Refresh agent context from finalized plan metadata.

**Output**: `data-model.md`, `contracts/*`, `quickstart.md`

## Complexity Tracking

No constitution violations expected; table not required.
