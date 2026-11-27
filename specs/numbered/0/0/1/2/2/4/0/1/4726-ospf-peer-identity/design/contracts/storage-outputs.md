# Contract: OSPF Storage Outputs

This contract defines the three outputs that the change writes and the rule for the legacy outputs. The producer code paths are the SQLite leg (`SQLiteDatabaseWriter`), the Redis JSON leg (`RedisJSONWriter` through `DatabaseRouter`), and the ArangoDB leg (`ArangoDBWriter` through `DatabaseRouter`).

## SQLite Output

### Table Name

- Menus 70 and 225 write to `<legacy site table>_v2`. The legacy site table name is `SiteOspfStats_<site>`. The site segment is the sanitized site name. Menu 70 builds the name in `_build_export_filename` (RV-38). Menu 225 builds it from the prefix and the site name (RV-33).
- Menu 55 writes to `OrgOspfStats_v2`. The org filename is `OrgOspfStats.csv` (RV-35). The SQLite leg drops the `.csv` suffix to form the table name (RV-100).

### Columns

- One text column for each field in the flattened batch.
- The column `misthelper_ospf_peer_key` holds the identity key. It is declared `TEXT NOT NULL`.
- The audit columns that the existing writer appends.

### Primary Key

- The primary key is `misthelper_ospf_peer_key`. No other column is part of the primary key.
- An existing `_v2` table with another primary key causes a failed write. The error names the table and no row is written.

### Insert Mode

- The writer uses `INSERT OR REPLACE` (RV-12). A row with an existing key is replaced by the same key.

## Redis JSON Output

### Key

- Menu 55 uses the key `searchOrgOspfStats:ospf_<hex>`.
- Menus 70 and 225 use the key `searchSiteOspfStats:ospf_<hex>`.

The key builder joins the endpoint name and the strategy primary key value (RV-15 and RV-16).

### Value

- The full record as JSON, with the field `misthelper_ospf_peer_key`.

### Expiry

- Each key expires after `REDIS_JSON_TTL_SECONDS`. The default is 7 days (RV-18).

## ArangoDB Output

### Collection

- The collection name is the API function name (RV-22). Menu 55 uses `searchOrgOspfStats`. Menus 70 and 225 use `searchSiteOspfStats`.

### Document Key

- The `_key` value is the identity key (RV-19).

### Graph

- The OSPF graph mapping keeps its current behavior. The mapping uses `id` as its key field (RV-20 and RV-21). The change does not add graph vertices for OSPF records. A follow-up issue owns that defect.

## Legacy Outputs

| Output | Legacy shape | Rule |
| - | - | - |
| SQLite table | `SiteOspfStats_<site>` or `OrgOspfStats` with the old primary key | Not read and not written by this change. |
| Redis key | `searchSiteOspfStats:<mac>:<peer_ip>:<timestamp>` or the same shape with `unknown` | Not read and not written by this change. Expires by the TTL. |
| ArangoDB document | Keyed by the MAC for site records, or by a generated UUID for org records | Not read and not written by this change. Stays in the collection. |

Warning: Removing a legacy output deletes data that this tool cannot rebuild. Removal needs a separate human decision (D-9).

## CSV Output

The CSV files keep their names and columns. A CSV file does not contain the identity key.
