# Feature Specification: The poll of a stored capture stops

**Issue**: #3378
**Feature Branch**: `fix/3378-stored-capture-poll`
**Status**: Draft
**Found by**: the user journey harness of #3200

## Problem

The capture page asks the status endpoint for the progress of one capture. The
page stops that poll when the `state` field holds a finished word. The finished
words are `verified`, `failed`, and `write_failed` (`FINISHED_STATES` in
`portal.js`).

The worker process holds the progress of each live capture in memory. A restart
empties that memory, and a trim removes the oldest record after 200 records.
The status endpoint then reads the stored capture instead, through
`stored_progress` in `src/upgrade_portal/app/routes/capture.py`.

That function copies the `capture_status` field of the document into `state`.
The shipped store writes `complete`, `partial`, or `failed` into
`capture_status`. The words `complete` and `partial` are not finished words, so
the page asks the endpoint again every 3 seconds for as long as the tab stays
open.

| Path | `state` at the end | `verified` | The page stops the poll |
| - | - | - | - |
| Live capture | `verified` or `failed` | The read-back result | Yes |
| Stored capture, now | `complete`, `partial`, or `failed` | The read-back result | Only for `failed` |

Each poll of a stored capture reads the whole capture document from the store.
One idle tab therefore reads one document 20 times each minute and never stops.

The multi-site pre-check card reads the same body. It accepts a pre-check only
when `state` holds `verified`, so a stored answer holds that card too.

## User Story 1 (P1): The page of a stored capture stops the poll

An operator opens the page of a capture that ended before a restart.

**Acceptance scenarios**:

1. **Given** a stored capture with `capture_status` `complete` and a read-back
   that holds, **When** the operator opens its page, **Then** the page sends one
   status request and no more.
2. **Given** the same page, **When** the page paints the status, **Then** the
   state cell reads `verified` and the badge reads `Verified`.
3. **Given** a stored capture with `capture_status` `partial` and a read-back
   that holds, **When** the page paints the status, **Then** the state cell
   reads `verified` and the partial warning names the lost sections.

## User Story 2 (P1): The status endpoint uses one rule for both paths

**Acceptance scenarios**:

1. **Given** a stored capture that the portal read back unchanged, **When** a
   client reads the status endpoint, **Then** `state` holds `verified` and
   `verified` holds true.
2. **Given** a stored capture that this release cannot compare, **When** a
   client reads the status endpoint, **Then** `state` holds `failed` and
   `verified` holds false. This covers a capture that never reached the
   verified state and a capture that a later release wrote.
3. **Given** any stored capture, **When** a client reads the status endpoint,
   **Then** `state` holds a word that ends the poll of the capture page and the
   poll of the multi-site pre-check card.

## Functional requirements

- **FR-001**: A stored capture reports `verified` in `state` when the read-back
  holds. It reports `failed` in every other case. The live path uses the same
  rule (`progress_change` in `src/upgrade_portal/capture/collector.py`).
- **FR-002**: The `verified` field keeps the read-back result, so `state` holds
  `verified` exactly when `verified` holds true.
- **FR-003**: The stored document keeps its `capture_status` field. The history
  page and the comparison page read that field, and the capture page shows a
  partial capture through `partial_reasons`.
- **FR-004**: The status body keeps the fields that the contract names. No field
  is added and no field is removed.
- **FR-005**: The contract text states the poll interval of 3 seconds and the
  words that end the poll.

## Out of scope

- The browser seeds that hold `capture_status` `verified`. Issue #3375 moves
  them to the shipped shape.
- A change to `portal.js`. The page already stops on `verified` and `failed`.

## Success criteria

- **SC-001**: A unit test proves each scenario of user story 2. The old code
  fails the scenarios for `complete` and `partial`.
- **SC-002**: The contract test of the stored status reads a document in the
  shipped shape. It fails on the old code and passes after the repair.
- **SC-003**: A browser journey opens a stored capture in the shipped shape. It
  counts one status request over three poll intervals, and it reads `verified`
  in the state cell. The journey fails on the old code. Each screenshot is read.
- **SC-004**: The browser suite and the portal suites pass.
