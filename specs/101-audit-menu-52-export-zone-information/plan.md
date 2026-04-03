# Implementation Plan: Audit - Export zone information (Menu #52)

Branch: `101-export-zone-information` | Date: 2026-04-03 | Spec: spec.md
Input: Feature specification from specs/101-audit-menu-52-export-zone-information/spec.md

## Summary

This plan implements the audit recommendations for "Export zone information" (Menu #52) — SiteConfigExporter.zones. Deliverables are: a focused Phase 0 research record resolving open questions about flattening, empty-output semantics, and SQLite typing; Phase 1 design artifacts (data-model.md, contracts where applicable, quickstart.md); and Phase 2 tasks for implementation and tests.

Primary approach: keep changes minimal and well-tested. Fix behavioral regressions first (empty-output handling, explicit api_function_name propagation), harden flattening heuristics conservatively, and add unit + integration tests to cover CSV and SQLite outputs.

## Technical Context

Language/Version: Python 3.13 (per Constitution)
Primary Dependencies: mistapi >= 0.59, sqlite3 (stdlib), pytest (dev), typing, json
Storage: data/ directory for CSVs; SQLite database at data/mist_data.db (or test-specific DB)
Testing: pytest + unittest.mock; in-memory or temp-file SQLite for tests
Target Platform: Local developer (Windows) and Linux containers (Podman) — maintain cross-platform path handling
Project Type: CLI (single-project script + modular utilities in MistHelper.py)
Performance Goals: None beyond correctness; robust to reasonably sized site zone lists (typical < 1k objects)
Constraints: All outputs must be written under data/; logging must be ASCII-only; must follow Constitution I-V
Scale/Scope: Small feature-level change + tests

Unknowns / NEEDS CLARIFICATION (must be resolved in Phase 0 research):
- Empty-output semantics: should an explicit empty list always create a header-only CSV when no fields are provided, or should it create a small informational file? (spec suggests header-only or informational row; choose one)
- Stable flattening strategy: what is the preferred limit for list-of-dicts indexed expansion (max elements to unroll)? Should we cap at e.g., 3 items, or derive a policy per-endpoint?
- String parsing heuristics: enable heuristic JSON parsing by default or only when callers indicate field contains stringified JSON?
- SQLite typing vs string coercion: prefer preserving NULLs and native numeric/boolean types or store everything as TEXT for simplicity?
- Exact SQLite table naming conventions (SiteZones vs sanitized endpoint name) and column naming casing convention

## Constitution Check

GATES (evaluated against MistHelper Constitution):
- Five-Item Rule: NO structural violations introduced by this plan (small number of files and tests). PASS.
- Class-Based Architecture: Changes will preserve class-based utilities (DataExporter, SQLiteDatabaseWriter). PASS.
- Safety-First: No destructive operations. Any interactive destructive menus unaffected. PASS.
- Full Deployment Pipeline: All code changes MUST follow the pipeline (syntax check, commit message format, CI). This is a non-negotiable requirement — documented as a checklist in Phase 2 tasks. PASS (must be executed during implementation).
- Observability & Logging: Logging changes will use ASCII and structured messages. PASS.

No constitution violations identified that require explicit justification.

## Project Structure

Selected structure: single project (root) with modular utilities.

Suggested layout (existing repo):
- MistHelper.py (entrypoint / menu definitions)
- misthelper/
  - exporters.py (SiteConfigExporter, SiteExportUtils)
  - data_export/
    - data_exporter.py (DataExporter)
    - db_writer.py (SQLiteDatabaseWriter, DatabaseSchemaUtils)
    - processing.py (DataProcessingUtils)
- tests/
  - unit/
  - integration/

Structure Decision: adopt lightweight module separation in misthelper/data_export while keeping the existing MistHelper.py menu definitions intact.

## Complexity Tracking

No gate violations requiring complexity justification.

## Phase 0 — Outline & Research (deliverable: research.md)

Goals:
- Resolve all NEEDS CLARIFICATION items above with concrete, actionable decisions.
- Produce short recommendations for each decision and rationale to feed Phase 1 design.

Research tasks (owners: @author or feature owner):
- Research-1: "Empty-output semantics" — Decide header-only CSV vs informational row; pick behavior and examples.
- Research-2: "Flattening strategy" — Find best practices for list-of-dicts flattening in exports (CSV + SQLite), propose a deterministic strategy (indexed up to N, or explode to JSON column) and show trade-offs.
- Research-3: "String parsing heuristics" — Determine safe heuristics for auto-parsing stringified JSON, recommend default (opt-in vs opt-out).
- Research-4: "SQLite typing" — Decide whether to preserve types/NULLs or coerce to TEXT. Identify approach for preserving None->NULL and numbers/booleans mapping.
- Research-5: "Table & column naming conventions" — Confirm canonical naming for SiteZones table and column normalization rules.

Outputs:
- research.md containing Decision / Rationale / Alternatives for each unknown above.

Timing: 1-2 workdays of focused research + draft.

Phase 0 Acceptance: research.md resolves all NEEDS CLARIFICATION entries.

## Phase 1 — Design & Contracts (prereq: research.md)

Deliverables: data-model.md, contracts/ (if external interfaces), quickstart.md, update agent context

Phase 1 tasks:
1. Data Model (data-model.md)
   - Extract Zone entity attributes from spec and example API responses.
   - Define CSV header canonical order and SQLite table schema (column names, types, PK strategy).
   - Document flattening conventions: nested dicts -> underscore keys, list-of-dicts -> indexed keys up to N (document N), fallback: include JSON blob column for overflow.
   - Document handling for multiline strings and NULLs.

2. Contracts/
   - For CLI: define the command schema for the export menu (parameters accepted, flags for format, filename override) in contracts/cli-export-zone-info.md.
   - For libraries/modules: define Python function signature for SiteExportUtils._export_data and DataExporter.write_with_format_selection, documenting api_call parameter propagation (must include api_call.__name__).

3. Quickstart (quickstart.md)
   - Short instructions for developers to run the exporter locally and run tests (how to run pytest with temp DB, env vars to set OUTPUT_FORMAT).

4. Agent context update
   - Run .specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot (developer will run locally). The update should add any new technology (SQLite typing, flattening decisions) into the agent context file while preserving manual edits between markers.

Phase 1 Acceptance: data-model.md and contract docs exist and are reviewed; agent context updated.

## Phase 2 — Implementation (high level tasks)

(Not creating tasks.md here — Phase 2 task list summarized for planning)

- Implement DataExporter._validate_write_inputs change to allow explicit empty list to create header-only CSV (AC-1.1 / AC-1.2).
- Update SiteExportUtils._export_data / APIDataFetcher to pass api_call.__name__ to DataExporter/SQLiteDatabaseWriter.
- Harden flattening logic in DataProcessingUtils per Phase 0 decision (cap indexed list-of-dicts, add JSON overflow column, conservative string parsing flag).
- Update SQLiteDatabaseWriter to preserve NULLs and native numeric/boolean types if Phase 0 decides to do so; otherwise document consistent coercion.
- Add unit tests for each AC (flattening, empty output, parsing, SQLite PK behavior).
- Add integration test for full pipeline (CSV + SQLite) with mocked API responses.
- Run full deployment pipeline and follow commit message format.

## Test Plan (summary)

- Unit tests: flatten_nested_fields, escape_multiline, write_csv, sqlite_writer (in-memory DB), strategy resolution tests.
- Integration test: full exporter pipeline with mocked listSiteZones response verifying CSV file and SQLite table behavior.
- CI: ensure tests run in GitHub Actions container; note requirement for data/ write permissions in ephemeral runner.

## Risks & Mitigations

- Risk: Altering flattening behavior may break downstream consumers expecting previous column layout.
  - Mitigation: Maintain backward-compatible defaults where possible, increase version in README, and add a migration note in quickstart.
- Risk: Preserving types in SQLite complicates schema generation.
  - Mitigation: Default to preserving NULLs and numbers where obvious (isinstance check) and fall back to TEXT; document decisions.

## Outputs (files to be created by this plan)

- specs/101-audit-menu-52-export-zone-information/research.md
- specs/101-audit-menu-52-export-zone-information/data-model.md
- specs/101-audit-menu-52-export-zone-information/quickstart.md
- specs/101-audit-menu-52-export-zone-information/contracts/cli-export-zone-info.md
- tests/unit/test_sitezones_export.py
- tests/integration/test_sitezones_pipeline.py

---

Prepared-by: speckit.plan

