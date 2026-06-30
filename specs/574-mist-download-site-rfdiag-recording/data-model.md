# Phase 1 Data Model: downloadSiteRfdiagRecording

## Endpoint Response Shape

The endpoint returns a single value per the OpenAPI 200 schema:

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
}
```

That is, the response body is a **base64-encoded string** representing a
binary `raw_events` blob -- not a JSON object with named fields. There
is no upstream entity to flatten. The MistHelper data model therefore
captures the *download event* (a metadata receipt) plus the *on-disk
blob* (an opaque file), not the contents of the blob itself.

## Entity 1: SiteRfdiagDownload (Metadata Receipt)

A row written to the `site_rfdiag_downloads` table on every successful
download. Synthesized by MistHelper; not returned by the API.

### Fields

| Field           | Type      | PK / FK | Source                                                | Description |
|-----------------|-----------|---------|-------------------------------------------------------|-------------|
| `site_id`       | TEXT (UUID) | PK part 1, FK -> `sites.id` | User prompt | Mist site UUID owning the recording |
| `rfdiag_id`     | TEXT (UUID) | PK part 2 | User prompt | Mist RF diagnostics recording UUID (per-site, opaque) |
| `filename`      | TEXT      |         | Computed: `data/rfdiags/<site_id>_<rfdiag_id>.raw`     | Absolute or repo-relative path to the on-disk blob |
| `byte_count`    | INTEGER   |         | `len(decoded_bytes)`                                  | Decoded blob size in bytes (0 on empty payload) |
| `sha256`        | TEXT (64 hex) | Indexed | `hashlib.sha256(decoded_bytes).hexdigest()`         | Content fingerprint for de-dup queries |
| `downloaded_at` | TEXT (ISO 8601 UTC) | Indexed | `datetime.utcnow().isoformat(timespec="seconds") + "Z"` | When MistHelper completed the download |
| `org_id`        | TEXT (UUID) | FK -> `orgs.id` | `apisession.org_id` (when set) | Optional org context for cross-org queries; nullable |

### Primary Key

Composite: `(site_id, rfdiag_id)`. Repeated downloads of the same
recording upsert this row (the blob file on disk is overwritten
in-place at the same path).

### Foreign Keys

- `site_id` references `sites(id)` (the table populated by
  `listOrgSites` exports). Enforced only logically -- SQLite foreign
  keys are off by default in MistHelper to avoid ordering surprises
  during multi-table sweeps.
- `org_id` references `orgs(id)` when present.

### Indexes

- `idx_site_rfdiag_downloads_downloaded_at` on `downloaded_at` --
  supports "show me the last N rfdiag downloads" queries.
- `idx_site_rfdiag_downloads_sha256` on `sha256` -- supports
  "did we already download this blob under a different rfdiag_id?"
  queries.

## Entity 2: Recording Blob (On-Disk File)

The decoded `raw_events` payload, stored on the filesystem (not in any
SQL database).

| Attribute     | Value |
|---------------|-------|
| Path template | `data/rfdiags/<site_id>_<rfdiag_id>.raw` |
| Open mode     | `"wb"` (binary write, truncate-on-open) |
| Permissions   | Filesystem default (process umask; Linux container honors `0644`) |
| Lifecycle     | Overwritten on every successful re-download. Never auto-deleted by MistHelper. |
| Schema        | Opaque binary (`raw_events` blob defined by the Mist RF diagnostics subsystem) |

## State Transitions

**N/A -- read-only endpoint.** The only state mutation is the
local-filesystem write of the blob and the upsert of the
`site_rfdiag_downloads` row. There are no multi-step state machines.

## SQLite DDL

The following DDL is emitted by `DataExporter` on first run using the
PK strategy registered below. Documented here for reviewer clarity.

```sql
CREATE TABLE IF NOT EXISTS site_rfdiag_downloads (
    site_id        TEXT NOT NULL,
    rfdiag_id      TEXT NOT NULL,
    filename       TEXT NOT NULL,
    byte_count     INTEGER NOT NULL DEFAULT 0,
    sha256         TEXT NOT NULL,
    downloaded_at  TEXT NOT NULL,
    org_id         TEXT,
    PRIMARY KEY (site_id, rfdiag_id)
);

CREATE INDEX IF NOT EXISTS idx_site_rfdiag_downloads_downloaded_at
    ON site_rfdiag_downloads (downloaded_at);

CREATE INDEX IF NOT EXISTS idx_site_rfdiag_downloads_sha256
    ON site_rfdiag_downloads (sha256);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict
in `MistHelper.py` (the dict that starts around line 1672 in the
current monolith):

```python
'downloadSiteRfdiagRecording': {                       # operationId -- matches mistapi SDK function name
    'type': 'composite_pk',                            # PK strategy: composite natural key on (site_id, rfdiag_id)
    'primary_key': ['site_id', 'rfdiag_id'],           # ordered PK columns -- both required, both stable
    'indexes': ['downloaded_at', 'sha256'],            # support time-range and de-dup queries
    'table_name': 'site_rfdiag_downloads',             # explicit table name (overrides default operationId snake_case)
},
```

## Round-Trip Guarantees

- Re-running menu 96 with the same `(site_id, rfdiag_id)` overwrites
  the blob file and upserts the ledger row -- exactly one row per
  pair after any number of runs.
- The `sha256` field changes only if the upstream recording itself
  changed (or if the same recording is encoded differently by the
  Mist backend). The user can spot drift by querying the SQLite
  table for the same `(site_id, rfdiag_id)` over time.
- The `filename` column is the canonical reference; downstream
  tooling should join SQLite rows to the file system via this
  column rather than reconstructing the path manually.
