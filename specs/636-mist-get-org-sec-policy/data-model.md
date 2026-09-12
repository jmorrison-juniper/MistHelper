# Phase 1 Data Model: getOrgSecPolicy

**Feature**: 636-mist-get-org-sec-policy
**Date**: 2026-06-30
**Source schema**:
`documentation/api/orgs/GET_orgs_org_id_secpolicies_secpolicy_id.md` (200 response).

## Entities

The endpoint returns a single JSON object (not a list). Two persisted entities are
derived from it: the top-level `SecPolicy` and the child `SecPolicyWlan` (one row per
element in the `wlans[]` array).

### Entity 1: SecPolicy (parent)

Represents the WAN-edge security policy record itself.

| Field           | Type    | Nullable | Notes / Source                                              |
|-----------------|---------|----------|-------------------------------------------------------------|
| `id`            | TEXT    | No       | Mist UUID; server-issued; PRIMARY KEY.                      |
| `org_id`        | TEXT    | No       | Owning organization UUID; foreign key to sites/orgs graph.  |
| `site_id`       | TEXT    | Yes      | Optional site scope; foreign key to `sites.id` when set.    |
| `name`          | TEXT    | Yes      | Human-readable label.                                       |
| `created_time`  | REAL    | Yes      | Epoch seconds when policy was created (readOnly).           |
| `modified_time` | REAL    | Yes      | Epoch seconds of last modification (readOnly).              |
| `wlans_count`   | INTEGER | No       | Denormalized `len(response.get("wlans", []))` for quick UI. |
| `raw_json`      | TEXT    | No       | Full raw JSON of the response for schema-drift diagnostics. |

Primary key: `id` (single column).
Foreign keys (soft; enforced only when the polyglot graph backend is active):
`org_id -> orgs.id`, `site_id -> sites.id`.

### Entity 2: SecPolicyWlan (child; one row per `wlans[]` element)

Represents one WLAN block attached to the security policy.

| Field                    | Type    | Nullable | Notes / Source                                                          |
|--------------------------|---------|----------|-------------------------------------------------------------------------|
| `secpolicy_id`           | TEXT    | No       | FK to parent `SecPolicy.id`; part of composite PK.                      |
| `ssid`                   | TEXT    | No       | Required per `wlan` schema; part of composite PK.                       |
| `org_id`                 | TEXT    | No       | Copied from parent for query convenience.                               |
| `acct_immediate_update`  | INTEGER | Yes      | Bool as 0/1.                                                            |
| `acct_interim_interval`  | INTEGER | Yes      | 0-65535.                                                                |
| `acct_servers_json`      | TEXT    | Yes      | JSON-encoded array of RADIUS accounting servers (host, secret, ports).  |
| `auth_servers_json`      | TEXT    | Yes      | JSON-encoded auth server array (schema too wide for individual columns). |
| `enabled`                | INTEGER | Yes      | Bool as 0/1.                                                            |
| `raw_json`               | TEXT    | No       | Full raw JSON of this wlan[] element for schema-drift diagnostics.      |

Primary key: `(secpolicy_id, ssid)` (composite).
Foreign key: `secpolicy_id -> org_sec_policy.id` (ON DELETE CASCADE at the DataExporter
layer when the polyglot backend is active; SQLite fallback uses standard upsert
semantics).

**Design note on wide sub-objects**: The `wlan` schema in the OpenAPI response is
extremely wide (dozens of RADIUS, 802.1X, coa, and dynamic-VLAN sub-fields). Rather
than exploding every leaf into its own column and creating a brittle schema that
breaks the moment Mist adds a new field, the flattener promotes only the
frequently-queried scalars (`ssid`, `enabled`, `acct_*`) to columns and stores the
rest as JSON-encoded strings in `*_json` columns. `raw_json` preserves the entire
sub-object for downstream tooling and schema-drift audits.

## State Transitions

**N/A -- read-only endpoint.** The GET call captures a point-in-time snapshot; no
state machine is triggered on the MistHelper side. Repeated runs upsert into SQLite
via the primary key strategy; existing rows are replaced with the fresher payload.

## SQLite DDL

The tables below are created lazily by `DataExporter` on first write when the
operationId is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. DDL is documented
here for reviewer clarity and downstream tooling.

```sql
-- Parent: one row per security policy retrieved.
CREATE TABLE IF NOT EXISTS org_sec_policy (
    id            TEXT    PRIMARY KEY,
    org_id        TEXT    NOT NULL,
    site_id       TEXT,
    name          TEXT,
    created_time  REAL,
    modified_time REAL,
    wlans_count   INTEGER NOT NULL DEFAULT 0,
    raw_json      TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_org_sec_policy_org_id
    ON org_sec_policy(org_id);
CREATE INDEX IF NOT EXISTS idx_org_sec_policy_name
    ON org_sec_policy(name);
CREATE INDEX IF NOT EXISTS idx_org_sec_policy_site_id
    ON org_sec_policy(site_id);

-- Child: one row per WLAN block inside the policy.
CREATE TABLE IF NOT EXISTS org_sec_policy_wlans (
    secpolicy_id           TEXT    NOT NULL,
    ssid                   TEXT    NOT NULL,
    org_id                 TEXT    NOT NULL,
    acct_immediate_update  INTEGER,
    acct_interim_interval  INTEGER,
    acct_servers_json      TEXT,
    auth_servers_json      TEXT,
    enabled                INTEGER,
    raw_json               TEXT    NOT NULL,
    PRIMARY KEY (secpolicy_id, ssid)
);

CREATE INDEX IF NOT EXISTS idx_org_sec_policy_wlans_org_id
    ON org_sec_policy_wlans(org_id);
CREATE INDEX IF NOT EXISTS idx_org_sec_policy_wlans_ssid
    ON org_sec_policy_wlans(ssid);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Two entries must be added to the dictionary (currently around line 4761 of
`MistHelper.py`, grouped with `listOrgServicePolicies` and `listOrgSecIntelProfiles`):

```python
"getOrgSecPolicy": {
    "type": "natural_pk",                                  # Server-issued UUID stable across reads.
    "primary_key": ["id"],                                 # Single-column PK per response schema.
    "indexes": ["org_id", "name", "site_id"],              # Common query facets.
    "unique_constraints": [],                              # No secondary uniqueness beyond id.
    "description": "Organization security policy record (WAN edge firewall + WLAN blocks).",
},
"getOrgSecPolicyWlans": {
    "type": "composite_pk",                                # No wlan id; ssid is required by schema.
    "primary_key": ["secpolicy_id", "ssid"],               # Composite: parent id + required ssid.
    "indexes": ["org_id", "ssid"],                         # Filter by org or SSID name.
    "unique_constraints": [],                              # Composite PK already enforces uniqueness.
    "description": "WLAN blocks nested inside a security policy (child rows of getOrgSecPolicy).",
},
```

The first entry is registered against the actual mistapi operationId
(`getOrgSecPolicy`); the second is a synthetic operationId (`getOrgSecPolicyWlans`) so
`DataExporter.write_with_format_selection()` can route the child rows to the correct
table using the same `api_function_name=` mechanism, without a second HTTP call.
