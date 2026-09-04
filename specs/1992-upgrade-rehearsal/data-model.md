# Data Model: The upgrade rehearsal harness

**Feature**: `specs/1992-upgrade-rehearsal/` | **Date**: 2026-09-04

This document names each record that the harness adds. It also names the shipped
records that the harness reads. The harness holds no settle rule, no phase
order, and no stop rule.

## 1. RehearsalClock

**Module**: `tests/support/rehearsal/clock.py`

**Purpose**: One time source for the whole run.

| Field | Type | Meaning |
| - | - | - |
| `_reading` | `float` | The current time in epoch seconds. |
| `_guard` | `threading.Lock` | Protects the reading across two threads. |
| `_sleeps` | `list[float]` | Each interval that the poll loop asked for. |

**Methods**:

- `now() -> float` returns the reading. The gate reads it through
  `SettleGate.now`.
- `sleep(seconds: float) -> None` adds the interval to the reading and records
  it. It waits no real time.
- `now_text() -> str` renders the reading as an ISO stamp. It satisfies the
  `Clock` protocol at `driver.py:244`.
- `advance(seconds: float) -> None` moves the reading with no sleep record. A
  test uses it to place the start of a run.

**Rules**:

1. The reading starts at a fixed epoch value. A fixed start keeps every test
   result the same on every worker.
2. The reading never moves backwards. A backwards move would break the deadline
   test of the phase gate.
3. Only the driver thread writes the reading. The guard protects the read of the
   test thread.

## 2. DeviceScript

**Module**: `tests/support/rehearsal/script.py`

**Purpose**: The plan of one device through the rehearsal.

| Field | Type | Meaning |
| - | - | - |
| `mac` | `str` | The address in lower case with no separator. |
| `device_type` | `str` | One of `gateway`, `switch`, or `ap`. |
| `version_before` | `str` | The firmware version before the upgrade. |
| `version_after` | `str` | The firmware version after the upgrade. |
| `uptime_before` | `int` | The uptime in seconds before the reboot. |
| `reconnect_at` | `float` | The offset of the reconnect event. |
| `version_at` | `float` | The offset of the version change. |

**Rules**:

1. `reconnect_at` never exceeds `version_at`. The gate opens on the reconnect
   event, so a version change before it would prove nothing.
2. `version_at` stays far below the phase deadline of 1800 seconds. A device
   that passes the deadline cannot settle.
3. A script with a `version_after` equal to `version_before` never settles. One
   edge case test uses that script.

## 3. FleetScript

**Module**: `tests/support/rehearsal/script.py`

**Purpose**: The scripts of the whole run.

| Field | Type | Meaning |
| - | - | - |
| `scripts` | `tuple[DeviceScript, ...]` | One script for each device. |
| `started_at` | `float` | The clock reading at the start of the run. |

**Methods**:

- `script_for(mac: str) -> DeviceScript | None` answers the lookup by address.
- `scripts_of_type(device_type: str) -> tuple[DeviceScript, ...]` answers the
  device family of one event search.

**Rules**:

1. Each address appears one time. A repeated address would make the lookup
   ambiguous.
2. The fleet of the cascade test holds 2 gateways, 2 switches, and 2 access
   points. The fleet of the stop test adds 1 session smart router.

## 4. StandInCloud

**Module**: `tests/support/rehearsal/cloud.py`

**Purpose**: The answers of the cloud and the counters of the calls.

| Field | Type | Meaning |
| - | - | - |
| `fleet` | `FleetScript` | The scripts of the run. |
| `clock` | `RehearsalClock` | The one time source. |
| `_calls` | `dict[str, int]` | The count of each call name. |
| `_pause` | `Callable[[], None] \| None` | The hook of the run status test. |

**Methods**: One method answers each of the five attachment points. The contract
`contracts/rehearsal-cloud.md` records each signature.

**Rules**:

1. Every answer carries `status_code` set to 200, unless a test asks for a
   fault. A fault answer proves the partial round of the edge cases.
2. The statistics answer holds `results`, `total`, and `next`. FR-009 asks for
   that paged shape.
3. An event search with no `device_type` answers access points only. FR-010 asks
   for that behavior, and the real cloud shares it.
4. The three firmware write endpoints raise `RehearsalFirmwareError`. FR-005 and
   SC-005 both need that refusal.

## 5. RehearsalHarness and RehearsalDeps

**Module**: `tests/support/rehearsal/harness.py`

`RehearsalDeps` is a frozen record of 4 members.

| Field | Type | Meaning |
| - | - | - |
| `clock` | `RehearsalClock` | The one time source. |
| `fleet` | `FleetScript` | The scripts of the run. |
| `store` | `RunRecordStore` | The in-memory run record store. |
| `capture` | `CaptureStarter` | The post-check capture double. |

`RehearsalHarness` publishes 4 methods.

- `attach(monkeypatch) -> StandInCloud` replaces the attachment points.
- `start() -> threading.Thread` builds the run record and starts the driver.
- `join(timeout: float = 5.0) -> None` waits for the driver thread.
- `record() -> dict` returns the run record that the store holds.

**Rules**:

1. Each run holds a unique run identifier. `RunDriver._THREADS` at
   `driver.py:1200` keys the live thread by that identifier.
2. `join` uses a real timeout of 5 seconds. A run that hangs then fails the test
   instead of hanging the whole suite.

## 6. The shipped records that the suite reads

The harness reads these records and writes none of their rules.

| Record | Module | What the suite reads |
| - | - | - |
| The run record | The store double | `current_state`, `phases`, and `targets` |
| `PhaseOutcome` | `driver.py:281` | `name`, `state`, `settled`, and `total` |
| `GateProgress` | `gate.py` | `reconnected`, `reboot_at`, and `settled_at` |
| `StopOutcome` | `signals.py` | The three lists and the message |
| `PhaseProgress` | `phase_gate.py:93` | The progress report of each poll round |

## 7. The state of one device through the rehearsal

A device moves through 4 states. The gate owns every transition.

1. **Waiting**. The device shows no reconnect event. The gate records nothing.
2. **Reconnected**. The clock passed `reconnect_at`. `GateProgress.reconnected`
   is true, and `reboot_at` is still empty.
3. **Rebooted**. The clock passed `version_at`. The statistics show a decreased
   uptime and a changed version. `GateProgress.reboot_at` holds the reading.
4. **Settled**. The clock passed `reboot_at` plus the wait of the device type.
   `GateProgress.settled_at` holds the reading.

The wait is 60 seconds for a gateway and for a switch. The wait is 120 seconds
for an access point. `gate.settle_wait_seconds` owns both numbers, and the
harness reads them from that function.
