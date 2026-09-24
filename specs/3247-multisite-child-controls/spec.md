# Feature Specification: Retry, reschedule, and reconciliation for multi-site upgrades

**Issue**: #3247
**Branch**: `feat/3247-multisite-child-controls`
**Parent**: #3200, parity rows P-43, P-44, and P-45

## Problem

The single-site progress page gives the operator three recovery controls:

1. A retry of the devices that failed.
2. A reschedule of a run that has not begun.
3. A reconciliation of a run whose outcome is not certain.

The multi-site progress page gives the operator a cancel control only. If one site of ten fails, the operator must plan all ten sites again. If a child job holds the state `submission_unknown`, the page shows `attention_required`, and the site locks stay held until the lease expires. The operator has no control that reads the devices and settles the child job.

## User stories

### US1: Retry the failed devices (P1)

As a NOC engineer, I read a settled multi-site upgrade in which some devices failed. I want one control that plans a new upgrade for those devices only. I want to read and change the options before I type CONFIRM again.

1. If every child job is settled and one or more devices did not reach the target version, the progress page shows the control "Retry the failed devices". The control names each device.
2. If I use the control, the options page opens. The page names the source operation and lists the retry devices. The device types and the target versions of the earlier plan are filled in. The start time is empty.
3. If I save the options, the new plan holds only the retry devices. The new plan names the source operation.
4. If I choose "Plan every device instead", the options page plans every device of the selected sites.
5. If a child job can still write firmware, the page shows no retry control, and the route refuses a retry.

### US2: Reconcile an uncertain child job (P1)

As a NOC engineer, I read a multi-site upgrade that shows `attention_required` because the outcome of a child job is not known. I want the portal to read the devices and settle the child job when the devices prove the outcome.

1. If a child job holds the state `submission_unknown`, the progress page shows the reconciliation control. The control asks me to type `RECONCILE <operation identifier>`.
2. If every device of the child job runs the target version, and the version before was a different version, the child job moves to `completed`. The page shows the evidence.
3. If a device does not prove the upgrade, the child job keeps its state. The page shows how many devices run the target version, and it tells me to check the Mist dashboard.
4. If every child job is settled after the reconciliation, the portal releases the site locks.

### US3: Reschedule a planned operation (P2)

As a NOC engineer, I read the confirmation page of a multi-site plan. I want to change the start time without a new plan.

1. The confirmation page shows the start time of the plan.
2. If no child job has started, the page shows a form that changes the start time. An empty value starts the upgrade at once after I type CONFIRM.
3. If I give a time in the past, or a time beyond the site lock window, the portal refuses the change and names the control.
4. If the plan holds a reboot delay, the portal computes the reboot time again with the rule of the save.

## Functional requirements

- **FR-001**: A device needs a retry when its version check is not `version_match`, and when one of two facts is true. The device state is `failed`, `rejected`, `not_submitted`, `cancelled`, or `skipped`. Or the version check is `version_mismatch`.
- **FR-002**: The retry control shows only when every child job holds a state in which no firmware write can follow. That set is `completed`, `cancelled`, `failed`, `rejected`, and `not_submitted`.
- **FR-003**: The retry route makes no cloud call and no durable write. It stores the retry plan in the signed browser session, selects the multi-site mode and the retry sites, and opens the options page.
- **FR-004**: The retry plan never enters the saved options of the session. A session with saved options and no operation identifier uses the legacy submission path of access points only.
- **FR-005**: When a retry plan applies, the options page and the save keep only the retry devices. If the save then holds no device, the portal refuses the save and names the device type legend.
- **FR-006**: Each new operation stores the typed options as `plan_options`. A retry operation also stores `retry_of_operation_id`.
- **FR-007**: A change of the organization, the mode, or the site set drops the retry plan. A successful submission also drops the retry plan.
- **FR-008**: The reconciliation control shows for each child job in the state `submission_unknown` or `unknown`. The typed word is `RECONCILE <operation identifier>`.
- **FR-008a**: The operation identifier holds small letters. If the typed word differs from the word in letter case only, the hint tells the operator to copy the capital and small letters of the page. The hint does not ask for capital letters.
- **FR-009**: The reconciliation reads the running version of each device through `listSiteDevicesStats`, as issue #2006 requires. The route reads each site one time.
- **FR-010**: A child job moves to `completed` only when every device runs the target version and the version before differs from the target version. The child job stores the evidence, the time, and a digest of the operator address.
- **FR-011**: The reconciliation needs the deployment write gate, because it changes the outcome of an operation.
- **FR-012**: The reschedule changes a plan only when the operation, every child job, and the parent claim prove that no cloud call started. The change uses one compare-and-set write.
- **FR-013**: The reschedule reads the time with the parser of the options page, and it applies the window rule of the single-site start time.
- **FR-013a**: The reschedule refuses a request that holds no start time field, with the code `org_upgrade_options_invalid`. An empty body and a malformed JSON body hold no field. Only an empty field starts the upgrade at once, so a damaged request never clears a planned start time.
- **FR-014**: The progress poll reloads the page one time when the set of controls changes, so that each control shows its typed word.

## Assumptions

- The retry uses the options page, not a direct submission. The operator reads every option before the typed CONFIRM.
- The reconciliation proves a completion only. It never marks a child job as not submitted, because a running version cannot prove that no cloud job exists.
- The reschedule works before submission only. Mist has no call that moves a submitted job. After submission, the operator cancels the operation and uses the retry.
- The multi-site reschedule uses the date and time control of the multi-site options page. The single-site reschedule uses a duration.

## Out of scope

- The full display of the sites, the phases, and the child plan on the confirmation page (#3222).
- A cancel control for a planned operation (P-42).
- A child job that the running versions cannot prove. That child job keeps the operation open until an operator acts, and it blocks the retry.

## Success criteria

- **SC-001**: A browser test retries a failed switch of a two-site operation and confirms a new operation that holds that switch only.
- **SC-002**: A browser test reconciles two uncertain child jobs. One child job moves to `completed`, and the other child job shows the evidence "0 of 1".
- **SC-003**: A browser test changes the start time of a plan and reads the new time on the confirmation page.
- **SC-004**: The retry and the reschedule make no cloud call. The reconciliation makes one read for each site.
