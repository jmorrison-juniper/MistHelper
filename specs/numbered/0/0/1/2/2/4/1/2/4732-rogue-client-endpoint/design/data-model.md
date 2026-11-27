# Data Model: Rogue client exports use the client endpoint name

## Entities

### Rogue client observation

- **Source endpoint**: `listSiteRogueClients`. The collector calls `mistapi.api.v1.sites.insights.listSiteRogueClients` at `src/operations/exporting/export/org_client_security_exporter.py:88`.
- **Response fields**: `client_mac`, `bssid`, `ap_mac`, `num_aps`, `band`, `avg_rssi`, and `annotation`. The schema requires all seven fields (`documentation/mist-api-openapi31yaml.yaml:81833-81866`).
- **Site context fields**: `site_id` and `site_name`. The helper adds them to each row (`org_client_security_exporter.py:178-179`).
- **Natural key**: `client_mac` and `bssid`. The strategy is at `src/foundation/support/refactors/endpoint_primary_key_strategies.py:1305`.
- **Index columns**: `site_id`, `ap_mac`, and `band` (`endpoint_primary_key_strategies.py:1306`).
- **Targets**: The SQLite table `OrgRogueClients`. The table name is the CSV base name (`src/operations/exporting/export/data_exporter.py:381`). The ArangoDB collection `rogue_clients` (`src/foundation/persistence/db/writers/arango_writer.py:1120`). The Redis namespace is listed as Unverified in `design/research.md`.

### Rogue AP observation

- **Source endpoint**: `listSiteRogueAPs`. The collector calls it at `org_client_security_exporter.py:111`.
- **Response fields**: `ap_mac`, `avg_rssi`, `bssid`, `channel`, and `num_aps` are required (`documentation/mist-api-openapi31yaml.yaml:81826-81831`). The schema also defines `ssid`, `delta_x`, `delta_y`, `seen_on_lan`, and `times_heard`.
- **Natural key**: `bssid` and `ap_mac` (`endpoint_primary_key_strategies.py:1298`).
- **Index columns**: `site_id`, `ssid`, and `channel` (`endpoint_primary_key_strategies.py:1299`).
- **Targets**: The SQLite table `OrgRogueAPs` and the ArangoDB collection `rogue_aps` (`arango_writer.py:1119`).

### Existing SQLite table

- **Creation**: The DDL uses `CREATE TABLE IF NOT EXISTS` (`src/foundation/persistence/db/database_schema_utils.py:149`).
- **Key rule**: The key of the first write stays in the table. A later write with another endpoint name does not change it. The writer adds missing columns only (`src/foundation/support/refactors/sqlite_database_writer.py:288`).

## Key Rules

- The endpoint name selects the strategy. `get_endpoint_strategy` returns the configured strategy when the name exists (`database_schema_utils.py:80-81`).
- A key column is declared `NOT NULL` (`database_schema_utils.py:125`).
- `INSERT OR REPLACE` removes the existing row that has the same key (`sqlite_database_writer.py:368`).

Warning: `INSERT OR REPLACE` discards the existing row that shares the key of the new row. Do not rebuild an existing table before decision D-3 is approved.

## State Transitions

### SQLite table lifecycle

| State | Trigger | Result | Phase |
| - | - | - | - |
| A. Absent | First write with `listSiteRogueClients` | Created with primary key `(client_mac, bssid)` | Phase 1 (correct) |
| B. Absent | First write with `listSiteRogueAPs` | Created with primary key `(bssid, ap_mac)` | Earlier code path (unchanged) |
| C. Present with another key | Write with the client endpoint name | Phase 1: unchanged. Phase 2: stop before insert and report both keys (FR-014) | Phase 2 HOLD |
| D. Present with another key | Approved naming plan (D-3, option b) | New table with the client key. The old table stays unchanged | Phase 2 HOLD |

Caution: A table in state B keeps its AP primary key after Phase 1. New client rows still collapse in that table.

### ArangoDB document lifecycle

- **Current**: A client row upserts the `rogue_clients` document keyed by `client_mac` (`arango_writer.py:1846`). One client on two BSSIDs keeps one document.
- **Phase 2 target**: The vertex key includes `client_mac` and `bssid` (FR-016).
- **Replaced AP documents**: Documents that earlier runs replaced stay in place until decision D-4 is approved (FR-017).

### Export run lifecycle (Phase 1)

| Condition | Writer call | Log |
| - | - | - |
| Fast-mode cache hit | None (FR-008) | Existing cache message |
| Empty result | None | Info line names the label (`org_client_security_exporter.py:221`) |
| Non-empty result | One call with the endpoint name (FR-001, FR-002) | Info line before the call. Debug line after it (FR-007) |
