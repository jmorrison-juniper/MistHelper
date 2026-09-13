# Research: Mist API Endpoint Reference Documentation

**Feature**: 008-mist-api-docs | **Date**: 2026-03-06

## R1: OpenAPI 3.1 Spec Structure

**Decision**: Use `documentation/mist-api-openapi31json.json` (17MB) as the sole authoritative source for generation.

**Rationale**: The JSON format is faster to parse than YAML (stdlib `json` vs third-party `pyyaml`). The 3.1 version supersedes the older 3.0 files. Both JSON and YAML contain identical data — no need to cross-reference.

**Findings**:
- **1,013 total operations** across **206 tags**
- **1,799 schema definitions** in `components.schemas`
- **1,177 unique `$ref` targets** referenced across all schemas
- **0 self-referencing schemas** — no circular ref handling needed
- **Max ref nesting depth: 6** (schema `ap_template` → `ap_template_matching` → ... → leaf). Most schemas (65%) have depth 0 (no nested refs).
- Depth distribution: 0=131, 1=47, 2=17, 3=1, 4=2, 5=1, 6=1 (sample of 200 schemas)

**Alternatives considered**:
- YAML source: Rejected — requires `pyyaml` dependency, slower parsing, identical data
- Dual-source (JSON + YAML): Rejected — adds complexity for zero benefit

## R2: Tag-to-Directory Mapping

**Decision**: Map the first word of each OpenAPI tag to a lowercase directory name.

**Rationale**: All 206 tags follow the pattern `{Category} {Resource}` (e.g., "Orgs Sites", "Sites Devices"). The first word consistently maps to one of 8 categories.

**Findings**:
| Tag Prefix | Operation Count | Directory Name |
|------------|----------------|----------------|
| Orgs | 449 | `orgs/` |
| Sites | 330 | `sites/` |
| Utilities | 103 | `utilities/` |
| MSPs | 50 | `msps/` |
| Constants | 27 | `constants/` |
| Installer | 23 | `installer/` |
| Self | 18 | `self/` |
| Admins | 13 | `admins/` |

**Alternatives considered**:
- Flat structure (all 1,013 files in one directory): Rejected — too many files for navigation
- Two-level nesting (e.g., `orgs/sites/`): Rejected — adds complexity, most tags only have 2 words

## R3: File Naming Convention

**Decision**: `{METHOD}_{path_slug}.md` where path_slug is the URL path with `/api/v1/` stripped, braces removed, and slashes replaced with underscores.

**Rationale**: Produces unique, readable, grep-friendly filenames that directly map to the API path.

**Findings**:
- Example: `GET /api/v1/orgs/{org_id}/sites` → `GET_orgs_org_id_sites.md`
- Example: `DELETE /api/v1/orgs/{org_id}/sites/{site_id}` → `DELETE_orgs_org_id_sites_site_id.md`
- Longest filename: 89 chars (`GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary-trend.md`) — within Windows MAX_PATH limits
- All filenames are unique (method + path combination is unique per OpenAPI spec)

**Alternatives considered**:
- Using operationId as filename: Rejected — not grep-friendly for path-based lookups
- Hashing long paths: Rejected — loses readability

## R4: operationId to mistapi Mapping

**Decision**: Map `operationId` directly to `mistapi.api.v1.{scope}.{resource}.{operationId}()` where scope and resource are derived from the tag name.

**Rationale**: Thomas Munzer's mistapi library auto-generates function names from the OpenAPI operationId. The package structure mirrors the tag hierarchy.

**Findings**:
- Tag "Orgs Sites" → `mistapi.api.v1.orgs.sites`
- Tag "Sites Devices" → `mistapi.api.v1.sites.devices`
- operationId `listOrgSites` → function `listOrgSites()`
- Full path: `mistapi.api.v1.orgs.sites.listOrgSites()`
- Multi-word resource names (e.g., "Orgs NAC Tags") map to snake_case module names (e.g., `nac_tags`)

**Alternatives considered**:
- Importing mistapi and inspecting at runtime: Rejected — adds runtime dependency, not needed when the mapping is deterministic

## R5: Schema Dereferencing Strategy

**Decision**: Fully resolve all `$ref` references inline at generation time, with no depth limit. Use iterative resolution (not recursive) with a visited-set to prevent infinite loops (though none exist in the current spec).

**Rationale**: User explicitly chose full resolution (Clarification Q1, Option B). Self-contained files are the priority. Max observed depth is 6, which is manageable.

**Findings**:
- No circular/self-referencing schemas exist (verified programmatically)
- Deepest chain: 6 levels (e.g., `ap_template` → ... → leaf properties)
- Most schemas are shallow (65% at depth 0, 89% at depth <=1)
- Estimated largest resolved schema: ~500 properties when fully flattened (e.g., `network_template`)
- Output file sizes: majority <200 lines; deepest schemas may reach 1,000-2,000 lines

**Alternatives considered**:
- Depth-limited resolution: Rejected by user (Clarification Q1)
- Lazy resolution with cross-file links: Rejected — violates SC-004 self-containment

## R6: Two-Phase Generation Approach

**Decision**: Phase 1 = Python script generates raw markdown from OpenAPI spec. Phase 2 = AI agent rewrites each file with enriched content.

**Rationale**: User explicitly chose hybrid approach (Clarification Q2). Script ensures consistency and repeatability for all 1,013 files. AI enrichment adds domain knowledge that can't be extracted from the spec alone.

**Findings**:
- Script output per file: ~50-200 lines of structured data (parameters table, schema JSON, response codes)
- AI enrichment adds: 2-5 paragraph usage context, gotcha notes, cross-references to related endpoints, MistHelper-specific notes
- No code examples included (Clarification Q3)
- Estimated AI enrichment time: ~30 seconds per file × 1,013 files = ~8.4 hours of AI processing (can be batched across sessions)

**Alternatives considered**:
- Script-only (no AI enrichment): Rejected by user (Clarification Q2)
- AI-only (no script): Rejected — too slow, inconsistent formatting across 1,013 files

## R7: Markdown Template Structure

**Decision**: Each endpoint file follows a fixed template with consistent section headers for reliable machine parsing.

**Template**:
```markdown
# {operationId}

> {summary}

## HTTP

`{METHOD} {path}`

## Description

{description from OpenAPI spec}

## Authentication

{auth requirements}

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|

## Request Body

{schema as JSON with descriptions, or "None"}

## Response

### {status_code}

{response schema as JSON with descriptions}

## Errors

| Status | Description |
|--------|-------------|

## Pagination

{pagination details or "Not paginated"}

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.{scope}.{resource}.{operationId}()`

## Usage Context

{AI-enriched: when to use this endpoint, common use cases}

## Gotchas

{AI-enriched: known pitfalls, non-obvious behaviors}

## Related Endpoints

{AI-enriched: cross-references to endpoints commonly used together}

## MistHelper Notes

{AI-enriched: how MistHelper uses this endpoint, relevant menu operations}
```
