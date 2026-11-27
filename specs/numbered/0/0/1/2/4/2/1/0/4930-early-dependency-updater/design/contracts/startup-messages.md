# Contract: Startup dependency check messages

This contract lists each log record that the early check writes for this change. The text is ASCII only. Each template uses the logging `%s` form, and the logger receives the template with its values. The level column gives the logging level.

## Records

| ID | Level | Trigger | Template |
| - | - | - | - |
| M-01 | debug | `DISABLE_AUTO_INSTALL` is true (existing record, unchanged) | Early dependency auto-install disabled via DISABLE_AUTO_INSTALL |
| M-02 | error | More than five packages are missing, broken, or off their pin | Refusing to change %s packages in this process. Run uv sync --locked --extra dev |
| M-03 | warning | A loaded package would change | Skipping %s: this process has loaded it. Close the process, then run uv sync --locked --extra dev |
| M-04 | warning | A broken package would change | Skipping %s: its RECORD file is incomplete. Close the process, then run uv sync --locked --extra dev |
| M-05 | debug | A snapshot holds the RECORD files of one package | Captured %s RECORD files for %s before the upgrade |
| M-06 | error | A snapshot cannot be captured | Skipped the upgrade of %s: the snapshot failed |
| M-07 | info | Before each in-process install (existing record, unchanged) | Installing %s with UV... |
| M-08 | info | Before each in-process upgrade (existing record, unchanged) | Upgrading %s from %s with UV... |
| M-09 | debug | After each in-process upgrade | Upgrade result for %s: %s |
| M-10 | info | A snapshot is restored after a failed upgrade | Restored %s RECORD files for %s after the failed upgrade |
| M-11 | error | A restore fails | Could not restore %s. The snapshot is kept at %s. Close the process, then run uv sync --locked --extra dev |
| M-12 | debug | After each in-process install | Install result for %s: %s |

## Order rules

- Each in-process install writes M-07 before the install, and M-12 after it.
- Each in-process upgrade writes M-05 before the upgrade. It writes M-08 before the upgrade, and M-09 after it.
- A failed upgrade writes M-10 when the restore succeeds, or M-11 when the restore fails.
- Each skipped package writes one of M-03 or M-04, and no other change record.
- A refusal writes M-02 once, and no change record follows it.

## Stability

The text in each template is part of the operator interface. The message IDs are for the test cases and for this record. A change to a template needs a change to this file and to the matching test case.
