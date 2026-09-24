# Feature Specification: The cascade phases of a multi-site upgrade

**Issue**: #3245
**Branch**: `feat/3245-multisite-phase-cascade`
**Parent**: #3200, journey finding F-upj-multisite-014

## Problem

The single-site run page shows four cascade phases: gateways, switches, access points, and wireless clients. For each phase, the page shows the state, the count of devices that returned, and a note. A settle gate decides each phase. The gate reads the reconnect events and the device statistics every 20 seconds, and it stops after 30 minutes.

The multi-site progress page shows no phase. It shows the cloud word of each child job. The cloud word "completed" tells the operator that the cloud sent the firmware. It does not tell the operator that the device rebooted, came back, and runs the new version.

## A correction to the premise of the issue

The issue asks for the single-site phase order in the multi-site mode. The research for this feature found that the single-site mode does not write the phases in order. The driver sends every device family in one step, and then it starts the settle gate for each phase in turn. The single-site cascade therefore watches the return of each family in order. It does not hold a family back until the family before it returns.

This feature gives the multi-site mode the same watch. Issue #3332 records the write order, and it asks the maintainer for a decision. The comment on issue #3245 states the correction.

## User stories

### US1: Watch each phase of a multi-site upgrade (P1)

As a NOC engineer, I start a multi-site upgrade. I want to see each phase settle in the cascade order, as I see it for a single site.

1. After the cloud accepts the operation, the portal watches the gateway phase, then the switch phase, then the access point phase, and then the wireless client phase.
2. For each phase, the portal uses the same settle gate as a single-site run. The gate uses the same 20-second poll, the same 30-minute limit, and the same settle rules.
3. The progress page shows a "Cascade phases" section. The section shows the state, the count of devices that returned, and the note of each phase.
4. The poll updates the section while the watch runs.

### US2: Get the same verdict rules as a single site (P1)

As a NOC engineer, I want a multi-site phase to end with the same verdict that a single-site phase gives for the same devices.

1. If the operation holds no device of a family, the phase shows "skipped".
2. If no access point returned, the wireless client phase fails with the single-site text.
3. If one phase fails, the portal continues to watch the next phases. The first failure names the verdict of the watch.
4. If the cloud refused the child job of a device, the portal does not wait for that device. The phase fails, and its note names the count of devices that the cloud did not accept.

### US3: Wait for a scheduled start (P1)

As a NOC engineer, I schedule a multi-site upgrade for a later time. I do not want a false failure while the upgrade waits for its start.

1. If the operation holds a start time in the future, the watch waits until that time before the first phase.
2. While the watch waits, the section says that the watch waits for the scheduled start.

### US4: Stop and resume the watch (P2)

As a NOC engineer, I cancel a multi-site upgrade, or the portal restarts during the upgrade. I want the watch to stop after a cancel and to continue after a restart.

1. If the operator requests the cancellation, the watch stops before the next poll round. The section says that the watch stopped.
2. If the portal restarts, the next page load or poll starts the watch again. The watch keeps each phase that already ended, and it continues with the first phase that did not end.
3. Only one watch runs for one operation.

### US5: Keep the cloud call budget (P2)

As a NOC engineer, I upgrade many sites. I want the watch to stay inside the cloud call budget of a single-site run.

1. One poll round reads the events of one family and the statistics of one family.
2. If the statistics read needs more than one page, the watch waits longer between two rounds. The watch then stays at or below 360 calls each hour.

## Functional requirements

- **FR-001**: Before the first child job reaches the cloud, the submission reads the uptime and the last report time of each device. The record stores these anchors in `settle_anchors`, keyed by the device address.
- **FR-002**: If the anchor read fails, the submission continues. The record stores a null anchor for each device, and the watch note names the gap. The gate then uses the weaker rule that reads the version alone, as a single-site run does.
- **FR-003**: The record holds `phases` with one entry for each cascade phase, in the order gateways, switches, aps, and clients. Each entry has the single-site shape: name, state, settled, total, settled_at, note, and failures.
- **FR-004**: The record holds `phase_watch` with a state and a note. The states are `not_started`, `waiting_for_start`, `running`, `finished`, `stopped`, and `failed`.
- **FR-005**: After the cloud accepts one or more child jobs, the portal starts one watch thread for the operation.
- **FR-006**: The watch takes the devices of each phase from the child jobs. It does not wait for a device whose child job has the state `planned`, `not_submitted`, or `rejected`.
- **FR-007**: The watch runs the phases in the single-site order, with the single-site rules for an empty family, for the client gate, and for the first failure.
- **FR-008**: The watch builds one `PhaseSettleGate` for each phase. It does not change the settle rules, the poll interval, or the phase limit.
- **FR-009**: The watch copies the stored reboot time of a child job onto each device of that child job, so the gate waits for a scheduled reboot.
- **FR-010**: If the operation holds a future start time, the watch waits for that time before the first phase. The watch reads the stop request during the wait.
- **FR-011**: If `cancellation.requested` is true, the watch stops before the next poll round, and it writes the state `stopped`.
- **FR-012**: Each page load and each status poll makes sure that the watch runs. The call starts no second thread for one operation. It starts no thread for a watch that ended.
- **FR-013**: A watch that starts again keeps each phase that ended, and it continues with the first phase that did not end.
- **FR-014**: Each write of the watch reads the current record and writes through the compare-and-set of the store. A conflict causes a new read and a new try, up to five tries. The watch never removes a field that another writer stored.
- **FR-015**: If the targets of one phase sit at one site, the statistics read asks for that site. If they sit at more than one site, the read asks for the whole organization and for the one family.
- **FR-016**: The watch stretches the wait between two rounds by the page count of the statistics read, so one watch stays at or below 360 calls each hour.
- **FR-017**: The status poll and the progress page show `phases` and `phase_watch`. The page shows the "Cascade phases" section with the single-site cells and headings.
- **FR-018**: The poll of the page does not stop while the watch runs, although the child jobs ended.
- **FR-019**: The "Current phase" line shows the label of the phase that the watch waits for, or "Not reported" when no phase waits.

## Success criteria

- **SC-001**: A rehearsal of two gateways, two switches, and two access points at two sites ends with four phase entries in the single-site order: settled, settled, settled, and settled.
- **SC-002**: A rehearsal with a start time one hour in the future makes no statistics read before the start.
- **SC-003**: A rehearsal with a statistics read of three pages makes no more than 360 calls in one hour.
- **SC-004**: A browser journey shows the "Cascade phases" section, and a screenshot proves each phase cell.
- **SC-005**: Every single-site phase test passes with no change.

## Out of scope

- The renewal of the site locks during the watch. Issue #3333 tracks it.
- A write order that holds a family back. Issue #3332 asks for a decision.
- The start time rule of the single-site gate. Issue #3331 tracks it.
- The captures before and after the upgrade. Issues #3243 and #3244 track them.
- A longer access point limit for a canary job.

## Assumptions

- The capture portal runs one server process. The registry of watch threads lives in that process. The single-site driver uses the same rule.
- The watch reads the cloud only. A restart that starts the watch again cannot send a second firmware write.
- A reconnect event from before a restart does not reach the watch that starts again. The statistics rules still settle each device that returned.
