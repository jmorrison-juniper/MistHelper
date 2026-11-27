# Security Requirements Checklist: Menu 97 SQLite Write Status

**Purpose**: Confirm that the change keeps the security rules for logs, input, SQL, and tests.

**Created**: 2026-11-26

**Feature**: `spec.md` and `plan.md` in this record

## Secrets and Logging

- [x] The new log lines name the table, row counts, and the discard statement only. No token, password, or credential reaches them.
- [x] The continuation token stays out of the new log lines. The existing resume log line keeps its current content.
- [x] The new log lines use ASCII only.
- [x] No new `print` call is added.

## Input Handling

- [x] The change adds no external input. The rows come from the existing response normalization in `device_events_52w_exporter.py`.
- [x] The new flag is a Boolean with a default of False. It has no free-text input.
- [x] No path is built by joining strings. The writer keeps its current path handling.

## SQL and Data Safety

- [x] The writer keeps parameterized inserts. The change adds no SQL text built from input.
- [x] The rejection path rolls back uncommitted rows only. Committed rows of earlier batches stay in the table.
- [x] The change adds no destructive file operation. The checkpoint removal stays in its current place after completion.

## Suppressions and Scanners

- [x] No `# nosec`, `# noqa`, or `# type: ignore` comment is added.
- [x] Bandit runs on `src` as part of the local gates. The existing `nosec` comment for the writer's SQL string stays unchanged.
- [x] `pip-audit` is not applicable, because `requirements.txt` does not change.

## Tests

- [x] Each test uses `tmp_path` or `monkeypatch`. No test writes to the repository `data/` folder.
- [x] The trigger in TC-10 exists only in a temporary database.
- [x] Each test sets `MISTHELPER_STANDALONE` to true when the polyglot mirror could run. The mirror opens no network connection.
- [x] No test uses a production credential. The Mist API is mocked.
