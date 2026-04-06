# Spec

## Summary of current state
- Feature: Site Inventory Health Analysis (menu_id: 121)
- Notes: PK entries exist for sitesMissingInfrastructure and sitesWithOfflineInfrastructure but require verification. SQL export is relevant (sql_export_relevant = 1).
- Function reference: SiteInventoryHealthAnalyzer.analyze
- Spec files location: specs/090-audit-menu-121-inventory-health

## Purpose
Provide a reliable, idempotent analysis that enumerates site-level inventory health issues (missing infrastructure, offline infrastructure, etc.) and exports results to CSV and an SQLite/SQL backend with correct primary-key strategy and upsert behavior for safe reconcilation across repeated runs.

## Stakeholders
- NOC engineers (primary users)
- Platform engineers (DB/CI owners)
- Product manager / audit stakeholders
- Documentation owners

## Acceptance criteria
1. Analyzer runs and produces expected output fields for the two known PK sets (sitesMissingInfrastructure, sitesWithOfflineInfrastructure).
2. SQL export persists data without duplicates and is idempotent across repeated analyzer runs.
3. Upsert semantics: rows with the same primary key are updated, not duplicated.
4. Queries for downstream reports return consistent results within 2 seconds for orgs up to 5k sites.
5. Tests: unit tests for analyzer logic, integration tests for exporter+DB upsert behavior pass in CI.
6. Documentation: specs/090-audit-menu-121-inventory-health contains spec and test artifacts.

### SQL upsert behavior (explicit)
- For natural primary keys: use INSERT OR REPLACE / INSERT ... ON CONFLICT(primary_key) DO UPDATE to update the row when the primary key matches.
- For composite primary keys: enforce a UNIQUE constraint across the composite columns and use ON CONFLICT DO UPDATE to upsert.
- For auto_increment_with_unique: use an auto-increment PK with an additional unique constraint on the business key; upserts should locate rows by the business key and update the auto-id row.
- All upserts must be executed within a transaction and be idempotent: running analyzer twice without data changes must not change row counts.

## Required API function
- SiteInventoryHealthAnalyzer.analyze
  - Must return structured JSON/list of records suitable for flattening and export (rows must include fields used by the chosen PK strategy).

## Recommended primary-key strategy and rationale
- Recommended: natural_pk
  - Reasoning: site-level entities normally have stable UUIDs (site.id). Existing PK entries (sitesMissingInfrastructure, sitesWithOfflineInfrastructure) imply one row per site per condition; a natural PK using ['site_id', 'condition_key'] (or just ['site_id'] per table depending on table granularity) ensures correspondence to real-world entities and straightforward upserts.
- Alternative: composite_pk if the records are time-series (e.g., snapshots with timestamp). Use composite_pk with primary_key = ['site_id','condition_key','snapshot_ts'] if snapshots must be retained.
- Avoid auto_increment_with_unique unless the business data lacks stable keys — this adds complexity for idempotency.

## Test Plan Outline
1. Unit tests
   - Validate analyze() returns expected structure for mocked inputs (sites with/without infra, offline infra). Assert expected fields exist (site_id, site_name, condition_key, severity, timestamp).
   - Edge cases: empty org, site with partial data, malformed device entries.
2. Integration tests (DB + exporter)
   - Use ephemeral SQLite DB to test write/export flow. Verify INSERT/UPDATE semantics by running analyzer twice with no changes and asserting stable row counts and idempotency.
   - Test composite key behavior if snapshots are used: ensure new snapshot rows are inserted and old snapshots remain (if design requires). Test index performance on sample data.
3. SQL verification
   - Run SQL script that: clears test table, calls exporter to write sample rows, asserts row count, modifies a field in sample, re-run exporter, assert updated column, assert no duplicate primary keys.
   - Verify indexes exist and EXPLAIN query times for key lookups are acceptable.

## Files/locations
- Spec root: specs/090-audit-menu-121-inventory-health
- Tests: tests/unit/test_site_inventory_health_analyzer.py, tests/integration/test_inventory_sql_upsert.py (to be created)


