# Export Site Maps (menu_id: 51)

## Summary
Export all site maps from the Mist API for a selected org/site into CSV and SQLite. Produces a flattened, queryable dataset of maps (floor plans, images, metadata) suitable for audits and downstream analytics.

## Purpose
Provide a reproducible, scriptable export of site maps to support asset inventory, audit trails, and offline visualization workflows.

## Stakeholders
- NOC engineers (primary consumers)
- Asset management team
- Platform integrators (analytics, CMDB)
- QA/Release engineer (validation)

## Acceptance Criteria (pass / fail)
Pass:
- Tool retrieves all maps for the chosen site(s) without unhandled exceptions (handles pagination/rate limits).
- Output produced in user-selected formats: CSV and SQLite. SQLite contains a maps table with appropriate PK/indexes.
- Flattened records include id, site_id, name, floor, image_url, width, height, scale, orientation, tags, created_at, updated_at.
- Upsert semantics: re-running with the same data does not create duplicates in SQLite.

Fail:
- Missing required fields in output (id, site_id, name) or duplicate rows for same id in SQLite.
- Unhandled API errors or silent data truncation.

## API function(s) used
- mistapi.api.v1.sites.listSiteMaps (or equivalent site-level maps listing endpoint)
- (Optional) mistapi.api.v1.sites.getSiteMap for single-map detail if enrichment needed

## SQL export relevance & recommendation
- sql_export_relevant: true
- Recommendation: export both CSV (human-readable) and a normalized SQLite table for queries and upserts. Use `INSERT OR REPLACE` semantics for natural PKs.

## Primary key strategy suggestion
- Type: natural_pk
- primary_key: ["id"]
- indexes: ["site_id", "name", "floor"]

## Example flattened schema (columns)
- id (TEXT) -- map UUID (primary key)
- site_id (TEXT) -- site UUID
- name (TEXT)
- floor (TEXT) -- floor name/label
- image_url (TEXT)
- width (REAL) -- image width (pixels or meters as available)
- height (REAL)
- scale (REAL) -- meters per pixel or map scale if provided
- orientation (TEXT)
- tags (TEXT) -- JSON-encoded array/string
- vendor_metadata (TEXT) -- JSON blob of other map metadata
- created_at (TEXT) -- ISO8601
- updated_at (TEXT) -- ISO8601
- misthelper_exported_at (TEXT) -- export timestamp

Notes:
- Keep vendor_metadata as a JSON string for future schema evolution.
- Ensure width/height units documented in README update.