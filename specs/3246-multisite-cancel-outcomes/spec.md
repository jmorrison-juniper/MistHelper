# Feature Specification: The cancellation result of a multi-site upgrade

**Issue**: #3246
**Branch**: `feat/3246-multisite-cancel-outcomes`
**Parent**: #3200, journey finding F-upj-multisite-015

## Problem

The single-site run page has a stop control. After a stop, the page shows three lists:

1. The devices that the stop cancelled.
2. The devices that still write firmware.
3. The devices that have no cancel path.

The multi-site progress page has one cancellation form. After a cancel, each child job shows one text cell. The cell joins the words of the result on one line. The access point child job of the organization shows the status word only, because the service stores no device list for it.

An operator must know which device still writes firmware. A switch that loses power during a write does not start again. The multi-site page does not give that fact for each device.

## User stories

### US1: Read the result of a cancel for each device (P1)

As a NOC engineer, I cancel a multi-site upgrade. I want to read, for each child job, which devices stopped, which devices can still write firmware, and which devices have no cancel path.

1. If a child job holds a cancellation result, the progress page shows a "Cancellation result" panel.
2. The panel shows one section for each child job that holds a result, in the order of the plan.
3. Each section names the site and the device type. It shows the result word and the message of the result.
4. Each section shows three headed lists with one MAC address on each line. The headings and the empty texts are the same as the single-site stop.
5. If I load the page again, the panel shows the same result.

### US2: Sort the access points of the organization child job (P1)

As a NOC engineer, I cancel a multi-site upgrade that holds access points. I want the access points in the same three lists as the switches and the gateways.

1. If the cloud accepts the cancel, each access point that the last status read names in `reboot_in_progress` goes to the writing list. Each other access point goes to the cancelled list.
2. If the portal cannot read the lists of a site, each access point of the child job goes to the writing list. The message says that the portal cannot tell which device writes firmware.
3. If the cloud refuses the cancel, each access point goes to the writing list. The message keeps the error text of the cloud answer.

### US3: Read the risk before the cancel (P2)

As a NOC engineer, I read the cancellation form before I type CANCEL. I want the same Caution text as the single-site stop.

1. The form shows a Caution text. The text says that a device that writes firmware finishes the write, and that each site can hold two firmware versions after the cancel.

### US4: See a cancel from another browser tab (P3)

As a NOC engineer, I keep the progress page open. Another tab cancels the operation. I want my page to show the panel.

1. If the set of cancellation results changes, the poll loads the page again. The panel then shows the new result.

## Functional requirements

- **FR-001**: The progress page of an aggregate operation shows the panel "Cancellation result" when one or more child jobs hold a cancellation result. The page shows no panel when no child job holds a result.
- **FR-002**: The panel shows one section for each child job that holds a result, in the order of the plan. The section names the site, or the text "Multiple sites" for a job that serves more than one site without a name. The section names the device type.
- **FR-003**: Each section shows the result word, the message, and three lists: "Cancelled", "Writing firmware", and "No cancel available". Each list shows one MAC address on each line.
- **FR-004**: An empty list shows the empty text of the single-site stop. The texts are "The portal canceled no device.", "No device writes firmware.", and "Every device has a cancel path."
- **FR-005**: If a result holds all three lists, the section shows the stored lists.
- **FR-006**: If a result holds no lists, and the child job never reached the cloud, the three lists stay empty. The section adds the note "No upgrade of this child job exists in the cloud, so no device of it writes firmware." The record proves that a child job never reached the cloud in three cases.
  - The state of the child job is `not_submitted`.
  - The state of the child job is `planned`, and the operation holds no live submission claim. A live claim can still send the child job. Issue #3327 tracks that race.
  - The state of the child job is `rejected`, and the cloud answered with a status from 400 through 499. A server error or a damaged success can hide a cloud job.
- **FR-007**: If a result holds no lists, and the child job can have reached the cloud, each device of the child job goes to the writing list. The section adds the note "The portal cannot tell which devices of this child job stopped. Treat each device as a device that can still write firmware." This rule covers the results `cancel_claimed`, `cancel_unknown`, `unknown`, and `unavailable`, and a result from an earlier release.
- **FR-008**: The panel never shows "No device writes firmware." for a child job unless a status read proves it, or the child job never reached the cloud.
- **FR-009**: The service sorts the access points of the organization child job after the cloud accepts the cancel. It reads `reboot_in_progress` from each site entry of `upgrades` and `site_upgrades` in the last stored status read. It also reads the root of the answer when the root holds `targets` or `reboot_in_progress`.
- **FR-010**: If a site of the child job has no readable site entry, or a list has a shape that the portal cannot read, the service treats every access point as a device that can still write firmware. The message is the doubt sentence of the single-site stop.
- **FR-011**: If the cloud answer of the cancel holds an error, the service lists each access point as a device that can still write firmware. The message keeps the error text, and it adds one sentence that tells the operator to treat each access point as a device that can still write firmware.
- **FR-012**: The single-site stop and the organization child job use one sort rule. The rule moves into the public function `upgrade_service.sort_cancel`. The reader of the reboot list moves into the public function `upgrade_service.reboot_macs`. No wrapper stays behind.
- **FR-013**: The cancellation form shows the Caution text: "Caution: the cancellation stops each upgrade that waits to start. A device that already writes firmware finishes the write. Each site can hold two firmware versions after the cancellation. The cancellation does not restore a device that already upgraded."
- **FR-014**: The poll signature of the progress page adds the part `cancel=<child identifier>:<result word>` for each result. The poll loads the page again when the part changes.
- **FR-015**: The status answer of the poll adds the field `cancel_outcomes`. The field holds the same sections as the panel.
- **FR-016**: The change sends no new cloud call. The cancel still sends at most one cancel call for each child job.

## Out of scope

- The final-state guard of the cancel route. Issue #3225 owns it.
- The text cell of the child table. The cell keeps its current words, so the existing poll test stays valid.
- The legacy organization job of access points only. That page holds no durable record.

## New test identifiers

| Identifier | Element |
| - | - |
| `org-cancel-outcome` | The panel |
| `org-cancel-outcome-<child identifier>` | The section of one child job |
| `org-cancel-outcome-status-<child identifier>` | The result word |
| `org-cancel-outcome-message-<child identifier>` | The message |
| `org-cancel-outcome-note-<child identifier>` | The note of a derived list |
| `org-cancel-outcome-cancelled-<child identifier>` | The list of cancelled devices |
| `org-cancel-outcome-writing-<child identifier>` | The list of devices that can still write firmware |
| `org-cancel-outcome-no-cancel-<child identifier>` | The list of devices with no cancel path |
| `org-upgrade-cancel-caution` | The Caution text of the form |

## Acceptance criteria

1. A contract test renders a stored operation with four child jobs. The jobs hold a stored result, a claimed result, an unavailable result of a rejected job, and no result. The page shows three sections with the correct lists and notes.
2. A unit test proves each branch of the access point sort: accepted with a reboot list, accepted with a site that has no list, a damaged list, and a refused cancel.
3. The existing single-site stop tests pass without a change.
4. A browser journey cancels a seeded operation. The screenshot shows one access point in the writing list and one access point in the cancelled list. A reload shows the same panel.
