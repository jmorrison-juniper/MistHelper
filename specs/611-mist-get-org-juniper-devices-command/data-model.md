# Phase 1 Data Model: getOrgJuniperDevicesCommand

## Entities

The endpoint returns a single, flat JSON object. There is exactly one logical
entity.

### Entity: `OrgJuniperOutboundSshCommand`

Represents the per-org (optionally per-site) outbound SSH + NETCONF bootstrap
command string that Mist generates for Juniper OC (OpenConfig) devices to
phone home.

| Field | Type | Source | Nullable | Description |
|---|---|---|---|---|
| `misthelper_internal_id` | INTEGER | Synthetic (autoincrement) | No | Surrogate primary key. Required because the upstream payload has no stable ID. |
| `org_id` | TEXT (UUID) | User input (path param) | No | The organization the command was generated for. |
| `site_id` | TEXT (UUID) | User input (query param) | No | Empty string when not supplied; otherwise the site UUID Mist used for proxy-config check / auto-assignment. |
| `cmd` | TEXT | API response field `cmd` | No | The multi-line CLI snippet Mist returns. Stored verbatim. Never logged. |
| `cmd_length` | INTEGER | Derived from `cmd` | No | `len(cmd)`. Materialized for audit queries without re-exposing the body. |
| `retrieved_at` | TEXT (ISO-8601 UTC) | Synthetic at fetch time | No | Wall-clock instant the SDK call returned 200. |

### Primary Key

- **PK**: `misthelper_internal_id` (INTEGER PRIMARY KEY AUTOINCREMENT).
- **Unique constraint**: `(org_id, site_id)` -- ensures repeated runs upsert
  in place instead of appending. `site_id = ''` is the sentinel for "no site
  context" and participates in the unique tuple normally.

### Foreign Keys

- `org_id` logically references the `orgs` collection populated by other
  MistHelper menu items (e.g. menu 1 `listMistOrgs`). The FK is *not*
  enforced at the SQLite layer because MistHelper does not currently enable
  `PRAGMA foreign_keys=ON`, and the user may invoke this menu against an
  org they have not yet exported via menu 1. ArangoDB edge population (per
  the polyglot backend spec) is the recommended place to materialize the
  org -> command relationship as a graph edge.
- `site_id` (when non-empty) logically references the `sites` collection
  populated by menu items in the 1-7 cluster. Same non-enforcement rule
  applies.

## State Transitions

**N/A -- this is a read-only HTTP GET endpoint.** Each invocation is an
idempotent fetch. The MistHelper-side row is replaced (UNIQUE upsert) on
each successful re-run; there is no lifecycle, no status field, and no
audit trail beyond the `retrieved_at` timestamp.

If multi-version retention is ever required (e.g. to detect command
rotation across Mist releases), the recommended migration is to switch the
PK strategy to `composite_pk` over `(org_id, site_id, retrieved_at)` -- a
separate spec.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_juniper_devices_outbound_ssh_cmd (
    misthelper_internal_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id                  TEXT    NOT NULL,
    site_id                 TEXT    NOT NULL DEFAULT '',
    cmd                     TEXT    NOT NULL,
    cmd_length              INTEGER NOT NULL,
    retrieved_at            TEXT    NOT NULL,
    UNIQUE (org_id, site_id)
);

CREATE INDEX IF NOT EXISTS idx_ojdsc_org_id
    ON org_juniper_devices_outbound_ssh_cmd (org_id);

CREATE INDEX IF NOT EXISTS idx_ojdsc_site_id
    ON org_juniper_devices_outbound_ssh_cmd (site_id);

CREATE INDEX IF NOT EXISTS idx_ojdsc_retrieved_at
    ON org_juniper_devices_outbound_ssh_cmd (retrieved_at);
```

The `DataExporter.write_with_format_selection()` SQLite codepath issues an
`INSERT OR REPLACE` (semantically: "upsert by UNIQUE tuple"). Because the
surrogate PK is autoincrement, the PK value is allowed to change on
replacement -- callers must not rely on a stable
`misthelper_internal_id` across re-runs of the same `(org_id, site_id)`.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (near other org-devices entries):

```python
"getOrgJuniperDevicesCommand": {                               # operationId -> strategy mapping for the new menu item
    "type": "auto_increment_with_unique",                       # no stable upstream ID; surrogate PK keeps re-runs deduped
    "primary_key": ["misthelper_internal_id"],                  # surrogate INTEGER PK AUTOINCREMENT
    "unique_constraint": ["org_id", "site_id"],                 # upsert key: empty string site_id sentinel allowed
    "indexes": ["org_id", "site_id", "retrieved_at"],           # supports audit and history queries
},
```

Every line in the dict literal carries an inline comment, satisfying
Principle VI (Inline Comments) for the registration site.

## Output Row Construction

The single API response object is flattened into exactly one row before
being handed to `DataExporter`:

```python
juniper_command_row = {                                         # one-row flatten of the single-object response payload
    "org_id": org_id,                                           # echo input so the row is self-describing
    "site_id": site_id or "",                                   # normalize None -> '' so the UNIQUE constraint is deterministic
    "cmd": response_data.get("cmd", ""),                        # the only API-supplied field; required per the 200 schema
    "cmd_length": len(response_data.get("cmd", "") or ""),      # materialize length for audit without logging the body
    "retrieved_at": datetime.now(timezone.utc).isoformat(),     # ISO-8601 UTC timestamp captured at fetch time
}
```

`DataExporter.write_with_format_selection([juniper_command_row], "org_juniper_devices_outbound_ssh_cmd", api_function_name="getOrgJuniperDevicesCommand")`
is then invoked. The list-of-dicts shape is required by `DataExporter`
even for single-row payloads.
