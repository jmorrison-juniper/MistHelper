# Contract: Operator Messages and Rendered Output

This contract lists each message and each output rule that an operator or a reviewer sees. Text in quotation marks is exact. A text with a `%s` value shows the value position.

## Warning for a failed MSP organization list

- Logger: the module logger of `src/mist/intelligence/reports/subscription_expiry/client.py`.
- Level: WARNING. The change emits exactly one line for each failed call.
- HTTP 403 text: "MSP organization list is not permitted for this account (HTTP 403). The report continues with direct organizations."
- Other status text: "MSP organization list returned HTTP %s. The report continues with direct organizations." The `%s` value is the HTTP status.
- Transport failure: no warning line. The client line from `_request_with_retry` is the only line. Its text is "Mist request %s failed for %s with %s" and it names the exception type, not the message.

## Info and debug lines around the MSP organization list call

- Info line, before the call: "Requesting the MSP organization list for %s." The `%s` value is the MSP identifier.
- Debug line, after the call: "MSP organization list returned status %s." The `%s` value is the HTTP status, or the sentinel 0.

## SDK error lines during the MSP call

- Records at level ERROR from the logger `mistapi` do not reach the handlers while the call runs.
- Records from other loggers, and records below ERROR, reach the handlers as before.
- The filter ends when the call returns or raises.

## Failure row in the report output

These fields exist on main and do not change in this change:

- `org_id`: the missing-value marker.
- `org_name`: "MSP %s" with the MSP identifier.
- `source`: "msp".
- `request_status`: "failed".
- `error`: "HTTP %s" with the HTTP status. A transport failure shows "HTTP 0" (observation O-6 in `analysis.md`).

## Traceback output

- Frame locals: not printed. The formatter sets `show_locals` to false.
- Stream that is a terminal: color codes are allowed.
- Stream that is not a terminal: no ESC character (U+001B) appears in the output.
- `NO_COLOR` set to any non-empty value: no color code appears in the output.

## Operator guide sentence

After T012, line 502 of `documentation/operator-guide.md` reads: "If the MSP list is denied, the menu says so once and continues with direct organizations." The sentence names the same outcome as the 403 warning text.

## Changelog bullets

The fragment `changelog.d/issue-4943-request-admission-org-scope.md` has one `###` heading and two bullets:

- **Fixed**: Site requests count against their organization under shared admission. Issue #4921. Issue #4943.
- **Security**: Traceback output hides frame locals and writes no ANSI codes to a non-terminal stream. Issue #4943.
