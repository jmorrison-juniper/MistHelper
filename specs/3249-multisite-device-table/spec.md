# Feature Specification: Multi-site device table and version check

**Issue**: #3249
**Branch**: `feat/3249-multisite-device-table`
**Status**: Implemented in the pull request that closes #3249.

## Problem

The single-site progress page shows one row for each device. Each row shows the name, the MAC address, the type, and the state. The row also shows the version before, the target version, the version after, the version check, and the failure reason. The page also shows the typed operator address, the Mist account, and the last update time.

The multi-site progress page shows one row for each child job, with counts only. The operator cannot see which device failed. The operator cannot see which version each device runs after the upgrade. The page shows no Mist account and no last update time. The journey harness of #3200 recorded this gap as finding F-upj-multisite-018.

Four facts in the code cause the gap.

1. The template `upgrade/org_progress.html` has no device table.
2. The access point child stores the MAC addresses only. It stores no name, no model, no version before, and no target version.
3. No part of the multi-site path reads the running version of a device after the upgrade.
4. No part of the multi-site path records the Mist account, and no store writes `updated_at` on the operation record.

## User story

As a NOC engineer, I watch a multi-site upgrade. I want to see each device of each site, with its state and its version check. I want the columns of the single-site page. If a device fails, I want to read the reason.

### Acceptance scenarios

1. If an operation holds access points at two sites and one switch, the page shows one row for each device. Each row names its site.
2. If the cloud lists a device as upgraded, the row shows the state `upgraded`. After the portal reads the running version, the row shows the version after and "Version matches".
3. If the cloud lists a device as failed, the row shows the state `failed` and a failure reason.
4. If a device runs a version other than the target version after its child ends, the row shows "Version mismatch".
5. If the cloud refused a child, each device row of that child shows the state `rejected` and the refusal text as the failure reason.
6. The page shows the typed operator address, the Mist account, and the last update time.
7. If the page stays open, the poll repaints each device row and the last update time without a reload.

## Functional requirements

- **FR-001**: The progress page shows one device row for each target of each child, in plan order. A row shows the site, the name, the MAC address, the type, and the state. The row also shows the version before, the target version, the version after, the version check, and the failure reason.
- **FR-002**: The access point child stores one target record for each access point. The record holds the fields that a site child stores. A record from an earlier release holds MAC addresses only. For that record, the row shows the MAC address and the target version from the stored request body. That record names no site, so the portal does not read a running version for it.
- **FR-003**: The device state comes from the target lists of the cloud answer. The priority order is `failed`, `upgraded`, `skipped`, `rebooted`, `reboot_in_progress`, `downloaded`, `downloading`, `download_requested`, and `scheduled`. A device in no list shows `pending` while its child runs. Otherwise the device shows the state of its child.
- **FR-004**: If the cloud lists a device as failed, the failure reason is the child error. If the child has no error, the reason is "The cloud lists this device as failed." A device in no list of a refused or unknown child shows the child error.
- **FR-005**: The version after is the running version from `listSiteDevicesStats`. Issue #2006 requires that source. The portal never shows the configured version of `listSiteDevices`.
- **FR-006**: The version check uses `gate.version_outcome`, the one rule of FR-051. The words are "Version matches", "Version mismatch", and "Awaiting version".
- **FR-007**: The portal reads the running versions of a site only when a device of that site needs a reading. The Read budget section states the rule. The portal reads each site at most one time for each refresh. A read failure changes no child state. A failed read stores no reading, and the final children of that site stay open.
- **FR-008**: The portal stores each reading in the operation record through one compare-and-set write. A second browser tab therefore does not read the same site again.
- **FR-009**: The operation record stores the typed operator address and the Mist account before the first cloud write. The page shows "Not recorded" for a record from an earlier release.
- **FR-010**: The aggregate service writes `updated_at` on each write that changes the record. A poll that changes nothing does not move the time. The page shows the age through `RunStalePolicy`, the rule of the single-site page.
- **FR-011**: The poll answer carries the device rows, the Mist account, the operator address, and the update time. The browser repaints the device table and the age from that answer.

## Read budget

The Mist API allows 5,000 calls each hour for one token, and the operations portal uses the same token. The device table must therefore add few calls.

A device wants a reading when the cloud lists it as failed, upgraded, or skipped. Every device of a child that ended as completed, failed, or cancelled also wants a reading. A device of a refused child wants no reading, because no job ran.

The portal reads a site in three cases.

1. A device wants a reading, and the portal holds no reading for it.
2. The child ended, and a device holds a reading that does not match. The portal reads one final time, then it marks the child as final.
3. The child runs, an upgraded device holds a mismatch or an empty reading, and the portal read that device fewer than two times.

The portal reads each site one time for each refresh, for all children of that site.

A failed read stores no reading. An empty answer also stores no reading, because it proves nothing. The final children of that site stay open, so the next refresh reads the site again. The cost stays small for three reasons.

1. The browser stops the poll when the operation is cancelled, completed, or failed.
2. After the end, only a page load or the Refresh button starts a read.
3. While the operation runs, each poll already reads the status of each child.

## Out of scope

- The phase cascade and the settle gate. Issue #3245 covers them.
- The pre-check capture for each site (#3243), the post-check (#3244), the stop page (#3246), the controls (#3247), and the history (#3248).
- A stale badge. An aggregate state is not a single-site run state, so `RunStalePolicy` never marks the operation stale. The page shows the age only.

## Success criteria

- **SC-001**: The browser test shows one device row for each selected device, with its site and a version check word.
- **SC-002**: A poll of an operation with every child marked final makes no stats read.
- **SC-003**: If each read succeeds, a device that the cloud lists as failed costs at most two reads of its site: the first reading and the final read.
