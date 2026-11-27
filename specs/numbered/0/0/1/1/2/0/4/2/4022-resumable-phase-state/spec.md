# Feature Specification: Persist resumable firmware phase state

**Issue**: #4022, child 4 of 4 of parent #3332
**Feature Branch**: `feat/4022-resumable-phase-state`
**Created**: 2026-11-26
**Status**: Draft. The implementation is on hold. See Clarifications and decision D-11.
**Input**: Issue #4022 body and comments dated 2026-10-07 and 2026-11-10.

## Glossary

- **Phase**: One cascade step of a site upgrade. The order is gateways, switches, aps, and clients. The issue text calls a phase a family. This record uses phase only.
- **Recovery phase**: The first phase in cascade order that is neither settled nor skipped.
- **Recovery point**: The durable record that names the recovery phase, the reason, and its submission state.
- **Submission state**: The portal record of one firmware call for one phase. Values: `not_sent`, `accepted`, `refused`, `unknown`.
- **Site lock**: The Redis lock in `runtime/lock.py`. It expires and it has a quiet period.
- **Site hold**: The durable block in the run record. It refuses new firmware writes at the site.

## User Scenarios and Testing *(mandatory)*

### User Story 1 - See the stop and the next step (Priority: P1)

An operator opens a stopped single-site run. The page names the stopped phase, the reason, and one next step.

**Why this priority**: A stop with no next step makes the operator guess. A guess repeats or skips a phase.

**Independent Test**: Render a stopped run that holds a recovery point. Confirm the phase, the reason, and the disabled resume control. Covers TC-23 and TC-24.

**Acceptance Scenarios**:

1. **Given** a stopped run with a recovery point, **When** the operator opens the run page, **Then** the page names the recovery phase. **And** the page gives the reason and one next step.
2. **Given** a stopped run without a recovery point, **When** the operator opens the run page, **Then** no resume control appears.

---

### User Story 2 - Resume only the recovery phase (Priority: P1)

An operator repairs the cause of a stop. The operator types RESUME. The portal reads live state and sends firmware only to the recovery phase.

**Why this priority**: A resume that repeats a settled phase or skips an unsettled phase can damage production hardware.

**Independent Test**: Resume a stopped run with fake submitter and fake readers. Confirm that settled phases receive no call. Covers TC-11 to TC-16.

**Acceptance Scenarios**:

1. **Given** a stopped run with recovery submission `not_sent`, **When** the operator types RESUME, **Then** the portal sends one firmware call for that phase only.
2. **Given** a device that already runs its target version, **When** the resume starts, **Then** the portal sends no firmware to that device.
3. **Given** a stopped run with recovery submission `accepted`, **When** the operator types RESUME, **Then** the portal observes the phase and sends no firmware.

---

### User Story 3 - Keep the site held after an unknown reply (Priority: P1)

A firmware call ends with a transport fault, a server error, or a reply that proves neither refusal nor acceptance. The site stays held until reconciliation proves the outcome.

**Why this priority**: A released site lock lets a second operator start a second write while the first write may still run.

**Independent Test**: Simulate a timeout and a 503 reply. Confirm that the submission state is `unknown`, the site hold remains, and no route starts a new write. Covers TC-01 to TC-06, TC-10, TC-21, and TC-22.

**Acceptance Scenarios**:

1. **Given** a firmware call that raises a transport fault, **When** the run stops, **Then** the phase reads `unknown` and the site hold remains.
2. **Given** an active site hold, **When** an operator starts a new run at the site, **Then** the start route refuses the request.

---

### User Story 4 - Resume a multi-site phase after the gate exists (Priority: P2)

After issue #4021 merges, an operator resumes the unresolved child jobs of a multi-site operation by phase.

**Why this priority**: The multi-site submission has no phase gate yet. A resume before that gate exists repeats the defect of issue #3332.

**Independent Test**: Resume a stopped multi-site operation with fake child jobs. Covers TC-27 to TC-29.

---

### User Story 5 - Keep operator text accurate (Priority: P2)

Every stop, failure, and unknown message names the phase, the reason, and one next step. A changed string updates each test that asserts it.

**Why this priority**: An operator reads these messages during a firmware write. A message with no next step causes a wrong action.

**Independent Test**: Run the parity and contract tests that assert the phase text. Covers TC-25 and TC-26.

## Edge Cases

- A stop lands during the settle wait. The driver returns before it writes the phase outcome. The recovery phase keeps its submission state.
- A stop lands after a firmware call returns. The submission state is `accepted`, and the resume observes the phase.
- The recovery point write is not verified. The site hold remains, and the stop is not reported as clean.
- The browser closes during a resume. The next read shows the last durable state. The site lock owner rules still apply.
- Two resume requests arrive at once. The dispatch gate admits one request. The other request refuses with the run state.
- A device changes version between the stop and the resume. The portal treats the device as at target only when its version equals the target version.
- A cloud job exists for an `unknown` submission. The submission state becomes `accepted`, and the phase is observed.
- No cloud job exists for an `unknown` submission. The hold remains until the operator reads the evidence and FR-014 passes.
- The clients phase has no firmware plan. The clients phase is observation only.
- A phase has no device of its family. The phase is skipped and never waited for or submitted.
- A retry request arrives during a site hold. The retry route refuses the request.
- A multi-site child is partly accepted. Only unresolved children resume, after issue #4021 merges.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST store one recovery point on each stopped run that has an unsettled phase.
- **FR-002**: The portal MUST store one submission state for each phase. The values are `not_sent`, `accepted`, `refused`, and `unknown`.
- **FR-003**: The portal MUST verify each recovery point and each resume attempt by read-back before it reports success.
- **FR-004**: When a verified write fails, the portal MUST keep the site hold and MUST NOT report a clean stop.
- **FR-005**: The run page MUST name the recovery phase, the reason, and one next step in plain words.
- **FR-006**: The portal MUST offer the resume control only for a stopped run that holds a recovery point.
- **FR-007**: The resume request MUST require the exact typed word `RESUME`, with exact letter case.
- **FR-008**: A missing or wrong typed word MUST refuse the resume before any Mist request.
- **FR-009**: The resume MUST refuse when another operator holds the site, when a driver thread is live, or when the run state is not `stopped`.
- **FR-010**: The resume MUST read the live state of each device of the recovery phase before any firmware write.
- **FR-011**: The resume MUST NOT send firmware to a device that already runs its target version.
- **FR-012**: The resume MUST NOT send firmware to a phase that is settled or skipped, and MUST NOT wait for that phase again.
- **FR-013**: The resume MUST send at most one firmware call for the recovery phase in each attempt. It MUST send only when the submission state is `not_sent` or `refused`.
- **FR-014**: The resume MUST NOT send firmware for an `unknown` submission until reconciliation proves that no cloud job exists and that no device changed version.
- **FR-015**: For an `accepted` submission, the resume MUST observe the phase and MUST NOT send firmware again.
- **FR-016**: The resume MUST NOT send firmware to a phase after the recovery phase until the recovery phase settles.
- **FR-017**: The portal MUST keep the site hold while any phase has submission state `unknown`, or `accepted` with an unsettled phase.
- **FR-018**: The portal MUST NOT release the site lock at `stopped` or `failed` while FR-017 holds.
- **FR-019**: The portal MUST classify each firmware reply as `accepted`, `refused`, or `unknown`, with the shared submission certainty rule.
- **FR-020**: The portal MUST NOT describe an `unknown` reply as a refusal.
- **FR-021**: The portal MUST NOT retry a firmware write after an `unknown` reply without an explicit operator resume.
- **FR-022**: The start, pre-check, takeover, and retry routes MUST refuse each request while the site hold is active.
- **FR-023**: The phase watch MUST observe the phases after a failed phase without a new wait. The resume MUST reset the recovery phase before it observes that phase again.
- **FR-024**: The multi-site resume MUST wait for the family gate of issue #4021. It MUST apply FR-010 to FR-018 to each child job.
- **FR-025**: Each stop, failure, and unknown message MUST name the phase, the reason, and one next step.
- **FR-026**: Each changed operator string MUST update every test that asserts its exact text in the same change.
- **FR-027**: Each new interactive control MUST carry a stable `data-testid` attribute.
- **FR-028**: Every Mist request MUST use a mistapi method. The portal MUST NOT send direct HTTP to a Mist endpoint.
- **FR-029**: Each resume action MUST write an info log line before it runs and a debug log line after it runs. Logs MUST NOT contain secrets.
- **FR-030**: The change MUST NOT add a menu operation, and MUST NOT change the destructive category of any menu.

### Mist Cloud Transport Requirements

- Site write: `upgradeSiteDevices` (RC-098) and `upgradeDevice` (RC-030). Both use the existing `invoke_upgrade` seam (RC-031).
- Organization write, after issue #4021: `upgradeOrgDevices` (RC-103).
- Site reconcile reads: `listSiteDeviceUpgrades` (RC-101), `getSiteDeviceUpgrade` (RC-099), and `listSiteDevicesStats` (RC-102).
- Organization reconcile reads, after issue #4021: `listOrgDeviceUpgrades` (RC-105) and `getOrgDeviceUpgrade` (RC-104).
- Site cancel: `cancelSiteDeviceUpgrade` (RC-100), unchanged.
- The change owns no WebSocket transport. The change claims no SDK insufficiency. The change sends no direct HTTP.
- Contract evidence: the SDK compatibility guard `tests/integration/test_mistapi_sdk_compatibility.py` (RC-086) must pass.

### Key Entities

- **Recovery point**: The recovery phase, the reason, the submission state, the hold flag, and the next step.
- **Phase entry**: The existing phase record. This change adds one field, `submission`.
- **Resume attempt**: One record for each resume request. It holds the reconciliation counts and the outcome.
- **Site hold**: The durable block that FR-017 derives. It uses the natural Mist keys `org_id` and `site_id`.
- **Reconciliation proof**: The read-only evidence and the decision that the proof supports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each stopped run with an unsettled phase shows the phase, the reason, and one next step. Verified by TC-23.
- **SC-002**: No resume sends firmware to a settled, skipped, or at-target device. Verified by TC-12 and TC-13.
- **SC-003**: No `unknown` reply releases the site lock. No `unknown` reply allows a new write before proof. Verified by TC-05, TC-06, and TC-14.
- **SC-004**: Each changed operator string updates its test in the same change. Verified by TC-25 and TC-26.
- **SC-005**: The multi-site resume passes its contract and end-to-end tests after issue #4021 merges. Verified by TC-27 to TC-29.
- **SC-006**: Each gate in `T-LOCAL-GATES` passes, or the record reports its exact output.

## Assumptions

- **A-1**: Mist reads return the job state and the firmware version at the time of the read. No live Mist request ran during this record.
- **A-2**: The existing `PhaseSettleGate` remains the only method that observes a phase.
- **A-3**: The operator holds the site lock, or the operator takes it by the existing lock rules.
- **A-4**: Issue #4020 stays merged. Pull request #4109 merged it as commit `acaae1ad`.
- **A-5**: This record performs no firmware operation and no production store change.

## Out of Scope

- New menu operations, menu registry changes, and changes to the destructive set.
- Changes to the Mist API, the `mistapi` pin, or the upgrade capture portal port.
- Changes to the retry flow. The retry flow creates a new run and keeps its current rules.
- Changes to `ops-portal/` and `mist-ops-platform/`.
- Splitting the tracked debt in the upgrade portal folders. That work needs a separate remediation action.

## Clarifications

### Session 2026-11-26

- **Q1**: Issue #4022 owner decision 4 asks how a resume works after a stopped phase. **A1**: Adopt the recommended option. Resume only after the operator confirms the repair. Never repeat a settled phase. Never skip a phase without a settled result. Basis: the owner-approved retry rule on issue #4020, comment 6031475938. See D-2.
- **Q2**: Does the portal store phase state durably today? **A2**: Yes for phase entries on single-site runs (RC-005) and on multi-site records (RC-010). The missing parts are the recovery point, the submission state, the resume action, and the site hold. The issue body says that no durable state exists. The 2026-10-07 comment corrects that statement.
- **Q3**: Do issues #4020 and #3726 still block this work? **A3**: Issue #4020 is closed. Its single-site prerequisite merged as commit `acaae1ad` in PR #4109. Issue #3726 is closed. PR #4701 merged its fix as commit `53ad73cc`. Issue #4021 is open. See analysis.md, corrections C-03 and C-04.
- **Q4**: Which typed word confirms the resume? **A4**: `RESUME`. See D-4.
- **Q5**: Does a stopped run keep the site lock? **A5**: It keeps the site hold while a phase is unresolved. A clean stop keeps the current release rule. See D-6.
- **Q6**: Is a retry a resume? **A6**: No. The retry route creates a new run (RC-054). The resume runs in place. See D-3.
- **Q7**: Does the multi-site resume ship with this change? **A7**: Only after issue #4021 merges. See D-1.

## Safety Statements

Warning: A repeated firmware write can reach a device that already upgraded. Do not resume an `unknown` phase before reconciliation proves the outcome.

Warning: A released site lock during an unknown outcome lets a second operator start a second write.

Caution: A held site stays blocked until the operator resolves the recovery phase. The run page shows the next step.

HUMAN-DECISION-REQUIRED: Decision D-11 holds the implementation until the owner approves the start. See `design/research.md`.
