## Plan for Export Site Beacons (menu_id: 50)

### High-level approach
1. Inspect SiteClientExporter.beacons to confirm API contract and returned fields.
2. Implement a flattening function to normalize nested API responses into the schema above.
3. Add exporter wrapper that calls DataExporter.write_with_format_selection(data, filename, api_function_name=...).
4. Ensure SQLite export uses composite_pk upsert logic and creates suggested indexes.
5. Add unit and integration tests using sample data and test_input.txt.
6. Update README/menu metadata and create spec files under specs/099-audit-menu-50-site-beacons.

### Deliverables
- Code: SiteClientExporter.beacons exporter implementation and flattening helper
- DB: SQLite upsert logic and table schema creation with indexes
- Tests: unit tests for flattening and integration test for full export
- Docs: brief README entry and spec files in the specified spec_dir

### Milestones
- M1 (Discovery, 0.5 days): Confirm API fields and spec.
- M2 (Implementation, 1 day): Implement exporter, flattening, and DB upsert.
- M3 (Tests, 0.5 days): Add unit/integration tests and sample data.
- M4 (Docs & Commit, 0.25 days): Update README/spec and commit.

### People / Roles
- Single engineer responsible for implementation, testing, and docs (assume full-stack within repo).

### Verification plan
- Unit tests validate flattening rules and field types.
- Integration test runs exporter against sample/test API response and asserts CSV columns, SQLite table exists, and upsert prevents duplicates.
- Manual smoke test: run menu operation and open generated CSV/SQLite to confirm data and timestamps.
