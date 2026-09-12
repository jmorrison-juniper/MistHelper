# Phase 1 Data Model: getOrgMxEdgeVmParams

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_mxedges_mxedge_id_vm_params.md` (200
OK body).

## Entities

The endpoint returns a single JSON object describing the VM provisioning
parameters of one Mist Edge appliance in one organization. MistHelper persists
this as a single logical entity flattened to one row.

### Entity 1: `MxEdgeVmParams`

One row per `(org_id, mxedge_id)` pair.

| Field                       | Type     | Source                    | PK? | FK?                | Notes |
|-----------------------------|----------|---------------------------|-----|--------------------|-------|
| `org_id`                    | TEXT     | MistHelper user prompt    | YES | sites.org_id       | UUID supplied by user; injected before write. |
| `mxedge_id`                 | TEXT     | MistHelper user prompt    | YES | mxedges.id         | UUID supplied by user; injected before write. |
| `model`                     | TEXT     | API `model`               | --  | --                 | SKU string, e.g. `ME-VM`. |
| `name`                      | TEXT     | API `name`                | --  | --                 | Optional user-supplied display name; may be NULL. |
| `user_data_b64`             | TEXT     | API `user_data`           | --  | --                 | Base64-encoded cloud-init payload. Sensitive: never logged in full, only persisted. |
| `user_data_length`          | INTEGER  | len(API `user_data`)      | --  | --                 | Length of the base64 payload, useful for audit + change detection. |
| `user_data_sha256`          | TEXT     | sha256(API `user_data`)   | --  | --                 | Hex digest of the base64 payload. Cheap change-detection without exposing content. |
| `polled_at_utc`             | TEXT     | MistHelper clock          | --  | --                 | ISO8601 UTC timestamp of the poll, for audit. |

Notes:

- `user_data_b64` is stored as-is (base64 string from the API). Decoding to
  cleartext is deliberately *not* performed at flatten time because the
  decoded payload typically contains bootstrap credentials. Downstream
  tooling can decode on demand from the SQLite cell.
- `user_data_sha256` is added by MistHelper at flatten time. It is *not* in
  the API response; it lets operators detect a changed user_data without
  reading the raw bytes.

## State Transitions

N/A -- this is a read-only endpoint. The underlying *Mist Edge appliance* on
the Mist side may be re-provisioned (changing `model`, `name`, or
`user_data`), but MistHelper does not drive or model those transitions; it
merely captures snapshots. Each poll overwrites the prior snapshot for the
same `(org_id, mxedge_id)` tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per (org, mxedge) describing the appliance's VM parameters.
CREATE TABLE IF NOT EXISTS org_mxedge_vm_params (
    org_id              TEXT     NOT NULL,
    mxedge_id           TEXT     NOT NULL,
    model               TEXT,
    name                TEXT,
    user_data_b64       TEXT,
    user_data_length    INTEGER,
    user_data_sha256    TEXT,
    polled_at_utc       TEXT,
    PRIMARY KEY (org_id, mxedge_id)
);

CREATE INDEX IF NOT EXISTS idx_org_mxedge_vm_params_model
    ON org_mxedge_vm_params (model);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per (org, mxedge) describing the VM provisioning parameters
    # of a single virtualized Mist Edge appliance. Repeat polls upsert.
    'getOrgMxEdgeVmParams': {                                                       # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of two UUIDs
        'primary_key': ['org_id', 'mxedge_id'],                                     # both injected from user prompts
        'indexes': ['model'],                                                       # fast filter for SKU audits
        'table': 'org_mxedge_vm_params',                                            # target SQLite table
    },
}
```

The operationId `getOrgMxEdgeVmParams` is the canonical lookup key used by
`DataExporter` when MistHelper writes the flattened row. No additional sub-
table identifier is required because the response contains no nested arrays.
