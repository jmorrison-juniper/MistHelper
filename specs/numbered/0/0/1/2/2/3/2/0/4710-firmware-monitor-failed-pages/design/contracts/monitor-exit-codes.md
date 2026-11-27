# Contract: Monitor Exit Codes and Console Output

## Exit Codes (Unchanged)

| Constant | Value | Meaning |
| - | - | - |
| `MONITOR_EXIT_COMPLETE` | 0 | Every upgrade finished, after a complete walk. |
| `MONITOR_EXIT_FAILED` | 1 | Five failed checks in a row. |
| `MONITOR_EXIT_CANCELLED` | 2 | The operator pressed Ctrl+C. |

The constants are defined at `src/operations/execution/firmware/firmware_manager.py` lines 56 to 58. Line 56 holds the completion code (research RC-36).

## Console Outcomes

| Event | Console text | Source (`firmware_manager.py`) |
| - | - | - |
| Zero active upgrades after a complete walk | `All upgrades completed!` | `_handle_monitoring_result`, line 511 |
| A failed check | `Error fetching upgrade status.` | `_handle_monitoring_result`, from line 504 |
| A failed check with retries left | `Retry <n> of 5 in <seconds> seconds`, followed by three periods | `_record_monitoring_attempt`, from line 440 |
| The failure limit reached | `MONITORING STOPPED after <n> failed status checks in a row.` | `_present_monitoring_failure`, from line 468 |
| Ctrl+C | `Monitoring mode cancelled by user.` | `_continuous_monitoring_mode`, from line 377 |

The text of the new failure path does not change. The status check returns no count, and the existing messages appear.

## Waits Between Checks

| Failed check number | Wait after the check (seconds) |
| - | - |
| 1 | 7 |
| 2 | 14 |
| 3 | 28 |
| 4 | 56 |
| 5 | None. The loop stops. |

The total wait before the loop stops is 105 seconds. The values come from `MonitoringRetryPolicy.next_delay_seconds` (line 177) and the constants at lines 52 to 55.

## Menu Caller

Menu 137 discards the exit code. `_dispatch_status_scope` (lines 365 to 369) logs the code at `debug` level and returns no value. The operator sees the console text only. A scripted caller of `_continuous_monitoring_mode` receives the exit code.
