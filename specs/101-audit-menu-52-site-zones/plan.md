# Plan: Export Site Zones (menu_id:52)

## High-level approach
1. Discover/confirm SiteConfigExporter.zones API contract and pagination behavior.
2. Implement exporter wrapper in MistHelper that calls the API, normalizes fields, and returns list of dicts.
3. Add DataExporter plumbing to write CSV/SQLite using existing patterns (respecting ENDPOINT_PRIMARY_KEY_STRATEGIES).
4. Add unit/integration tests and sample fixtures.
5. Update README/menu index and add spec to specs/101-audit-menu-52-site-zones.

## Deliverables
- Spec artifact (this document) placed under specs/101-audit-menu-52-site-zones
- Code: new or updated SiteConfigExporter.zones integration point and MistHelper menu entry
- SQL export mapping/entry in ENDPOINT_PRIMARY_KEY_STRATEGIES (composite natural PK)
- Unit and integration tests + test fixtures
- README/menu entry updated with operation count and short description

## Milestones
- M1: API contract verification & spec finalized (this spec)
- M2: Implementation (exporter + MistHelper menu hook)
- M3: Tests (unit + integration) and sample fixture data
- M4: Documentation and README update
- M5: Validation & merge

## Verification plan
- Unit tests: simulate API responses (empty, one zone, many zones, malformed) and assert normalization and raw_json inclusion
- Integration test: run the menu operation in a sandbox with a recorded fixture and verify CSV/SQLite output schema and primary key behavior
- Manual check: run operation for a known site and validate CSV and SQLite contents (unique PKs, indexes)
- CI: ensure python -m py_compile passes, and tests run cleanly

## Rollback / Safety
- Implementation should be additive and non-destructive; no live changes to Mist configuration.
- If primary key ambiguity discovered post-merge, update ENDPOINT_PRIMARY_KEY_STRATEGIES and rerun migrations of export tables.

