# Feature Specification: The upgrade rehearsal harness

**Feature Branch**: `feat/1992-upgrade-rehearsal`

**Created**: 2026-09-04

**Status**: Implemented

**Input**: Prove the upgrade settle gate and the stop control of the upgrade
capture portal without a write of firmware to production hardware. GitHub issue
#1992 records that scenario C and scenario D of
`specs/1823-upgrade-capture-portal/quickstart.md` never ran.

## Background

The upgrade capture portal holds two controls that no test proves end to end.
The first control is the settle gate. The gate waits for each device to return
after a reboot, and it holds the phase order. The second control is the stop.
The stop cancels each device that did not start to write firmware.

Scenario C and scenario D of the quickstart cover these two controls. Both
scenarios need a write of firmware to real hardware. Issue #1992 states that a
person must make that decision. Scenario A, scenario B, scenario E, and
scenario F now pass.

Almost every pass condition of the two scenarios describes portal logic. The
answers of the cloud drive that logic. The firmware itself drives very little of
it. A rehearsal that replays those cloud answers therefore proves the logic.

Issue #2007 records the cost of a wrong live run. One switch rebooted with the
reboot control off. The switch took six access points down for about six
minutes. That outage is the reason for the guard on the live run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove the settle gate through the whole cascade (Priority: P1)

An engineer starts one upgrade run against a stand-in cloud. The run drives the
shipped code through all four phases. The stand-in cloud answers the device
events and the device statistics. No call reaches the real cloud, and no device
writes firmware. The engineer reads the run record and confirms the phase order,
the settle signals, and the automatic post-check.

**Why this priority**: This story covers the largest untested area of the
portal. The settle gate holds the timing rules of the whole upgrade. A defect
here shows only on real hardware today.

**Independent Test**: Run the rehearsal test alone. The test starts the driver,
drives the clock forward, and asserts the phase order and the settle rules. The
test needs no browser and no network.

**Acceptance Scenarios**:

1. **Given** a run record with gateways, switches, access points, and clients,
   **When** the harness starts the driver, **Then** the phases settle in the
   order gateways, switches, access points, clients.
2. **Given** a phase that did not settle, **When** the harness inspects the run,
   **Then** no later phase started.
3. **Given** a device with a reconnect event and a decreased uptime and a
   changed version, **When** the harness moves the clock 59 seconds, **Then**
   the device stays unsettled.
4. **Given** the same device, **When** the harness moves the clock to 60
   seconds, **Then** the gate marks the device settled.
5. **Given** an access point with the same three signals, **When** the harness
   moves the clock to 60 seconds, **Then** the access point stays unsettled.
6. **Given** that same access point, **When** the harness moves the clock to 120
   seconds, **Then** the gate marks the access point settled.
7. **Given** a settled client phase, **When** the run continues, **Then** the
   driver starts the post-check capture without an operator action.
8. **Given** a run in progress, **When** a reader asks for the run status,
   **Then** the answer arrives in under 1 second.

---

### User Story 2 - Prove the stop control in mid-run (Priority: P1)

An engineer starts the same rehearsal run and stops it in the middle. Some
devices did not start to write firmware. One device writes firmware now. The
engineer reads the outcome and confirms the three lists and the plain sentence.

**Why this priority**: The stop is a safety control. An operator presses the
stop when an upgrade goes wrong. A wrong stop message misleads the operator at
the worst moment.

**Independent Test**: Run the stop rehearsal test alone. The test starts a run,
holds one device in the write state, and calls the stop. The test asserts the
lists and the message.

**Acceptance Scenarios**:

1. **Given** a run with devices that did not start to write firmware, **When**
   the engineer stops the run, **Then** the portal cancels every one of those
   devices.
2. **Given** a device that writes firmware now, **When** the engineer stops the
   run, **Then** the portal does not interrupt that device.
3. **Given** that same device, **When** the engineer reads the outcome, **Then**
   the device appears in the `already_writing` list.
4. **Given** a stop outcome with one device in mid-write, **When** the engineer
   reads the message, **Then** the message states that the device will finish
   the write.
5. **Given** a session smart router in the run, **When** the engineer stops the
   run, **Then** the portal cancels through the organization scope call.
6. **Given** that same session smart router, **When** the engineer reads the run
   record, **Then** the record shows `scope: "org"` for that device.

---

### User Story 3 - Catch the three known defect classes (Priority: P2)

An engineer breaks the portal code on purpose, one defect at a time. The
rehearsal test fails for each defect. The engineer then repairs the code and the
test passes again.

**Why this priority**: A harness that passes against broken code gives false
confidence. The quickstart names three real defects. The harness must catch each
one.

**Independent Test**: Apply each defect to a scratch copy of the branch and run
the rehearsal suite. Record the failure of each run.

**Acceptance Scenarios**:

1. **Given** an event search that omits `device_type`, **When** the rehearsal
   runs, **Then** the switch phase and the gateway phase fail to settle and the
   test fails.
2. **Given** a gate that compares a cloud timestamp against the local clock,
   **When** the rehearsal runs, **Then** a device settles at once and the test
   fails.
3. **Given** code that reads a `phase` field instead of `current_phase`, **When**
   the rehearsal runs, **Then** the run reports a missing field and the test
   fails.

---

### User Story 4 - Reduce the live run to a short confirmation (Priority: P3)

An engineer prepares the live run of scenario C and scenario D. The engineer
reads a short checklist. The checklist names only the facts that the rehearsal
cannot prove. Those facts are the cloud acceptance of the call and the reboot of
the hardware.

**Why this priority**: The live run stays a human decision. This story does not
block the harness. It makes the eventual live run shorter and safer.

**Independent Test**: Read the checklist and confirm that each item needs real
hardware. Remove any item that the rehearsal already proves.

**Acceptance Scenarios**:

1. **Given** the finished harness, **When** an engineer reads the live checklist,
   **Then** every item needs real hardware.
2. **Given** the live checklist, **When** an engineer reads the warning, **Then**
   the warning names the reboot risk and names issue #2007.

---

### Edge Cases

- A phase passes its deadline and no device returns. The run must record the
  timeout and must not start the next phase.
- A statistics read fails for one poll round. The run must mark the round
  partial and must continue.
- A device reports a changed version but no earlier uptime. The gate must warn
  and must record the weaker proof.
- A device reports a stale statistics record. The gate must not treat the stale
  record as a return.
- The stop arrives before any device starts to write firmware. Every device
  belongs in the cancelled list, and the `already_writing` list is empty.
- The stop arrives after every device finished the write. No device belongs in
  the cancelled list.
- The portal cannot read the state of one device. The outcome must place that
  device in `already_writing` and must not claim a cancel.

## Requirements *(mandatory)*

### Functional Requirements

#### The harness and the shipped code

- **FR-001**: The harness MUST drive the shipped run driver in
  `src/upgrade_portal/upgrade/driver.py`. The entry point is the `start` method,
  which spawns the thread of the run.
- **FR-002**: The harness MUST reach the shipped settle gate in
  `src/upgrade_portal/upgrade/gate.py` and in
  `src/upgrade_portal/upgrade/phase_gate.py`.
- **FR-003**: The harness MUST reach the shipped stop path in
  `src/upgrade_portal/upgrade/stop.py`.
- **FR-004**: The harness MUST NOT hold a copy of any settle rule, any phase
  order, or any stop rule. Every such rule stays in the shipped code. This rule
  holds by review, and no automated check proves it.
- **FR-005**: The harness MUST NOT write firmware. No test may call the real
  upgrade endpoint of the cloud.

#### The stand-in cloud

- **FR-006**: The stand-in cloud MUST answer the device event search and the
  device statistics read itself. No call may reach the network.
- **FR-007**: The stand-in cloud MUST answer the shape that the real cloud
  answers. The shape rules of `src/upgrade_portal/app/seam_shapes.py` and of
  `specs/1823-upgrade-capture-portal/seam-shape-audit.md` apply.
- **FR-008**: The stand-in cloud MUST sit at the boundary of the cloud client
  library. The shipped reader code must run above it.
- **FR-009**: The stand-in cloud MUST answer the paged shape, so the shipped
  page guard runs against a real page count.
- **FR-010**: The stand-in cloud MUST answer the device event search with the
  device type that the caller passes. A search without a device type must answer
  access points only, the same as the real cloud.
- **FR-011**: The stand-in cloud MUST hold a device model with a version, an
  uptime, and a last seen time. Each value must change when the rehearsal
  reboots the device.
- **FR-012**: The stand-in cloud MUST offer a scripted lifecycle for each
  device. The script names the moment of the reconnect event and the moment of
  the version change.
- **FR-013**: The stand-in cloud MUST offer an upgrade status answer for each
  device, so the stop path reads a real status shape.

#### The clock

- **FR-014**: The harness MUST drive the clock. A test must move time forward
  without a real wait.
- **FR-015**: The harness MUST drive the sleep of the phase gate through the
  same clock. One clock must serve the phase deadline and the device waits.
- **FR-016**: A rehearsal test MUST NOT wait a real settle window of 60 seconds.

#### The proofs

- **FR-017**: The suite MUST prove the fixed cascade order across all four
  phases in one composed run.
- **FR-018**: The suite MUST prove that a later phase never starts before an
  earlier phase settles.
- **FR-019**: The suite MUST prove the three settle signals of one device. The
  signals are the reconnect event, the decreased uptime with the changed
  version, and the further wait.
- **FR-020**: The suite MUST prove the extra wait of an access point.
- **FR-021**: The suite MUST prove that the run status answer arrives in under 1
  second while a run is in progress.
- **FR-022**: The suite MUST prove that the driver starts the post-check capture
  after the client phase settles.
- **FR-023**: The suite MUST prove a stop in the middle of a composed run.
- **FR-024**: The suite MUST prove that the stop cancels every device that did
  not start to write firmware.
- **FR-025**: The suite MUST prove that the stop does not interrupt a device that
  writes firmware, and that the outcome names that device in the
  `already_writing` list.
- **FR-026**: The suite MUST prove that the outcome message states that a device
  in mid-write will finish.
- **FR-027**: The suite MUST prove that a session smart router cancels through
  the organization scope call, and that the run record shows `scope: "org"` for
  that device.
- **FR-028**: The suite MUST fail for each of the three defect classes that
  section 5 of the quickstart names.

#### The scope guard

- **FR-029**: The live run of scenario C and scenario D MUST stay a human
  decision. This feature does not close issue #1992.
- **FR-030**: The feature MUST record a short live checklist. The checklist names
  only the facts that the rehearsal cannot prove.
- **FR-031**: The live checklist MUST carry a warning about the reboot. The
  warning must state the outage of issue #2007 as the consequence.

#### The prose

- **FR-032**: Every Markdown file of this feature MUST reach an STE score of 80
  or above.

### Key Entities

- **The rehearsal harness**: The test support code that builds a run record,
  starts the shipped driver, and drives the clock.
- **The stand-in cloud**: The object that answers the device event search, the
  device statistics read, and the upgrade status read.
- **The device script**: The plan of one device through the rehearsal. It holds
  the moment of the reconnect, the moment of the version change, the uptime
  before, and the uptime after.
- **The test clock**: The single time source of the run. It serves the phase
  deadline, the device waits, and the sleep of the poll loop.
- **The run record**: The shipped record of one upgrade run. The suite reads it
  for the phase order, the current phase, and the device scope.
- **The stop outcome**: The shipped result of one stop. It holds `cancelled`,
  `already_writing`, `no_cancel_available`, and `message`. A device with an
  unreadable state lands in `already_writing`.
- **The live checklist**: The short document for the human run of scenario C and
  scenario D.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The rehearsal suite proves 8 of the 9 portal pass conditions of
  scenario C and scenario D. The ninth is condition C1 of scenario C, "the
  portal refuses to start the upgrade when no verified pre-check exists". That
  condition belongs to the start route, and the rehearsal starts below that
  route on purpose, so the rehearsal cannot prove it and must not claim to. The
  contract test
  `tests/contract/upgrade_portal/test_capture_attach.py::test_a_start_before_the_pre_check_still_refuses`
  proves C1 at the level that owns it. All 9 conditions therefore hold, and this
  criterion states which suite proves each part.
- **SC-002**: The whole rehearsal suite finishes in under 60 seconds on a
  continuous integration worker.
- **SC-003**: No rehearsal test waits more than 1 real second for a settle
  window.
- **SC-004**: The suite makes zero network calls. A network block during the run
  changes no result.
- **SC-005**: The suite writes zero firmware calls. A count of the upgrade calls
  of the stand-in cloud is zero.
- **SC-006**: Each of the 3 named defect classes makes at least one rehearsal
  test fail.
- **SC-007**: The live checklist holds 5 items or fewer.
- **SC-008**: Every Markdown file of this feature scores 80 or above with the
  repository linter.

## Assumptions

- The rehearsal tests live beside the other tests of the portal, and the
  standard test command runs them.
- The stand-in cloud covers the device event search, the device statistics read,
  and the upgrade status read. It does not cover the whole cloud interface.
- The four phases of the rehearsal use a small device count. Two devices for
  each phase give enough proof of the order.
- The clients phase settles through the shipped rule of the driver, and the
  rehearsal does not add a new client rule.
- The harness reuses the run record shape that the shipped store already writes.
- The rehearsal does not replace the browser suite. The browser suite keeps the
  lock, the reschedule, the cancel, and the retry.
- The unit tests of the gate, of the phase gate, of the driver, of the events,
  and of the stop stay in place. This feature adds the composed level above
  them.
