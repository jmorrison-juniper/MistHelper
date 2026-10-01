# Menu Contract: Alert Digest Acknowledge

## Menu 280: Alert digest

| Contract item | Value |
| - | - |
| Menu number | `280` |
| Category | `safe` |
| Handler | `src.reports.alert_digest.operation.AlertDigestOperation.run_digest` |
| Prompts | None in `--test` mode. |
| Output | `data/AlertDigest.csv` and `data/AlertDigest.md`. |
| Mist calls | `listAlarmDefinitions`, then paged `searchOrgAlarms`. |
| Lookback | `ALERT_DIGEST_HOURS` when set, otherwise `24` hours. |

### Required behavior

1. Resolve the organization through `SourceDependencyResolver.ConfigUtils`.
2. Read alarm definitions from `listAlarmDefinitions`.
3. Read alarm rows from `searchOrgAlarms` with `duration=<hours>h`.
4. Group rows by definition category, alarm type, and site.
5. Write one CSV row per group.
6. Write one Markdown section per category that has rows.
7. Write empty-state files when no alarms exist.

## Menu 281: Acknowledge alarms

| Contract item | Value |
| - | - |
| Menu number | `281` |
| Category | `destructive` |
| Handler | `src.reports.alert_digest.operation.AlertDigestOperation.run_acknowledge` |
| Confirmation | `ACK <count>` |
| Dry run | Supported. It sends no request. |
| Output | `data/AlertAcknowledgeLog.csv`. |
| Mist calls | `listAlarmDefinitions`, paged `searchOrgAlarms`, and confirmed `ackOrgMultipleAlarms`. |

### Required behavior

1. Resolve the organization through `SourceDependencyResolver.ConfigUtils`.
2. Read the same lookback window as menu 280.
3. Filter to alarms with `acked` false.
4. Log and display the exact candidate count.
5. If `--dry-run` is active, print each alarm ID and return without a write to Mist.
6. Prompt for `ACK <count>` before a live request.
7. If confirmation differs, log cancellation and send no request.
8. If confirmation matches, send one bulk request with all alarm IDs.
9. Write one acknowledgement result row per alarm ID.

## Test contract

- Tests must use fixtures and fake clients. They must not use the network.
- Tests must prove all required acceptance criteria from `spec.md`.
- Tests must prove that the wrong confirmation and `--dry-run` send zero destructive requests.
