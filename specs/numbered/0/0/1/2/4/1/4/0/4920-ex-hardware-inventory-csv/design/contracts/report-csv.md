# Contract: Report CSV

The report is one CSV file for one run. Both front ends write the same columns and the same rules.

## File

- Encoding: UTF-8 text, no byte order mark.
- Line end: the CSV writer default, so `\r\n`.
- One header row, then one row for each report row. A text value with a comma, a quote, or a line break uses standard CSV quoting.
- CLI name: `ExHardwareInventory_<YYYYMMDDTHHMMSSZ>.csv` in `data/`.
- Portal name: `hardware/inventory.csv` in the run folder, and the download name `ex-hardware-inventory.csv`.

## Columns

The fixed columns come first, in this order:

| Column | Holds |
|--------|-------|
| `report_run_utc` | The start of the run, in UTC, `YYYY-MM-DDTHH:MM:SSZ`. |
| `scope` | `organization` or `msp`. |
| `org_id` | The organization identifier. |
| `org_name` | The organization name. |
| `site_id` | The site identifier. |
| `site_name` | The site name. |
| `device_id` | The logical device identifier. |
| `device_name` | The device name. |
| `record_type` | `hardware_item` or `device_outcome`. |
| `collection_status` | `collected`, `failed`, `skipped`, or `cancelled`. |
| `collection_detail` | The reason, empty for `collected`. |
| `device_cli_banner` | The role marker of the shell, for example `{master:0}`. |
| `item_level` | The depth of the item. The chassis is 0. |
| `item_path` | The names of the item and its parents joined by `/`. |
| `item_type` | The element name, for example `chassis-module`. |

The item columns follow. The first seven are fixed: `item_name`, `item_version`, `item_part_number`, `item_serial_number`, `item_model_number`, `item_clei_code`, `item_description`. Every other field that any switch returned follows in sorted order, for example `item_disk_size`, `item_model`, `item_product`, `item_product_number`, `item_vendor`, and `item_attr_style`.

## Rows

- A `hardware_item` row stands for one part of a switch. A switch with a chassis, two modules, and one sub-module has four rows.
- A `device_outcome` row stands for one attempted switch that returned no valid reply. Its item columns are empty and its `item_path` is empty.
- A switch that collected has no `device_outcome` row.
- The row order is: organization name, site name, device name, then the order of the reply. A `device_outcome` row sorts by the same keys.

## Cell rules

- A missing field is an empty cell. A field that holds only white space is an empty cell.
- A text value that starts with `=`, `+`, `-`, `@`, a tab, or a carriage return gets a leading apostrophe. The apostrophe is part of the cell.
- The columns `item_level`, `record_type`, `collection_status`, and `scope` never get an apostrophe.
- The report holds no credential. A reply that holds one never reaches the report.

## Natural key

`org_id`, `device_id`, and `item_path` identify a row. The key is unique within one report.

## Example

The values below are invented.

```text
report_run_utc,scope,org_id,org_name,site_id,site_name,device_id,device_name,record_type,collection_status,collection_detail,device_cli_banner,item_level,item_path,item_type,item_name,item_version,item_part_number,item_serial_number,item_model_number,item_clei_code,item_description
2026-11-24T23:00:00Z,organization,ORG-1,Example Org,SITE-1,Example Site,DEV-1,ex-switch-01,hardware_item,collected,,{master:0},0,Chassis,chassis,Chassis,,,SERIAL-0001,,,EX-EXAMPLE-48
2026-11-24T23:00:00Z,organization,ORG-1,Example Org,SITE-1,Example Site,DEV-1,ex-switch-01,hardware_item,collected,,{master:0},1,Chassis/FPC 0,chassis-module,FPC 0,REV 01,000-000001,SERIAL-0002,EX-EXAMPLE-48,CLEI-0001,EX-EXAMPLE-48
2026-11-24T23:00:00Z,organization,ORG-1,Example Org,SITE-1,Example Site,DEV-2,ex-switch-02,device_outcome,failed,The shell did not show a stable prompt.,,,,,,,,,,,
```
