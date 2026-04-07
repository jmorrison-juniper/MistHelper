# Data Model — SSID Template Consolidation

## Phase1Matrix (SQLite)
- `site_id` TEXT PRIMARY KEY
- `site_name` TEXT
- `template_id` TEXT
- `template_name` TEXT
- `target_ssid_name` TEXT
- `target_ssid_id` TEXT
- `psk_detected` INTEGER (0/1)
- `edge_cluster_id` TEXT
- `edge_cluster_name` TEXT
- `anomaly_code` TEXT
- `collected_at` TIMESTAMP

## DeviationReport (JSON blob)
- `cluster_id` -> `parameter_name` -> { value -> count }

## OperationsLog
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `phase` INTEGER
- `site_id` TEXT
- `action` TEXT
- `status` TEXT
- `message` TEXT
- `timestamp` TIMESTAMP

