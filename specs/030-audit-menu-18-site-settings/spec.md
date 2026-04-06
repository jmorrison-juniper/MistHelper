# Spec

## Summary of current state
- Menu ID: 18
- Description: Export configuration settings for all sites
- Function ref: SiteConfigExporter.settings
- Spec directory: specs/030-audit-menu-18-site-settings
- SQL relevance: 1
- Notes: SQL NON-COMPLIANT: no PK entry for getSiteSetting, no api_function_name, no tests

## Purpose
Provide a reliable operation that exports every site's configuration settings into user-selectable backends (CSV and SQLite). When SQL output is selected, exported records must be stored with a deterministic primary key and upsert behavior so repeated runs do not create duplicates.

## Stakeholders
- NOC engineers (primary users)
- Platform/backend engineers (maintainers)
- QA/Test team
- Data consumers/analytics team

## Acceptance criteria
1. Functional
   - The SiteConfigExporter.settings operation collects configuration settings for all sites and produces CSV and/or SQLite output.
   - Export includes metadata to identify site and setting (site_id, setting_name, setting_value, source, last_updated).
2. SQL correctness
   - SQLite schema includes a PK strategy (see below) preventing duplicate logical rows.
   - Upsert semantics (INSERT OR REPLACE or equivalent) are used so re-running export updates existing rows rather than inserting duplicates.
3. Metadata & instrumentation
   - Endpoint metadata must include api_function_name (required for auditability & writer plumbing).
   - Tests (unit + integration + SQL verification) cover exporter behavior, SQL schema, and upsert semantics.
4. Observability & resilience
   - Errors are logged and non-fatal failures per-site are reported; partial exports produce a non-zero exit code and an artifact describing failures.

## Required API function name
- Required API function: getSiteSetting (or authoritative Mist SDK name that returns one site's settings or listing of settings). This must be set in endpoint metadata as api_function_name so DataExporter plumbing can record provenance and apply PK strategy.

## Recommended primary-key strategy
- Recommendation: composite_pk
  - primary_key: ["site_id", "setting_name"]
  - Reasoning: A site's settings are uniquely identified by the site and the setting key/name. This composite is stable and prevents duplicates across runs (site-scoped uniqueness). Using composite_pk allows deterministic upserts without introducing synthetic IDs.
  - Indexes: add indexes on site_id and setting_name for efficient queries (optional cluster for reporting).

## SQL upsert behavior
- For composite_pk strategy, implement upsert via `INSERT OR REPLACE` (SQLite) or `INSERT ... ON CONFLICT(site_id, setting_name) DO UPDATE SET ...` semantics to update existing rows.
- Ensure the exporter supplies the api_function_name to DataExporter.write_with_format_selection so that the SQL table name, PK strategy, and indexes are applied consistently.

## Test plan outline
- Unit tests
  - Mock Mist API responses for multiple sites and various setting shapes.
  - Assert SiteConfigExporter.settings flattens/normalizes settings and calls DataExporter.write_with_format_selection with api_function_name and the resolved sql metadata.
  - Test error handling for single-site failures and malformed settings.
- Integration tests (SQLite)
  - Run exporter against a synthetic dataset (few sites) writing to a test SQLite DB.
  - Verify schema includes composite PK (site_id, setting_name) and indexes.
  - Run exporter twice with different values to verify upsert replaces existing rows (no duplicates) and updates values.
- SQL verification steps
  - Inspect `PRAGMA table_info(table_name)` and `PRAGMA index_list(table_name)` to confirm PK and indexes.
  - Insert a duplicate logical row via exporter and assert row count remains stable and values updated.
  - Validate nulls / absent fields behavior and constraints.


---

