# Feature Specification: Multi-site upgrades in the history

**Issue**: #3248
**Branch**: `feat/3248-multisite-history`
**Parent**: #3200, finding F-upj-multisite-017

## Problem

The history page lists the single-site runs. Each row links to the run and to its captures. A multi-site upgrade has no history entry. The only way back to its progress page is the address of the job.

A read-only query of the live store found a second defect. The store keeps each multi-site operation record in the `upgrade_runs` collection, beside the single-site runs. When the history page names no site, `list_runs` also returns the operation records. The Runs table then shows each operation record as a broken single-site row:

1. The row links to `/runs/org-run-...`, and that page cannot show an operation.
2. The bulk cancel box and the bulk retry box can select the row.
3. The row shows no site, no device count, and no start time.

On 2026-09-24, the live store held 71 records in `upgrade_runs`. 3 of these records were operation records.

## User story

As a NOC engineer, I start a multi-site upgrade and close the browser tab. Later, I open the history page. I want to find the upgrade and read its sites, its device types, and its state. Then I want to open its progress page again.

### Acceptance scenarios

1. If I start a multi-site upgrade, the history page shows the upgrade in the section "Multi-site upgrades".
2. The row names the sites, the device types, the state, the typed operator, the Mist account, the start time, and the last update time.
3. If my browser session started the upgrade, the operation identifier links to the progress page of the upgrade.
4. If another browser session started the upgrade, the row shows no link. The row shows the text "Another browser session started this upgrade."
5. If no organization is selected, the section tells me to select an organization. The portal then reads no operation record.
6. If the page names a site, the section lists only the upgrades that include that site.
7. The Runs table shows no multi-site operation record.

## Functional requirements

- **FR-001**: The history page shows the section "Multi-site upgrades" after the Runs section and before the Audit log.
- **FR-002**: Each row shows the operation identifier, the site names, the device types, the typed operator, the Mist account, the state, the start time, and the last update time. If a site has no stored name, the row shows the site identifier. If a value is missing, the row shows "Not recorded".
- **FR-003**: The device types come from the `device_family` value of each child job. The order is access points, switches, gateways, and Session Smart Routers. If the portal does not know a family word, the row shows the stored word.
- **FR-004**: The operation identifier links to `/upgrade/org/jobs/<operation_id>` only when the owner key of the record matches the owner key of the current browser session. The job page refuses the other sessions with `JOB_NOT_OWNED`. A link for another session would only lead to that refusal.
- **FR-005**: The section lists only the operations of the selected organization, because the job page requires the same organization. If no organization is selected, the section reads no record.
- **FR-006**: If the page names a site, the section lists only the operations whose `site_ids` value holds that site.
- **FR-007**: The section lists the newest operations first, by `created_at` and then by `updated_at`. A record with no time sorts last. The section reads no more rows than the page size of the history page.
- **FR-008**: If the database does not answer, the section tells the operator that the portal cannot read the multi-site upgrades. The page does not show an empty list as a fact.
- **FR-009**: `list_runs` excludes each record that holds an `operation_id` value. In `upgrade_runs`, only an operation record holds that field.
- **FR-010**: The aggregate service writes `created_at` in each new operation record. The value is the same time as the first `updated_at` value.
- **FR-011**: The owner key never reaches the template or the browser.

## Out of scope

- The pre-check capture for each site (#3243), the post-check (#3244), the stop page (#3246), and the controls (#3247).
- A bulk cancel or a bulk retry of a multi-site operation.
- A comparison link. A multi-site operation holds no capture pair yet.
- A stale badge. An aggregate state is not a single-site run state, so the section shows the last update time only.
- The site scan of FR-037. Issue #3315 records a separate defect in that scan.

## Success criteria

- **SC-001**: A browser test starts a multi-site upgrade, finds its row in the history, and opens the progress page through the row link.
- **SC-002**: The browser test proves that the Runs table holds no row for the operation.
- **SC-003**: The section costs one database query. The query returns the projected fields and never the whole record.
