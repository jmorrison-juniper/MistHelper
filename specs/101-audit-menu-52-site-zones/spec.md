# Export Site Zones (menu_id: 52)

## Summary
Export Site Zones for a given organization/site. Produces a normalized table of site zone metadata and optionally exports raw JSON. Intended for audit, inventory reconciliation, and downstream analysis.

## Purpose
Provide a deterministic, repeatable export of all zones configured per site in Mist so NOC and audit teams can analyze segmentation, track changes, and feed into compliance workflows.

## Stakeholders
- NOC Engineers (primary consumers)
- Audit & Compliance
- Platform Automation (integration/consumers)
- Product Owner for MistHelper

## Acceptance Criteria
- Runs as MistHelper menu operation (menu_id 52) and calls SiteConfigExporter.zones
- Returns all zones for the selected site(s) with consistent columns
- SQL export enabled and creates stable primary keys/indexes
- CSV export matches SQL output column ordering
- Includes raw JSON payload per row for full-fidelity troubleshooting
- Unit tests cover empty, single-zone, multi-zone, and malformed API responses

## API function(s)
- SiteConfigExporter.zones(org_id: str, site_id: str, page_size: int=100) -> List[dict]
  - Expected behavior: iterate/paginate Mist API (site-level) to return zone objects
  - Should raise descriptive error on auth/permission failures

## SQL export relevance & recommendation
- sql_export_relevant: true
- Recommendation: persist as normalized table `site_zones` with a natural/composite primary key (site_id + zone_id) so upserts are deterministic.
- Export both normalized fields and the raw JSON payload for forensic purposes.

## Primary key suggestion
Type: natural_pk (composite)
Primary key fields: ["site_id", "zone_id"]
Indexes: ["site_id", "name"]

## Example schema (SQLite/CSV friendly)
- site_id TEXT NOT NULL -- Mist site UUID
- zone_id TEXT NOT NULL -- Zone UUID (from API)
- name TEXT
- description TEXT
- rules_count INTEGER -- number of rules associated with zone (if available)
- created_at TEXT -- RFC3339 timestamp (if present in API)
- updated_at TEXT -- RFC3339 timestamp (if present)
- raw_json TEXT -- full JSON payload as string

Example CREATE TABLE (illustrative):
```
CREATE TABLE site_zones (
  site_id TEXT NOT NULL,
  zone_id TEXT NOT NULL,
  name TEXT,
  description TEXT,
  rules_count INTEGER,
  created_at TEXT,
  updated_at TEXT,
  raw_json TEXT,
  PRIMARY KEY (site_id, zone_id)
);
```

## Spec directory
specs/101-audit-menu-52-site-zones

## Notes / Assumptions
- Assumes SiteConfigExporter.zones returns stable `id`/`zone_id` per zone. If API lacks UUID, generate stable composite key from site_id + zone name (normalized) and document collision risk.
- Timestamps, counts are optional and only populated if present in API response.

