# Research: A cancel that stops part of the work makes the operation read cancelled

**Issue**: #3371

## Decision 1: Use the word cancelled

- **Decision**: A set of final states that holds `cancelled` and no failure
  maps to `cancelled`.
- **Rationale**: The word `completed` states that every child job did its
  work. After a cancel that stopped one child job, that statement is false.
  The single-site stop uses `stopped` for a stopped run, whatever part of the
  devices upgraded. The multi-site service already uses `cancelled` as the
  match of `stopped`.
- **Alternative**: A new word, such as `partially_completed`. The spec
  rejects it. Every set of final states, the poll rule of the page, the
  history badge, and the operations portal would need a change.

## Decision 2: One helper for the operation and the access point job

- **Decision**: The operation rule and the access point site rule call one
  helper.
- **Rationale**: Both rules held the same test, `== {"cancelled"}`. If only
  the operation rule changes, an access point job that completed at one site
  and stopped at another site still reads `completed`. An operation with only
  that job then still reads `completed`.

## Decision 3: Keep the failure priority

- **Decision**: The helper runs only after the failure rules.
- **Rationale**: `SETTLED_STATE_RULES` puts a failure first. A set of one
  failed child job and one cancelled child job reads `failed`. The operator
  must see the failure first.

## Evidence

- `AggregateUpgradeService._settled_state` returned
  `"cancelled" if states == {"cancelled"} else "completed"`.
- `AggregateUpgradeService._combined_site_status` returned
  `"cancelled" if seen == {"cancelled"} else "completed"`.
- These readers treat both words as final, so their result does not change:
  - `FINAL_OPERATION_STATES` controls the cancel form and the final note.
  - `SETTLED_OPERATION_STATES` and `FINAL_WRITE_STATES` in `org_upgrade.py`
    are also final sets.
  - `ORG_UPGRADE_FINISHED_STATES` in `portal.js` stops the page poll.
- `_operation_is_settled` in `org_upgrade.py` decides the retry and the lock
  release from the child states. It reads the operation word only for a record
  with no child job.
- The org retry reads the device rows only.
- The history list prints the word as a badge.
- The cascade stop rule reads `cancellation.requested`, not the state word.
- The screenshot `ended-after.png` of the #3367 journey shows
  `Status: completed` above the cancel result panel of the same operation.
