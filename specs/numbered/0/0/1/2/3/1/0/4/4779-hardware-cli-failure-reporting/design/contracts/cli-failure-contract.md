# Contract: Hardware CLI Failure Boundary

**Applies to**: `HardwareCollectionCli.run` and `HardwareCliWorkflow.Completion.cancel` in `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py` on the publication branch.

## 1. Exception Classes

| Exception class | Class of failure | Behavior in `run` | Behavior in `cancel` |
| - | - | - | - |
| `EOFError`, `KeyboardInterrupt` | Interruption | Cancel an admitted parent. Return `cancelled` before admission. | A second interruption returns `incomplete`. |
| `NotImplementedError`, `RecursionError` | Programming error | Propagate. | Propagate. |
| Any other exception class | Programming error | Propagate. | Propagate. |
| `StreamRequestError` | Operational failure with a stable code | Print the code. Return `incomplete`. | Return `incomplete`. Print the cancellation message. |
| `OSError`, `RuntimeError` | Operational failure with a class name | Print the class name. Return `incomplete`. | Return `incomplete`. Print the cancellation message. |

## 2. Admission States

| State | Set when | Caution on an incomplete result |
| - | - | - |
| `not_started` | The initial value | None |
| `uncertain` | Before the start request is sent | `Caution: the collection may have started. Check the portal before you run again.` |
| `admitted` | After a verified start reply | `Caution: the admitted collection may still be active. Check the portal before you run again.` |

Print the caution after each incomplete result whose state is `uncertain` or `admitted`. Print no caution for `not_started`.

## 3. Operator Text

Print these lines exactly. The cause value is a class name or a code.

- `Hardware collection failed (OSError).` The example shows the form. The cause value replaces `OSError` at run time.
- `Hardware collection has no verified completion.`
- `Hardware cancellation has no verified completion.`
- The two caution texts from section 2.

## 4. Stable Causes

- Class names: `OSError` and `RuntimeError`.
- Codes: `not_ready`, `bad_request`, `confirmation`, `picker_incomplete`, `output_failed`, and `admission_unverified`.

## 5. Log Lines

| Level | Text | When |
| - | - | - |
| info | `Hardware CLI requests the target preview.` | Before the preview request |
| debug | `Hardware CLI received a preview with %d targets.` | After the preview request. The value is the target count. |
| info | `Hardware CLI sends the start request once.` | Before the start request |
| debug | `Hardware CLI start reply verified with admission state %s.` | After a verified start reply. The value is `admitted`. |
| error | `Hardware CLI ends without verified completion. Cause: %s. Admission state: %s.` | On each operational failure |

Log only the stable cause and the admission state. Do not log raw exception text, a session identifier, or an operator answer.

## 6. Return Statuses

- `cancelled`: an interruption before admission, or an interruption during the start request.
- `incomplete`: an operational failure or an unverified completion.
- A verified completion returns the batch status: `completed`, `partial`, `failed`, or `stopped`.

## 7. Test Mapping

- `never_retries[OSError]` and `never_retries[RuntimeError]`: sections 1, 3, and 5.
- `never_retries[TypeError]`, `never_retries[NotImplementedError]`, and `never_retries[RecursionError]`: section 1, propagation.
- `never_retries[KeyboardInterrupt]`: section 2 (uncertain caution) and section 6 (`cancelled`).
- `refuses[OSError]`: section 2 (no caution before admission).
- `reply_without_session`: section 4 (`admission_unverified`) and section 2 (uncertain caution).
- `poll_failure`: section 2 (admitted caution) and no durable directory.
- `cancel_programming_error`: section 1 (propagation in `cancel`).
