# Approach

1. Implement a lightweight caller that invokes SiteExportUtils.insights with robust parameter normalization (org/site/metric/start/end/interval), handles pagination and retries, and returns raw JSON.
2. Flatten nested insight JSON into the schema above using a deterministic flattening function (timestamp -> epoch int, metric_name, value, tags JSON).
3. Export: support CSV (streamed write) and SQLite upsert (CREATE TABLE if not exists + INSERT OR REPLACE) using the composite PK.
4. Add unit tests for flattening and SQLite upsert, and a small integration test that mocks API responses.

# Deliverables

- Code: new menu operation metadata + implementation hook invoking SiteExportUtils.insights and flatten/export utilities.
- SQL schema and migration logic for SQLite export.
- Unit and integration tests covering flattening, export, and PK behavior.
- README/specs update under specs/102-audit-menu-53-sle-insights.

# Milestones

1. Design & spec file (this artifact) — complete.
2. Implementation: API wrapper + flatten function + export hooks (CSV + SQLite). (1–2 dev hours)
3. Tests: unit tests for flattening and SQLite behavior; integration test with mocked API (1 hour).
4. Docs: update README/specs and changelog (0.5 hour).
5. Validation: run tests and verify SQLite indexing/performance (0.5 hour).

# Verification plan

- Unit tests
  - Flattening: given representative nested insight JSON, assert produced rows match expected schema and types.
  - SQL upsert: create temporary SQLite DB, run upsert twice for same sample data, assert only one row exists and values equal expected.

- Integration test (mocked API)
  - Mock SiteExportUtils.insights to return paginated time-series; run operation and assert CSV/SQLite outputs created and have correct row counts.

- Manual verification
  - Open resulting SQLite and run queries: 
    - SELECT COUNT(*) FROM sle_insights WHERE site_id = ? AND timestamp BETWEEN ? AND ?;
    - SELECT metric_name, avg(value) FROM sle_insights WHERE site_id = ? GROUP BY metric_name;

# Time-series indexing in SQLite

Recommended schema and indexes (example SQL):

```sql
CREATE TABLE IF NOT EXISTS sle_insights (
  timestamp INTEGER NOT NULL,
  site_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  value REAL,
  units TEXT,
  tags TEXT,
  collected_at INTEGER,
  PRIMARY KEY (timestamp, site_id, metric_name)
);
-- Index for fast range queries per site
CREATE INDEX IF NOT EXISTS idx_sle_site_time ON sle_insights(site_id, timestamp);
-- Index for metric-centric queries
CREATE INDEX IF NOT EXISTS idx_sle_metric_time ON sle_insights(metric_name, timestamp);
```

Notes: use WITHOUT ROWID only if SQLite version and use-case justify it; composite PK + indexes suffice for most local analytics.

