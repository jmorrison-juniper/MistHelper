# Contract: Audit Report

## Command

The audit runs as one pytest module. It needs no network access and no credential.

`python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py`

## Output Lines

Each run writes these ASCII lines to the test log.

| Line | Meaning | Required value |
| --- | --- | --- |
| `audit: rows examined=<n>` | Comparison rows read from the register | 40 |
| `audit: tasks examined=<n>` | Parity task statuses read from the task table | 33 |
| `audit: gates examined=<n>` | Gate rows read from the gate table | 6 |
| `audit: links examined=<n>` | Local Markdown links checked | At least 1 |
| `audit: result=<pass or fail>` | Overall result | `pass` only when every check passes |

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | Every check passes |
| 1 | At least one check fails. The log names each failed check |
| 2 | An input file is missing or unreadable. The audit fails closed |

## Rules

1. Zero rows, tasks, gates, or links make the audit fail.
2. An unreadable input makes the audit fail with exit code 2. The audit never skips a file silently.
3. Each read writes an info line before the read. Each read writes a debug line after the read with its count.
4. Logging uses message templates with values. The log never prints a secret or a secret-like value.
5. Secret-like matches print the line number and the pattern name only.
6. Each refused completion claim prints the first blocking row, task, or gate.

## Example Output

```text
audit: rows examined=40
audit: tasks examined=33
audit: gates examined=6
audit: links examined=12
audit: result=fail
fail: completion claim refused, row C01 is open
```

The example shows the baseline state. The fail line names the first blocking row.
