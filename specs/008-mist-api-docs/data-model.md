# Data Model: Mist API Endpoint Reference Documentation

**Feature**: 008-mist-api-docs | **Date**: 2026-03-06

## Entities

### OpenApiSpec

The parsed OpenAPI 3.1 specification loaded from `documentation/mist-api-openapi31json.json`.

**Fields**:
- `paths`: dict — URL path → HTTP method → operation definition
- `components.schemas`: dict — schema name → JSON Schema definition (1,799 entries)
- `tags`: list — tag metadata with name and description (206 entries)
- `info`: dict — API version, title, description

**Relationships**: Contains all Operation and Schema entities.

### Operation

A single API operation extracted from the spec. One per HTTP method + URL path combination.

**Fields**:
- `method`: str — HTTP method (GET, POST, PUT, DELETE, PATCH)
- `path`: str — URL path (e.g., `/api/v1/orgs/{org_id}/sites`)
- `operation_id`: str — unique identifier (e.g., `listOrgSites`)
- `tags`: list[str] — OpenAPI tags (e.g., `["Orgs Sites"]`)
- `summary`: str — one-line description
- `description`: str — detailed description
- `parameters`: list[Parameter] — path, query, and header parameters
- `request_body`: Schema | None — request body schema (POST/PUT/PATCH)
- `responses`: dict[str, ResponseDef] — status code → response definition
- `deprecated`: bool — whether the endpoint is deprecated

**Relationships**: Belongs to one or more Tags. Has zero or more Parameters. Has zero or one RequestBody. Has one or more Responses.

**Derived Fields**:
- `category`: str — first word of first tag, lowercased (e.g., `"orgs"`)
- `filename`: str — `{METHOD}_{path_slug}.md`
- `mistapi_path`: str — `mistapi.api.v1.{scope}.{resource}.{operation_id}()`
- `output_dir`: str — `documentation/api/{category}/`

### Parameter

A single parameter for an operation.

**Fields**:
- `name`: str — parameter name
- `location`: str — "path", "query", or "header"
- `param_type`: str — JSON Schema type (string, integer, boolean, array, etc.)
- `required`: bool — whether the parameter is required
- `default`: any | None — default value if not provided
- `enum`: list | None — allowed values
- `description`: str — parameter description

### Schema

A JSON Schema definition, fully resolved (all `$ref` dereferenced).

**Fields**:
- `schema_type`: str — "object", "array", "string", etc.
- `properties`: dict[str, Schema] — nested properties (for object types)
- `items`: Schema | None — array item schema
- `required`: list[str] — required property names
- `description`: str — schema description
- `enum`: list | None — allowed values
- `format`: str | None — format hint (e.g., "uuid", "date-time")
- `all_of` / `one_of` / `any_of`: list[Schema] | None — composition schemas

### ResponseDef

A response definition for a specific HTTP status code.

**Fields**:
- `status_code`: str — HTTP status code ("200", "400", "401", etc.)
- `description`: str — response description
- `content_type`: str — media type (typically "application/json")
- `schema`: Schema | None — response body schema

### Tag

An OpenAPI tag grouping related operations.

**Fields**:
- `name`: str — tag name (e.g., "Orgs Sites")
- `description`: str — tag description
- `category`: str — derived first word (e.g., "orgs")
- `operations`: list[Operation] — operations belonging to this tag

### IndexEntry

A single entry in the master INDEX.md file.

**Fields**:
- `tag_name`: str — OpenAPI tag name
- `method`: str — HTTP method
- `path`: str — URL path
- `operation_id`: str — operation identifier
- `filename`: str — relative path to the markdown file
- `summary`: str — one-line description

## State Transitions

This feature has no runtime state — it is a one-shot generation pipeline:

```
OpenAPI JSON File → Parse → Resolve $refs → Generate Raw MD → AI Enrichment → Done
```

No data is updated after initial generation. Regeneration starts from scratch.

## Validation Rules

- Every operation MUST have a non-empty `operation_id`
- Every operation MUST have at least one tag
- File naming MUST produce unique filenames (enforced by method+path uniqueness)
- Schema resolution MUST terminate (guaranteed by 0 circular refs in current spec)
- Every output file MUST contain all mandatory sections (even if some say "None")
