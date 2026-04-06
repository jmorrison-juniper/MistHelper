# Spec: MSP Inventory Export (menu_id: 117)

## Summary of current state
- Menu: 117 — "MSP Inventory Export"
- Function reference: MSPInventoryExporter.execute
- Spec directory: specs/088-audit-menu-117-msp-inventory
- SQL export relevant: yes
- Notes: Needs PK / api_function_name verification, no tests currently exist.

## Purpose
Provide a reliable export of MSP inventory (organizations, sites, devices, firmware, ownership metadata) with dual output (CSV and SQL/SQLite). Exported SQL must support idempotent upserts so repeated runs update existing records without duplication.

## Stakeholders
- NOC Engineers (primary consumers)
- Platform Owner / Product Manager
- QA / Automation Engineers
- Release/CI Owners (for test automation)

## Acceptance Criteria
1. Exports run via MSPInventoryExporter.execute produce identical CSV output and a corresponding SQL/SQLite output when SQL mode selected.
2. SQL output must use an upsert strategy: inserting new rows and updating existing rows for the same business key without creating duplicates.
3. Upsert behavior is verified by automated SQL tests (see Test Plan Outline). Tests must confirm: insert on first run, no duplicate on second run, and field updates applied on changed source data.
4. Performance: export of a typical MSP (baseline sample) completes within operational SLA (TBD in implementation), and export preserves all required fields.
5. README/specs updated: records required API function name and the chosen primary-key strategy.

## SQL Upsert Behavior (required)
- Use business keys as the upsert target. Preferred implementation: `INSERT OR REPLACE` or `INSERT ... ON CONFLICT(primary_key) DO UPDATE` depending on SQLite dialect used.
- All exported tables must declare appropriate primary keys and at least the indexes listed in the PK strategy section.
- For composite/time-series records (if any), the composite primary key must include the stable identifier(s) and timestamp where applicable.

## Required API function name (verification required)
- The exporter must map to the Mist API operation(s) that supply inventory. SQL-relevance flag = 1 implies we must confirm the exact API function(s) used (e.g., `listOrgSites`, `listOrgDevices`, `getOrgDevices`, etc.).
- Action required (pre-implementation): verify and record the canonical API function name(s) and expected response payload keys in `specs/088-audit-menu-117-msp-inventory/`.

## Recommended Primary-Key Strategy
Recommended: natural_pk
- Rationale: Inventory entities (orgs/sites/devices) expose stable UUID identifiers in the Mist API; using those natural UUIDs as primary keys guarantees idempotent upserts and preserves business identity.
- Exceptions: If any exported dataset is time-series (events/stats), use composite_pk (e.g., [id, device_id, timestamp]). If an exported summary lacks stable business keys, fall back to auto_increment_with_unique but accompany with a unique constraint to avoid duplicate logical records.

## Test Plan Outline
1. Unit tests:
   - Validate JSON->flattened-row mapping logic for each entity type.
   - Verify primary-key extraction function returns expected key(s) for typical and malformed payloads.
2. Integration tests (offline/mock):
   - Use recorded API fixtures (sample payloads) to run MSPInventoryExporter.execute in CSV and SQL modes.
   - Confirm CSV contents match golden files.
3. SQL verification tests:
   - Run export against fixture A: assert rows inserted.
   - Modify fixture A to change fields and run again: assert rows updated (no duplicates).
   - Run export with added/removed devices: assert inserts/deletes/updates behave per spec (deletes may be soft/not implemented — define in implementation).

## Notes & Open Questions
- Confirm exact API function name(s) and shape of response — currently unknown; this is blocking for implementing schema & PKs.
- Decide whether exporter will perform soft-deletes for missing inventory or leave deletions as an explicit optional operation.

---
(Place this file as specs/088-audit-menu-117-msp-inventory/spec.md and update when API function names are verified.)