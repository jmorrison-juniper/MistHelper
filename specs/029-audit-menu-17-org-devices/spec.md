# Spec

## Summary of current state
- Menu ID: 17
- Description: Export all devices in the organization
- Function reference: OrgInventoryExporter.devices
- Location for spec artifacts: specs/029-audit-menu-17-org-devices
- SQL relevance: yes (sql_export_relevant: 1)
- Notes: SQL PARTIAL: api_function_name flows but PK mismatch (getOrgDevices vs listOrgDevices). No tests exist for this operation.

## Purpose
Provide a robust, fully-tested exporter for organizational devices that supports dual output (CSV/SQLite) and correct SQL upsert semantics so repeated exports do not create duplicates and updates are applied predictably.

## Stakeholders
- NOC Engineers (consumers)
- Platform Engineers (maintainers)
- QA / Test Engineers
- Release Manager

## Acceptance criteria
1. OrgInventoryExporter.devices produces the same flattened row shape for CSV and SQLite outputs.
2. SQL writes use a documented upsert strategy (no duplicate device rows after repeated runs).
3. The exporter supplies a stable api_function_name to the DataExporter.write_with_format_selection flow that matches the PK strategy.
4. Primary key config added to ENDPOINT_PRIMARY_KEY_STRATEGIES for the chosen API function(s).
5. Unit tests cover: JSON->flatten mapping, primary-key extraction, call into write_with_format_selection (mocked), and handling of missing fields.
6. Integration tests verify: exporter against a mocked Mist API returns expected rows, SQL database receives correct INSERT OR REPLACE behavior and enforces no duplicates.

### SQL upsert behavior (explicit)
- For natural_pk strategy: create table with PRIMARY KEY on the natural key(s) and use `INSERT OR REPLACE` (SQLite) so subsequent runs update existing rows.
- Verify indexes exist for frequent query columns (org_id, mac, serial_number). Use explicit unique constraints for composite PK if needed.

## Required API function name (SQL relevant)
- The SQL export pipeline expects a stable api_function_name value. Current metadata indicates both `getOrgDevices` and `listOrgDevices` appear in code paths; these must be reconciled.
- Recommendation: canonicalize to `listOrgDevices` for listing endpoints (aligns with other exporters), and add mapping entries so `getOrgDevices` calls (if any) map to the same PK strategy.

## Recommended primary-key strategy and reasons
- Recommended: natural_pk
  - primary_key: ["id"] (device UUID provided by Mist API)
  - indexes: ["org_id", "mac", "serial_number"]
- Rationale: devices have stable API-provided UUIDs suitable as natural keys; simpler upsert semantics (INSERT OR REPLACE). Composite PK is unnecessary for device entities (not time-series). Auto-increment is inappropriate because device identity is business-provided.
- Contingency: if API variant `getOrgDevices` returns a different key shape, define an alias in ENDPOINT_PRIMARY_KEY_STRATEGIES mapping both API names to the same natural_pk strategy.

## Test plan outline
- Unit tests
  - Test flattening: nested device JSON -> flat dict fields, required fields present.
  - Test primary key extraction: device -> primary key tuple (id) and fallback behavior if id missing.
  - Test exporter wiring: OrgInventoryExporter.devices calls DataExporter.write_with_format_selection with the expected api_function_name and payload shape (use mocks).
- Integration tests
  - Mock Mist API responses (listOrgDevices) and run exporter writing to ephemeral SQLite file. Assert table schema, PK constraint, row counts, and that repeated runs do not increase row counts but update changed fields.
  - SQL verification: run queries to assert `COUNT(*)` stability, specific `SELECT` for a device to verify updated timestamp/fields.

