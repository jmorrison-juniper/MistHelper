# Contract: log record for a continued handler

A handler that the code continues past writes one log record at error level (FR-013). The record names the operation and the exception type. It never carries a secret.

## Record format

| Part | Value |
| - | - |
| Level | `ERROR`. Log level policy stays with issues #1766 and #1793. |
| Logger | The module logger of the changed file. |
| Message template | `"Operation %s failed with %s: %s"` |
| Argument 1 | Operation name. A fixed string that names the operation in the changed code. |
| Argument 2 | Exception type name. Use `type(error).__name__`. |
| Argument 3 | Redacted message. Use the text after the handler chain applies `SensitiveFilter`. |
| Traceback | Required for each `keep` site (FR-012). Pass `exc_info=True`. |

Use `%s` formatting in each call. Do not use f-strings in log calls (AGENTS.md logging rule).

## Redaction

- The record passes through the handler chain that installs `SensitiveFilter`. That filter redacts `exc_text` (RC-060, RC-061).
- A changed log call never includes a raw credential, a raw address, raw user input, or a raw response body (FR-016).
- Each slice that changes a log call adds one redaction test. The test uses a synthetic credential and the real handler chain (FR-016).
- A filter or a formatter never logs its own actions. A handler inside a logging filter keeps its broad catch with a recursion note (spec edge cases).

## Verification

- A propagation test proves that a programming error reaches the caller (FR-021).
- A log test proves that the record names the operation and the exception type (FR-013).
- A redaction test proves that the synthetic credential does not appear in the record (FR-016).
