# Data Model: SLE metrics insights

Entity: SLEMetricInsight (backed by SQLite table `sle_metrics`)

Columns (suggested types for SQLite):
- site_id TEXT NOT NULL
- site_name TEXT
- metric TEXT NOT NULL
- duration TEXT NOT NULL
- timestamp TEXT NOT NULL  -- ISO8601 string
- value_json TEXT         -- JSON string of numeric/quantile values
- details_json TEXT       -- JSON string for nested details
- raw_payload TEXT        -- optional full JSON string for auditability

Primary key:
- Composite PK: (site_id, metric, duration, timestamp)
- Rationale: combination uniquely identifies a metric datapoint within a time window.

Indexes:
- idx_sle_metrics_site_metric_duration ON (site_id, metric, duration)
- idx_sle_metrics_timestamp ON (timestamp)

Validation rules:
- site_id, metric, duration, timestamp must be present for rows used in SQLite upserts.
- timestamp must be parseable as ISO8601 in tests (production code should log and skip invalid formats).

State transitions:
- Raw API payload -> flattened dict -> persisted (CSV row + SQLite upsert)
- Re-run export: upsert will overwrite existing row (idempotent). If product requests merge semantics, extend with merge rule.

Notes on flattening:
- Nested dicts -> dotted keys (e.g., details.region -> details.region)
- Arrays -> JSON-encoded in a single string cell
- Multiline strings -> escaped so CSV remains one-line per record

Storage file:
- data/mist_data.db (convention from constitution). Table: sle_metrics

DDL (reference):

CREATE TABLE IF NOT EXISTS sle_metrics (
  site_id TEXT NOT NULL,
  site_name TEXT,
  metric TEXT NOT NULL,
  duration TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  value_json TEXT,
  details_json TEXT,
  raw_payload TEXT,
  PRIMARY KEY (site_id, metric, duration, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_sle_metrics_site_metric_duration ON sle_metrics(site_id, metric, duration);
CREATE INDEX IF NOT EXISTS idx_sle_metrics_timestamp ON sle_metrics(timestamp);

Deduplication strategy:
- Use ON CONFLICT(primary_key) DO UPDATE to replace value_json and details_json with the latest write. This ensures repeated exports for same key do not create duplicates.

If product requires keeping historical versions, a separate `sle_metrics_history` table or appending logs with synthetic ids is recommended; this plan assumes dedup by canonical key.


