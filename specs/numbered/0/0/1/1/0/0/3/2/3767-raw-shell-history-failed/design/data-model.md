# Data Model: Raw shell history test failure (issue 3767)

This record changes no stored entity, key, or schema. The model below describes the runtime values that the failing path uses. It supports the signature table for the controlled run.

## Entities and Natural Keys

| Entity | Natural key | Source (accepted main `d4d1110`) |
| - | - | - |
| Failing test | Pytest node ID `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py::test_shell_history_preserves_raw_control_and_split_utf8_bytes` | Test file, lines 454 and 464 (R-01, R-03) |
| Terminal connection close | Tuple of `code`, `dropped`, and `status` in the log record `terminal_connection_closed` | `reading.py` line 46 (R-12) |
| Session state | Enumeration value `finished` or `failed` | `state.py` line 28 for `failed` (R-22) |
| Plain outcome reason | Constant name in `OutcomeReasons` | `outcomes.py` line 55 for the DROPPED result (R-08) |

## Outcome Mapping

`TerminalOutcomes.finish` checks each condition in order. The first true condition sets the state and the reason. The accepted-main order is shown below.

| Order | Condition (accepted main `outcomes.py` line) | Result state | Reason constant |
| - | - | - | - |
| 1 | An operator stop request is set (line 45, R-71) | `stopped` | `STOPPED` |
| 2 | A mode override exists (line 47, R-72) | Mode-defined | Mode-defined |
| 3 | No output was seen (line 48, R-09) | `failed` | `NO_ANSWER` |
| 4 | The close was local, so `dropped` is false (line 50, R-73) | `failed` | `WRITE_FAILED` |
| 5 | A close code exists (line 52, R-74) | `finished` | Closed reason of the mode |
| 6 | Otherwise, the connection dropped with no code (line 55, R-08) | `failed` | `DROPPED` |

The failing test expects `finished`, which row 5 produces. The observed `failed` state matches row 3 (no output), row 4 (local close), or row 6 (dropped with no code after output). The controlled-run signatures decide which row applies.

## Close Origins

| Origin | Code | Dropped | Source |
| - | - | - | - |
| Dead-peer close after two quiet intervals | `None` | `True` | `keepalive.py` line 36 on accepted main (R-69) |
| Socket read error or end of stream | `None` | `True` | `frame_reader.py` line 56 on accepted main (R-16) |
| Close frame from the device with status code 1000 | `1000` | `True` | `frame_reader.py` line 68 on accepted main (R-18) |
| Close frame with an empty payload | `1005` | `True` | `contracts.py` line 42 on accepted main (R-20) |
| Local close before a read | `None` | `False` | `shell_client.py` line 107 on current main (R-34) |

## Controlled-Run Signature Table

The controlled run uses the DEBUG log events. Each signature names the events that the record must show.

| Signature | Log evidence before `terminal_connection_closed` | Logged fields | Hypothesis |
| - | - | - | - |
| S1 Dead-peer close | `socket_close_started` (`socket_runtime.py` line 84, R-19), with no `frame_read_completed` whose status is `closed` | `"code":null,"dropped":true,"status":"output"` | H1 confirmed by this run |
| S2 Socket read error | `frame_read_completed` with `"status":"closed"` (`frame_reader.py` line 55, R-17) | `"code":null,"dropped":true,"status":"output"` | H1 rejected for this run. A transport error caused the close. Stop and open a new record. |
| S3 Normal close | None specific | `"code":1000,"dropped":true,"status":"output"` | Expected path. The test passes in this run. |
| S4 Silent close | None specific | `"status":"silent"` | H5. The output frames arrive first, so this branch needs a broken device. |
| S5 Local close | None specific | `"dropped":false` | Other branch. Stop and open a new record. |
| S6 Unexpected exception | `terminal_unexpected_failure` at ERROR level, with `detail` set to the exception type | Not applicable | Other branch. `reading.py` line 51 on accepted main (R-68). Stop and open a new record. |

Each signature needs the matching log line. A missing line means the run does not show that signature.
