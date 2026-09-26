# Feature Specification: A child job that the check proves counts its devices as upgraded

**Issue**: #3457
**Feature Branch**: `fix/3457-reconcile-upgraded-count`
**Status**: Draft
**Found by**: the browser journey of the multi-site check, on 2026-09-26

## Problem

The multi-site check reads the running version of each device of an uncertain
child job. If each device runs the target version, the check proves the child
job. The portal then marks the child job completed.

The counts of the progress page do not change after that proof.

- The child row shows the status completed beside Upgraded 0.
- The operation block shows Upgraded 0.
- The device table shows each device of the child job as completed, with the
  result "Version matches".

The page therefore contradicts itself. The single-site check marks each proven
device as settled, so its counts include each proven device. The two modes do
not agree.

## User Scenarios & Testing

### User Story 1 (P1): The child row counts each proven device

The operator must read the correct counts after the check proves a child job.

**Independent test**: Seed an operation with two uncertain child jobs. Make the
check prove one child job, and open the progress page.

**Acceptance scenarios**:

1. **Given** a proven child job of one device. **When** the progress page
   opens. **Then** the child row shows Targets 1, Upgraded 1, and Failed 0.
2. **Given** a proven child job and a child job with no proof. **When** the
   progress page opens. **Then** the row of the child job with no proof shows
   Upgraded 0 and Failed 0.
3. **Given** two proven child jobs of one device each. **When** the progress
   page opens. **Then** each child row shows Upgraded 1.

### User Story 2 (P1): The operation block counts each proven device

**Independent test**: Use the operation of User Story 1, and read the
operation block.

**Acceptance scenarios**:

1. **Given** a proven child job of one device and a child job with no proof.
   **When** the progress page opens. **Then** the operation block shows Total
   targets 2, Upgraded 1, and Failed 0.
2. **Given** two proven child jobs of one device each. **When** the progress
   page opens. **Then** the operation block shows Upgraded 2 and Failed 0.

### User Story 3 (P1): The status poll shows the same counts

The progress page asks the portal for the status at a fixed interval. Each
answer paints the counts again.

**Independent test**: Use the operation of User Story 1, and read the status
answer.

**Acceptance scenarios**:

1. **Given** the operation of User Story 2. **When** the status answer
   arrives. **Then** the answer holds the same operation counts as the page.
2. **Given** the operation of User Story 2. **When** the status answer
   arrives. **Then** each child row of the answer holds the same counts as the
   page.

### User Story 4 (P3): A device that the cloud lists as failed stays failed

The cloud answer of a child job can name a device as failed. The device table
then shows that device as failed.

**Independent test**: Store a proven child job of two devices, with a cloud
answer that names one device as failed.

**Acceptance scenarios**:

1. **Given** that child job. **When** the progress page opens. **Then** the
   child row shows Targets 2, Upgraded 1, and Failed 1. The device table shows
   one completed device and one failed device.

### User Story 5 (P2): The operator sees the correct counts in a real browser

**Acceptance scenarios**:

1. **Given** a real browser and the seeded operation of the check journey.
   **When** the check proves the child job of the first site. **Then** the
   child row of the first site shows Targets 1, Upgraded 1, and Failed 0.
2. **Given** the same page. **When** the operator reads the operation block.
   **Then** it shows Total targets 2, Upgraded 1, and Failed 0. A screenshot
   records the page.

### Edge Cases

- A child job that the check does not prove keeps its counts. The check
  stores its evidence, and the counts do not change.
- A child job that completes through the cloud keeps the counts of its cloud
  answer. The new rule reads only a child job that the check proved.
- A child job from an earlier release stores the device addresses only. The
  rule counts those devices too.
- The Failed count of a child row cannot be larger than its Targets count.

## Requirements

### Functional Requirements

- **FR-001**: After the check proves a child job, the Upgraded count of its
  child row includes each of its devices. The Upgraded count does not include
  a device that the cloud lists as failed.
- **FR-002**: The Failed count of a proven child row equals the count of its
  devices that the cloud lists as failed. If the cloud lists no failed device,
  the count is 0.
- **FR-003**: The operation block adds the counts of each child row. It adds a
  proven child row and a child row with no proof in the same way.
- **FR-004**: The status answer holds the same counts as the page, for the
  operation and for each child row.
- **FR-005**: A child job that the check did not prove keeps the counts of its
  cloud answer.
- **FR-006**: The Targets count and the Total targets count do not change.
- **FR-007**: The change adds no cloud read and no write. The stored record of
  the operation does not change.

## Success Criteria

- **SC-001**: After the check proves a child job, the child row, the operation
  block, and the device table agree for each device.
- **SC-002**: The page and the status answer show the same counts.
- **SC-003**: The change adds no cloud read, no write, and no route change.

## Assumptions

- A proven child job is a child job that the check marked completed with a
  proof.
- The multi-site history section shows no device count. The issue asks that
  the history page show the same counts. No count appears there, so that
  request needs no change.
- The stored proof and the stored cloud answer do not change. The counts come
  from the proof each time the page or the status answer reads the operation.

## Out of Scope

- Issue #3329: a rejected child job adds no failed device. That issue gets its
  own repair.
- The single-site mode. Its check already counts each proven device.
- The result text of the check. Issue #3453 repaired that text.
