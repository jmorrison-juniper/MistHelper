# Contract: Combined Exports

Scope: the three combined exports that `src/mist/resources/inventory/org_device_inventory_msp.py` writes after a batch with two or more successful results.

## File Names

`{msp_name}` is the MSP name after `_sanitize_msp_name`. The constants `_MODEL_EXPORT_SUFFIX`, `_VERSION_EXPORT_SUFFIX`, and `_PIVOT_EXPORT_SUFFIX` are at lines 24-26.

| Batch | Prefix | Model export | Firmware export | Version-per-model export |
| --- | --- | --- | --- | --- |
| Complete | `MSP_{msp_name}` | `MSP_{msp_name}_CombinedDeviceModelCounts` | `MSP_{msp_name}_CombinedDeviceFirmwareSummary` | `MSP_{msp_name}_CombinedDeviceVersionPerModel` |
| Partial | `MSP_{msp_name}_Partial` | `MSP_{msp_name}_Partial_CombinedDeviceModelCounts` | `MSP_{msp_name}_Partial_CombinedDeviceFirmwareSummary` | `MSP_{msp_name}_Partial_CombinedDeviceVersionPerModel` |

The complete names match the names on `main`. The partial names add the `_Partial` marker before the suffix.

## Writer Calls

Every export goes through `DataExporter.write_with_format_selection`. The calls keep their identifiers and their field order.

| Report | Identifier | Field order | Call on `main` |
| --- | --- | --- | --- |
| Model | `orgDeviceModelSummary` | `Org`, `Device Type`, `Model`, `Count` | Line 415, identifier at line 418 |
| Firmware | `orgDeviceFirmwareSummary` | `Org`, `Device Type`, `Version`, `Count` | Line 426, identifier at line 429 |
| Version per model | `orgDeviceVersionPerModel` | `Org`, `Model`, `Device Type`, one column for each version, `Total` | Line 382, identifier at line 385 |

## Rows

- Each row comes from a successful result.
- A skipped record and a failed record produce no row.
- Each row keeps its existing fields. The change adds no field and removes no field.
- A partial batch adds no completeness field to any row. The file name carries the partial state.

## Threshold

- Combined exports need at least two successful results.
- With fewer than two successful results, the batch writes no export file. The batch logs the reason at info level.

## Compatibility

- Complete batches keep every file name, identifier, field order, and row rule that `main` uses.
- Partial batches use the `_Partial` names. A consumer that reads partial files must match the partial names.
- Files that `main` wrote for an earlier partial batch carry complete names. The change does not rename those files.
