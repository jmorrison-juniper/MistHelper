# Phase 1 Data Model: getOrgCapturingStatus

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/utilities/GET_orgs_org_id_pcaps_capture.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing the currently-active org-level
packet capture (or 404 if none). MistHelper splits this into two logical entities
for clean multi-backend persistence: a summary row and a per-AP detail set lifted
from the nested `pcap_aps` map.

### Entity 1: `OrgCapturingStatusSummary`

One row per active capture. PK is the Mist-supplied capture UUID (`id`).

| Field             | Type    | Source              | PK? | FK?           | Notes |
|-------------------|---------|---------------------|-----|---------------|-------|
| `id`              | TEXT    | API `id`            | YES | --            | UUID; readOnly; REQUIRED per schema. |
| `org_id`          | TEXT    | MistHelper context  | --  | sites.org_id  | UUID supplied by user; injected before write. |
| `type`            | TEXT    | API `type`          | --  | --            | Enum: `client`, `gateway`, `new_assoc`, `radiotap`, `radiotap,wired`, `wired`, `wireless`. REQUIRED per schema. |
| `format`          | TEXT    | API `format`        | --  | --            | `stream` (to Mist cloud) or `tzsp` (UDP TZSP to remote host). |
| `ap_mac`          | TEXT    | API `ap_mac`        | --  | --            | Nullable. Specific AP being captured for client/new_assoc types. |
| `client_mac`      | TEXT    | API `client_mac`    | --  | --            | Nullable. Target client MAC. |
| `ssid`            | TEXT    | API `ssid`          | --  | --            | Nullable. SSID filter. |
| `duration`        | INTEGER | API `duration`      | --  | --            | Configured capture duration in seconds. |
| `started_time`    | INTEGER | API `started_time`  | --  | --            | Epoch seconds when the capture started. |
| `max_num_packets` | INTEGER | API `max_num_packets` | --| --            | User-configured packet cap. |
| `max_pkt_len`     | INTEGER | API `max_pkt_len`   | --  | --            | Max bytes captured per packet. |
| `num_packets`     | INTEGER | API `num_packets`   | --  | --            | Total packets captured by all APs (not applicable for type `client`/`new_assoc`). |
| `includes_mcast`  | INTEGER | API `includes_mcast`| --  | --            | Stored 0/1; SQLite has no native bool. |
| `aps_list`        | TEXT    | API `aps`           | --  | --            | Comma-joined target AP MACs (denormalized for human review; per-AP detail goes to `org_pcap_capture_status_aps`). |
| `ok_list`         | TEXT    | API `ok`            | --  | --            | Comma-joined APs that were successfully configured. |
| `failed_list`     | TEXT    | API `failed`        | --  | --            | Comma-joined APs whose configuration attempt failed. |
| `switches_list`   | TEXT    | API `switches`      | --  | --            | Comma-joined switch IDs in scope. |
| `gateways_list`   | TEXT    | API `gateways`      | --  | --            | Comma-joined gateway IDs in scope. |
| `mxedges_list`    | TEXT    | API `mxedges`       | --  | --            | Comma-joined mxedge IDs in scope. |
| `tcpdump_expression` | TEXT | API `tcpdump_expression` | -- | --          | Common tcpdump filter. |
| `radiotap_tcpdump_expression` | TEXT | API `radiotap_tcpdump_expression` | -- | -- | Only when `type=radiotap`. |
| `scan_tcpdump_expression` | TEXT | API `scan_tcpdump_expression` | -- | -- | Only when `type=scan`. |
| `wired_tcpdump_expression` | TEXT | API `wired_tcpdump_expression` | -- | -- | Only when `type=wired`. |
| `wireless_tcpdump_expression` | TEXT | API `wireless_tcpdump_expression` | -- | -- | Only when `type=wireless`. |
| `tzsp_host`       | TEXT    | API `tzsp_host`     | --  | --            | Required when `format=tzsp`. |
| `tzsp_port`       | INTEGER | API `tzsp_port`     | --  | --            | 1-65535. Required when `format=tzsp`. |
| `polled_at_utc`   | TEXT    | MistHelper clock    | --  | --            | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `OrgCapturingStatusAp`

Zero or more rows per active capture, lifted from the nested `pcap_aps` map. Each
key in the map is an AP MAC; each value is a small object describing the radio
parameters in use on that AP.

| Field              | Type    | Source                       | PK? | FK?                                    | Notes |
|--------------------|---------|------------------------------|-----|----------------------------------------|-------|
| `org_id`           | TEXT    | MistHelper context           | YES | org_pcap_capture_status.org_id         | UUID. |
| `capture_id`       | TEXT    | API `id` (parent)            | YES | org_pcap_capture_status.id             | Capture UUID. |
| `ap_mac`           | TEXT    | API `pcap_aps` key           | YES | --                                     | AP MAC address (12 lowercase hex). |
| `band`             | INTEGER | API `pcap_aps[mac].band`     | --  | --                                     | 2 / 5 / 6 GHz integer. |
| `bandwidth`        | INTEGER | API `pcap_aps[mac].bandwidth`| --  | --                                     | MHz (e.g., 20, 40, 80, 160). |
| `channel`          | INTEGER | API `pcap_aps[mac].channel`  | --  | --                                     | 802.11 channel number. |
| `tcpdump_expression` | TEXT  | API `pcap_aps[mac].tcpdump_expression` | -- | --                          | Nullable per-AP filter override. |
| `polled_at_utc`    | TEXT    | MistHelper clock             | --  | --                                     | ISO8601 UTC timestamp of the poll. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *capture* on the Mist side
progresses through configuration (`failed`/`ok` AP lists update), then packet
capture (`num_packets` grows), then terminates (the endpoint returns 404). MistHelper
does not drive or model those transitions; it captures snapshots. Each poll
overwrites the prior snapshot for the same `id` (summary) and `(org_id, capture_id,
ap_mac)` (detail) via SQLite `INSERT OR REPLACE`.

A 404 response is recorded as zero rows written; the prior snapshot (if any)
remains in SQLite as a historical record of the last observed capture.

## SQLite DDL

```sql
-- Summary table: one row per active org-level packet capture (Mist UUID PK).
CREATE TABLE IF NOT EXISTS org_pcap_capture_status (
    id                              TEXT     NOT NULL,
    org_id                          TEXT     NOT NULL,
    type                            TEXT,
    format                          TEXT,
    ap_mac                          TEXT,
    client_mac                      TEXT,
    ssid                            TEXT,
    duration                        INTEGER,
    started_time                    INTEGER,
    max_num_packets                 INTEGER,
    max_pkt_len                     INTEGER,
    num_packets                     INTEGER,
    includes_mcast                  INTEGER,
    aps_list                        TEXT,
    ok_list                         TEXT,
    failed_list                     TEXT,
    switches_list                   TEXT,
    gateways_list                   TEXT,
    mxedges_list                    TEXT,
    tcpdump_expression              TEXT,
    radiotap_tcpdump_expression     TEXT,
    scan_tcpdump_expression         TEXT,
    wired_tcpdump_expression        TEXT,
    wireless_tcpdump_expression     TEXT,
    tzsp_host                       TEXT,
    tzsp_port                       INTEGER,
    polled_at_utc                   TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_capture_status_org
    ON org_pcap_capture_status (org_id);
CREATE INDEX IF NOT EXISTS idx_capture_status_type
    ON org_pcap_capture_status (type);
CREATE INDEX IF NOT EXISTS idx_capture_status_started
    ON org_pcap_capture_status (started_time);

-- Per-AP detail table: zero-or-more rows per active capture, one per target AP.
CREATE TABLE IF NOT EXISTS org_pcap_capture_status_aps (
    org_id              TEXT     NOT NULL,
    capture_id          TEXT     NOT NULL,
    ap_mac              TEXT     NOT NULL,
    band                INTEGER,
    bandwidth           INTEGER,
    channel             INTEGER,
    tcpdump_expression  TEXT,
    polled_at_utc       TEXT,
    PRIMARY KEY (org_id, capture_id, ap_mac),
    FOREIGN KEY (capture_id)
        REFERENCES org_pcap_capture_status(id)
);

CREATE INDEX IF NOT EXISTS idx_capture_aps_capture
    ON org_pcap_capture_status_aps (capture_id);
CREATE INDEX IF NOT EXISTS idx_capture_aps_mac
    ON org_pcap_capture_status_aps (ap_mac);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper does
not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (two dict inserts in the existing literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per active org capture, keyed by the Mist-supplied capture UUID.
    'getOrgCapturingStatus': {                                                      # operationId from OpenAPI
        'type': 'natural_pk',                                                       # Mist UUID is the stable, unique key
        'primary_key': ['id'],                                                      # capture UUID, readOnly, REQUIRED in schema
        'indexes': ['org_id', 'type', 'started_time'],                              # common per-org / per-type / time filters
        'table': 'org_pcap_capture_status',                                         # target SQLite table for summary rows
    },

    # Per-AP detail rows flattened from the nested pcap_aps map.
    'getOrgCapturingStatusAps': {                                                   # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of org + parent capture + AP MAC
        'primary_key': ['org_id', 'capture_id', 'ap_mac'],                          # unique per-AP snapshot per capture per org
        'indexes': ['capture_id', 'ap_mac'],                                        # fast joins back to summary; fast MAC lookup
        'table': 'org_pcap_capture_status_aps',                                     # target SQLite table for per-AP rows
    },
}
```

The `getOrgCapturingStatusAps` key is a MistHelper-internal identifier (the Mist
API has no operationId for the nested `pcap_aps` map). This pattern matches how
MistHelper already splits other endpoints whose response contains nested maps or
arrays (see Plan 500 for the same convention applied to async claim status
details).
