# Contract: Operator Failure Message for the WLAN RADIUS Timer Write

## Identity

- **Menu**: 148, "Manage WLAN RADIUS Authentication Timers" (research RC-13, RC-12).
- **Producer**: `WLANRadiusTimerManager._apply_changes` in `src/foundation/support/refactors/wlanradius_timer_manager.py` (research RC-11).
- **Consumer**: The network operations center operator who reads the console.

## Output

- **Stream**: Standard output (stdout).
- **Trigger**: Any `Exception` that the write path raises inside `_apply_changes`. The code catches `Exception` at line 732 (research RC-11).
- **Line format**: One blank line, then the failure line. The failure line starts with `[!] Error applying changes: ` and ends with the exception text.
- **Source line**: `print(f"\n[!] Error applying changes: {error}")` at line 733 (research RC-11).
- **Encoding**: ASCII only. The line contains no non-ASCII character.

## Example

For an `OSError("no route")` raised by the site WLAN write, the console shows:

```text
[!] Error applying changes: no route
```

The blank line before the failure line comes from the leading `\n` in the print format.

## Test Assertion

The target test checks the substring below on captured stdout.

```text
Error applying changes: no route
```

The check reads the output through the `capsys` fixture (decision D-2).

## Stability Rules

- A change to the prefix `Error applying changes: ` changes this contract. The target test must change in the same commit.
- A change to the stream from stdout to stderr changes this contract. The target test then fails, which is intended.
- The logger call that follows the print (`logging.exception` at line 734, research RC-11) is not part of this contract. The target test reads only the stdout part of the captured output.

## Out of Scope

- Messages for other inheritance levels. Those paths use other methods and other tests.
- The unknown-level message in the same method. It has its own message path.
