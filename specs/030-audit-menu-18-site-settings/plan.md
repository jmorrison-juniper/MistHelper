# Plan

## Goal
Move menu item 18 from SQL NON-COMPLIANT to fully-spec-compliant: add PK metadata and api_function_name, implement correct exporter behavior, and add unit + integration tests verifying SQL upsert semantics.

## High-level phases
1. Analysis & Spec (done)
   - Confirm required API name and recommended PK strategy (composite_pk [site_id, setting_name]).
2. Prepare metadata & scaffolding (pre-implementation)
   - Add PK entry for getSiteSetting to ENDPOINT_PRIMARY_KEY_STRATEGIES.
   - Add api_function_name metadata for the endpoint.
   - Create spec files in specs/030-audit-menu-18-site-settings.
3. Implementation
   - Refactor SiteConfigExporter.settings to call DataExporter.write_with_format_selection(..., api_function_name=...).
   - Ensure exporter flattens/normalizes settings to a stable record shape.
4. Testing
   - Create unit tests that mock API and assert correct calls/outputs.
   - Create integration tests against a temporary SQLite DB to verify table schema and upsert semantics.
5. Documentation & Release
   - Update README and changelog with menu 18 entry and version.
   - Ensure CI runs new tests.

## Milestones & checkpoints
- M1: Metadata updated (PK + api_function_name) — blocker must be cleared before implementation starts.
- M2: Exporter refactor completed and linted.
- M3: Unit tests pass locally.
- M4: Integration SQLite tests pass, demonstrating upsert semantics.
- M5: Docs updated and PR ready for review.

## Dependencies and sequencing
- Metadata updates (M1) must precede implementation (M2) because exporter reads endpoint PK metadata to create SQL schema and to apply upserts.
- Unit tests can be developed in-parallel with refactor but must pass after implementation.
- Integration + SQL verification require both metadata and implemented exporter.

## Risk & mitigation
- Risk: Ambiguity in API shape for settings (single record vs list). Mitigation: create adapter in exporter that accepts both list and dict forms; include normalization unit tests.
- Risk: Existing DB naming conflicts. Mitigation: derive table name from api_function_name and validate before schema changes.

## Deliverables
- Updated ENDPOINT_PRIMARY_KEY_STRATEGIES entry for getSiteSetting
- SiteConfigExporter.settings refactor using write_with_format_selection with api_function_name
- Unit and integration tests validating exporter and SQL upsert behavior
- Spec files in specs/030-audit-menu-18-site-settings and README update


