# Contract: Route Submission

This contract defines the organization upgrade submit route in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. The route calls `_send_aggregate`, which calls the aggregate service submit method.

## Request Flow

1. The route runs the existing request checks. These checks include the reboot anchor and the operator confirmation.
2. The route runs the replay read of the parent record. The read claims nothing and sends no cloud call. A replay or a parent claim conflict returns the existing conflict response.
3. The route starts one background run for the operation identifier. A run that already exists keeps its thread. The route returns the existing job page.
4. The route returns the job page with the existing redirect to `/upgrade/org/jobs/{operation_id}`.
5. The route releases site locks only when the operation reaches a final state. The release rule does not change.

The route makes no family gate wait. The HTTP request returns before the first family gate.

## Background Run

1. The background run claims the parent record for one family send.
2. The background run sends each child of the family in plan order.
3. The background run releases the parent claim after the family send.
4. The background run waits for the family gate and refreshes the wait marker every 20 seconds.
5. A stop writes the stop record and ends the run. A settled gate starts the next family.

## Phase Watch Handoff

- The route starts the phase watch after the background run is registered.
- The phase watch reads the stored family gate results (FR-016).
- The phase watch makes no gate call for a family with a stored result.
- After a stop record, the phase watch marks later families as not submitted.

## Error Mapping

- A synchronous conflict returns the existing conflict response. The response carries the sentence of the conflict. It names no host or token.
- A background fault writes a stop record. The reason code is `process_lost` when the wait marker is stale. Otherwise the fault is logged with its exception type only.
- The operator text of the old single response (research row 86) does not reach the background path. The stop sentences of the stop record contract replace it.

## Status Codes

- The route keeps the existing success and conflict codes.
- The route adds no new status code.
