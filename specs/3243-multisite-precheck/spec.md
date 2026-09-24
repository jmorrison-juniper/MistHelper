# Feature Specification: The pre-check captures of a multi-site upgrade

**Issue**: #3243
**Branch**: `feat/3243-multisite-precheck`
**Parent**: #3200, journey finding F-upj-multisite-011

## Problem

The single-site mode needs a saved pre-check capture before an upgrade starts. The confirm page shows the pre-check capture of the run. If the run has no pre-check capture, the page keeps the confirmation field disabled. The start route also refuses with the code `pre_capture_missing`.

The multi-site mode has no pre-check step and no gate. An operator can start a multi-site upgrade with no record of the devices and the clients before the change. After the upgrade, the operator cannot prove what changed at each site.

## Parity with the single-site mode

| Behavior | Single-site mode | Multi-site mode before | Multi-site mode after |
| - | - | - | - |
| The confirm page names the pre-check capture | Yes | No | Yes, one row for each site |
| The confirm page takes a pre-check capture | Yes, on the capture page | No | Yes, on the confirm page |
| The confirmation field stays disabled without a pre-check | Yes | No | Yes |
| The start route refuses without a pre-check | Yes, 409 `pre_capture_missing` | No | Yes, 409 `pre_capture_missing` |
| The operator chooses the data tier | Yes, tier 2 or tier 3 | No | Yes, tier 2 or tier 3 |
| The capture takes the site lock | Yes | No | Yes |
| The record names the pre-check capture | Yes, `pre_capture_id` | No | Yes, `pre_captures` |
| The progress page links the pre-check capture | Yes | No | Yes |

## User stories

### US1: See the pre-check state of each site (P1)

As a NOC engineer, I open the multi-site confirm page. I want to see which sites hold a saved pre-check capture.

1. The page shows the card "Pre-check captures".
2. The card shows one row for each selected site, in the order of the selection.
3. Each row names the site, the pre-check capture, and the data tier.
4. The capture identifier links to the capture page. A site with no pre-check capture shows "None saved".

### US2: Take the missing pre-check captures (P1)

As a NOC engineer, I see a site with no pre-check capture. I want to take the missing captures from the confirm page.

1. I choose the data tier, and I push "Take the missing pre-checks".
2. The page takes one capture at a time, in the order of the selection. Each row shows the state of its capture.
3. When every capture verifies, the page loads again. The rows then show the new captures, and the confirmation field opens.
4. If a capture fails, the page stops. The card shows the cause, and I can push a button again.

### US3: The start route refuses a site with no pre-check capture (P1)

As a NOC engineer, I must not start a multi-site upgrade without a baseline for each site.

1. If one or more sites hold no pre-check capture, the confirmation field stays disabled. The card shows the hint "The portal needs a saved pre-check capture for each site before an upgrade starts. Take the missing pre-checks first."
2. If a request reaches the start route without a pre-check capture for each site, the route refuses with 409 `pre_capture_missing`. The message names each site that holds no pre-check capture.
3. The refusal comes before any site lock and before any cloud write.

### US4: Read the pre-check captures of an operation (P2)

As a NOC engineer, I open the progress page of a multi-site upgrade. I want to find the pre-check capture of each site.

1. The progress page shows the card "Pre-check captures", with one row and one link for each site.
2. An operation from an earlier release holds no list. The card then shows "The portal stored no pre-check capture for this operation."

### US5: Take a new pre-check capture of each site (P3)

As a NOC engineer, I know that a saved pre-check capture is old. I want a new baseline of every site before the upgrade.

1. I push "Take new pre-checks for all sites". The page takes one new capture of each site, in the order of the selection.

## Functional requirements

- **FR-001**: The multi-site confirm page shows the card "Pre-check captures". The card shows one row for each selected site, in the order of the selection. Each row names the site, the capture identifier, and the tier. The identifier links to `/captures/<capture identifier>`. A site with no capture shows "None saved".
- **FR-002**: The portal finds the pre-check capture of a site with the rule of the single-site run. The rule picks the newest verified capture of the site that holds the role `pre` and names no run. The multi-site mode reads the capture through the same seam, `PRECHECK_ADOPTER`.
- **FR-003**: If the portal cannot read the capture store, the site counts as a site with no pre-check capture. The gate fails closed.
- **FR-004**: If one or more sites hold no pre-check capture, the confirmation field stays disabled. The start button stays locked. The card shows the hint of US3.
- **FR-005**: The card holds a tier choice with the values 2 and 3. The default is 2. The card holds two buttons: "Take the missing pre-checks" and "Take new pre-checks for all sites". The first button is disabled when no site misses a capture.
- **FR-006**: A button takes one capture at a time, in the order of the selection. Each row shows the state of its capture: queued, reading, verified, or failed. The page asks for the capture status every 3 seconds, as the capture page does.
- **FR-007**: When every capture of the button verifies, the page loads again. The server then shows the new state of the gate.
- **FR-008**: If one capture fails or the portal refuses it, the page stops the run. The card shows the cause, and the page enables the buttons again.
- **FR-009**: The new endpoint `POST /api/org-upgrades/prechecks/<site_id>` starts one pre-check capture of one site with no run. The body is `{"tier": 2}` or `{"tier": 3}`. The answer is 202 with `capture_id` and `status_url`, the same shape as the capture route.
- **FR-010**: The endpoint refuses in this order:
  1. 400 `org_upgrade_options_invalid` when the browser holds no multi-site selection or no saved options.
  2. 404 `site_not_found` when the site is not in the selection or not in the organization.
  3. 400 `bad_tier` when the tier is not 2 or 3.
  4. 409 `site_locked` when another operator holds the site.
  5. 409 `site_lock_wrong_run` when the lock of the operator names another run.
- **FR-011**: The endpoint takes the site lock for the operator with no run, as the capture page does. The endpoint keeps no copy of the lock in the browser session. A lock copy for each site would make the session cookie larger than a browser keeps. If the operator holds the lock with no run, or with the run of this operation, the endpoint keeps the lock as it is. The endpoint does not renew that lock, because the capture page does not renew a lock with no run. If the lock store does not answer, the capture starts without a lock, as the capture contract permits.
- **FR-012**: The start route `POST /api/org-upgrades` refuses with 409 `pre_capture_missing` when one or more selected sites hold no pre-check capture. The message is "Save a verified pre-check capture for each selected site before you start the upgrade." It adds the names of the sites that hold no capture. The refusal covers the durable plan and the legacy request for access points only.
- **FR-013**: Before the first site lock, the start route stores the list `pre_captures` in the operation record. The list holds one entry for each site with `site_id`, `site_name`, `capture_id`, and `tier`. The route stores a new list while the operation is planned and holds no submission claim. After a claim, the route keeps the stored list.
- **FR-014**: The start route binds a site lock with no run to the operation when the same operator and the same browser hold it. The route renews that lock with the name of the operation. The route still refuses a lock of the same operator that names another run, with 409 `site_lock_wrong_run`.
- **FR-015**: The progress page shows the card "Pre-check captures" with one row for each stored entry. Each row links to the capture page. A record with no list shows the text of US4.
- **FR-016**: The pre-check reader of the capture store returns the fields that the portal uses, and not the whole capture document. The multi-site confirm page reads one pre-check for each site on each load and on each start. A whole document holds every device and every client of a site.
- **FR-017**: The change sends no firmware request. A pre-check capture reads the site and writes one capture document.

## Out of scope

- An age limit for a pre-check capture. The single-site mode has no age limit. Parity comes first.
- A graph edge from the operation to each pre-check capture. The history graph walks runs, and the operation is not a run.
- The post-check capture and the comparison of a multi-site upgrade. Issue #3244 owns them, and it reads the list `pre_captures`.
- A lock beat on the confirm page. The pre-check lock goes quiet after the cooldown, as a lock of an idle capture page does.

## New test identifiers

| Identifier | Element |
| - | - |
| `org-upgrade-prechecks` | The card on the confirm page |
| `org-upgrade-precheck-row-<site>` | The row of one site |
| `org-upgrade-precheck-capture-<site>` | The capture link, or the text "None saved" |
| `org-upgrade-precheck-tier-<site>` | The tier of the stored capture |
| `org-upgrade-precheck-state-<site>` | The state of a capture that the page takes |
| `org-upgrade-precheck-tier` | The tier choice |
| `org-upgrade-precheck-missing` | The button "Take the missing pre-checks" |
| `org-upgrade-precheck-all` | The button "Take new pre-checks for all sites" |
| `org-upgrade-precheck-hint` | The hint of the gate |
| `org-upgrade-precheck-error` | The region that shows a failed capture |
| `org-upgrade-precheck-list` | The card on the progress page |
| `org-upgrade-precheck-link-<site>` | The capture link of one site on the progress page |

## Acceptance criteria

1. A contract test renders the confirm page for two sites. One site holds a capture and one site does not. The page shows both rows, the hint, and a disabled confirmation field.
2. A contract test proves that the start route refuses with 409 `pre_capture_missing` and writes no lock and no child job.
3. A contract test proves each refusal of the endpoint, and one 202 answer that takes the lock with no run.
4. A contract test proves that the start route binds a lock with no run and refuses a lock that names another run.
5. A contract test proves that the operation stores `pre_captures`, and that the progress page links each capture.
6. A parity test proves that both modes refuse a start with no pre-check capture with the same code.
7. A browser journey opens the confirm page, takes the missing pre-check capture, and starts the upgrade. The screenshots show the card before and after the capture.
