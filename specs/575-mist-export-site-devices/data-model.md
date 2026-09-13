# Phase 1 Data Model: exportSiteDevices

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_devices_export.md` (200 OK body).
The response is a single JSON wrapper around a base64-encoded CSV file:

```json
{ "type": "string", "description": "File", "contentEncoding": "base64" }
```

MistHelper decodes the base64 payload, parses the CSV with `csv.DictReader`, and
materializes one entity row per CSV line.

## Entities

The decoded CSV contains one row per device assigned to the requested site.
MistHelper models it as a single entity.

### Entity 1: `SiteDeviceExportRow`

One row per (site, device).

| Field           | Type    | Source                | PK? | FK?           | Notes |
|-----------------|---------|-----------------------|-----|---------------|-------|
| `site_id`       | TEXT    | MistHelper context    | YES | sites.id      | UUID supplied by user; injected before write so the row is always pinned to the queried site, even if the Mist CSV column is missing in a future release. |
| `mac`           | TEXT    | CSV `mac` column      | YES | --            | Device factory MAC address. Globally unique on Mist hardware. |
| `name`          | TEXT    | CSV `name` column     | --  | --            | Device name as set by the operator (often hostname). May be empty. |
| `serial`        | TEXT    | CSV `serial` column   | --  | --            | Device serial number. Stable across reboots; used as a secondary lookup key. |
| `model`         | TEXT    | CSV `model` column    | --  | --            | Device model code (e.g., `AP43`, `EX4400-48P`, `SRX320`). |
| `type`          | TEXT    | CSV `type` column     | --  | --            | Device class enum (`ap`, `switch`, `gateway`). |
| `hw_rev`        | TEXT    | CSV `hw_rev` column   | --  | --            | Hardware revision string. Empty for some models. |
| `version`       | TEXT    | CSV `version` column  | --  | --            | Firmware version currently reported by the device. |
| `status`        | TEXT    | CSV `status` column   | --  | --            | Connection status snapshot (`connected`, `disconnected`, `unassigned`). |
| `exported_at_utc` | TEXT  | MistHelper clock      | --  | --            | ISO8601 UTC timestamp of the export, for audit. |

CSV columns not enumerated above are preserved verbatim by `DataExporter` -- the
exporter widens the table on first write to absorb any additional columns Mist
chooses to emit. The fields above are the *minimum* guaranteed set that
downstream MistHelper code may rely on.

## State Transitions

N/A -- this is a read-only endpoint. The underlying *device* on the Mist side
transitions through `unassigned -> connected -> disconnected` and through
firmware upgrade cycles, but MistHelper does not drive or model those
transitions; it merely captures snapshots. Each export overwrites the prior
snapshot for the same `(site_id, mac)` tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Site device inventory snapshot: one row per (site, device).
CREATE TABLE IF NOT EXISTS site_device_export (
    site_id          TEXT NOT NULL,
    mac              TEXT NOT NULL,
    name             TEXT,
    serial           TEXT,
    model            TEXT,
    type             TEXT,
    hw_rev           TEXT,
    version          TEXT,
    status           TEXT,
    exported_at_utc  TEXT,
    PRIMARY KEY (site_id, mac)
);

CREATE INDEX IF NOT EXISTS idx_site_device_export_serial
    ON site_device_export (serial);

CREATE INDEX IF NOT EXISTS idx_site_device_export_model
    ON site_device_export (model);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly. The exporter will also widen the table to add
any extra CSV columns Mist emits beyond the guaranteed minimum set listed
above.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Site device inventory snapshot, keyed by (site, device MAC).
    'exportSiteDevices': {                                                          # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['site_id', 'mac'],                                          # stable across re-exports of same site
        'indexes': ['serial', 'model'],                                             # fast lookup by serial or by model
        'table': 'site_device_export',                                              # target SQLite table
    },
}
```

The operationId `exportSiteDevices` is used verbatim as the dictionary key (the
same string MistHelper passes as `api_function_name` to
`DataExporter.write_with_format_selection()`). No MistHelper-internal sub-table
identifier is needed because the parsed CSV is a single flat row list with no
nested arrays.
