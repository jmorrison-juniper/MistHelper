# Security and Safety Checklist: Organization Config Export Refusal

**Purpose**: Confirm that the change keeps the secret, log, and destructive-operation rules.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Secrets and private data

- [x] No token, password, or API key is read, logged, or written. The change reads the session only as the first argument of each SDK call.
- [x] Response bodies are not logged. The only logged response fact is the integer HTTP status, or the word `unavailable`.
- [x] Exception text is not logged. The log names the exception class only (`RuntimeError`, for example). The contract in `contracts/menu-messages.md` states the rule.
- [x] The bundle contains configuration data only. The change adds no credential field to the metadata.
- [x] Tests use synthetic markers, not production credentials. Tests use `tmp_path` and `monkeypatch.chdir` for output.

## Destructive operation

- [x] Menu 187 keeps the typed IMPORT confirmation. The phrase and the prompt do not change.
- [x] Menu 187 keeps the dry-run default (`[Y/n]`).
- [x] The new gates run before the first create call, for dry-run and live modes.
- [x] A rejected bundle stops before the preview and before any prompt.
- [x] The change adds no new destructive operation and no new menu.

## Fail-closed behavior

- [x] An unknown or missing status is unavailable, not success.
- [x] A 2xx response with an unknown payload is invalid, not success.
- [x] An exception produces a not verified outcome, not an empty list.
- [x] A failed follow-up page discards the objects of its type.
- [x] A legacy bundle is refused. The operator runs menu 58 again.

## Transport and dependencies

- [x] Every REST call uses a mistapi function. The change adds no direct HTTP call and no owned WebSocket transport.
- [x] No dependency changes. `pyproject.toml` and `requirements.txt` stay unchanged.
- [x] No dynamic SDK call site is added. The guard baselines in `tests/integration/test_mistapi_sdk_compatibility.py` lines 16 and 17 stay the limit.

## Static analysis

- [x] No `# nosec`, `# noqa`, or `# type: ignore` suppression is added to hide a finding.
- [x] Bandit runs on `src/mist/resources/org` (task T-LOCAL-GATES).
- [x] No broad `except` clause hides an error without a log line. Each clause logs the category.

## Notes

- The change does not alter the SDK debug output settings or the file permissions. The constitution rules for `data/` remain in force.
- Remaining risk: the live response shape of a refusal is not confirmed. Analysis item U-3 records that gap.
