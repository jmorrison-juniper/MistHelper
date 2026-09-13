# Feature Specification: Mist API Endpoint Reference Documentation

**Feature Branch**: `008-mist-api-docs`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Create comprehensive per-endpoint Mist API documentation markdown files in the documentation folder. One markdown file per API operation (GET, POST, PUT, DELETE, etc.). Files are authored for AI consumption, not humans. Sources: Juniper OpenAPI 3.1 spec, Thomas Munzer's mistapi_python library, existing HTML docs and legacy Mist portal files. Raw source files must also be saved to the documentation folder."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Agent Looks Up Endpoint Details for Feature Implementation (Priority: P1)

An AI agent is implementing a new MistHelper feature (e.g., "list all org WLANs"). The agent needs to know the exact HTTP method, URL path, required/optional parameters, request body schema, response schema, error codes, pagination behavior, and the corresponding `mistapi` Python function call. The agent opens one markdown file and finds everything needed to write correct code on the first attempt.

**Why this priority**: This is the core value proposition. Every other MistHelper feature depends on accurate API knowledge. Eliminating multi-source lookups saves significant time and prevents errors.

**Independent Test**: Can be fully tested by selecting any 5 random endpoints, verifying each markdown file contains all required sections (HTTP details, parameters, schemas, mistapi function, examples), and confirming the information matches the OpenAPI spec.

**Acceptance Scenarios**:

1. **Given** an AI agent needs to call `GET /api/v1/orgs/{org_id}/inventory`, **When** the agent reads `documentation/api/orgs/GET_orgs_org_id_inventory.md`, **Then** it finds the full URL, all query parameters with types and defaults, response JSON schema with field descriptions, rate limit notes, pagination details, and the `mistapi.api.v1.orgs.inventory.getOrgInventory()` function signature.
2. **Given** an AI agent needs to create a site, **When** the agent reads `documentation/api/orgs/POST_orgs_org_id_sites.md`, **Then** it finds the request body schema with required vs optional fields, response schema with field types and descriptions, and the `mistapi.api.v1.orgs.sites.createOrgSite()` function signature.
3. **Given** an endpoint has been deprecated or changed, **When** the agent reads the endpoint file, **Then** it finds deprecation warnings and migration guidance if applicable.

---

### User Story 2 - AI Agent Discovers Available Endpoints for a Domain (Priority: P2)

An AI agent is asked to "get all client data for an org" but doesn't know which endpoints exist. The agent needs to browse by category to discover all client-related endpoints (wireless clients, wired clients, SDK clients, WAN clients, NAC clients).

**Why this priority**: Discovery is the second most common use case. Agents need to find endpoints they don't already know about.

**Independent Test**: Can be tested by verifying a category index file (e.g., `documentation/api/INDEX.md`) lists all endpoints organized by tag/category, and each entry links to the correct detail file.

**Acceptance Scenarios**:

1. **Given** an AI agent needs client-related endpoints, **When** it reads the index file, **Then** it finds all 6 client categories (Wireless, Wired, WAN, SDK, NAC, Marvis) with their endpoint files listed.
2. **Given** an AI agent needs to understand the full API surface, **When** it reads the index, **Then** all 1,013 operations are listed and categorized by their OpenAPI tags.

---

### User Story 3 - Raw Source Files Available Locally (Priority: P3)

The documentation folder contains all raw source files (OpenAPI 3.1 JSON/YAML, downloaded HTML pages, mistapi Python source references) so that future documentation regeneration does not require web access.

**Why this priority**: Eliminates external dependencies. Corporate proxy/Zscaler issues make web fetching unreliable.

**Independent Test**: Can be tested by verifying all source files exist in the documentation folder and are non-empty.

**Acceptance Scenarios**:

1. **Given** the documentation folder, **When** listing its contents, **Then** it contains `mist-api-openapi31json.json`, `mist-api-openapi31yaml.yaml`, and any downloaded HTML reference pages.
2. **Given** network access is unavailable, **When** an agent needs to regenerate docs, **Then** it can do so entirely from local files.

---

### Edge Cases

- What happens when an endpoint has no request body (GET/DELETE)? The "Request Body" section is omitted or states "None".
- What happens when an endpoint is tagged with multiple OpenAPI tags? It appears in each relevant category in the index.
- What happens when the OpenAPI spec has no description for a parameter? The file notes "No description provided in spec" rather than leaving it blank.
- What happens when an endpoint supports both query parameters and path parameters? Both are documented in separate subsections.
- What happens when an endpoint requires specific permissions (e.g., MSP-only)? The file notes required privilege level.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Generation MUST follow a two-phase approach: (1) A Python script parses the OpenAPI 3.1 spec and generates one raw markdown file per API operation (~1,013 files) containing all extracted data (parameters, schemas, paths, operationIds). (2) An AI agent then reads each raw file and rewrites it with interpreted, enriched content — adding context, usage guidance, common patterns, and clearer schema explanations optimized for AI consumption.
- **FR-002**: Each markdown file MUST contain these sections: Title, HTTP Method & Path, Description, Authentication requirements, Path Parameters, Query Parameters, Request Body Schema, Response Schema, Error Codes, Pagination behavior, Rate Limiting notes, and mistapi Python function signature. The AI rewrite phase MUST enrich each file with: usage context and common use cases, recommended parameter combinations, known gotchas and pitfalls, integration patterns with related endpoints (cross-references), and MistHelper-specific notes where applicable. No curl or Python code examples are included.
- **FR-003**: System MUST organize files into subdirectories matching the API tag hierarchy: `documentation/api/orgs/`, `documentation/api/sites/`, `documentation/api/msps/`, `documentation/api/self/`, `documentation/api/constants/`, `documentation/api/installer/`, `documentation/api/utilities/`, `documentation/api/admins/`.
- **FR-004**: System MUST generate a master index file (`documentation/api/INDEX.md`) listing every endpoint grouped by OpenAPI tag, with relative links to each detail file.
- **FR-005**: File naming MUST follow the pattern `{METHOD}_{path_segments}.md` (e.g., `GET_orgs_org_id_sites.md`, `POST_orgs_org_id_sites.md`, `DELETE_orgs_org_id_sites_site_id.md`).
- **FR-006**: System MUST save all raw source files (OpenAPI 3.1 JSON, OpenAPI 3.1 YAML) to the documentation folder for offline regeneration.
- **FR-007**: Each file MUST include the `mistapi` Python SDK function path (e.g., `mistapi.api.v1.orgs.inventory.getOrgInventory`) mapped from the OpenAPI `operationId`.
- **FR-008**: Schema definitions MUST be fully resolved (dereferenced from `$ref`) to unlimited depth so each file is completely self-contained — no cross-referencing required. Files may exceed 2,000 lines for deeply nested schemas; this is acceptable because AI agents can read specific line ranges and the self-contained guarantee (SC-004) takes priority over file size.
- **FR-009**: Parameter documentation MUST include: name, location (path/query/header), type, required/optional, default value, allowed values (enum), and description.
- **FR-010**: Response documentation MUST include the HTTP status code, content type, and the full JSON schema with field names, types, and descriptions.
- **FR-011**: The Authentication section MUST render per-endpoint `security` requirements from the OpenAPI spec. If an endpoint has no per-endpoint security override, the section MUST display the spec-level default: "Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation."

### Key Entities

- **API Endpoint**: A unique HTTP method + URL path combination. Has parameters, request/response schemas, tags, and an operationId.
- **OpenAPI Tag**: A category label grouping related endpoints (e.g., "Orgs Inventory", "Sites Devices"). 206 tags exist in the current spec.
- **Operation**: A single API action (GET, POST, PUT, DELETE, PATCH) on a specific path. 1,013 total operations.
- **Schema**: A JSON Schema definition describing request bodies or response payloads. Referenced via `$ref` in the OpenAPI spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 1,013 API operations have a corresponding markdown file in the documentation folder.
- **SC-002**: Every markdown file contains all mandatory sections (Method, Path, Parameters, Response Schema, mistapi function).
- **SC-003**: An AI agent can find any endpoint's documentation in under 2 file reads (index lookup + detail file).
- **SC-004**: All information in a single endpoint file is self-contained — no need to read other files or access the web to understand the endpoint.
- **SC-005**: The index file correctly categorizes all 1,013 operations across 206 tags with working relative links.

## Assumptions

- The OpenAPI 3.1 spec files (already downloaded at 17MB JSON, 11MB YAML) are the authoritative source of truth for endpoint definitions.
- The `operationId` field in the OpenAPI spec maps directly to the `mistapi` Python function name (e.g., operationId `listOrgSites` maps to `mistapi.api.v1.orgs.sites.listOrgSites`).
- The mistapi Python package structure follows `mistapi.api.v1.{scope}.{resource}.{operationId}` where scope is `orgs`, `sites`, `const`, etc.
- Files are optimized for AI token efficiency: structured with consistent headers, tables for parameters, and code blocks for schemas — no narrative prose.
- The existing OpenAPI 3.0 files (`mist-api-openapi3json.json`, `mist-api-openapi3yaml.yaml`) are superseded by the 3.1 versions but retained for reference.
- Rate limiting details not present in the OpenAPI spec are documented as "Standard Mist API rate limits apply" with a reference to general rate limit documentation.

## Clarifications

### Session 2026-03-06

- Q: Should schema dereferencing have a max nesting depth to limit file size, or resolve fully regardless of depth? → A: Fully resolve all schemas regardless of depth (Option B). Self-contained files are the priority; large files are acceptable.
- Q: Should docs be generated by a Python script, an AI agent interactively, or a hybrid approach? → A: Hybrid — Python script generates raw data files from the OpenAPI spec first, then AI agent rewrites each file with interpreted/enriched content afterward.
- Q: How much interpretation should the AI add beyond raw OpenAPI data? → A: Heavy enrichment without examples — add usage context, common pitfalls, integration patterns, MistHelper-specific notes, and cross-references to related endpoints, but no curl or Python code examples.
