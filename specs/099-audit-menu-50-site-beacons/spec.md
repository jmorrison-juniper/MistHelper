## Export Site Beacons (menu_id: 50)

### Summary
Export site beacon events (wireless beacon detections) for a given site into CSV and/or SQLite with a flattened schema suitable for analysts and downstream ingestion.

### Purpose
Provide a one-click export of beacon records for troubleshooting RF issues, location analytics, and audit trails. Enable both quick CSV downloads and durable SQLite imports for historical analysis.

### Stakeholders
- NOC Engineers (primary users)
- Network Automation Engineer (maintainer)
- Analytics Team (consumer of exports)

### Acceptance Criteria (pass/fail)
- PASS if: Running the menu operation produces CSV and/or SQLite with rows matching API data, columns match the flattened schema below, no duplicate rows for the same beacon event when upserting into SQLite, and exported timestamps are ISO-8601 UTC.
- FAIL if: Missing required fields (beacon_id, site_id, timestamp, signal_strength, mac), corrupt CSV/DB files, or duplicates persist due to missing PK strategy.

### API function(s) used
- SiteClientExporter.beacons (function_ref provided) — expected to call Mist API endpoint that returns beacon/client-radio records for a site. If multiple endpoints exist, prefer the site-scoped beacon/events endpoint.

### SQL export relevance & recommendation
- sql_export_relevant: true
- Recommendation: Provide both CSV and SQLite output. For SQLite, use an upsert/INSERT OR REPLACE strategy keyed by the composite primary key to prevent duplicates.

### Primary key strategy suggestion
- Type: composite_pk
- Primary key: ["beacon_id", "site_id", "timestamp"]
- Indexes: ["site_id", "mac", "timestamp"]
- Rationale: beacon_id alone may not be unique across sources or may be missing; composite with site and timestamp ensures uniqueness for time-series beacon events.

### Example flattened schema
- beacon_id: TEXT  # API event id or generated UUID
- site_id: TEXT    # Mist site UUID
- timestamp: TEXT  # ISO-8601 UTC string (e.g., 2024-04-01T12:34:56Z)
- signal_strength: INTEGER  # RSSI in dBm
- mac: TEXT  # Beacon MAC address
- ssid: TEXT
- channel: INTEGER
- frequency: INTEGER
- rssi_stddev: REAL
- vendor: TEXT
- first_seen: TEXT
- last_seen: TEXT
- raw_payload: TEXT  # Optional JSON string of original record for audit

(The exporter should include the five required fields explicitly: beacon_id, site_id, timestamp, signal_strength, mac.)