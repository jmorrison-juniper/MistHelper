# Feature Specification: The multi-site check result uses correct grammar for each count

**Issue**: #3453
**Feature Branch**: `fix/3453-reconcile-summary-grammar`
**Status**: Draft
**Found by**: a code scan during the work on #3447

## Problem

The multi-site progress page lists each uncertain child job. After a check,
each row shows the result of the last check. The first sentence of that
result always uses the plural noun "devices" and the plural verb "run".

A child job of one device is common. A site often holds one gateway. The row
then says "0 of 1 devices run the target version" or "1 of 1 devices run the
target version". When one device of three matches, the row says "1 of 3
devices run the target version".

The unread sentence has the same defect. A child job of one device with no
reading says "The portal could not read 1 of the 1 devices".

The operator reads this result to decide the next step. Wrong grammar makes
the counts look wrong, and the operator can then doubt a correct result.

The single-site check does not write this sentence, so the single-site mode
does not change.

## User Scenarios & Testing

### User Story 1 (P1): A child job of one device reads as one device

The operator must read correct grammar for a child job of one device.

**Independent test**: Check an uncertain child job of one device, and read the
result.

**Acceptance scenarios**:

1. **Given** a child job of one device that runs the target version, **When**
   the check ends, **Then** the result says "The target version runs on 1 of
   1 device".
2. **Given** a child job of one device with no reading, **When** the check
   ends, **Then** the result says "The target version runs on 0 of 1 device"
   and "The portal could not read 1 of 1 device".
3. **Given** a child job of one device that ran the target version before the
   upgrade, **When** the check ends, **Then** the first sentence says "The
   target version runs on 1 of 1 device".

### User Story 2 (P1): A child job of two or more devices reads as devices

**Independent test**: Check an uncertain child job of three devices.

**Acceptance scenarios**:

1. **Given** a child job of three devices where one device matches, **When**
   the check ends, **Then** the result says "The target version runs on 1 of
   3 devices".
2. **Given** two of three devices match, and one device gives no reading.
   **When** the check ends, **Then** the result says "The target version runs
   on 2 of 3 devices". The result also says "The portal could not read 1 of 3
   devices".

### User Story 3 (P2): The operator sees the correct result in a real browser

**Acceptance scenarios**:

1. **Given** a real browser and an operation with two uncertain child jobs.
   **When** the operator types the check word, and presses "Check the child
   jobs". **Then** the row with no proof says "The target version runs on 0 of
   1 device". A screenshot records the row.

### Edge Cases

- The child job names no device. The result keeps the text "The child job
  names no device. The portal cannot prove its outcome".
- A check that ran before this change keeps its stored text. The page shows
  the stored text of the last check.
- The count 11 or 21 takes the plural noun. Only the total 1 takes the
  singular noun.

## Requirements

### Functional Requirements

- **FR-001**: The first sentence of each result has the form "The target
  version runs on M of T device" for the total 1. For each other total, the
  sentence uses "devices".
- **FR-002**: The unread sentence has the form "The portal could not read U
  of T device" for the total 1. For each other total, the sentence uses
  "devices".
- **FR-003**: The other sentences of each result do not change.
- **FR-004**: The result of a child job with no device does not change.
- **FR-005**: The verdict values, the proof rule, and the stored fields do not
  change. Only the text of the summary changes.

## Success Criteria

- **SC-001**: For each count from 0 to 3, the result reads as correct English.
- **SC-002**: The change adds no cloud read and no write.

## Assumptions

- The page uses the English plural rule. The total 1 takes the singular noun.
  Each other total takes the plural noun. The portal has no other language.
- The subject of the new first sentence is "the target version". That subject
  is singular for each count, so the verb "runs" never changes.

## Out of Scope

- The single-site check.
- The stored text of an earlier check.
- A shared plural helper for all modules.