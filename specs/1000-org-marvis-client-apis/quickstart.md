# Quickstart: Org Marvis Client APIs Planning-to-Implementation Handoff

## Goal

Implement five new Org Marvis Client menu operations from `specs/1000-org-marvis-client-apis/spec.md` without changing architectural patterns.

## Planned Operation Set

- Insights export (safe)
- Events count (safe)
- Events search (safe, paginated, search-after)
- Stats count (safe)
- Stats search (safe, paginated, search-after)

## Menu Number Assignments

- **211**: Export Org Marvis Client Insights (safe)
- **212**: Count Org Marvis Client Events (safe)
- **213**: Search Org Marvis Client Events (safe, paginated)
- **214**: Count Org Marvis Client Stats (safe)
- **215**: Search Org Marvis Client Stats (safe, paginated)

## SDK Endpoint Mapping (mistapi 0.63.0 verified)

- Insights: `mistapi.api.v1.orgs.insights.getOrgMarvisClientInsights`
- Events Count: `mistapi.api.v1.orgs.marvisclients.countOrgMarvisClientEvents`
- Events Search: `mistapi.api.v1.orgs.marvisclients.searchOrgMarvisClientEvents`
- Stats Count: `mistapi.api.v1.orgs.stats.countOrgMarvisClientsStats`
- Stats Search: `mistapi.api.v1.orgs.stats.searchOrgMarvisClientsStats`

## Implementation Sequence

1. Add menu entries and handlers in `MistHelper.py` for all five operations.
2. Add prompt collection for optional filters and duration/window input.
3. Add search-after prompt/continuation flow for both search operations.
4. Register endpoint PK strategies in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
5. Route all outputs through existing exporter pipeline for CSV/SQLite support.
6. Add operation summaries (filters, effective window, page traversal, row counts).
7. Add/adjust tests for happy paths, invalid input, continuation errors, and dedupe invariants.
8. Update `README.md` operation count/menu references and `CHANGELOG.md` entry.

## Verification Checklist

### Static quality gates
- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py`
- `python -m black --check MistHelper.py`

### Test coverage targets
- per-operation happy path
- duration/filter validation failures
- events/stats search multi-page no-dup/no-drop checks
- malformed/expired search-after token handling
- CSV + SQLite export compatibility for every operation

### Manual behavior checks
- optional filters can be skipped cleanly
- invalid duration is rejected with corrective guidance
- search-after prompt is accepted; if endpoint does not accept token in SDK signature, handler degrades safely to first-page retrieval with explicit user guidance
- execution summary includes applied filters, window, page status, row counts

## Done Criteria

Feature moves to `/speckit.tasks` when:
- plan/research/model/contract artifacts are complete,
- all spec FRs are covered by tasks,
- no unresolved clarifications remain.
