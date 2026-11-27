# Contract: SQLite Identity Table

## Applies to

The identity table holds rows for the endpoint `searchOrgDeviceEvents`. The tables are `OrgDeviceEvents` and `OrgDeviceEvents_52w`.

## Columns

| Column | Type | Null | Rule |
| - | - | - | - |
| Each source field | TEXT | Allowed | Name is sanitized with the existing rule that replaces each character outside `[A-Za-z0-9_]` with `_` (R81). |
| `org_id` | TEXT | Not allowed | Stores an empty string when the event has no `org_id`. Part of the primary key. |
| `misthelper_row_fingerprint` | TEXT | Not allowed | 64 lowercase hexadecimal characters. Part of the primary key. |
| `misthelper_created_time` | TEXT | Allowed | Default `CURRENT_TIMESTAMP`. Set on insert. |
| `misthelper_updated_time` | TEXT | Allowed | Default `CURRENT_TIMESTAMP`. Set on insert. |

## Primary key

`PRIMARY KEY (org_id, misthelper_row_fingerprint)`

## Indexes

One index for each field in the catalog index list that the table holds. The list for `searchOrgDeviceEvents` is `device_id`, `timestamp`, `type`, `org_id`, and `site_id` (R5, line 268). The index name follows `idx_<table>_<column>` (R80).

## Fingerprint

1. Take each stored column and its stored string value.
2. Drop each pair whose value is empty.
3. Drop the audit columns and the fingerprint column.
4. Sort the remaining pairs by column name in ASCII order.
5. Serialize the sorted pairs as a JSON array of two-item arrays. Use `ensure_ascii` set to True and separators `,` and `:`.
6. Encode the text as ASCII bytes and compute the SHA-256 hexadecimal digest.

## Insert rule

Each row uses `INSERT OR IGNORE`. A row whose primary key exists is ignored. The identity table never uses `INSERT OR REPLACE` for this endpoint.

## Verification rule

After all inserts in the batch, the store selects each `(org_id, misthelper_row_fingerprint)` pair from the batch. The select runs in chunks of 500 keys. Each pair must exist in the table. A missing pair discards the transaction and returns False from the writer (see the writer contract).

## Legacy detection

The table is legacy when it exists and its primary key is not `(org_id, misthelper_row_fingerprint)`. A legacy table can have no primary key. The store treats such a table as legacy.

## Schema evolution

A new source field adds a TEXT column with `ALTER TABLE ADD COLUMN`. The primary key does not change. This matches the existing column rule in the writer (R82).
