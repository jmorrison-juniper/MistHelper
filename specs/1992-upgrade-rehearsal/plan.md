# Implementation Plan: The upgrade rehearsal harness

**Branch**: `feat/1992-upgrade-rehearsal` | **Date**: 2026-09-04 | **Spec**:
[spec.md](./spec.md)

**Input**: Feature specification from
`specs/1992-upgrade-rehearsal/spec.md`

## Summary

This feature adds a rehearsal harness to the test suite. The harness starts the
shipped run driver against a stand-in cloud. The stand-in cloud answers the
device event search, the device statistics read, and the upgrade status read.
The harness drives one clock, so no test waits a real settle window.

The harness holds no settle rule, no phase order, and no stop rule. Every such
rule stays in the shipped code. The harness only supplies the answers of the
cloud and the readings of the clock.

The harness adds one package under `tests/support/rehearsal/` and three test
modules under `tests/unit/upgrade_portal/`. It changes no file under `src/`.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: pytest, `mistapi` 0.63.3, and the shipped package
`src/upgrade_portal/`.

**Storage**: None. The harness holds the run record in memory.

**Testing**: pytest. The tests live in `tests/unit/upgrade_portal/`.

**Target Platform**: Windows 11 for local work, and Linux for the continuous
integration worker.

**Project Type**: A test support package and a test suite for a web portal.

**Performance Goals**: The whole rehearsal suite finishes in under 60 seconds.
No test waits more than 1 real second for a settle window.

**Constraints**: The suite makes zero network calls. The suite makes zero
firmware write calls. The harness copies no rule of the shipped code.

**Scale/Scope**: Four phases. Two devices for each device phase. Six devices in
total, plus one session smart router for the stop test.

## Constitution Check

*GATE: This gate passed before Phase 0. It passed again after Phase 1.*

| Principle | How this plan meets it |
| - | - |
| I. Five-Item Rule | The new package holds 5 modules. Every planned function keeps 5 parameters, 5 blocks, and 25 lines. Each record groups its fields, as `RunDriverDeps` does. |
| II. Class-Based Architecture | Each module holds one named class. `RehearsalClock`, `StandInCloud`, `DeviceScript`, `RehearsalHarness`, and `DefectDrill` own the behavior. |
| III. Safety-First | The harness reads no operator input. The stand-in resolver refuses every firmware write endpoint and raises. |
| IV. Full Deployment Pipeline | The implementation phase runs the pipeline. This plan writes prose only. |
| V. Observability and Logging | Every module uses ASCII log text and `%s` formatting. |
| VI. Inline Comments | Every executable line of the new code carries a comment that states why. |
| VII. Action Logging | Every action carries an `info` line before it and a `debug` line after it. |

Two conditions need a record. The Complexity Tracking table below holds both.

## Project Structure

### Documentation (this feature)

```text
specs/1992-upgrade-rehearsal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── rehearsal-cloud.md
│   └── rehearsal-clock.md
└── tasks.md             # Phase 2 output, which /speckit.tasks writes
```

### Source Code (repository root)

```text
tests/support/rehearsal/
├── __init__.py          # The package marker and the public names
├── clock.py             # RehearsalClock: one time source for the whole run
├── script.py            # DeviceScript and FleetScript: the device lifecycle
├── cloud.py             # StandInCloud: the answers and the call counters
├── harness.py           # RehearsalHarness: the run record and the wiring
└── defects.py           # DefectDrill: the three defect classes

tests/unit/upgrade_portal/
├── test_rehearsal_cascade.py   # User Story 1
├── test_rehearsal_stop.py      # User Story 2
└── test_rehearsal_defects.py   # User Story 3
```

**Structure Decision**: The harness lives under `tests/support/`, beside
`lock_store_double.py` and `thread_scoped_sleep.py`. Those two modules are the
shared test support of this repository. The harness is support code and never
production code, so it must not reach `src/`.

## Design decision 1: where the stand-in cloud attaches

The stand-in cloud attaches at the boundary of the `mistapi` library, and at the
one endpoint resolver of the firmware module. FR-008 asks for that boundary. The
harness replaces five attributes with `monkeypatch`, and pytest restores each
one at the end of the test.

| Attachment point | The shipped caller |
| - | - |
| `mistapi.api.v1.orgs.stats.listOrgDevicesStats` | `gate.read_fleet_statistics` at `gate.py:845` |
| `mistapi.get_all` | The page walk of the same read at `gate.py:856` |
| `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents` | `events.read_device_events` at `events.py:430` |
| `mistapi.api.v1.const.device_events.listDeviceEventsDefinitions` | The event key catalogue of `events.py` |
| `src.firmware.upgrade_service._resolve_endpoint` | The status read and the cancel call of `stop.py` |

The fifth point is one function at `upgrade_service.py:547`. It is the single
door to every sanctioned cloud endpoint of the upgrade module. A stand-in there
covers the status read and the cancel call together, and it also blocks every
firmware write.

### Why a higher seam skips shipped code

`PhaseGateDeps` at `phase_gate.py:319` offers an `event_reader` seat and a
`statistics_reader` seat. A stand-in in either seat looks simpler. It is the
wrong choice, because it skips the reader code that this feature must prove.

A stand-in at `statistics_reader` skips `read_fleet_statistics`, the page guard
`guard_page_count`, `reading_from_record`, and the stale record screen. FR-002
and FR-009 then fail.

A stand-in at `event_reader` skips `drain_device_events`, `read_cursor`, the
window split, and the `device_type` parameter of the search. Defect class 1 of
User Story 3 lives in that parameter. A harness that skips it cannot catch it.

### How the harness obeys the seam shape rule

`src/upgrade_portal/app/seam_shapes.py` states the rule of issue #1991. A
stand-in must answer the call that the caller really makes. The harness obeys
that rule in three ways.

First, each stand-in function copies the signature of the real cloud function.
The signature of the stand-in accepts every call that the shipped reader makes.

Second, the contract `contracts/rehearsal-cloud.md` records each call. It names
the parameters that the shipped reader passes. It names the file and the line of
the caller.

Third, the cascade test asserts the shape at run time. It reads the recorded
call of each stand-in. It compares the keyword names against the contract. A
shipped reader that changes its call then fails the test.

The seam registry `SEAM_SHAPES` records the application seams of the routes. It
records no cloud library seam today. This feature adds no entry, because the
harness patches a library attribute and never an application key.

## Design decision 2: how the harness drives the clock

The shipped code reads time through four injected seats. The harness fills all
four seats with one `RehearsalClock` object. No test patches the `time` module.

| Seat | The shipped default | What the harness passes |
| - | - | - |
| `gate.SettleGate(clock=...)` at `gate.py:928` | `time.time` | `clock.now` |
| `PhaseGateDeps.sleep` at `phase_gate.py:340` | `time.sleep` | `clock.sleep` |
| `CloudReconnectReader(clock=...)` at `phase_gate.py:264` | No default | `clock.now` |
| `RunDriverDeps.clock` at `driver.py:749` | `SystemClock` | The same object |

`clock.sleep` adds the interval to a counter and returns at once. It waits no
real time. `clock.now` returns the counter as epoch seconds. `clock.now_text`
renders the same counter as an ISO stamp, which satisfies the `Clock` protocol
at `driver.py:244`.

One counter therefore serves the phase deadline, the device waits, the event
window, and the run record stamps. FR-015 asks for that single source. Two
counters would drift, and the drift would hide a settle defect.

The poll interval is 20 seconds and the settle wait is 60 seconds. Three sleep
calls therefore carry a device from the reboot to the settle. The suite spends
no real time inside a settle window, which meets FR-016 and SC-003.

The driver thread is the only writer of the counter. A lock protects the read,
because the test thread reads the counter while the driver thread runs.

## Design decision 3: how the stand-in cloud models a device lifecycle

`DeviceScript` holds the plan of one device. `FleetScript` holds the scripts of
the whole run, and it answers a lookup by address. The stand-in cloud reads the
clock and the script, and it builds every answer from the two.

A script names two moments. `reconnect_at` is the clock reading of the reconnect
event. `version_at` is the clock reading of the version change. Both are offsets
from the start of the run, so a test reads them without arithmetic.

The stand-in answers each of the three signals at the scripted moment.

1. The event search answers a reconnect event of the device when the clock
   passes `reconnect_at` and the window covers that moment.
2. The statistics read answers `version_before` until the clock passes
   `version_at`. After that moment it answers `version_after`.
3. The statistics read answers `uptime_before` plus the elapsed seconds until
   the clock passes `version_at`. After that moment it answers the seconds since
   `version_at`, which is a much smaller number. The gate then reads a decreased
   uptime.

The `last_seen` field always holds the current clock reading, so no answer looks
stale. One script sets a fixed `last_seen`, which proves the stale record rule
of the edge cases.

The gate adds its own wait above these signals. A switch settles 60 seconds
after the reboot proof. An access point settles 120 seconds after it. The
harness never states either number. `gate.settle_wait_seconds` owns both.

The stand-in also answers an upgrade status for each device. The status carries
`status`, `current_phase`, and `targets.reboot_in_progress`. The stop path reads
that shape at `stop.py:162`.

## Design decision 4: where the new files live and what each one holds

Every function below keeps 5 parameters, 5 logical blocks, and 25 lines. Each
class groups its fields in a frozen record, which is the pattern of
`RunDriverDeps` and `PhaseGateDeps`.

### The clock module

`tests/support/rehearsal/clock.py` holds `RehearsalClock`. The class holds the
counter, the lock, and the logger. It publishes `now`, `sleep`, `now_text`, and
`advance`. Each method holds one block.

### The script module

`tests/support/rehearsal/script.py` holds `DeviceScript` and `FleetScript`.
`DeviceScript` is a frozen record of 7 fields. `FleetScript` holds a tuple of
scripts, and it answers `script_for` and `scripts_of_type`. Two module builders
create the fleet of the cascade test and the fleet of the stop test.

### The cloud module

`tests/support/rehearsal/cloud.py` holds `StandInCloud`. The class holds the
fleet script, the clock, and the call counters. It publishes five answer
methods, one for each attachment point. Four private builders turn one script
and one clock reading into one record. The class publishes `calls_of`, which
reports the count of one call name.

### The harness module

`tests/support/rehearsal/harness.py` holds `RehearsalHarness` and
`RehearsalDeps`. `RehearsalDeps` is a frozen record. It holds the clock, the
fleet script, the store double, and the capture double. `RehearsalHarness`
builds the run record and attaches the stand-in cloud. It then wires
`RunDriverDeps` and
starts the driver. It publishes `attach`, `start`, `join`, and `record`.

### The defect module

`tests/support/rehearsal/defects.py` holds `DefectDrill`. The class publishes
one applier for each of the three defect classes. Each applier takes the pytest
`monkeypatch` fixture and the stand-in cloud. Each applier holds one block.

## Design decision 5: how the suite proves it makes no call

### No network call, for SC-004

A fixture replaces `socket.socket` with a function that raises
`RehearsalNetworkError`. The fixture counts each attempt. Every rehearsal test
asserts that the count stayed at zero.

The harness passes a `StandInSession` object to the shipped readers. The object
carries no host and no token, so a call that escaped the stand-in would fail at
once. The five attachment points cover every cloud call that the run makes.

The proof holds in two directions. A blocked socket changes no result, because
no code opens one. A stand-in that missed a call would raise at the socket
guard, and the test would then name the call.

### No firmware call, for SC-005

`_resolve_endpoint` at `upgrade_service.py:547` is the only door to every
upgrade endpoint. The stand-in resolver raises `RehearsalFirmwareError` for
`upgradeSiteDevices`, for `upgradeDevice`, and for `upgradeOrgSsrs`.

The stand-in also counts each name that it answers. Each test asserts that the
count of the three write names is zero. The `UpgradeSubmitter` seat of
`RunDriverDeps` holds a double. The double writes the upgrade identifiers into
the run record, and it calls no cloud endpoint.

## Design decision 6: how the defect drill runs, for SC-006

`DefectDrill` applies each defect through `monkeypatch`, so pytest reverts it at
the end of the test. No test edits a file under `src/`. The revert needs no
step, and a failed test leaves the branch clean.

| Defect class | Where the drill applies it | The failure the suite reports |
| - | - | - |
| The event search omits `device_type` | The drill wraps the stand-in event search and drops the parameter. The stand-in then answers access points only, as FR-010 states the real cloud does. | The gateway phase and the switch phase reach the phase deadline and report failed. |
| The gate compares a cloud timestamp against the local clock | The drill replaces `gate.uptime_decreased` with a rule that compares `last_seen` against `time.time`. `advance` calls that name as a module global, so the patch takes. | A device settles on the first poll round. The settle reading then falls below the scripted reboot moment. |
| The code reads `phase` instead of `current_phase` | The drill replaces `upgrade_service._normalize_status` with a copy that reads `phase`. The cloud names the field `current_phase`, as the comment at `upgrade_service.py:1583` states. | The status carries no phase, and the stop test reports the missing field. |

Each drill test states the defect, applies it, runs the matching rehearsal, and
asserts the failure. The test passes when the rehearsal fails. That inversion
proves the harness, and it needs no scratch copy of the branch.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `tests/unit/upgrade_portal/` already holds far more than 5 files. This feature adds 3 more. | The repository holds every portal unit test in that one directory. The standard test command reads it. | A new subdirectory would split the portal tests across two places. A reader would then miss half of them. The spec assumes the tests sit beside the other portal tests. |
| The harness patches 5 library attributes rather than 1 application seam. | FR-008 places the stand-in at the cloud library boundary, so the shipped reader code runs. | One application seam skips `read_fleet_statistics`, `drain_device_events`, the page guard, and the `device_type` parameter. Defect class 1 lives in code that the seam skips. |
