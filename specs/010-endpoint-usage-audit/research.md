# Research: Mist API Endpoint Usage Audit

**Feature**: 010-endpoint-usage-audit  
**Date**: 2026-03-08  
**Status**: Complete — all unknowns resolved

## R1: Endpoint-to-Documentation Matching Strategy

**Decision**: Match API calls to docs via the `## mistapi SDK` section in each enriched doc file.

**Rationale**: Each of the 1,013 enriched doc files contains a `## mistapi SDK` section with the exact function call signature (e.g., `mistapi.api.v1.orgs.sites.listOrgSites()`). This provides a deterministic mapping between code call sites and documentation.

**Alternatives considered**:
- HTTP method + URL path matching: Rejected — requires reverse-engineering the SDK's URL mapping, which is fragile.
- File name convention matching: Rejected — while the pattern `{HTTP_METHOD}_{path_with_underscores}.md` is consistent, the SDK function name doesn't trivially map to this (e.g., `listOrgSites` vs `GET_orgs_org_id_sites`). The SDK section is more reliable.

**Matching workflow**:
1. Extract all `mistapi.api.v1.*` call sites from source code (function name + parameters)
2. Build an index of all doc files by parsing the `## mistapi SDK` section
3. Join on function name to get the endpoint's documentation
4. Flag unmatched calls (API calls without docs or docs without calls)

**Coverage**: All 1,013 doc files have the `## mistapi SDK` section (verified in Feature 009 enrichment).

## R2: Pagination Audit Methodology

**Decision**: Audit pagination by checking whether each list/search endpoint call uses `mistapi.get_all()` for complete result retrieval.

**Rationale**: The `mistapi` SDK provides `mistapi.get_all(response, mist_session)` as the standard pagination helper. MistHelper uses this pattern 30+ times. Operations that call a list/search endpoint without `mistapi.get_all()` may silently truncate results.

**Key facts**:
- Mist API default page limit: 100 records (when limit not specified)
- MistHelper override: `DEFAULT_API_PAGE_LIMIT = 1000` (max allowed by API)
- Even with limit=1000, datasets larger than 1000 records require cursor-based pagination
- `mistapi.get_all()` handles cursor-based pagination automatically

**Audit criteria**:
- **Incorrect**: A list/search call that omits both `limit` and `get_all()`, potentially returning only 100 records
- **Incorrect**: A list/search call with `limit=1000` but no `get_all()`, potentially truncating at 1000
- **Suboptimal**: Using a manual pagination loop when `get_all()` would be simpler
- **Correct**: Using `get_all()` after the initial API call

**Alternatives considered**:
- Only flag missing `get_all()`: Rejected — some endpoints return small datasets where pagination isn't needed (e.g., `getSelf`). The audit should be endpoint-aware.
- Flag all non-paginated calls: Rejected — single-entity `get` calls (e.g., `getSiteDevice(device_id)`) don't paginate.

## R3: WebSocket Audit Differentiation

**Decision**: Audit WebSocket operations (menus 5-8, 87-89) using a separate checklist focused on the REST initiation call, not the WebSocket streaming itself.

**Rationale**: WebSocket operations follow a hybrid pattern:
1. **REST call** initiates the command (e.g., `servicePingFromSsr()`)
2. **WebSocket connection** subscribes for streaming results
3. Results arrive asynchronously via WebSocket messages

The REST initiation call is auditable against the same API documentation. The WebSocket streaming layer uses the SDK's internal WebSocket manager and doesn't map to REST endpoints.

**Audit criteria for WebSocket operations**:
- Verify the REST initiation call uses the correct endpoint and parameters
- Verify device type validation (e.g., SSR-only commands aren't sent to APs)
- Verify timeout handling exists
- Skip WebSocket message format validation (SDK-internal)

**Alternatives considered**:
- Full WebSocket protocol audit: Rejected — WebSocket frame format is SDK-internal, not documented in the enriched API docs.
- Exclude WebSocket operations entirely: Rejected — the REST setup calls are auditable and may have parameter issues.

## R4: Cross-File Scope

**Decision**: Audit MistHelper.py as primary, maps_manager.py as secondary, wsgi.py as tertiary.

**Rationale**:
- **MistHelper.py** (~44K lines): 300+ API call sites, 77+ unique functions — the bulk of the audit
- **maps_manager.py**: 50+ API call sites, focused on map/zone CRUD operations. All API calls also appear in MistHelper.py — no unique endpoints. Uses `type="all"` correctly on all `listSiteDevices` calls.
- **wsgi.py**: Single API call (`getSelf`) for org_id resolution — trivial, included for completeness

**Key finding**: maps_manager.py has NO unique API calls not also used in MistHelper.py. However, it may use the same endpoints with different parameters, so it's still worth auditing for parameter correctness.

## R5: Known Pitfall Patterns

**Decision**: Pre-seed the audit with known pitfalls from project documentation, then systematically discover new ones.

**Known pitfalls (from agents.md and copilot-instructions.md)**:

| Pitfall | Description | Pre-audit Status |
|---------|-------------|------------------|
| `listSiteDevices` type filter | Defaults to APs only without `type="all"` | All 23 calls pass `type` correctly |
| Dash 3.x `app.run_server()` | Deprecated, use `app.run()` | maps_manager.py uses correct pattern |
| Rate limiting | HTTP 429 handling | Auto-rotates tokens, properly handled |
| `listOrgDevices` type filter | Same default-to-APs behavior | Needs audit — not yet verified |

**Audit should discover**:
- Missing required parameters (not just `type`)
- Org-level vs site-level scope mismatches
- Missing `get_all()` on paginated endpoints
- Deprecated parameters documented in `## Gotchas` sections
- Endpoints with documented gotchas that MistHelper ignores

## R6: Report Schema Design

**Decision**: Use a flat JSON array of finding objects with a companion Markdown summary.

**Rationale**: A flat array is easiest to filter, sort, and process. The Markdown summary provides human-readable overview with statistics and top findings. Both files live in `specs/010-endpoint-usage-audit/`.

**Finding object schema** (detailed in data-model.md):
- Unique finding ID
- Severity (Critical/High/Medium/Low)
- Tier (Incorrect/Suboptimal)
- Category (endpoint-selection/parameter-usage/pagination/deprecation/best-practice)
- Menu operation(s) affected
- Source file and line number
- Current behavior description
- Recommended change
- Rationale
- Reference doc path

**Alternatives considered**:
- Nested JSON by category: Rejected — harder to sort by severity across categories.
- SQLite database: Rejected — overkill for a one-time report; Markdown/JSON more accessible.
- Single Markdown only: Rejected — user specified JSON + Markdown in clarification Q3.
