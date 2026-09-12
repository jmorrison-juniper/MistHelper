# Phase 1 Data Model: getOrgOtherDevice

Feature: `629-mist-get-org-other-device`
Endpoint: `GET /api/v1/orgs/{org_id}/otherdevices/{device_mac}`

## Entities Returned

The endpoint returns a single `OrgOtherDevice` JSON object (not an array). It
represents one non-Juniper (third-party) device tracked by the organization.

### Entity: `OrgOtherDevice`

| Field           | Type          | Nullable | Description                                                  | Notes                              |
|-----------------|---------------|----------|--------------------------------------------------------------|------------------------------------|
| `id`            | string (UUID) | No       | Unique object ID in the Mist organization; API-provided.     | **Primary key** (natural).         |
| `org_id`        | string (UUID) | No       | Tenant owning the record; API-provided.                      | Foreign key -> `orgs.id`.          |
| `site_id`       | string (UUID) | Yes      | Optional site scoping.                                       | Foreign key -> `sites.id` if set.  |
| `device_mac`    | string        | No       | MAC of the third-party device (as recorded by Mist).         | Format per Mist convention.        |
| `mac`           | string        | No       | Interface-level MAC (may equal `device_mac` on single-NIC).  | Not a key; may duplicate.          |
| `vendor`        | string        | Yes      | Vendor label (e.g., `cisco`, `aruba`, `dell`).               | Indexed for reporting.             |
| `model`         | string        | Yes      | Vendor model string.                                         | Indexed for reporting.             |
| `serial`        | string        | Yes      | Chassis / device serial number.                              |                                    |
| `name`          | string        | Yes      | Operator-friendly device name.                               |                                    |
| `state`         | string        | Yes      | Current lifecycle state as returned by Mist.                 | Indexed for filtering.             |
| `vendor_api_id` | string        | Yes      | External vendor-API correlation ID.                          |                                    |
| `created_time`  | number (epoch)| No       | Object creation timestamp; API-provided, read-only.          |                                    |
| `modified_time` | number (epoch)| No       | Last-modified timestamp; API-provided, read-only.            |                                    |

**Primary key**: `id` (natural key -- API-provided stable UUID).
**Foreign keys**:
- `org_id` -> `orgs.id` (logical FK; enforced by application, not SQLite constraint).
- `site_id` -> `sites.id` (logical FK when non-null).

## State Transitions

**N/A -- read-only endpoint.** This is an HTTP GET that returns the current snapshot of
one record. MistHelper does not maintain state machines for third-party device records;
consumers observe `state` and `modified_time` on subsequent reads to detect drift.

## SQLite DDL

The `DataExporter` schema-inference pipeline generates this DDL automatically from the
first observed payload plus the registered PK strategy. Reference form:

```sql
CREATE TABLE IF NOT EXISTS org_other_device (
    id             TEXT    NOT NULL PRIMARY KEY,
    org_id         TEXT    NOT NULL,
    site_id        TEXT,
    device_mac     TEXT    NOT NULL,
    mac            TEXT,
    vendor         TEXT,
    model          TEXT,
    serial         TEXT,
    name           TEXT,
    state          TEXT,
    vendor_api_id  TEXT,
    created_time   REAL,
    modified_time  REAL
);

CREATE INDEX IF NOT EXISTS idx_org_other_device_org_id   ON org_other_device (org_id);
CREATE INDEX IF NOT EXISTS idx_org_other_device_site_id  ON org_other_device (site_id);
CREATE INDEX IF NOT EXISTS idx_org_other_device_mac      ON org_other_device (mac);
CREATE INDEX IF NOT EXISTS idx_org_other_device_vendor   ON org_other_device (vendor);
CREATE INDEX IF NOT EXISTS idx_org_other_device_model    ON org_other_device (model);
CREATE INDEX IF NOT EXISTS idx_org_other_device_state    ON org_other_device (state);
```

Upserts use `INSERT OR REPLACE` keyed on `id` per the `natural_pk` strategy, so
repeated invocations of menu 96 for the same device converge on a single row without
duplicates.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Dictionary Entry

Insert the following entry into the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py`. Place it immediately after the existing `listOrgOtherDevices` entry
(around line 4012) so the sibling operationIds sit together in source:

```python
"getOrgOtherDevice": {  # PK strategy for single third-party device lookup by MAC.
    "type": "natural_pk",  # id is a Mist-provided stable UUID; use it as the key.
    "primary_key": ["id"],  # Single-column PK enables clean INSERT OR REPLACE upserts.
    "indexes": [  # Cover the fields NOC engineers filter on most often.
        "org_id",  # Tenant scoping for multi-org queries.
        "site_id",  # Join key for per-site reports.
        "mac",  # Cross-reference against wired / wireless client tables.
        "vendor",  # Inventory reporting by vendor.
        "model",  # Inventory reporting by model.
        "state",  # Filter for devices in a particular lifecycle state.
    ],
    "unique_constraints": [],  # id already unique; no additional constraints needed.
    "description": "Single third-party device record retrieved by MAC",  # For docs.
},
```

Every executable line in the entry carries an inline comment per Constitution Principle
VI (Inline Comments, NON-NEGOTIABLE).

## Cross-Backend Behavior

- **CSV**: One row per invocation is written to `data/org_other_device.csv`. If the
  file exists, a new row is appended and the writer deduplicates on `id` before flush.
- **SQLite**: `INSERT OR REPLACE INTO org_other_device (...) VALUES (...)` via the
  strategy-driven upsert path.
- **ArangoDB**: Document upserted into the `org_other_device` collection with `_key =
  id`. Graph edges to `orgs/<org_id>` and (when present) `sites/<site_id>` are
  maintained per the graph-edge policy in spec `188-graph-edge-definitions`.
- **Redis**: Cache key `org_other_device:<id>` populated with the JSON payload and the
  standard MistHelper TTL.
