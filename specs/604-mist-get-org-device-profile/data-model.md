# Phase 1 Data Model: getOrgDeviceProfile

**Feature**: 604-mist-get-org-device-profile
**Endpoint**: `GET /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}`
**Returns**: Single JSON object (one device profile)

## Entities

The endpoint returns exactly one logical entity: an `OrgDeviceProfile`. The
upstream OpenAPI schema declares the response only as `{"type": "object"}`
(see `documentation/api/orgs/GET_orgs_org_id_deviceprofiles_deviceprofile_id.md`),
but the runtime shape is the standard Mist device-profile envelope shared
with the bulk `listOrgDeviceProfiles` endpoint and the PUT counterpart.
The field set below is consolidated from the sibling list endpoint, the PUT
update contract, and the documented gotcha ("Device profiles can apply to
APs, switches, or gateways depending on type").

### Entity: OrgDeviceProfile

| Field | Type | Notes / Source |
|-------|------|----------------|
| `id` | string (UUID) | **Primary key.** Stable server-assigned UUID. |
| `org_id` | string (UUID) | **Foreign key** -> `orgs.id`. Owning organization. |
| `name` | string | Human-readable profile name (org-unique). |
| `type` | string enum | `ap` \| `switch` \| `gateway`. Drives which sub-config keys are populated. |
| `created_time` | number (epoch seconds) | Server-set on profile creation. |
| `modified_time` | number (epoch seconds) | Server-set on each update. |
| `for_site` | boolean | Whether profile is intended for site-level inheritance. |
| `site_id` | string (UUID) \| null | Optional pin to a single site; null for org-wide profiles. |
| `ap_port_config` | object \| null | AP profile only -- per-port ethernet config. |
| `radio_config` | object \| null | AP profile only -- 2.4 / 5 / 6 GHz radio params. |
| `mesh` | object \| null | AP profile only -- mesh / wireless backhaul config. |
| `port_usages` | object \| null | Switch profile only -- named port-usage definitions. |
| `networks` | object \| null | Switch / gateway profile only -- VLAN / network definitions. |
| `dhcpd_config` | object \| null | Switch / gateway -- DHCP server config. |
| `oob_ip_config` | object \| null | Out-of-band management IP config. |
| `ntp_servers` | array[string] \| null | NTP server list. |
| `dns_servers` | array[string] \| null | DNS resolver list. |
| `additional_config_cmds` | array[string] \| null | Custom Junos / Mist OS commands appended to generated config. |

**Foreign keys**:
- `org_id` -> `orgs.id` (Mist organization).
- `site_id` -> `sites.id` (optional, only set when profile is site-pinned).

**State transitions**: N/A -- this is a read-only GET endpoint. The
underlying entity has a CRUD lifecycle managed by the sibling
POST / PUT / DELETE endpoints on the same resource, but no state machine
is observable from a single GET response.

## SQLite DDL

The new table is created by `DataExporter` on first write. Nested JSON
sub-objects are stored as serialized JSON text in their respective columns
(the existing DataExporter convention -- callers query them with the
`json_extract()` SQLite function when needed).

```sql
CREATE TABLE IF NOT EXISTS org_device_profile (
    id TEXT PRIMARY KEY NOT NULL,
    org_id TEXT NOT NULL,
    name TEXT,
    type TEXT,
    created_time REAL,
    modified_time REAL,
    for_site INTEGER,
    site_id TEXT,
    ap_port_config TEXT,
    radio_config TEXT,
    mesh TEXT,
    port_usages TEXT,
    networks TEXT,
    dhcpd_config TEXT,
    oob_ip_config TEXT,
    ntp_servers TEXT,
    dns_servers TEXT,
    additional_config_cmds TEXT,
    misthelper_fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_org_device_profile_org_id
    ON org_device_profile(org_id);
CREATE INDEX IF NOT EXISTS idx_org_device_profile_name
    ON org_device_profile(name);
CREATE INDEX IF NOT EXISTS idx_org_device_profile_type
    ON org_device_profile(type);
```

`misthelper_fetched_at` is the standard MistHelper ingestion timestamp
column added by `DataExporter` to every row regardless of endpoint -- it
is not part of the upstream payload.

Upsert behavior: `INSERT OR REPLACE INTO org_device_profile ...` keyed on
`id`. Re-running the menu against the same profile updates every column to
the latest API snapshot without creating a duplicate row.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (alongside the existing `listOrgDeviceProfiles` entry):

```python
'getOrgDeviceProfile': {
    'type': 'natural_pk',
    'primary_key': ['id'],
    'indexes': ['org_id', 'name', 'type'],
    'table_name': 'org_device_profile',
    'description': 'Single org-level device profile fetched by UUID',
},
```

The dictionary key (`getOrgDeviceProfile`) is the operationId, matched
verbatim against the `api_function_name=` keyword argument passed to
`DataExporter.write_with_format_selection()`.

## Cross-Backend Mapping Summary

| Backend | Artifact | Identity |
|---------|----------|----------|
| CSV | `data/org_device_profile.csv` | Re-written each run (singular file). |
| SQLite | `data/mist_data.db` table `org_device_profile` | `INSERT OR REPLACE` on `id`. |
| ArangoDB | Collection `org_device_profile` (document key = `id`) | `UPSERT` on `_key`. |
| Redis | Key `mist:org_device_profile:<id>` | TTL inherited from project default; value = JSON blob. |

All four backends share the same logical row produced by the single flatten
step in the new menu method.
