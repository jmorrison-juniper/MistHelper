# Spec

## Summary of current state
- Menu ID: 1 — Export all organization alarms from the past day.
- Implementation entrypoint: OrgAlarmEventExporter.alarms
- SQL export relevant: yes
- Notes: SQL compliant, missing unit tests
- Spec directory: specs/019-audit-menu-01-org-alarms

## Purpose
Provide a reproducible export of all organization alarms for the previous 24 hours, supporting CSV and SQLite outputs, and safe SQL upsert semantics so repeated runs do not create duplicates.

## Stakeholders
- NOC engineers (primary users)
- Platform maintainers (integration/CI)
- QA/Automation team (tests & verification)

## Acceptance criteria
1. When run, OrgAlarmEventExporter.alarms returns alarms covering the last 24 hours for the target org(s).
2. Output options: CSV and SQLite (via existing DataExporter.write_with_format_selection API).
3. SQL export performs idempotent upsert: repeated exports within overlap windows must not create duplicate alarm rows.
   - Upsert behavior: `INSERT OR REPLACE` (or equivalent UPSERT) on defined primary key(s).
4. Schema created/validated before writes; required indexes exist for common queries (org_id, timestamp).
5. Performance: single-org export for 24h completes within operational bounds (TBD by infra), and handles pagination and rate limits.
6. Unit tests and integration tests exist and pass.

## Required API function name (SQL-relevant)
- OrgAlarmEventExporter.alarms (function_ref)
- DataExporter.write_with_format_selection (consumer API for dual output)

## Recommended primary-key strategy
- Recommended: composite_pk
  - primary_key: ["id", "org_id", "timestamp"]
  - Reasoning: alarms are time-series events where `id` alone may not be globally stable across ingestion windows or across org-scoped exports; including org_id and timestamp ensures uniqueness for dedup/upsert and supports time-range deletes/rollups. Composite PK supports idempotent INSERT OR REPLACE upserts.
  - Indexes: add indexes on (org_id, timestamp) and on (timestamp) to support range queries and retention.

## Test plan outline
- Unit tests (fast, isolated):
  - Add unit tests for OrgAlarmEventExporter.alarms behavior using mocked API responses including pagination, empty result, single-item, duplicate IDs across pages, and error handling.
  - Validate that the exporter calls DataExporter.write_with_format_selection with expected flattened rows and metadata (api_function_name).

- Integration tests (end-to-end, CI):
  - Run the exporter against a staging/mocked Mist API or recorded VCR fixtures to produce CSV and SQLite outputs for a 24h window.
  - Verify output row counts, schema, and sample field values.

- SQL verification steps:
  - Create a temporary SQLite DB and run exporter twice for overlapping windows; assert no duplicate rows.
  - Verify `INSERT OR REPLACE` semantics by altering a field in source data and ensuring subsequent export updates the row.
  - Verify indexes exist and queries such as `SELECT COUNT(*) FROM alarms WHERE org_id=? AND timestamp BETWEEN ? AND ?` return expected counts.


---
Metadata: menu_id=1, spec_dir=specs/019-audit-menu-01-org-alarms
