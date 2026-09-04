# Contract: The rehearsal clock

**Feature**: `specs/1992-upgrade-rehearsal/` | **Date**: 2026-09-04

This contract records the four time seats of the shipped code. It records the
shape that each seat needs. One `RehearsalClock` object fills all four seats.

FR-014 asks the harness to drive the clock. FR-015 asks for one clock across the
phase deadline and the device waits. FR-016 forbids a real wait of 60 seconds.
This contract holds the design that meets all three.

## 1. The four seats

| Seat | Shape | Shipped default | Line |
| - | - | - | - |
| `SettleGate(clock=...)` | `Callable[[], float]` | `time.time` | `gate.py:928` |
| `PhaseGateDeps.sleep` | `Callable[[float], None]` | `time.sleep` | `phase_gate.py:340` |
| `CloudReconnectReader(clock=...)` | `Callable[[], float]` | No default | `phase_gate.py:264` |
| `RunDriverDeps.clock` | The `Clock` protocol | `SystemClock` | `driver.py:749` |

The `Clock` protocol at `driver.py:244` declares one method. The method is
`now_text`, and it returns an ISO stamp.

## 2. The methods of the clock

```python
class RehearsalClock:
    def now(self) -> float: ...          # The reading in epoch seconds.
    def sleep(self, seconds: float) -> None: ...   # Moves the reading.
    def now_text(self) -> str: ...       # The same reading as an ISO stamp.
    def advance(self, seconds: float) -> None: ...  # Moves with no record.
```

## 3. The rules of the clock

1. `now` returns epoch seconds as a float. The gate compares that value against
   the `last_seen` field of a statistics record. That field also holds epoch
   seconds.
2. `sleep` adds the interval to the reading and returns at once. It waits no
   real time, and it records the interval.
3. `now_text` renders the same reading. A record stamp and a gate reading
   therefore never disagree.
4. The reading never moves backwards. A backwards move would break the deadline
   test of `PhaseSettleGate`.
5. Only the driver thread calls `sleep`. The test thread calls `advance` before
   the run starts, and it calls `now` while the run runs.

## 4. The cadence of one phase

The shipped constants set the cadence. The harness states none of them.

| Constant | Value | Module |
| - | - | - |
| `POLL_INTERVAL_SECONDS` | 20 | `gate.py` |
| `SETTLE_WAIT_SECONDS` | 60 | `gate.py` |
| `ACCESS_POINT_EXTRA_WAIT_SECONDS` | 60 | `gate.py` |
| `PHASE_DEADLINE_SECONDS` | 1800 | `phase_gate.py:64` |

One poll round therefore moves the clock 20 seconds. A device that proves the
reboot at reading `T` settles at the first round at or after `T` plus 60. An
access point settles at the first round at or after `T` plus 120.

## 5. How the suite proves the settle window

Acceptance scenarios 3 to 6 of User Story 1 name the 59 second point and the 60
second point. The suite proves both from the poll record of one composed run.

1. The stand-in records the clock reading of each statistics answer.
2. The progress reporter records the settled count of each poll round.
3. The test finds the round that proved the reboot, and it reads that clock
   value as `T`.
4. The test asserts that every round below `T` plus 60 reported the device as
   unsettled.
5. The test asserts that the first round at or above `T` plus 60 reported the
   device as settled.

The same five steps prove the access point at `T` plus 120. The test never
states 60 or 120 as a literal. It reads both from `gate.settle_wait_seconds`.

## 6. The real time budget

| Measure | Limit | Source |
| - | - | - |
| The whole rehearsal suite | Under 60 real seconds | SC-002 |
| One wait for a settle window | Under 1 real second | SC-003 |
| The join of one driver thread | 5 real seconds | The harness |

The join timeout is a guard and not a wait. A healthy run finishes in
milliseconds, because every sleep returns at once. A run that hangs fails the
test at the timeout, and it does not hang the suite.
