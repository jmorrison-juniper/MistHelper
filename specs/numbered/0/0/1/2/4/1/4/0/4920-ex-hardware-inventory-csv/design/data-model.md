# Data Model: EX Hardware Inventory CSV

Each entity lists its fields and constraints. A task cites a field as `Entity.field`. The report holds natural keys from Mist, not artificial identifiers.

## OrganizationRef

One Mist organization in the scope of a run.

| Field | Type | Constraint |
|-------|------|------------|
| `OrganizationRef.org_id` | text | Required. A Mist UUID. Unique within one `ScopeDecision`. |
| `OrganizationRef.org_name` | text | Required. Uses the Mist name, or `org_id` when Mist gives no name. At most 256 characters. |
| `OrganizationRef.msp_id` | text | Empty for a direct grant. A Mist UUID for an organization that came from an MSP list. |
| `OrganizationRef.source` | enum | `direct` or `msp`. |

## ScopeDecision

The result of scope detection. It is built once for each run, before any device request.

| Field | Type | Constraint |
|-------|------|------------|
| `ScopeDecision.mode` | enum | `organization` or `msp`. `msp` only when the profile holds an MSP grant and `listMspOrgs` returned status 200 with at least one organization. |
| `ScopeDecision.credential_type` | enum | `api_token` or `login`. Display only. |
| `ScopeDecision.account_kind` | enum | `organization_token` when the profile has no `email`. `user` otherwise. Display only. |
| `ScopeDecision.organizations` | tuple of `OrganizationRef` | At least one. In `organization` mode exactly one. |
| `ScopeDecision.notes` | tuple of text | Each note is one plain sentence for the operator. Empty when nothing unusual happened. |

State: detection fails with `ScopeError` when the profile read does not return status 200, when no organization remains, or when `org_id` is needed and absent. A failed `listMspOrgs` call is not an error. It adds one note and keeps `organization` mode.

## HardwareConcurrency

The value of the setting `StreamSettings.hardware_concurrency`.

| Field | Type | Constraint |
|-------|------|------------|
| `StreamSettings.hardware_concurrency` | integer | 1 through 5. The default is 3. A value outside the range, or text that is not a whole number, gives the default and one warning that names `PORTAL_WS_HARDWARE_CONCURRENCY`. |

## TargetResult

The outcome of one target, as the report compiler reads it.

| Field | Type | Constraint |
|-------|------|------------|
| `TargetResult.identity` | mapping | Holds `org_id`, `site_id`, `site_label`, `device_id`, and `label`. `device_id` is required. |
| `TargetResult.org_name` | text | Comes from the `ScopeDecision`. |
| `TargetResult.state` | enum | `completed`, `failed`, `skipped`, or `stopped`. |
| `TargetResult.reason` | text | The batch reason code, or empty. At most 200 characters. |
| `TargetResult.xml_text` | text or none | The saved reply text. Present only when `state` is `completed`. At most 1 MiB. |

Mapping to `ReportRow.collection_status`: `completed` with text gives `collected`. `completed` without text gives `failed`. `failed` gives `failed`. `skipped` gives `skipped`. `stopped` gives `cancelled`.

## FlattenedItem

One hardware item that the flattener reads from one reply.

| Field | Type | Constraint |
|-------|------|------------|
| `FlattenedItem.level` | integer | 0 or more. The chassis is 0. |
| `FlattenedItem.path` | text | The item names joined by `/`, for example `Chassis/FPC 0/PIC 1/Xcvr 3`. A repeated name under one parent gets the suffix `#2`, `#3`, and so on. Unique within one device. At most 512 characters. |
| `FlattenedItem.item_type` | text | The local element name, for example `chassis-module`. |
| `FlattenedItem.fields` | mapping | Every non-item child element as a name and text. A nested non-item child adds its leaf values as `parent_child`. Every attribute adds `attr_<name>`. A name uses `_` for `-` and `:`. Text is trimmed. |

A device also holds `cli_banner`, the trimmed text of `cli/banner`, at most 64 characters.

## ReportRow

One row of the CSV file.

| Field | Type | Constraint |
|-------|------|------------|
| `ReportRow.report_run_utc` | text | ISO 8601 in UTC, form `YYYY-MM-DDTHH:MM:SSZ`. The same on every row of a run. |
| `ReportRow.scope` | enum | `organization` or `msp`. |
| `ReportRow.org_id` | text | Required. |
| `ReportRow.org_name` | text | From `OrganizationRef.org_name`. |
| `ReportRow.site_id` | text | Required. |
| `ReportRow.site_name` | text | From `TargetResult.identity` as `site_label`. |
| `ReportRow.device_id` | text | Required. The logical device. |
| `ReportRow.device_name` | text | From `TargetResult.identity` as `label`. |
| `ReportRow.record_type` | enum | `hardware_item` or `device_outcome`. |
| `ReportRow.collection_status` | enum | `collected`, `failed`, `skipped`, or `cancelled`. `hardware_item` rows use `collected`. |
| `ReportRow.collection_detail` | text | Empty for `collected`. Otherwise one plain reason. At most 200 characters. |
| `ReportRow.device_cli_banner` | text | The `FlattenedItem` device banner. Empty for `device_outcome` rows. |
| `ReportRow.item_level` | integer or empty | Empty for `device_outcome` rows. |
| `ReportRow.item_path` | text | Empty for `device_outcome` rows. |
| `ReportRow.item_type` | text | Empty for `device_outcome` rows. |
| `ReportRow.item_<field>` | text | One column for each field name in the union of all rows. Empty when a row lacks the field. |

Natural key for the database backends: `ReportRow.org_id`, `ReportRow.device_id`, and `ReportRow.item_path`. A `device_outcome` row has an empty `item_path`, so each device keeps one outcome row. The key type is `composite_pk`. A second run replaces the rows of the same device item.

Column order: the fixed columns in the order above, then the item columns. The item columns start with `item_name`, `item_version`, `item_part_number`, `item_serial_number`, `item_model_number`, `item_clei_code`, and `item_description`. Any other field follows in sorted order.

Text safety: a text value that starts with `=`, `+`, `-`, `@`, a tab, or a carriage return gets a leading apostrophe. The numeric `ReportRow.item_level` and the fixed enum values stay unchanged.

## ReportFile

The one CSV file of a run.

| Field | Type | Constraint |
|-------|------|------------|
| `ReportFile.name` | text | CLI: `ExHardwareInventory_<YYYYMMDDTHHMMSSZ>.csv` under `data/`. Portal: `hardware/inventory.csv` in the run folder. |
| `ReportFile.row_count` | integer | The number of data rows. At least 1. |
| `ReportFile.partial` | boolean | True when the operator cancelled or any target did not collect. |
| `ReportFile.size_bytes` | integer | At most the remaining quota of the run. The portal run limit is 64 MiB. |

## RunSummary

The console summary of one CLI run.

| Field | Type | Constraint |
|-------|------|------------|
| `RunSummary.organizations` | integer | At least 1. |
| `RunSummary.targets` | integer | The number of confirmed targets. |
| `RunSummary.counts` | mapping | `collected`, `failed`, `skipped`, `cancelled`, each an integer. |
| `RunSummary.report_path` | text | The path of the file. Empty when no row exists. |

## Relationships

- A `ScopeDecision` holds one or more `OrganizationRef` values.
- A run holds many `TargetResult` values. Each one belongs to one `OrganizationRef`.
- A collected `TargetResult` yields one device banner and one or more `FlattenedItem` values.
- Each `FlattenedItem` and each non-collected `TargetResult` becomes one `ReportRow`.
- All `ReportRow` values of a run go into one `ReportFile`.
