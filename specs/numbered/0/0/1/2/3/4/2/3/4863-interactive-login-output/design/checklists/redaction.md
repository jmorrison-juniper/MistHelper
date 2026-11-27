# Redaction Checklist: Interactive Login Output

**Purpose**: Confirm that a password and a 2FA code never appear in direct output or in any log record

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Code Paths

- [x] The 2FA code is passed only to the SDK replay call (`login_orchestrator.py`, the `two_factor=code` argument, remote blob fd475be9467068e6c34a819697c3c46235801047).
- [x] The 2FA prompt logs a fixed text without the code (`credential_prompter.py` debug record "2FA prompt accepted", remote blob e1b5197a78e7ec5993faa7dd66eed9c8a553336c).
- [x] The 2FA success line has no argument, so no value is printed (`design/contracts/operator-output.md`, row 20).
- [x] The debug record of the 2FA result logs only the boolean `authenticated` (`login_orchestrator.py` line 204).
- [x] The password reaches the SDK constructor and the SDK replay call only. No log call receives it.
- [x] The existing debug record of the password length stays unchanged. It logs a count, not a value.

## Test Evidence

- [x] `test_sentinel_password_and_2fa_code_stay_out_of_output` searches captured output and log records for both sentinel values (T006 and T015).
- [x] The sentinel values are fixed fake strings, and they appear in no fixture file name or test identifier.
- [ ] Explained: the sentinel test runs after the change. T015 records the result.

## Explained Exceptions

- The SDK logger records of the module `mistapi` follow `CONSOLE_LOG_LEVEL`. At threshold 20 they may show the account email, which the existing info record at line 84 already shows. An email is not a secret under the constitution. This change does not change that behavior.
- The SDK password redaction is not a dependency of this change. The change does not print or log any SDK value.
