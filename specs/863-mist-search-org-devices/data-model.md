# Data Model: searchOrgDevices

The endpoint returns a list of device objects. The exporter preserves all
fields after nested-field flattening and multiline escaping.

| Entity | Storage | Primary key | Important indexes |
|---|---|---|---|
| Organization device search row | CSV, SQLite, ArangoDB `devices` | `id`, `mac` | `org_id`, `site_id`, `model`, `type`, `hostname` |

No migration is required. The existing backend creates or updates the target
storage using `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
