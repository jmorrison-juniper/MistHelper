# Data Model: Mist API Endpoint Usage Audit

**Feature**: 010-endpoint-usage-audit  
**Date**: 2026-03-08

## Entity: AuditFinding

A single discrepancy between how an API endpoint is used in MistHelper and how it should be used according to the enriched API documentation.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique finding identifier (format: `F-{NNN}`, e.g., `F-001`) |
| severity | enum | Yes | `Critical`, `High`, `Medium`, `Low` |
| tier | enum | Yes | `Incorrect` (causes wrong/incomplete results) or `Suboptimal` (works but not best practice) |
| category | enum | Yes | `endpoint-selection`, `parameter-usage`, `pagination`, `deprecation`, `best-practice` |
| menu_operations | array[int] | Yes | Menu number(s) affected (e.g., `[11, 20, 27]`) |
| source_file | string | Yes | File containing the call (e.g., `MistHelper.py`) |
| line_number | int | Yes | Line number of the API call site |
| api_function | string | Yes | Full mistapi function name (e.g., `mistapi.api.v1.orgs.sites.listOrgSites`) |
| current_behavior | string | Yes | Description of what the code currently does |
| recommended_change | string | Yes | Specific fix to apply |
| rationale | string | Yes | Why this change is needed |
| reference_doc | string | No | Path to the enriched API doc file (e.g., `documentation/api/orgs/GET_orgs_org_id_sites.md`) |

### Severity Definitions

| Severity | Definition | Examples |
|----------|------------|---------|
| Critical | Wrong endpoint used — operation returns fundamentally wrong data or performs wrong action | Calling a stats endpoint instead of events/search; calling create instead of update |
| High | Correct endpoint but missing/wrong parameters cause incomplete or incorrect results | Missing `type="all"` causing only APs returned; missing required filter |
| Medium | Pagination gap or deprecated usage that may cause data loss in large environments | No `get_all()` on paginated endpoint; using deprecated parameter |
| Low | Suboptimal but functional — best practice improvement | Per-site iteration when org-level bulk exists; missing optional parameter that improves perf |

### Tier Definitions

| Tier | Definition |
|------|------------|
| Incorrect | The current usage produces wrong or incomplete results. Data returned is missing, wrong, or the operation fails silently. |
| Suboptimal | The current usage works correctly but does not follow best practices, misses performance improvements, or uses deprecated patterns. |

## Entity: AuditReport

The complete audit output, containing metadata and all findings.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | string | Yes | Report format version (e.g., `1.0.0`) |
| generated_at | string | Yes | ISO 8601 timestamp of report generation |
| branch | string | Yes | Git branch name |
| scope | object | Yes | Audit scope metadata (see below) |
| summary | object | Yes | Aggregate statistics (see below) |
| findings | array[AuditFinding] | Yes | All findings, sorted by severity then category |

### Scope Sub-Object

| Field | Type | Description |
|-------|------|-------------|
| files_audited | array[string] | Source files analyzed |
| total_call_sites | int | Total API call sites examined |
| unique_api_functions | int | Distinct API functions found |
| menu_operations_covered | int | Menu operations with API calls |
| reference_docs_available | int | Enriched docs used for cross-reference |

### Summary Sub-Object

| Field | Type | Description |
|-------|------|-------------|
| total_findings | int | Total finding count |
| by_severity | object | Counts per severity level |
| by_tier | object | Counts per tier (Incorrect/Suboptimal) |
| by_category | object | Counts per category |
| coverage_percentage | float | Percentage of call sites reviewed (target: 100%) |

## Entity: EndpointCatalogEntry

An intermediate entity used during the audit to map each API call site to its documentation. Not included in the final report but used as working data.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| api_function | string | Full mistapi function name |
| source_file | string | Source file containing the call |
| line_number | int | Line number of the call |
| parameters_passed | array[string] | Parameter names passed at this call site |
| menu_operation | int or null | Menu number that triggers this call (if traceable) |
| doc_file | string or null | Matched enriched API doc path |
| doc_parameters | array[string] | Parameters documented for this endpoint |
| doc_gotchas | string or null | Gotchas text from the doc |
| uses_pagination | boolean | Whether `get_all()` is used after this call |
| is_paginated_endpoint | boolean | Whether the endpoint returns paginated results |

## Relationships

```
AuditReport (1) ---contains---> (N) AuditFinding
AuditFinding (N) ---references---> (1) EndpointCatalogEntry
EndpointCatalogEntry (1) ---maps-to---> (0..1) Endpoint Documentation file
EndpointCatalogEntry (N) ---called-by---> (1) Menu Operation
```

## State Transitions

This feature has no runtime state — it produces a static report. The audit workflow is:

```
Catalog API calls -> Match to docs -> Analyze each dimension -> Generate findings -> Compile report
```

## Validation Rules

- Finding IDs must be unique and sequential (`F-001`, `F-002`, ...)
- Every finding must reference a valid source file and line number
- Every finding must have a non-empty `recommended_change`
- Severity and tier must use the defined enum values
- `coverage_percentage` in the summary must equal 100.0 for a complete audit
