# Data Model: Firmware Monitor Treats Failed Stats Pages as Failed Checks

## Entities

| Entity | Source | Natural key | Fields used by the change |
| - | - | - | - |
| Stats page | One Mist stats response per request | None. Position comes from the page order and the next link. | `status_code` (integer or None), `data` (list expected), `headers` (`X-Page-Total`, `X-Page-Limit`, `X-Page-Page`), and `next` (link or None). |
| Device row | One element of a stats page body | The `mac` field. The `stats_device` schema holds it at `documentation/mist-api-openapi31yaml.yaml` line 107198. | `name`, `type`, `model`, and the `fwupdate` record with `status`, `progress`, and `timestamp`. |
| Active upgrade | A device row that `_is_active_fw_update` (`firmware_manager.py` line 649) marks as active | The `mac` of the device row | `name`, `type`, `model`, `progress`, and `status`, as built in `_get_active_upgrades_from_stats` (line 662). |
| Status check result | The return value of `_execute_monitoring_check` (line 702) | None. The result is a count. | An integer count of active upgrades, or None when the check fails. |
| Retry streak | `consecutive_failures` in `MonitoringRetryPolicy` (class at line 144) | None. The streak is one counter. | An integer count of consecutive failed checks. |

The monitor counts device rows. It does not remove a duplicate `mac` value. The existing code does the same.

## Validation Rules for a Stats Page

- The status must equal the integer 200. A missing or non-integer status fails the page.
- The body must be a list. Any other type fails the page.
- The last page must announce a total with `X-Page-Total` when the header is present. The total must be an integer. The collected row count must be at least that total.
- A next link must not repeat within one walk.

## State Transitions for Continuous Monitoring

| From | Event | To | Effect |
| - | - | - | - |
| Watching (streak 0) | A status check returns a count above zero | Watching (streak 0) | Prints the count and waits 7 seconds. |
| Watching (streak 0) | A status check completes a walk with zero active upgrades | Completed | Prints the completion banner. The exit code is 0. |
| Watching (streak 0) | A status check fails | Retrying (streak 1) | Prints the retry notice and waits 7 seconds. |
| Retrying (streak n, where n is 1 to 4) | A status check fails | Retrying (streak n + 1) | Waits `min(7 * 2 ** (n - 1), 60)` seconds. |
| Retrying (streak n) | A status check returns a count | Watching (streak 0) | Resets the streak. |
| Retrying (streak n) | A status check completes with zero active upgrades | Completed | The exit code is 0. |
| Retrying (streak 5) | A status check fails | Failed | Prints the stop block. The exit code is 1. No wait occurs. |
| Any state | The operator presses Ctrl+C | Cancelled | The exit code is 2. The firmware upgrade keeps running. |

Caution: the Cancelled state stops only the monitor. The firmware upgrade continues on the Mist cloud.
