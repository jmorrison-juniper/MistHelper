# Phase 1 Data Model: GetOrgCurrentMatchingClientsOfAWxTag

**Branch**: `603-mist-get-org-current-matching-clients-of-a-wx-tag`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document captures the entities, fields, primary-key strategy, SQLite DDL, and
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration for the new menu item.

---

## Entity: `WxTagMatchingClient`

The endpoint returns a JSON array. Each element is one matching-client record. There
is exactly one entity type produced by this call.

### Fields (post-flatten, as persisted)

| Column          | Type        | Source        | Nullable | Notes                                                                                                         |
|-----------------|-------------|---------------|----------|---------------------------------------------------------------------------------------------------------------|
| `org_id`        | TEXT (UUID) | path param    | NO       | Copied from the URL onto every row at flatten time so the table is self-describing and queryable cross-org.   |
| `wxtag_id`      | TEXT (UUID) | path param    | NO       | Copied from the URL onto every row at flatten time. Foreign key to the WxTag entity (see Related Entities).   |
| `mac`           | TEXT        | response item | NO       | Client MAC address. Normalized to lowercase, separator-free (e.g. `5684dae9ac8b`) on insert.                  |
| `since`         | INTEGER     | response item | NO       | Epoch seconds for the start of the current match window. Stored as INTEGER for direct datetime arithmetic.    |
| `retrieved_at`  | INTEGER     | client clock  | NO       | Epoch seconds at the time MistHelper made the API call. Lets analysts distinguish stale rows from fresh ones. |

### Primary Key

- **Type**: `composite_pk`
- **Key**: `(org_id, wxtag_id, mac)`
- **Justification**: a given MAC matches a given tag in a given org at most once at any
  point in time. `since` is mutable across runs and cannot be part of the key.

### Foreign Keys

- `(org_id)` references the conceptual `Org` entity (no enforced FK in SQLite -- Mist
  Cloud orgs are external to MistHelper).
- `(org_id, wxtag_id)` references the `WxTag` entity (populated by the existing
  `listOrgWxTags` / `getOrgWxTag` operations under `mistapi.api.v1.orgs.wxtags`). No
  enforced FK -- the user may have exported clients for a tag they have not yet
  exported the tag detail for, and that should not block the insert.

### State Transitions

**N/A -- read-only endpoint.** MistHelper retrieves a current snapshot per invocation
and upserts it into the local store. There is no MistHelper-side state machine. The
underlying Mist API state (a client matches / un-matches a tag) is observed only via
re-invocation.

---

## Related Entities (read-only, not created by this feature)

| Entity      | Owning module                              | Linked-from column            |
|-------------|--------------------------------------------|-------------------------------|
| `Org`       | `mistapi.api.v1.orgs.orgs`                 | `org_id`                      |
| `WxTag`     | `mistapi.api.v1.orgs.wxtags`               | `(org_id, wxtag_id)`          |
| `Client`    | various client-search endpoints            | `(org_id, mac)` -- soft join  |

These entities are not produced by this feature; they are referenced for cross-table
joins by analysts. No DDL changes are required for them.

---

## SQLite DDL

The table is created on first run by `DataExporter` from the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry below. The equivalent explicit DDL, for
documentation and migration tooling, is:

```sql
-- Table: org_wxtag_matching_clients
-- Source: GET /api/v1/orgs/{org_id}/wxtags/{wxtag_id}/clients
-- operationId: getOrgCurrentMatchingClientsOfAWxTag
CREATE TABLE IF NOT EXISTS org_wxtag_matching_clients (
    org_id        TEXT    NOT NULL,            -- Mist Org UUID from the URL
    wxtag_id      TEXT    NOT NULL,            -- WxTag UUID from the URL
    mac           TEXT    NOT NULL,            -- Lowercase, separator-free MAC
    since         INTEGER NOT NULL,            -- Epoch seconds: start of current match window
    retrieved_at  INTEGER NOT NULL,            -- Epoch seconds: when MistHelper observed the row
    PRIMARY KEY (org_id, wxtag_id, mac)
);

-- Helper indexes for the common analyst queries:
CREATE INDEX IF NOT EXISTS idx_org_wxtag_matching_clients_mac
    ON org_wxtag_matching_clients (mac);
CREATE INDEX IF NOT EXISTS idx_org_wxtag_matching_clients_org_id
    ON org_wxtag_matching_clients (org_id);
CREATE INDEX IF NOT EXISTS idx_org_wxtag_matching_clients_wxtag_id
    ON org_wxtag_matching_clients (wxtag_id);
```

Repeated runs use `INSERT OR REPLACE` on the composite PK so the row's `since` and
`retrieved_at` reflect the most recent observation without producing duplicates.

---

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Registration

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (near line ~1672 per the project guide). The dictionary key is the
Mist `operationId`; values follow the project's established schema.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["getOrgCurrentMatchingClientsOfAWxTag"] = {  # Register PK strategy for new WxTag matching-clients export
    "type": "composite_pk",                                                  # Composite key chosen per research.md Task 2
    "primary_key": ["org_id", "wxtag_id", "mac"],                            # Org + tag + MAC uniquely identify a current match
    "table_name": "org_wxtag_matching_clients",                              # Stable SQLite table shared across runs
    "indexes": ["mac", "org_id", "wxtag_id"],                                # Indexes optimize per-MAC / per-org / per-tag lookups
    "columns": {                                                             # Explicit column types so DataExporter creates the table cleanly
        "org_id": "TEXT NOT NULL",                                           # Org UUID copied from URL onto each row at flatten
        "wxtag_id": "TEXT NOT NULL",                                         # Tag UUID copied from URL onto each row at flatten
        "mac": "TEXT NOT NULL",                                              # Lowercase separator-free MAC
        "since": "INTEGER NOT NULL",                                         # Epoch seconds: start of current match window
        "retrieved_at": "INTEGER NOT NULL",                                  # Epoch seconds: time of MistHelper observation
    },
}
```

The inline comment density above is illustrative -- every executable line in the
PR carries a comment explaining *why* it exists, per Constitution Principle VI.

---

## Row Production Notes (for the implementer)

1. MAC normalization: `mac_lower = raw_mac.lower().replace(":", "").replace("-", "")`
   before insert. This guards against future API changes that might add separators.
2. `since` is returned as a JSON number; cast with `int(payload["since"])` -- never
   `float()`, since fractional seconds are not part of the contract.
3. `retrieved_at` is generated client-side via `int(time.time())` inside the menu
   method, before the `DataExporter` call.
4. Empty response array: the menu method logs `INFO "WxTag %s has no current matching
   clients"` and returns 0; `DataExporter` is *not* called with an empty list, so no
   empty CSV is written and no SQLite insert happens.
