# Research: A child job that the check proves counts its devices as upgraded

**Issue**: #3457 | **Spec**: [spec.md](spec.md)

## R1. The source of the counts

**Decision**: Change the one function that builds the child counts.

**Evidence**:

- The function `aggregate_summary` in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
  builds each child row and the operation counts.
- The progress page, the status answer, and the cancel answer all read
  `aggregate_summary`.
- In `org_progress.html`, the page paints the operation block and the child
  rows from that summary.
- In `portal.js`, the status poll paints the same fields from the same summary.
- The helper `_aggregate_child_counts` reads the upgraded list and the failed
  list of the stored cloud answer.
- A child job in the state `submission_unknown` stores an empty cloud answer.
  Its lists are therefore empty, and its counts stay 0.

## R2. The record that the check stores

**Evidence**:

- In `src/operations/execution/firmware/aggregate_upgrade_service.py`, the method `_apply_verdict`
  stores each verdict under the key `reconciliation` of the child job.
- A proven verdict sets the status `completed` and clears the error.
- The method changes no count and no cloud answer.
- In `src/interfaces/portals/upgrade_portal/upgrade/org_reconcile.py`, the method `_verdict`
  proves a child job only when each target device runs the target version. No
  device can run that version before the upgrade.

## R3. The options

| Option | Decision | Reason |
| - | - | - |
| A. Write an upgraded list into the stored cloud answer at the check. | Rejected. | The stored answer then holds a list that the cloud never sent. A later reader cannot tell the cloud from the portal. The option also changes the aggregate service. |
| B. Compute the counts from the stored proof when the portal builds the summary. | Chosen. | The stored record does not change. One function feeds the page, the status answer, and the cancel answer. |
| C. Count the devices from the stored running versions. | Rejected. | That rule also counts a device of a child job that the cloud marked failed. The proof already holds the decision. |

## R4. A device that a cloud list names as failed

**Decision**: Count that device as failed.

**Evidence**:

- The device table shows the word of the first cloud list that names a device.
- The list of the failed devices comes first.
- The table therefore shows such a device as failed. The counts follow the
  same rule, so the child row and the device table agree.

## R5. The history page

**Decision**: No change.

**Evidence**:

- `src/interfaces/portals/upgrade_portal/upgrade/org_history.py` and `review/history.html` show
  each operation with its state, its sites, and its time.
- Neither file shows a count of the devices.

## R6. The single-site behavior

**Evidence**:

- In `src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py`, the
  method `_repair_target` sets each proven device to the state `settled`.
- The single-site counts then include each proven device.
- Option B gives the same counts in the multi-site mode.

## R7. The cost of each status answer

**Decision**: Build the device reader only for a proven child job.

**Evidence**:

- The portal builds each status answer again at each poll.
- A check of the proof reads two stored keys only.
- The device reader indexes each cloud list. Only a proven child job needs it.
