# Contract: Transceiver Master CSV

This contract defines the file that the CLI and the portal both write. Both front ends use the same writer.

## File Format

- Encoding: UTF-8.
- One header row, then one row for each record.
- The file passes the existing file check, `CsvVerifier.verify`, before publication (FR-018, task T007).
- Every text cell passes `CellGuard.clean` before the file is written (FR-017, task T006).
- A file above 64 MiB is not written (task T007).

## Header

The columns appear in this order.

1. `report_run_utc`: The UTC time of the run.
2. `source_format`: `xml` or `json`. The value is empty for an outcome row.
3. `org_id`: The organization identifier.
4. `org_name`: The organization name.
5. `site_id`: The site identifier.
6. `site_name`: The site name.
7. `device_id`: The switch identifier.
8. `device_name`: The switch hostname.
9. `record_type`: `transceiver_item`, `no_transceiver`, `device_outcome`, or `organization_outcome`.
10. `collection_status`: `collected`, `failed`, `skipped`, or `cancelled`.
11. `collection_detail`: Empty for a collected row. A plain reason for any other row.
12. `transceiver_name`: The item name, `Xcvr` followed by one space and an identifier.
13. `module_type`: The description text, trimmed, with repeated spaces collapsed.
14. `module_location`: The parent item path without the chassis root.
15. `part_number`: The part number of the item.
16. `serial_number`: The serial number of the item.
17. `model_number`: The model number of the item.
18. `item_path`: The full item path, which forms the natural key with `org_id` and `device_id`.

## Row Rules

- **Transceiver row**: `record_type` is `transceiver_item`. `collection_status` is `collected`. `collection_detail` is empty. The device and organization columns hold their values. An absent source value stays an empty cell (FR-010).
- **No-transceiver row**: `record_type` is `no_transceiver`. `collection_status` is `collected`. The transceiver columns and `item_path` are empty (FR-013).
- **Device outcome row**: `record_type` is `device_outcome`. `collection_status` is `failed`, `skipped`, or `cancelled`. `collection_detail` holds the plain reason. The transceiver columns are empty (FR-014).
- **Organization outcome row**: `record_type` is `organization_outcome`. `collection_status` is `failed`. The `device_id`, `device_name`, `site_id`, and `site_name` columns are empty (FR-015).
- **Source precedence**: The XML reply supplies the rows. A JSON reply supplies rows only when the XML reply is absent for a completed target (FR-011).

## Reason Text

The `collection_detail` column holds the plain reason. The reason texts come from `report/builder.py`.

- `completion_unproven`: The shell did not show a stable prompt (line 51).
- `format_failed`: The reply was not a valid chassis inventory (line 52).
- `output_failed`: The reply could not be saved (line 54).
- The texts for a missing reply file and an unreadable saved reply are at lines 87 and 88.

## Natural Key

The triple `org_id`, `device_id`, and `item_path` is unique in the file (FR-009). The composite key `ExTransceiverMaster` enforces it in the database backends (task T003).

## Equivalence

- For the same switch data, the XML-only, JSON-only, and both-format runs give equal transceiver rows in every column except `source_format` and `report_run_utc` (SC-001).
- A both-format run adds no row from the JSON reply when the XML reply is valid (FR-011).

## Example

The example shows only the column shape. It uses synthetic values (FR-031).

```
report_run_utc,source_format,org_id,org_name,site_id,site_name,device_id,device_name,record_type,collection_status,collection_detail,transceiver_name,module_type,module_location,part_number,serial_number,model_number,item_path
2026-11-26T08:00:00Z,xml,ORG-EXAMPLE,Example Org,SITE-EXAMPLE,Example Site,DEV-EXAMPLE-01,SW-EXAMPLE-01,transceiver_item,collected,,Xcvr 0,SFP+-10G-SR,FPC 0/PIC 0,740-000001,SERIAL-XC0,SFP-EXAMPLE,Chassis/FPC 0/PIC 0/Xcvr 0
```
