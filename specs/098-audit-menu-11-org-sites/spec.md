# Export Organization Sites: Specification

## Summary

Export Organization Sites: add a stable, dual-output operation (CSV + SQLite) that exports all sites for a given org using OrgSiteExporter.sites. This operation must produce a flattened, queryable dataset appropriate for audit, reporting, and downstream joins.

## Purpose

Provide NOC engineers an auditable export of organization site metadata for compliance, inventory reconciliation, and analytics. Support both human-friendly CSV and normalized SQLite (upserts) for downstream tooling.

## Stakeholders

- NOC Engineers (primary users)
- Platform SRE (data pipelines)
- Security/Compliance (audit needs)
- Product owner for MistHelper

## Acceptance Criteria (pass/fail)

Pass:
- OrgSiteExporter.sites returns all sites for the org and writes CSV and SQLite outputs.
- SQLite table schema matches the flattened schema below and uses the declared primary key strategy.
- Operation handles pagination and common optional fields without crashing.
- Unit tests cover flattening and SQL upsert logic.

Fail:
- Missing or duplicated site rows in SQLite when re-running for same org/timestamp.
- Unhandled API pagination or fatal exceptions on null fields.

## API function(s) used

- OrgSiteExporter.sites (function_ref)
- Underlying Mist API: GET /orgs/{org_id}/sites (via mistapi wrapper)

## SQL export relevance & recommendation

SQL export is relevant (sql_export_relevant: true). Recommend upsert-capable SQLite export with indexes on org_id and name for efficient querying and joins with device tables.

## Primary key strategy suggestion

natural_pk — justify: Site objects from Mist include stable UUID `id`. Using natural_pk (primary_key: ["id"]) preserves identity across runs, enables deterministic upserts, and prevents duplicates when the export is re-run.

## Example flattened schema

- id (TEXT, PK)
- org_id (TEXT)
- name (TEXT)
- country_code (TEXT)
- timezone (TEXT)
- address_street (TEXT)
- address_city (TEXT)
- address_state (TEXT)
- address_zip (TEXT)
- latitude (REAL)
- longitude (REAL)
- created_at (INTEGER/epoch)
- updated_at (INTEGER/epoch)
- contact_emails (TEXT, JSON-string if list)
- tags (TEXT, comma-separated)
- raw_payload (TEXT, optional compact JSON)

## Risks / Assumptions

- Assumes Mist API returns stable `id` and reasonable pagination behavior.
- Risk: API rate limits and transient errors — implement retry/backoff.
- Assumes sensitive PII (addresses) are permitted to be stored in SQLite per policy; if not, mask or exclude.
- Assumes exporter will be used on medium-size orgs; very large orgs may require streaming to avoid memory pressure.
