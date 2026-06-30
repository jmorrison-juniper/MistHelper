# Phase 1 Data Model: getOrgJseInfo

**Feature**: 609-mist-get-org-jse-info
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document captures the response entity exposed by the endpoint, the
MistHelper-side persistence shape, the SQLite DDL, and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration. Source schema is
`documentation/api/orgs/GET_orgs_org_id_setting_jse_info.md` (200 response example).

---

## Entities

The endpoint returns exactly one entity: an **OrgJseInfo** singleton describing the
JSE integration bound to one organization. The endpoint is not paginated and the
payload is always a single JSON object (or an empty object / 404 when the integration
is not configured).

### Entity: OrgJseInfo

| Field             | Type             | Source        | Nullable | Description |
|-------------------|------------------|---------------|----------|-------------|
| `org_id`          | string (UUID)    | injected      | No       | Mist organization UUID. NOT in the upstream payload -- the MistHelper menu method injects it from the user prompt / `MIST_ORG_ID` so the row is self-describing and serves as the natural primary key. |
| `cloud_name`      | string           | response body | Yes      | Hostname of the JSE cloud the org is linked to. Example value: `devcentral.juniperclouds.net`. |
| `org_names`       | string (CSV)     | response body | Yes      | Comma-joined, deterministically-sorted list flattened from the upstream `org_names` array (`type: array, items: string, uniqueItems: true`). Stored as a single string so CSV / SQLite cells stay flat; ArangoDB receives the original list as a sub-document. Empty list -> empty string. |
| `org_names_count` | integer          | derived       | No       | Cardinality of the upstream `org_names` array. Always present (0 when the upstream list is empty or absent). Lets downstream SQL queries filter without parsing the joined string. |
| `username`        | string           | response body | Yes      | JSE username currently bound to the integration. Example value: `john@abc.com`. |
| `fetched_at`      | string (ISO8601) | injected      | No       | UTC timestamp when MistHelper successfully retrieved the row. Useful for staleness reporting across repeated runs. |

**Primary Key**: `org_id` (natural_pk).
**Foreign Keys**: `org_id` references the existing `orgs.id` column written by the
`listOrgSites` / `getOrg` exports. The reference is logical, not enforced by SQLite
foreign-key constraints (the rest of the MistHelper schema uses logical FKs only).

---

## State Transitions

**N/A -- read-only endpoint.** The MistHelper menu method only reads the upstream
state and persists a snapshot. No write, update, or delete is performed against the
Mist API. The local SQLite row transitions through one state machine only:

```
(absent) --INSERT--> present --INSERT OR REPLACE--> present (updated)
```

The `INSERT OR REPLACE` is driven by the natural `org_id` primary key on every
re-run, so the row is overwritten in place with the latest cloud / username /
org_names values and the `fetched_at` timestamp.

---

## SQLite DDL

```sql
-- Created lazily on first invocation by
-- DataExporter.write_with_format_selection(...) when the SQLite backend is active.
CREATE TABLE IF NOT EXISTS org_jse_info (
    org_id           TEXT NOT NULL PRIMARY KEY,  -- Mist organization UUID; natural PK
    cloud_name       TEXT,                       -- JSE cloud hostname (nullable upstream)
    org_names        TEXT,                       -- comma-joined sorted list of JSE org names
    org_names_count  INTEGER NOT NULL DEFAULT 0, -- cardinality of org_names list
    username         TEXT,                       -- JSE-side username bound to the integration
    fetched_at       TEXT NOT NULL               -- ISO 8601 UTC timestamp of the read
);

-- Secondary index for cross-org "all orgs pointing at the same JSE cloud" queries.
CREATE INDEX IF NOT EXISTS idx_org_jse_info_cloud_name
    ON org_jse_info(cloud_name);
```

Upsert path used by `DataExporter` for natural_pk strategies:

```sql
INSERT OR REPLACE INTO org_jse_info
    (org_id, cloud_name, org_names, org_names_count, username, fetched_at)
VALUES (?, ?, ?, ?, ?, ?);
```

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Registration

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (located near line ~1672 in the current source). Inline comments are
required on every executable line per Constitution Principle VI:

```python
'getOrgJseInfo': {                              # operationId from the OpenAPI spec
    'type': 'natural_pk',                       # singleton row per org; org_id is stable
    'primary_key': ['org_id'],                  # injected by the menu method (not in payload)
    'indexes': ['cloud_name'],                  # supports cross-org "same JSE cloud" queries
    'table_name': 'org_jse_info',               # matches the documented SQLite table name
},
```

---

## Data Flow Summary

```
User prompt (org_id) ── safe_input() ─┐
                                      v
                          mistapi.api.v1.orgs.integration_jse
                          .getOrgJseInfo(apisession, org_id)
                                      |
                                      v  APIResponse.data = {cloud_name, org_names[], username}
                          flatten step (in-method, <=5 lines):
                            - inject org_id
                            - sort + join org_names list -> org_names (str)
                            - derive org_names_count
                            - inject fetched_at (UTC isoformat)
                                      |
                                      v
                  DataExporter.write_with_format_selection(
                      data=[row_dict],
                      filename="org_jse_info_<org_id>.csv",
                      api_function_name="getOrgJseInfo")
                                      |
                          ┌───────────┼───────────┐
                          v           v           v
                       CSV/JSON   SQLite       ArangoDB+Redis
                       under      INSERT OR    vertex + Redis
                       data/      REPLACE      cache update
```

The flatten step is the only transformation between the SDK response and the
persistence call; it stays inside the 25-line / 5-block / 5-param budget of the
single new method on the host class.
