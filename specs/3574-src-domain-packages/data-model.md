# Data Model: Source Package Map

## Domain Package Map

| Domain | Group | Current children |
| - | - | - |
| `foundation` | `runtime` | `bootstrap`, `config`, `input`, `time`, `validation` |
| `foundation` | `models` | `data`, `dataclasses` |
| `foundation` | `persistence` | `cache`, `db` |
| `foundation` | `support` | `refactors`, `utils` |
| `foundation` | direct module | `constants.py` |
| `mist` | `access` | `api`, `audit`, `auth` |
| `mist` | `resources` | `device`, `gateway`, `inventory`, `org`, `site` |
| `mist` | `intelligence` | `analytics`, `juniper_docs`, `marvis`, `reports`, `troubleshooting` |
| `mist` | `realtime` | `websocket`, `websocket_streams` |
| `mist` | `networking` | `network` |
| `operations` | `execution` | `capture`, `firmware`, `ssh`, `ssid_consolidation` |
| `operations` | `exporting` | `export` |
| `operations` | `hardware` | `mib_generator` |
| `operations` | `wan` | `org_data_collector.py`, `wan_hub_group_manager.py`, `wan_vpn_builder.py` |
| `operations` | `protection` | `security` |
| `interfaces` | `portals` | `upgrade_portal` |
| `interfaces` | `visualization` | `maps`, `ui` |
| `interfaces` | `monitoring` | `metrics_gateway` |

## Import Path Rule

For each row, insert the domain and group between `src` and the current child name.

Example:

```text
src.operations.execution.firmware.manager
src.operations.execution.firmware.manager
```

## Invariants

- Each domain package has five children or fewer.
- Each group package has five children or fewer.
- Each moved package keeps its current internal files and directories.
- Each moved module keeps its current module-level symbols.
- Each repository import uses one canonical path.
