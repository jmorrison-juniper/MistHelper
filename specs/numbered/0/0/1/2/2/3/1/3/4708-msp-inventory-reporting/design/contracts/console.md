# Contract: Batch Console Output

Scope: menu 13, batch mode 3, in `src/mist/resources/inventory/org_device_inventory_msp.py`.

Braces mark a value that the code fills. A leading `\n` means one blank line before the line.

## Lines Printed for Each Organization Record

| Case | Line | Status |
| --- | --- | --- |
| Batch start | The existing `Found N organizations` line, printed once before the first record. | Unchanged. Line 513. |
| Progress | `  [{position}/{total}] {name}` | Unchanged. Printed by `_process_org`. |
| Skipped record | `  [{position}/{total}] Skipping {name}: missing organization ID` | New. The `{name}` value is the record name. When the name is empty, the value is `unnamed record`. |
| Runner failure | `    X Error processing {name}: {error}` | Unchanged. Line 465. |

## Footer Lines

| Case | Line | Status |
| --- | --- | --- |
| Complete batch, every record succeeds | `\nMSP inventory summary complete. Processed {total} organizations.` | Unchanged text. Line 516 on `main`. |
| Partial batch, at least one record skipped or failed | `\nMSP inventory summary partial. Processed {successful} of {total} organizations. Skipped or failed: {skipped_or_failed}.` | New. |
| Zero successful records | The partial footer, with `{successful}` equal to zero. | New. No combined report follows. |

## Combined Report Headings

The batch prints the headings when it has two or more successful results.

| Report | Heading line |
| --- | --- |
| Model count | `  Combined MSP Model Count Summary ({label})` |
| Firmware version | `  Combined MSP Firmware Version Summary ({label})` |
| Version per model | `  Combined MSP Version Distribution per Model ({label})` |

The `{label}` value depends on the batch:

- Complete batch: `All Orgs`. This text is unchanged.
- Partial batch: `Partial: {successful} successful, {skipped_or_failed} skipped or failed`.

## Closing Line

`  Combined MSP reports written with prefix: {prefix}_` stays unchanged. The `{prefix}` value follows `design/contracts/export.md`.

## Log Lines

- Before the footer, the code writes this info line: `Reporting MSP inventory coverage: %d successful, %d skipped or failed`.
- After the footer, the code writes this debug line: `MSP inventory coverage printed for %d organizations: partial=%s`.
- Both lines use ASCII text and `%s` style formatting. Neither line holds a secret.
