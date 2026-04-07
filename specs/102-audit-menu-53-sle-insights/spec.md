# Export SLE Insights (menu_id: 53)

## Summary

Export SLE (Service Level Expectations) Insights for a site into CSV/SQLite using SiteExportUtils.insights. This operation retrieves time-series SLE metrics and writes a flattened, exportable table suitable for analysis and long-term storage.

## Purpose

Provide NOC engineers with a reproducible export of SLE insight metrics per site and timestamp to support SLA reporting, trend analysis, and archival in SQLite.

## Stakeholders

- NOC Engineers (primary users)
- Site Reliability / Reporting team
- Product owner for MistHelper

## Acceptance Criteria

1. The operation calls SiteExportUtils.insights and returns a time-series list of metric records.
2. Output supports both CSV and SQLite export formats.
3. Flattened records include at minimum: timestamp (epoch), site_id, metric_name, value, tags/context.
4. SQLite export creates a table with appropriate composite PK and indexes enabling efficient range and site queries.
5. Unit tests validate flattening logic and a sample SQLite upsert works without duplicates.

## API function(s)

- SiteExportUtils.insights(org_id: str, site_id: str, metric: str, start: int, end: int, interval: str) — primary call (assumed signature).  Implement caller wrapper that normalizes params and handles pagination, retries, and rate-limiting.

## SQL export relevance and recommendation

This operation is SQL-export relevant: time-series SLE data is best stored in SQLite for local querying and downstream ETL. Recommendation:

- Store as a time-series table with composite primary key to avoid duplicates on repeated exports.
- Use epoch seconds (INTEGER) for timestamp to simplify range queries.
- Provide indexes for (site_id, timestamp) and (metric_name, timestamp) to optimize common queries.

## Primary key strategy

Type: composite_pk
Primary key columns: ["timestamp", "site_id", "metric_name"]
Rationale: unique per metric per site per time-sample; allows idempotent upserts using INSERT OR REPLACE.

## Example flattened schema for time-series

| column        | type    | notes |
|---------------|---------|-------|
| timestamp     | INTEGER | epoch seconds (PRIMARY KEY part) |
| site_id       | TEXT    | Mist site UUID (PRIMARY KEY part) |
| metric_name   | TEXT    | e.g., "satisfaction_score" (PRIMARY KEY part) |
| value         | REAL    | numeric metric value |
| units         | TEXT    | optional, e.g., "ms" or "%" |
| tags          | TEXT    | JSON blob of context/labels |
| collected_at  | INTEGER | epoch seconds when exported |

