# Feature Specification: Mist API Read Operation -- countOrgJsiSirt

**Feature Branch**: `519-mist-count-org-jsi-sirt`
**Created**: 2026-06-29
**Status**: Draft
**Input**: User description: "Catalog the missing Mist API GET endpoint `countOrgJsiSirt` and add it as a new MistHelper menu item."

## Source Endpoint

- **operationId**: `countOrgJsiSirt`
- **Method**: `GET`
- **Path**: `/api/v1/orgs/{org_id}/jsi/sirt/count`
- **Tag**: `Orgs JSI`
- **mistapi SDK module**: `mistapi.api.v1.orgs.jsi.sirt.count`

### Description

Get count of SIRT advisories grouped by specified field

### Path Parameters

- `org_id` (required)

### Query Parameters

- `distinct` (required)
- `limit` (optional)
- `start` (optional)
- `end` (optional)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read-only data retrieval (Priority: P1)

A junior NOC engineer launches MistHelper, selects the new menu item, supplies the required identifiers
(org / site / device as applicable), and receives the JSON payload exposed by `countOrgJsiSirt` -- exported to the
configured storage backend (CSV, SQLite, or ArangoDB+Redis) under `data/`.

**Why this priority**: This is a read-only Mist API call -- no destructive effect, so it can ship as P1
without elaborate guardrails. Coverage of this endpoint unlocks data the user cannot currently extract
from MistHelper without writing custom code.

**Independent Test**: Run the new menu item against a known org/site; verify the resulting file exists
under `data/`, has at least one row when the upstream API returns data, and that re-running the menu
item upserts cleanly into SQLite (no duplicate primary keys).

**Acceptance Scenarios**:

1. **Given** valid credentials and org context, **When** the user selects the new menu item, **Then**
   MistHelper invokes `mistapi.api.v1.orgs.jsi.sirt.count.countOrgJsiSirt()` exactly once per required scope and persists results.
2. **Given** an SSH or container session, **When** the user is prompted for identifiers, **Then**
   `safe_input()` handles EOF gracefully and the operation exits 0 without a traceback.
3. **Given** repeated runs, **When** SQLite is the active backend, **Then** rows upsert by the configured
   primary key strategy (no duplicates).

### Edge Cases

- The API returns an empty list -> menu reports "no data returned" and exits cleanly.
- The user supplies an unknown org/site UUID -> 404 from Mist API surfaces as a logged warning, not a traceback.
- Rate limiting (429) triggers the adaptive delay system; no manual intervention required.
- The user runs with `--fast` -> retries cap respected, concurrency raised.
- Output backend is ArangoDB+Redis -> graph edges (per spec 188) and Redis caches are updated consistently.

## Requirements *(mandatory)*

**FR-001**: Provide a new menu item that invokes `mistapi.api.v1.orgs.jsi.sirt.count.countOrgJsiSirt()` via the `mistapi` SDK.
**FR-002**: Collect required inputs using `safe_input()` so the operation works in SSH and container contexts.
**FR-003**: Apply rate limiting and retry logic consistent with adjacent menu items (delay_metrics.json + tuning_data.json).
**FR-004**: Persist results using `DataExporter.write_with_format_selection(data, filename, api_function_name=...)` so CSV/SQLite/ArangoDB backends all work.
**FR-005**: Register the operationId `countOrgJsiSirt` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with the correct PK strategy (natural / composite / auto-increment).
**FR-006**: Log `INFO` before the API call and `DEBUG` with response counts after, ASCII-only, per Action Logging principle.
**FR-007**: Add inline comments on every new executable line per Inline Comments principle.
**FR-008**: Update README.md menu table and CHANGELOG.md with the new operation number.

## Constitution & Instructions Conformance

- Inline comments on every executable line (Constitution VI -- NON-NEGOTIABLE).
- Action logging before/after every meaningful step (Constitution VII -- NON-NEGOTIABLE).
- 5-Item Rule: implementation function <=25 lines, <=5 params, <=5 nesting blocks.
- ASCII-only logging (no Unicode/emoji).
- Multi-backend output via `DataExporter`.
- `safe_input()` wraps all `input()` calls.
- Primary key strategy registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- README menu table + CHANGELOG entry updated in the same PR.

## Non-Functional Requirements

- **Performance**: Single-page request <=5s; full paginated retrieval bounded by Mist API rate limits.
- **Security**: API token loaded from `.env`; never logged.
- **Compatibility**: Python 3.13+, mistapi 0.59+, runs in Podman container and on bare Windows venv.

## Out of Scope

- Write operations against the same path (POST/PUT/PATCH/DELETE) -- separate spec when needed.
- UI changes beyond the new menu item label.
- Database schema migrations beyond the new primary-key strategy entry.

## Acceptance Criteria Checklist

- [ ] Menu item added with sequential operation number.
- [ ] `ENDPOINT_PRIMARY_KEY_STRATEGIES` updated.
- [ ] Inline comments + action logging on every new line.
- [ ] `DataExporter.write_with_format_selection` used for output.
- [ ] `safe_input()` used for prompts.
- [ ] README.md and CHANGELOG.md updated.
- [ ] `python -m py_compile MistHelper.py`, `python -m ruff check`, `python -m black --check` all green.
- [ ] Test invocation via `python MistHelper.py --menu <num>` returns 0 on a known org.
