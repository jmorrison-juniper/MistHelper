# Research: The upgrade rehearsal harness

**Feature**: `specs/1992-upgrade-rehearsal/` | **Date**: 2026-09-04

The specification holds no open clarification. This document therefore records
the reading of the shipped code, and it records the choice that each reading
settled. Every line number belongs to the branch `feat/1992-upgrade-rehearsal`.

## Q1: Where does the harness start the run?

**Decision**: The harness calls `RunDriver.start` at `driver.py:1226`.

**Rationale**: `start` spawns the one thread that owns the run. That thread
calls `run`, which calls `_submit` and then `_cascade`. `_cascade` at
`driver.py:1420` walks `PHASE_ORDER` and calls the settle gate for each phase.
The whole lifecycle therefore runs from that one call, which FR-001 asks for.

**Alternatives considered**: A direct call to `RunDriver.run` skips the thread.
It would then hide a defect of the thread registry, and the run status test of
FR-021 needs a live thread. The harness therefore uses `start` and joins the
thread at the end.

## Q2: Where does the harness inject its doubles?

**Decision**: `RunDriverDeps` at `driver.py:722` is the seam of the harness.

**Rationale**: The record holds 7 members, and every member is a protocol or a
record. The harness fills `store`, `gate`, `capture`, `submit`, and `clock`. The
`gate` member holds the real `PhaseSettleGate`, so the shipped settle rules run.

**Alternatives considered**: A stand-in in the `gate` seat would meet FR-001 and
would fail FR-002. The gate holds the settle rules, so a stand-in there proves
nothing about them.

## Q3: Which cloud calls does one rehearsal run make?

**Decision**: A run makes four distinct cloud calls.

**Rationale**: A search of the portal package found these call sites.

| Call | Caller | Line |
| - | - | - |
| `listOrgDevicesStats` | `gate.read_fleet_statistics` | `gate.py:846` |
| `searchOrgDeviceEvents` | `events.read_device_events` | `events.py:430` |
| `listDeviceEventsDefinitions` | The event key catalogue | `events.py` |
| `getSiteDeviceUpgrade` and the cancel calls | `_resolve_endpoint` | `upgrade_service.py:547` |

The page walk `mistapi.get_all` at `gate.py:856` is a fifth attachment point. It
reads the answer that the stand-in built, so the stand-in must answer both.

**Alternatives considered**: A stand-in that answered only the two read calls
would leave the stop path on the real cloud. FR-013 asks for the status answer,
so the stand-in covers `_resolve_endpoint` as well.

## Q4: What answer shape must the stand-in build?

**Decision**: The stand-in answers an object with `data` and `status_code`.

**Rationale**: `guard_page_count` at `capture/devices.py:273` reads three facts
of the answer. It reads the status code. It reads whether the body is a list or
a mapping that holds `results`. It reads the `total` field. A body that fails
any of the three marks the poll partial.

`read_cursor` at `events.py:351` reads `search_after` first, and it reads the
`next` URL second. `mistapi.get_all` reads the same body.

**Alternatives considered**: A plain list body passes `_known_shape` and reports
no total. FR-009 asks for the paged shape, so the stand-in answers a mapping
with `results`, `total`, and `next`. The page guard then runs against a real
page count.

## Q5: How does the shipped code read time?

**Decision**: The shipped code reads time through four injected seats. The
harness fills all four with one object.

**Rationale**: `SettleGate.__init__` at `gate.py:928` takes a clock callable.
`PhaseGateDeps.sleep` at `phase_gate.py:340` takes a sleep callable.
`CloudReconnectReader.__init__` at `phase_gate.py:264` takes a clock callable.
`RunDriverDeps.clock` at `driver.py:749` takes a `Clock` protocol.

The docstring of `PhaseGateDeps` states the intent plainly at
`phase_gate.py:332`. A test passes a callable that moves a fake clock and waits
no real seconds. The shipped code already expects this harness.

**Alternatives considered**: A patch of `time.time` and `time.sleep` reaches
every thread of the interpreter. `tests/support/thread_scoped_sleep.py` records
the failure that such a patch caused on pull request #1820. The injected seats
avoid that whole class of fault.

## Q6: How does the gate prove that a device rebooted?

**Decision**: The stand-in drops the uptime and changes the version at the same
scripted moment.

**Rationale**: `_reboot_is_proven` at `gate.py:649` tries three paths. The fall
of two real uptime readings is the strongest path. `_note_reboot` at
`gate.py:687` needs a changed version as well. `_note_settled` at `gate.py:714`
then adds `settle_wait_seconds` of the device type.

A script that drops the uptime and changes the version together therefore takes
the strongest path. The two weaker paths stay available for the edge cases.

**Alternatives considered**: A script that changed the version alone would take
the version-only path and would raise a warning. That path belongs to one edge
case test and not to the main cascade.

## Q7: How does the drill inject each defect?

**Decision**: Each drill uses `monkeypatch`, and pytest reverts it.

**Rationale**: `advance` at `gate.py:733` calls `uptime_decreased` as a module
global. A patch of `gate.uptime_decreased` therefore reaches the rule.
`_normalize_status` at `upgrade_service.py:1612` reads `current_phase` from the
payload. A patch of that function reproduces the third defect.

The first defect belongs to the caller of the event search. The drill drops the
`device_type` parameter at the stand-in, so the stand-in answers access points
only. FR-010 states that the real cloud behaves the same way.

**Alternatives considered**: An edit of a file under `src/` would need a revert
step. A failed test would then leave the branch dirty. The instruction of User
Story 3 names a scratch copy, and `monkeypatch` gives the same proof with no
copy at all.

## Q8: How does the suite prove the run status answer of FR-021?

**Decision**: The stand-in pauses one poll round, and the test reads the record.

**Rationale**: The driver thread writes the run record after each phase. The
test thread must read the record while the run is in progress. The stand-in
therefore calls a hook on a chosen poll round. The hook blocks the driver thread
on an event.

The test thread then reads the record and measures the read. It sets the event,
and the run continues. The measured read is a few milliseconds, so the real wait
of the test stays far below 1 second.

**Alternatives considered**: A poll of the record in a loop would race with the
driver thread. The result would then depend on the speed of the worker, which
SC-002 cannot accept.

## Q9: Which devices does the rehearsal fleet hold?

**Decision**: Two gateways, two switches, and two access points.

**Rationale**: The assumptions of the specification name two devices for each
phase. Two devices prove the order and prove a phase that settles in parts. The
client phase holds no device, because `phase_targets` always answers empty for
it at `driver.py:1472`.

The stop fleet adds one session smart router. FR-027 needs that device for the
organization scope proof.

**Alternatives considered**: One device for each phase would hide a phase that
settles one member and misses the other. Six devices keep the suite under the 60
second budget of SC-002.
