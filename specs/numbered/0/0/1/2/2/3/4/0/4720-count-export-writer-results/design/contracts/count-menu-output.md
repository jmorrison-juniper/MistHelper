# Contract: Count menu messages

## Scope

This contract covers the console and log lines that `CountExporter._persist` and `CountExporter._run` produce for menus 235, 236, and 237. It names the change for each line. The CSV content and the filename rule do not change.

## Messages

| Outcome | Level | Text template | Source | Change |
| - | - | - | - | - |
| Info line before the writer call | info | `Writing %d %s rows to %s` | `_persist`, before the writer call (research row 1) | Added |
| Failure log | error | `%s failed to write %d rows to %s` | `_persist`, failure branch | Added |
| Failure notice | info | `! Write failed for %s. Do not treat %s as a complete export.` | `_persist`, failure branch | Added |
| Debug line after a successful write | debug | `%s persisted %d rows to %s` | `_persist`, after the writer call (research row 2) | Unchanged |
| Success notice | info | `! %d %s records exported to %s` | `_persist`, after the debug line (research row 2) | Unchanged text |
| No-data notice | info | `! No %s data found` | `_persist`, first branch after `if not rawdata:` (research row 3) | Unchanged |
| Raised error log | error | `Error running %s for %s: %s` | `_run`, `except Exception` block (research row 5) | Unchanged |
| Raised error notice | info | `! Error running %s: %s` | `_run`, `except Exception` block (research row 5) | Unchanged |

## Rules

- A failed write prints the failure notice and never prints the success notice.
- The failure notice never contains the text `records exported to`.
- The failure notice names the operation and the filename, and no other data.
- Every new string uses ASCII characters only.
- Every new log call uses `%s` formatting, not an f-string.
- No new line contains a token, a password, or a full response body.

## Examples

On a failed organization count for the organization `org-1`, the output contains these lines in order:

```text
Writing 3 countOrgDevices rows to countOrgDevices_org-1.csv
countOrgDevices failed to write 3 rows to countOrgDevices_org-1.csv
! Write failed for countOrgDevices. Do not treat countOrgDevices_org-1.csv as a complete export.
```

On a successful write of the same rows, the output contains the success notice instead:

```text
! 3 countOrgDevices records exported to countOrgDevices_org-1.csv
```

The info line and the error line use the logger. The lines that start with `!` are operator notices.
