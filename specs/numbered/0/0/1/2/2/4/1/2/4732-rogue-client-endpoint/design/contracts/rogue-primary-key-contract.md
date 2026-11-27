# Contract: Rogue primary keys

This contract names the primary key that each endpoint name selects. It covers the SQLite DDL and the ArangoDB vertex configuration.

## Strategy catalog

| Endpoint name | Strategy type | Primary key | Index columns | Source |
| - | - | - | - | - |
| `listSiteRogueClients` | `composite_pk` | `client_mac`, `bssid` | `site_id`, `ap_mac`, `band` | `src/foundation/support/refactors/endpoint_primary_key_strategies.py:1303-1306` |
| `listSiteRogueAPs` | `composite_pk` | `bssid`, `ap_mac` | `site_id`, `ssid`, `channel` | `src/foundation/support/refactors/endpoint_primary_key_strategies.py:1296-1299` |

The catalog is the single source of truth for each endpoint (`endpoint_primary_key_strategies.py:141`). The helper `get_endpoint_strategy` returns the configured strategy when the name exists (`src/foundation/persistence/db/database_schema_utils.py:80-81`).

## New SQLite table

When the table does not exist, `build_create_table_sql` builds the DDL with these rules.

- The DDL starts with `CREATE TABLE IF NOT EXISTS` (`database_schema_utils.py:149`).
- The DDL adds `PRIMARY KEY (<key columns>)` for the key columns that exist in the data (`database_schema_utils.py:172`).
- Each key column is declared `TEXT NOT NULL` (`database_schema_utils.py:125`).

Phase 1 expectations for the new tables:

- Endpoint `listSiteRogueClients` produces `PRIMARY KEY (client_mac, bssid)`.
- Endpoint `listSiteRogueAPs` produces `PRIMARY KEY (bssid, ap_mac)`.

## Existing SQLite table

- `CREATE TABLE IF NOT EXISTS` does not change the key of a table that already exists.
- The SQLite writer adds missing columns only (`src/foundation/support/refactors/sqlite_database_writer.py:288`).
- An insert uses `INSERT OR REPLACE` for keyed strategies (`sqlite_database_writer.py:368`).

Phase 1 keeps this behavior. Phase 2 stops the write on a key mismatch (FR-014).

Caution: A table that keeps the AP key still merges client rows that share `bssid` and `ap_mac` until Phase 2 ships.

## ArangoDB vertex configuration

| Endpoint name | Vertex collection | Key field | Edge collections | Source |
| - | - | - | - | - |
| `listSiteRogueClients` | `rogue_clients` | `client_mac` | `RogueClientDetectedByAP`, `RogueClientOnBSSID` | `src/foundation/persistence/db/writers/arango_writer.py:1844-1864` |
| `listSiteRogueAPs` | `rogue_aps` | `bssid` | `RogueAPDetectedBySite`, `RogueAPDetectedByAP` | `arango_writer.py:1823-1843` |

The collection mapping is at `arango_writer.py:1119-1120`.

Caution: The client key uses `client_mac` only. One client on two BSSIDs keeps one document. Phase 2 changes the key to `client_mac` and `bssid` (FR-016).

## Redis namespace

Not verified on `main`. See `design/research.md`, item U-E.
