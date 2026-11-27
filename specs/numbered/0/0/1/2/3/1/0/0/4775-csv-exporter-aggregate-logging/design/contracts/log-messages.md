# Contract: Log messages of the changed statements

This contract defines each log message that the change adds or keeps in the four exporter files. Tests T002 to T005 and task T014 check it.

## Added and changed messages

| Path after the change | Base line | Level | Template | Arguments | Content rule |
| - | - | - | - | - | - |
| `src/operations/exporting/export/data_exporter.py`, in `write_to_csv` | 410 | DEBUG | `Determined %s CSV fields` | `len(fields)` | Count only. The field names stay out. |
| `src/operations/exporting/export/data_exporter.py`, in `_emit_rows`, before the writes | 437 to 443 | INFO | `Emitting %s rows across %s fields` | `len(escaped_data)`, `len(fields)` | Count only. The message comes before the action. |
| `src/operations/exporting/export/data_exporter.py`, in `_emit_rows`, after the writes | 437 to 443 | DEBUG | `Emitted %s rows across %s fields` | `len(escaped_data)`, `len(fields)` | Count only. The message comes after the action. |
| `src/operations/exporting/export/org_inventory_exporter.py`, in `_enrich_devices_with_site_info`, before the loop | 604 to 616 | INFO | `Enriching %s devices with site info` | `len(inventory)` | Count only. |
| `src/operations/exporting/export/org_inventory_exporter.py`, in `_enrich_devices_with_site_info`, after the loop | 604 to 616 | DEBUG | `Enriched %s devices with site info` | `len(enriched_devices)` | Count only. |
| `src/operations/exporting/export/org_inventory_exporter.py`, in `_split_full_address` | 723 | DEBUG | `Failed to split a site address (%s)` | `type(exception).__name__` | Error type only. The address stays out. |
| `src/operations/exporting/export/sites_by_ap_model_exporter.py`, in `_split_address` | 88 | DEBUG | `Failed to split a site address (%s)` | `type(exception).__name__` | Error type only. The address stays out. |

## Removed messages

| Base path and line | Removed message or table | Reason |
| - | - | - |
| `data_exporter.py`, line 443 | `Row %s written: %s` with the first three rows | It logs every cell value of rows 0 to 2. |
| `org_inventory_exporter.py`, line 613 | `Enriched device %s (%s) with site info.` | It logs the name and MAC address of every device. |
| `org_inventory_exporter.py`, line 652 | Devices summary table | It logs device identifiers and location fields. |
| `org_inventory_exporter.py`, line 766 | Gateways summary table | It logs gateway identifiers and location fields. |
| `site_device_exporter.py`, line 110 | Inventory summary table | It logs every flattened field of every inventory row. |

## Kept messages

- The messages that report a count, a path, a fixed phrase, or an operation name stay unchanged. Research section "Log Statement Inventory" lists examples.
- The warnings and errors with exception text stay unchanged (D-8). They are `data_exporter.py` lines 121, 149, and 315, and `org_inventory_exporter.py` lines 136, 193, 327, 529, and 543.

## Forbidden content in every changed message

- A cell value of any row.
- A device name, MAC address, serial number, model, site name, site address, street, city, state, zip code, or country.
- A list of column names.
- A table rendered as text.
