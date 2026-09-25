# Feature Specification: A cancel that stops part of the work makes the operation read cancelled

**Issue**: #3371
**Feature Branch**: `fix/3371-mixed-cancel-state`
**Status**: Draft
**Found by**: the browser journey of #3367

## Problem

An operator cancels a running multi-site operation. One child job completed
before the cancel, and the cancel stops another child job. The operation then
reads `completed`.

The status card reads `Status: completed`. The card states "The operation is
final: completed." The history list shows the same success word. An operator
can then report a full upgrade that did not occur.

The service maps each set of final child states that holds no failure to one
word. The word is `cancelled` only when every child job is cancelled. The set
of one `completed` child job and one `cancelled` child job maps to
`completed`.

The access point job has the same rule for its sites. If the job completed at
one site and stopped at another site, the access point job reads `completed`.

The single-site stop sets the state `stopped` for a stopped run. It sets that
state whatever part of the devices upgraded. The multi-site match of `stopped`
is `cancelled`.

## User Story 1 (P1): The operation reads cancelled after a cancel that stopped part of the work

**Acceptance scenarios**:

1. **Given** a running operation with one completed child job and one running
   child job, **When** the operator sends the typed cancel and the next status
   read reports the running child job as `cancelled`, **Then** the operation
   reads `cancelled`.
2. **Given** the operation of scenario 1, **When** the operator reads the
   progress page, **Then** the status card reads `Status: cancelled`, and the
   note reads `The operation is final: cancelled. The portal sends no cancel
   request for it.`
3. **Given** the operation of scenario 1, **When** the operator reads the
   history list, **Then** the state badge of the operation reads `cancelled`.
4. **Given** an operation where every child job completed, **When** the
   portal reads it, **Then** the operation reads `completed`, as before.
5. **Given** an operation where every child job is cancelled, **When** the
   portal reads it, **Then** the operation reads `cancelled`, as before.
6. **Given** an operation with one failed child job and one cancelled child
   job, **When** the portal reads it, **Then** the operation reads `failed`, as
   before.
7. **Given** an operation with one child job that still runs, **When** the
   portal reads it, **Then** the operation reads `running` or `partial`, as
   before.

## User Story 2 (P2): The access point job reads cancelled when a cancel stopped one of its sites

**Acceptance scenarios**:

1. **Given** an access point status answer with no root state, one site in the
   state `completed`, and one site in the state `cancelled`, **When** the
   portal reads the access point job, **Then** the job reads `cancelled`.
2. **Given** an access point status answer with the site states `success` and
   `cancelled`, **When** the portal reads the job, **Then** the job reads
   `cancelled`.
3. **Given** an access point status answer where every site completed,
   **When** the portal reads the job, **Then** the job reads `completed`, as
   before.

## Functional requirements

- **FR-001**: One service helper decides the word for a set of final states
  that holds no failure. If the set holds `cancelled`, the word is
  `cancelled`. If the set holds no `cancelled`, the word is `completed`.
- **FR-002**: The operation rule `_settled_state` and the access point site
  rule `_combined_site_status` both use that helper.
- **FR-003**: The failure rules keep their priority. A failed child job, a
  rejected child job, or an uncertain child job decides the word before the
  helper runs.
- **FR-004**: No reader of the operation state changes. The page poll, the
  cancel form, the lock release, and the retry panel treat `cancelled` and
  `completed` as final states. The history list prints the word only.

## Out of scope

- A new state word, such as `partially_completed`. That word needs a change
  in every set of final states, in the poll rule of the page, and in the
  operations portal.
- The single-site word `stopped`. The multi-site page, the poll, and the
  history list already know the word `cancelled`.
- A child job that a person cancelled in the Mist dashboard also makes the
  operation read `cancelled`. That result is correct, because the operation
  did not do all of its work.

## Success criteria

- **SC-001**: A unit test proves the word for each set of final states in
  user story 1.
- **SC-002**: A unit test proves the path through the cancel and the next
  status read.
- **SC-003**: A unit test proves each site mix of user story 2, and the path
  through a status read of the access point job.
- **SC-004**: A browser journey cancels a seeded operation with one completed
  child job and one running child job. The journey reads the status card, the
  final note, and the history badge. Each screenshot is read.
