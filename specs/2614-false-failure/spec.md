# Feature Specification: False Failure Reconciliation

**Feature Branch**: `fix/2614-false-failure`

**Created**: 2026-09-15

**Status**: Ready to implement

**Input**: Issue #2614 reports a stored upgrade run that says a gateway failed after the gateway reached the target running firmware.

## Background

Run `run-51f8c319224a4db099ea2e3b14a16233` stored `state = failed`.
Its gateway target also stored `state = failed`.

The stored target kept `version_after`, `reboot_seen_at`, and `settled_at` as
null. The current cloud evidence shows the gateway connected on
`24.2R2-S3.3`, which is the target version. The `fwupdate` status is
`success` with progress `100`.

The live phase gate now uses this evidence before a timeout becomes a device
failure. The stored terminal run still cannot use the reconciliation control,
because terminal runs are not stale and the service accepts only `stopping`.

## User Scenarios and Testing

### User Story 1 - Repair a proven false failure (Priority: P1)

An operator reconciles a failed timeout run. The portal reads current cloud
evidence. If the target runs the requested firmware and `fwupdate` says
`success`, the portal removes the false failure.

**Independent Test**: Seed the run from issue #2614 and supply positive current
cloud evidence. Reconcile the run through the durable action path.

**Acceptance Scenarios**:

1. **Given** the issue #2614 run, **When** current evidence proves firmware
   success, **Then** the run state becomes `complete`.
2. **Given** the issue #2614 target, **When** reconciliation finishes, **Then**
   the target state becomes `settled`.
3. **Given** the phase gate did not measure reboot or settle time, **When** the
   target is repaired, **Then** `reboot_seen_at` and `settled_at` stay null.
4. **Given** the repair used later cloud evidence, **When** the record is stored,
   **Then** the record includes a reconciliation note and evidence digest.

### User Story 2 - Keep true failures failed (Priority: P1)

An operator reconciles a failed timeout run whose evidence is incomplete or
negative. The portal refuses the success path and keeps the failure visible.

**Independent Test**: Supply missing, active, conflicting, or mismatched current
evidence. Confirm the run does not move to `complete`.

**Acceptance Scenarios**:

1. **Given** a failed target with no current firmware success, **When** the
   operator reconciles the run, **Then** the run stays failed.
2. **Given** a failed target whose running version differs from the target
   version, **When** reconciliation runs, **Then** the result is unknown.
3. **Given** a target still writing firmware, **When** reconciliation runs,
   **Then** the portal refuses the mutation.

### User Story 3 - Use only running-version evidence (Priority: P1)

The portal reads running firmware from an endpoint that reports device state.
It never uses the configured version from `listSiteDevices` for this decision.

**Independent Test**: Inspect the evidence reader and run unit tests with
scripted site statistics.

**Acceptance Scenarios**:

1. **Given** a gateway target, **When** reconciliation reads evidence, **Then**
   the reader uses site device statistics with `type="all"`.
2. **Given** a configured version field is null or stale, **When** evidence is
   evaluated, **Then** the decision uses the running version only.

## Edge Cases

- Current evidence is unavailable.
- Current evidence reports an active firmware task.
- Current evidence reports `fwupdate` with a value other than `success`.
- Current evidence reports success but no target version.
- The stored run changes between the evidence read and the write.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST let reconciliation reach a failed run only when
  the stored error is an upgrade phase timeout.
- **FR-002**: The system MUST prove success with both a matching running version
  and `fwupdate` status `success`.
- **FR-003**: The system MUST use the shared gate version comparison rule.
- **FR-004**: The system MUST keep true failures in a failed or unknown result.
- **FR-005**: The system MUST leave unmeasured reboot and settle times null.
- **FR-006**: The system MUST write a reconciliation note and evidence digest.
- **FR-007**: The system MUST mutate the run and action outcome atomically.
- **FR-008**: The system MUST use `listSiteDevicesStats` with `type="all"` for
  production running-version evidence.

### Key Entities

- **Run record**: The stored upgrade result that the history and run pages show.
- **Target evidence**: The safe current evidence for one device target.
- **Reconciliation action**: The durable action row that records the repair.

## Success Criteria

- **SC-001**: The issue #2614 regression test fails before the repair and passes
  after the repair.
- **SC-002**: A proven false failure no longer stores `state = failed`.
- **SC-003**: An unmeasured reboot or settle time stays null and has an explicit
  note.
- **SC-004**: Local lint, format, type, and upgrade portal tests pass.

## Assumptions

- The operator already owns the site lock and has run-control write access.
- The run record remains in ArangoDB with a current revision.
- No live Mist request runs in unit tests.
