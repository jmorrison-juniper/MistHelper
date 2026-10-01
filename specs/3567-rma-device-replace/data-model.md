# Data Model: RMA Device Replacement

## InventoryDevice

Represents one row from `getOrgInventory`.

| Field | Type | Rule |
| - | - | - |
| `id` | string | Required for assigned old devices. |
| `mac` | string | Required for old and new devices. Store normalized lowercase text without separators. |
| `serial` | string | Optional display field. |
| `model` | string | Optional display field. |
| `type` | string | Required for type matching. Expected values include `ap`, `switch`, and `gateway`. |
| `site_id` | string or empty | Required for old devices. Empty means unassigned. |
| `name` | string | Optional selector and display field. |
| `raw` | mapping | Original inventory row for evidence. |

## ReplaceRequest

Represents the `replaceOrgDevices` body.

| Field | Type | Rule |
| - | - | - |
| `site_id` | string | Copied from the old device. |
| `mac` | string | Old device MAC address. |
| `inventory_mac` | string | Replacement device MAC address. |
| `discard` | list of string | Empty list for the first version. |

## DeviceConfigurationBackup

Represents one JSON backup file under `data/rma_backups/`.

| Field | Type | Rule |
| - | - | - |
| `backup_time` | string | UTC ISO 8601 timestamp. |
| `org_id` | string | Organization identifier. |
| `old_device` | object | Old inventory device fields. |
| `configuration` | object | `getSiteDevice` response data. |

## DeviceReplaceLogEntry

Represents one row in `data/DeviceReplaceLog.csv`.

| Field | Type | Rule |
| - | - | - |
| `timestamp` | string | UTC ISO 8601 timestamp. |
| `org_id` | string | Organization identifier. |
| `old_mac` | string | Old device MAC address. |
| `new_mac` | string | Replacement device MAC address. |
| `old_type` | string | Old device type. |
| `new_type` | string | Replacement device type. |
| `result` | string | `sent`, `dry_run`, `cancelled`, or `error`. |
| `backup_path` | string | Backup file path. |
| `message` | string | Short operator-readable result. |
