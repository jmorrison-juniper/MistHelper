# Data Model: Mist API Documentation Enrichment

**Feature**: 009-api-docs-enrichment
**Date**: 2026-03-06 (updated with clarification answers)

## Entities

### EndpointFile

An existing markdown file in `documentation/api/{category}/`. The AI agent reads and modifies these files.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| file_path | Path | File system | Absolute path to the .md file |
| category | str | Parent directory name | One of: admins, self, installer, constants, msps, utilities, sites, orgs |
| http_method | str | `## HTTP` section | GET, POST, PUT, DELETE |
| url_path | str | `## HTTP` section | API path (e.g., `/api/v1/orgs/{org_id}/sites`) |
| description | str | `## Description` section | Endpoint description text |
| is_deprecated | bool | Description/title content | Whether endpoint is marked deprecated |
| has_pagination | bool | `## Pagination` section | Whether endpoint supports pagination |
| parameters | list[str] | `## Parameters` section | Parameter names listed |
| required_body_fields | list[str] | `## Request Body` section | Required fields from request schema |
| mistapi_sdk_path | str | `## mistapi SDK` section | SDK call path (e.g., `mistapi.api.v1.orgs.sites.listOrgSites()`) |

### MistHelperMapping

Derived by the AI agent scanning MistHelper.py for `mistapi.api.v1.*` calls.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| operation_id | str | Regex match in MistHelper.py | The mistapi function name called |
| full_sdk_path | str | Regex match in MistHelper.py | Full `mistapi.api.v1.scope.resource.operation` path |
| menu_operations | list[int] | Context analysis | Menu operation numbers that call this endpoint |
| special_notes | str | Context analysis | Special parameter handling (e.g., `type=all`) |

### EnrichmentContent

The 4 sections the AI agent writes into each endpoint file.

| Field | Type | Description |
|-------|------|-------------|
| usage_context | str | Markdown text for the Usage Context section |
| gotchas | str | Markdown text for the Gotchas section |
| related_endpoints | str | Markdown text with relative links to related endpoint files |
| misthelper_notes | str | Markdown text describing MistHelper usage or "Not currently used" |

### ResourceGroup

Endpoints grouped by shared resource path for cross-referencing.

| Field | Type | Description |
|-------|------|-------------|
| base_path | str | Common path prefix (e.g., `/api/v1/orgs/{org_id}/sites`) |
| endpoints | list[EndpointFile] | All endpoints sharing this base path |
| category | str | Primary category for the group |

## Relationships

```text
EndpointFile 1──1 EnrichmentContent    (each endpoint gets exactly one enrichment)
EndpointFile *──1 ResourceGroup        (each endpoint belongs to one resource group)
EndpointFile *──0..1 MistHelperMapping (127 endpoints have mappings, 886 do not)
ResourceGroup 1──* EndpointFile        (each group contains 1+ endpoints)
```

## State Transitions

### Endpoint File States

```text
placeholder ──[enrich]──> enriched ──[regenerate]──> placeholder
     │                        │
     └── Contains "*To be     └── All 4 sections contain
         enriched by AI           substantive content
         agent.*" text
```

The `regenerate` transition occurs when `scripts/generate_api_docs.py` is re-run, resetting all files to placeholder state. The AI agent handles both states identically (overwrites section content).

## Validation Rules

1. **usage_context**: Must contain at least one bullet point with a concrete use case
2. **gotchas**: Must contain at least one bullet point or "No known gotchas for this endpoint."
3. **related_endpoints**: Must contain relative markdown links covering the full relationship graph (CRUD siblings, parent, sub-resources, cross-scope). All link targets must exist on disk.
4. **misthelper_notes**: Must contain either menu operation reference(s) or "Not currently used by MistHelper"
5. **Cross-category links**: Must use `../` prefix (e.g., `../orgs/GET_orgs_org_id.md`)
6. **Same-category links**: Must use bare filename (e.g., `GET_sites_site_id.md`)
