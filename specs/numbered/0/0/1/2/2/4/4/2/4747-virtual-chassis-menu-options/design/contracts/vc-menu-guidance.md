# Contract: Virtual chassis menu guidance

## Surface

The change affects two printed blocks in the MistHelper console. Block A prints after the status check (menu 14). Block B prints after a single conversion (menu 161) succeeds. The bulk path (menu 162) prints neither block.

## Block A: usage notes after the status check

Printed by the usage-note helper (`src/mist/resources/device/virtual_chassis.py` line 417, RC-10). The helper prints its header and notes at lines 419 to 424 (RC-101). The status check calls the helper at line 250 (RC-12).

| Line | Text after the change | Menu named | Registry category | Text before the change |
| - | - | - | - | - |
| 1 | Blank line, then `  Usage Notes:` | none | none | same |
| 2 | `   !? Use menu 161 to convert individual switches` | 161 | destructive (RC-34) | `   !? Use option 92 to convert individual switches` |
| 3 | `   !? Use menu 162 for bulk conversion by site list` | 162 | destructive (RC-35) | `   !? Use option 93 for bulk conversion by site list` |
| 4 | `   !? Virtual chassis switches without '020003' vc_mac prefix can be converted` | none | none | same (prefix constant at line 34, RC-100) |

## Block B: rollback guidance after a single conversion

Printed by the success helper (line 533, RC-11). The helper prints its six lines at lines 535 to 540 (RC-102). The response handler calls the helper on success (line 480, RC-13). The execute helper calls the convert endpoint before that (line 477, RC-14). HTTP and detail errors return before the helper (line 496, RC-89).

| Line | Text | Menu named |
| - | - | - |
| 1 | ` Conversion to virtual MAC triggered successfully!` | none |
| 2 | ` Check the device status in the Mist UI to monitor progress.` | none |
| 3 | Blank line, then `  Rollback Guidance:` | none |
| 4 | `   If the conversion causes issues, contact Juniper TAC.` | none |
| 5 | `   The device may need a factory reset and re-adoption to revert.` | none (RC-09) |
| 6 | `   Use menu 14 to verify conversion status after the device reboots.` | 14 (registry category `resource_intensive`, RC-36) |

Before the change, line 6 read `   Use Menu 94 to verify conversion status after the device reboots.`.

## Rules

- R1: Each guidance line names at most one menu.
- R2: Each named menu keeps the registry category that this contract lists.
- R3: The guidance uses the term `menu`, not `option`.
- R4: Printed output stays ASCII.
- R5: The bulk path (menu 162) prints neither block (RC-15).
- R6: A conversion that fails prints no Block B.
- R7: The typed `CONVERT` prompts and the convert calls do not change (RC-14, RC-16, RC-17).

## Example

Status check output tail, after the change:

```text
  Usage Notes:
   !? Use menu 161 to convert individual switches
   !? Use menu 162 for bulk conversion by site list
   !? Virtual chassis switches without '020003' vc_mac prefix can be converted
```

Single conversion output tail, after the change:

```text
 Conversion to virtual MAC triggered successfully!
 Check the device status in the Mist UI to monitor progress.

  Rollback Guidance:
   If the conversion causes issues, contact Juniper TAC.
   The device may need a factory reset and re-adoption to revert.
   Use menu 14 to verify conversion status after the device reboots.
```
