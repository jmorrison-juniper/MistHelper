# Wave 1 High-Risk Function Map

## Selection Criteria

A function is considered high-risk for Wave 1 if it:
- Handles user input or destructive confirmations, or
- Controls routing/selection logic with broad operational impact.

## Initial Candidate List

1. `main()`
2. `SSHRunnerManager._collect_missing_data()`
3. `SSHRunnerManager._confirm_execution()`
4. `WAN2MigrationManager._get_site_selection()`
5. `WAN2MigrationManager._confirm_site_variable_operation()`
6. `TroubleshootUtils.launch_interactive()`

## Wave 1 Logging Envelope Target Set (finalized 2026-05-15)

All 5 non-main candidates confirmed. `main()` is excluded because it is the
top-level entry point and already covered by the entry routing guardrails.

| # | Function | Module | Envelope Gap Before US3 |
|---|----------|--------|--------------------------|
| 1 | `SSHRunnerManager._collect_missing_data()` | `MistHelper.py` | No entry/exit log |
| 2 | `SSHRunnerManager._confirm_execution()` | `MistHelper.py` | No entry/exit log |
| 3 | `WAN2MigrationManager._get_site_selection()` | `MistHelper.py` | No entry/exit log |
| 4 | `WAN2MigrationManager._confirm_site_variable_operation()` | `MistHelper.py` | No entry/exit log |
| 5 | `TroubleshootUtils.launch_interactive()` | `MistHelper.py` | f-string logging, no exit log |

## Redaction Target

`SSHRunnerManager._collect_missing_data()` handles passwords.
`src/utils/logger_utils.py` provides `redact_secret()` to prevent credential leakage
in log output.

## Post-US3 Evidence

See `tests/guardrails/test_wave1_logging_envelopes.py` for machine-verifiable
envelope presence and secret-exposure negation tests.
See `baseline-compliance-metrics.md` SC-004 row for linked evidence.
