# Spec

## Summary of current state
- Menu: 12 - Export full device inventory
- Function reference: OrgInventoryExporter.inventory
- Spec dir: specs/024-audit-menu-12-org-inventory
- SQL export relevant: yes
- Notes: SQL compliant via APIDataFetcher, missing unit tests

## Purpose
Provide a menu operation that exports the complete device inventory for an organization, producing SQL-upsertable output (SQLite/CSV dual-backend) and a validated CSV export. The exporter must be idempotent, support upserts for incremental runs, and be test-covered.

## Stakeholders
- NOC Engineers (primary users)
- Platform Engineers / Release Owners
- QA/Test Engineers
- Documentation Owner

## Acceptance Criteria
1. The menu item calls OrgInventoryExporter.inventory and returns complete per-device records matching Mist API schema.
2. SQL output: data can be loaded into SQLite with deterministic upsert semantics (no duplicate business-rows after repeated runs).
   - Upsert behaviour: use INSERT OR REPLACE (or equivalent UPSERT) keyed by the defined primary key strategy.
   - Export must create/ensure appropriate indexes for query performance (org_id, mac, serial, name where applicable).
3. CSV output: columns stable and documented; importing CSV into the DB yields same rows as direct SQL export.
4. Error handling: API fetch failures are retried with exponential backoff and failures surface useful diagnostics.
5. Tests: unit tests cover exporter logic + APIDataFetcher integration mocks; integration tests validate SQL upsert behavior against a SQLite test DB.
6. Documentation: README/menu updated with menu entry and sample outputs (CSV & schema).

## Required API function name
- OrgInventoryExporter.inventory (per metadata)

## Recommended primary-key strategy
- recommended: natural_pk
  - primary_key fields: ["id"] (API-provided device UUID). Consider composite addition for safety: ["id", "org_id"] if exporter may be used across org-scoped runs.
  - rationale: devices expose stable UUIDs from the Mist API; using the API-provided UUID as the natural primary key ensures deterministic upserts and makes joins straightforward.

Alternate considered: composite_pk (e.g., for time-series snapshots) — NOT recommended because this is a stable inventory, not time-series. auto_increment_with_unique is unsuitable because we must avoid surrogate-only keys for inventories.

## Test plan outline
- Unit tests (fast):
  - Mock OrgInventoryExporter.inventory to return representative device payloads (including nested fields, missing optional fields).
  - Verify flattening/field mapping functions produce expected column set.
  - Assert exporter calls DataExporter.write_with_format_selection with correct api_function_name and metadata.
- Integration tests (medium):
  - Run exporter against a controlled test harness that serves static API responses (fixture JSON).
  - Load resulting SQL/CSV into a temporary SQLite DB and verify upsert behaviour: run exporter twice with modified records and assert expected final state (no duplicates, updated fields applied).
  - Validate indexes exist and queries by org_id/mac/serial return expected rows.


---
