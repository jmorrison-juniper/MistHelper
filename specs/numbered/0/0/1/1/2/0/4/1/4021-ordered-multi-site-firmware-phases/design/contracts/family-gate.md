# Contract: Family Gate

This contract defines the seam between the aggregate service and the upgrade portal. The aggregate module defines the seam. The phase watch module supplies the implementation.

## Interface

- **Protocol**: `FamilySettleGate` in `src/operations/execution/firmware/aggregate_upgrade_service.py`.
- **Method**: `settle(run_id, family, targets)`.
- **Inputs**:
  - `run_id`: The operation identifier. It starts with `org-run-`.
  - `family`: One of `gateway`, `switch`, or `ap`.
  - `targets`: The device entries of that family across all selected sites. The list is never empty.
- **Output**: A `FamilyGateResult` with three fields.
  - `state`: One of `settled`, `failed`, or `unknown`.
  - `not_returned`: The count of devices that did not return. The count is zero or more.
  - `note`: One ASCII sentence of at most 25 words.
- **Blocking**: The call blocks until the family settles or the phase limit of 1800 seconds ends.

## Call Rules

- The aggregate service calls the gate only after it sends every child of the family.
- The aggregate service never calls the gate for an empty family.
- The aggregate service never calls the gate for the client family.
- A missing or late result is a stop (FR-005).

## Adapter Mapping

The portal adapter `OrgFamilyGate` in `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` maps the phase outcome as follows.

| Phase outcome state | Family gate state |
| - | - |
| `settled` | `settled` |
| `failed` | `failed` |
| `pending`, `waiting`, `skipped`, or any other value | `unknown` |
| An exception from the phase gate | `unknown` |

The adapter copies `not_returned` and `note` from the phase outcome. The adapter does not change the phase limit.

## Logging

- Before the call, the aggregate service writes one info line with the family name and the target count.
- After the call, the aggregate service writes one debug line with the state and the `not_returned` count.
- The log lines use ASCII text and hold no host, token, or cloud body.
