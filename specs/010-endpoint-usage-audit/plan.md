# Implementation Plan: Mist API Endpoint Usage Audit

**Branch**: `010-endpoint-usage-audit` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/010-endpoint-usage-audit/spec.md`

## Summary

Systematically audit every `mistapi.api.v1.*` call in MistHelper (278 call sites across ~102 unique API functions in MistHelper.py, 91 in maps_manager.py, 1 in wsgi.py) against the enriched API documentation (1,013 files in `documentation/api/`). The audit cross-references endpoint selection, parameter correctness, pagination handling, and deprecation/best-practice compliance. Findings are categorized into two tiers (Incorrect vs Suboptimal) and four severity levels (Critical/High/Medium/Low). Output is a structured JSON report + Markdown summary. No code changes to MistHelper.py — report-first workflow.

## Technical Context

**Language/Version**: Python 3.13+ (analysis target), no runtime code produced  
**Primary Dependencies**: Static code analysis of MistHelper.py (~44K lines), maps_manager.py, wsgi.py; enriched API docs (1,013 .md files in `documentation/api/`)  
**Storage**: Output as JSON + Markdown files in `specs/010-endpoint-usage-audit/`  
**Testing**: Manual verification of findings against source code and API docs  
**Target Platform**: Developer workstation (Windows 11, VS Code)  
**Project Type**: Code review / audit activity (no runtime artifacts)  
**Performance Goals**: N/A — one-time analysis  
**Constraints**: Must cover 100% of API call sites; findings must be self-contained and actionable  
**Scale/Scope**: ~370 total API call sites, ~107 unique functions, 1,013 reference docs, 123 menu operations

### Existing Structures to Leverage

- **`ENDPOINT_PRIMARY_KEY_STRATEGIES`** (~line 3088): 50+ endpoints already classified with metadata — serves as a partial registry
- **`menu_actions`** (~line 50593): Dictionary mapping menu numbers to handler functions — provides menu-to-function mapping
- **Enriched API doc format**: Each doc has `## mistapi SDK` (function name), `## Usage Context`, `## Gotchas`, `## Related Endpoints`, `## MistHelper Notes` sections
- **Pagination infrastructure**: `DEFAULT_API_PAGE_LIMIT = 1000`, centralized pagination handling via cursor loops

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applicable? | Status | Notes |
|-----------|-------------|--------|-------|
| I. Five-Item Rule | No | PASS | This feature produces analysis documents only, not code. No classes, functions, or modules created. |
| II. Class-Based Architecture | No | PASS | No code produced — audit is a document deliverable. |
| III. Safety-First | No | PASS | No user input handling, no destructive operations. Read-only analysis of existing code. |
| IV. Full Deployment Pipeline | No | PASS | No code changes to MistHelper.py. Reports are spec-directory artifacts, not deployed software. |
| V. Observability & Logging | No | PASS | No logging produced. Output is structured JSON + Markdown. |

**Gate result**: PASS — All principles are non-applicable to a code-review audit feature. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/010-endpoint-usage-audit/
├── plan.md              # This file
├── research.md          # Phase 0: Endpoint mapping research
├── data-model.md        # Phase 1: Audit finding schema
├── quickstart.md        # Phase 1: How to run the audit
├── contracts/           # Phase 1: Report format contracts
│   └── audit-report-schema.json
├── tasks.md             # Phase 2: Task list (via /speckit.tasks)
├── audit-report.json    # Deliverable: Machine-parseable findings
└── audit-summary.md     # Deliverable: Human-readable summary
```

### Source Code (repository root)

No source code changes. The audit analyzes these existing files:
```text
MistHelper.py           # Primary target (~44K lines, 278 API call sites, 102 unique functions)
maps_manager.py         # Secondary target (91 API call sites, 24 unique functions)
wsgi.py                 # Tertiary target (1 API call site)
documentation/api/      # Reference corpus (1,013 enriched endpoint docs)
├── orgs/               # 449 files
├── sites/              # 330 files
├── utilities/          # 103 files
├── msps/               # 50 files
├── constants/          # 27 files
├── installer/          # 23 files
├── self/               # 18 files
└── admins/             # 13 files
```

**Structure Decision**: Output-only — all deliverables are Markdown/JSON files in the specs directory. No code is produced or modified.

## Complexity Tracking

No constitution violations. Table intentionally left empty.

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | Output directory has 5 items (plan, research, data-model, quickstart, contracts) + 2 deliverables. All within limits. |
| II. Class-Based Architecture | PASS | No classes created. JSON schema defines data structure, not code. |
| III. Safety-First | PASS | Audit is read-only analysis. No user input, no destructive operations. |
| IV. Full Deployment Pipeline | PASS | No code changes to commit/deploy. Spec artifacts are not deployed software. |
| V. Observability & Logging | PASS | Report uses ASCII-only content per convention. JSON output is machine-parseable. |

**Post-design gate result**: PASS — No violations introduced by the design phase.
