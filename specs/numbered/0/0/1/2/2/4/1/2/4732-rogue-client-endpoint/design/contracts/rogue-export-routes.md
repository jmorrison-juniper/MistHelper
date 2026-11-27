# Contract: Rogue export routes

This contract names the endpoint name that each rogue export sends to the export writer. It also names the output that each route creates.

## Route table

| Menu | Collector call (line) | Helper label | CSV base name | Endpoint name sent to the writer | Caller line after Phase 1 |
| - | - | - | - | - | - |
| 29 | `mistapi.api.v1.sites.insights.listSiteRogueClients` (`src/operations/exporting/export/org_client_security_exporter.py:88`) | `rogue clients` | `OrgRogueClients` | `listSiteRogueClients` | 94 |
| 30 | `mistapi.api.v1.sites.insights.listSiteRogueAPs` (`org_client_security_exporter.py:111`) | `rogue APs` | `OrgRogueAPs` | `listSiteRogueAPs` | 117 |

The menu registration stays the same. Menu 29 is `rogue_clients` at `MistHelper.py:4051`. Menu 30 is `rogue_aps` at `MistHelper.py:4059`. Both have category `safe` (`src/foundation/support/utils/operation_registry.py:692-693`).

## Export writer call

The helper calls the export writer with this shape (`src/operations/exporting/export/data_exporter.py:153-156`).

- `DataExporter.write_with_format_selection(rows, csv_base_name, api_function_name=<endpoint name>)`
- `rows` is the flattened list of dictionaries.
- `csv_base_name` is the CSV base name from the route table.
- `api_function_name` is the endpoint name from the route table. The name is required.

## Output names

- The CSV branch writes the file `<csv base name>.csv`.
- The SQLite branch writes the table named by the base name without `.csv` (`data_exporter.py:381`).
- The polyglot branch passes the same endpoint name to the router (`data_exporter.py:306` and `src/foundation/persistence/db/router.py:232`).

## Output columns

Each row keeps the flattened fields from the Mist response. The helper adds `site_id` and `site_name` (`org_client_security_exporter.py:178-179`). Phase 1 changes no column name.

## Empty result and cache hit

- An empty result makes no export writer call. The info line names the label (`org_client_security_exporter.py:221`).
- A fast-mode cache hit makes no fetch and no export writer call (FR-008).
