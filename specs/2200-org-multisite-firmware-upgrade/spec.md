# Feature Specification: Organization Upgrade Mode for Many Sites

**Feature Branch**: `feat/2200-org-multisite-firmware-upgrade`
**Created**: 2026-09-11
**Last corrected**: 2026-09-11
**Status**: Specified
**Application**: `src/upgrade_portal` (Flask, Jinja, plain JavaScript)

## Correction Notice

An earlier version of this specification described a React application under
`ops-portal/src`. That application is not the live portal. This version
describes the real portal only. Every anchor below names a file that exists.

## Overview

The upgrade portal upgrades one site for each run today. The operator signs in,
picks an organization, picks a site, and captures a pre-check. The operator then
sets the upgrade options, types a confirmation word, and watches the run.

This feature adds a second scope. The operator picks many sites in one
organization. The portal sends one organization job to the Mist cloud. The job
upgrades access points at the selected sites.

The portal keeps the same pages, the same words, and the same safety gates. Only
the scope changes from one site to many sites.

## Live Architecture Facts

The portal is a Flask application. It renders Jinja templates on the server. The
browser runs one plain JavaScript file. The portal uses no React and no
JavaScript build step.

| Concern | Real file |
| - | - |
| Organization, mode, and site pages | `src/upgrade_portal/app/routes/select.py` |
| Run, options, confirm, and progress pages | `src/upgrade_portal/app/routes/upgrade.py` |
| Organization job routes | `src/upgrade_portal/app/routes/org_upgrade.py` |
| Organization picker template | `src/upgrade_portal/app/assets/templates/select/orgs.html` |
| Mode picker template | `src/upgrade_portal/app/assets/templates/select/mode.html` |
| Site picker template | `src/upgrade_portal/app/assets/templates/select/sites.html` |
| Options template | `src/upgrade_portal/app/assets/templates/upgrade/options.html` |
| Confirmation template | `src/upgrade_portal/app/assets/templates/upgrade/confirm.html` |
| Progress template | `src/upgrade_portal/app/assets/templates/upgrade/progress.html` |
| Organization templates | `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`, `org_confirm.html`, `org_progress.html` |
| Browser behavior | `src/upgrade_portal/app/assets/static/js/portal.js` |
| Run record model and status view | `src/upgrade_portal/runtime/runs.py` |
| Service seams in the Flask config | `src/upgrade_portal/app/wiring.py` |
| Firmware plan and submit helpers | `src/firmware/upgrade_service.py` |
| Organization job service | `src/firmware/org_upgrade_service.py` |
| Organization request body rules | `src/firmware/org_upgrade_body.py` |
| Site lock rules | `src/upgrade_portal/runtime/lock.py` |

## Current State

Part of this feature already works. The list below separates the finished work
from the remaining work. Every claim comes from a source read.

The portal already holds these parts:

- `GET /select/mode` and `POST /select/mode` in `select.py`.
- The session key `selected_upgrade_mode` and the server-side site target set.
- Checkbox selection for many sites in `select/sites.html`.
- The route module `src/upgrade_portal/app/routes/org_upgrade.py` with seven
  routes.
- The blueprint name `org_upgrade` in `BLUEPRINT_NAMES` of `factory.py`.
- The three templates `org_options.html`, `org_confirm.html`, and
  `org_progress.html`.
- `OrgUpgradeService` and `OrgUpgradeBody` under `src/firmware`.
- The service seam `current_app.config["ORG_UPGRADE_SERVICE"]`.
- Offline tests in `tests/unit/upgrade_portal/test_org_upgrade_service.py` and
  `tests/contract/upgrade_portal/test_org_upgrade_routes.py`.

The portal does not hold these parts yet:

- A site lock for each selected site.
- A pre-check gate that blocks a job without a baseline.
- A post-check and a comparison for each selected site.
- A job history route that calls `listOrgDeviceUpgrades`.
- A run record for the organization job. The portal stores only the session key
 `org_upgrade_last_job`.
- An audit entry for the organization write.
The progress page reloads on the configured poll interval. The confirmation
field uses the shared browser gate. The status summary totals the target arrays
of all site upgrade entries.

## The Real Flow

The flow below names the real paths. Each row states the actor and the result.

| Step | Path | Handler or template |
| - | - | - |
| 1. Sign in | `/auth/signin` | `routes/auth.py`, `auth/signin.html` |
| 2. Pick the organization | `GET` and `POST /select/org` | `select.org_page`, `select.choose_org` |
| 3. Pick the mode | `GET` and `POST /select/mode` | `select.mode_page`, `select.choose_mode` |
| 4. Pick the target sites | `GET` and `POST /select/site` | `select.sites_page`, `select.choose_sites` |
| 5. Capture the pre-check | `/captures/new?site_id=<site_id>` | `routes/capture.py` |
| 6. Set the options | `GET /upgrade/org/options` | `org_upgrade.options_page` |
| 7. Type the confirmation | `GET /upgrade/org/confirm` | `org_upgrade.confirm_page` |
| 8. Submit the job | `POST /api/org-upgrades` | `org_upgrade.submit_upgrade` |
| 9. Poll the job | `GET /api/org-upgrades/<upgrade_id>` | `org_upgrade.upgrade_status` |
| 10. Capture the post-check | `/api/runs/<run_id>/capture/start` | `routes/capture.py` |
| 11. Compare the two captures | `/compare` and `/api/comparisons` | `routes/review.py` |

The single-site flow keeps its current paths. Those paths are `/select/site/<site_id>`,
`/runs/<run_id>/options`, `/runs/<run_id>/confirm`, and `/runs/<run_id>`.

## Device Family Scope

The Mist organization upgrade endpoint carries this description:
"Upgrade Multiple Sites (Only supported for Access Points upgrades)".

The first implementation therefore upgrades access points only. The portal sets
`device_type` to `ap` and sends one `versions` record with the `ap` firmware
type. `OrgUpgradeBody` rejects any other device type.

The portal does not claim switch support. The portal does not claim gateway
support. See the API conflict table for the reason.

SSR routers and Mist Edge devices form separate families. They use separate Mist
operations. The first implementation excludes both families.

## User Scenarios & Testing

### User Story 1 - Pick the Mode After the Organization (Priority: P1)

An operator signs in and picks an organization. The portal then asks for the
upgrade mode. The operator picks one site or many sites.

**Why this priority**: The mode decides the backend contract. Every later step
depends on the mode.

**Independent test**: A test client posts an organization to `/select/org`. The
answer names `/select/mode`. A second post stores the mode in the session.

**Acceptance scenarios**:

1. **Given** the operator signs in, **When** the operator posts an organization
   to `/select/org`, **Then** the portal answers with the next page
   `/select/mode`.
2. **Given** the operator opens `/select/mode`, **When** the page renders,
   **Then** the page offers `single_site` and `multi_site`.
3. **Given** the operator posts `multi_site`, **When** the portal stores the
   mode, **Then** the session key `selected_upgrade_mode` holds `multi_site`.
4. **Given** the operator posts an unknown mode, **When** the portal reads the
   body, **Then** the portal refuses the value and keeps the previous mode.

### User Story 2 - Select Many Sites in One Organization (Priority: P1)

The operator opens the site picker in multi-site mode. The picker shows a
checkbox for each site. The operator picks a subset and continues.

**Why this priority**: The site set defines the job. The portal cannot build a
request without it.

**Independent test**: A test fixture supplies an organization with twenty sites.
The client posts three site identifiers. The operator record holds those three
identifiers in order.

**Acceptance scenarios**:

1. **Given** the mode is `multi_site`, **When** the operator opens
   `/select/site`, **Then** each row shows a checkbox instead of an open link.
2. **Given** the operator picks three sites, **When** the operator posts the
   form, **Then** `OperatorSession.selected_site_ids` holds the three
   identifiers.
3. **Given** the operator picks no site, **When** the operator posts the form,
   **Then** the portal refuses the post and names the empty selection.
4. **Given** the operator picks the same site twice, **When** the portal reads
   the body, **Then** the portal refuses the duplicate selection.
5. **Given** the lock store does not answer, **When** the page renders, **Then**
   each affected row shows the lock state `Unknown`.

### User Story 3 - Capture a Pre-Check for Each Site (Priority: P1)

The operator captures a pre-check for each selected site. The portal blocks the
confirmation page until every selected site holds a verified pre-check.

**Why this priority**: The comparison needs a baseline. A job without a baseline
gives the operator no proof of a safe result.

**Independent test**: A fake capture store returns a verified capture for two of
three sites. The confirmation page then refuses the submission and names the
third site.

**Acceptance scenarios**:

1. **Given** the operator selects three sites, **When** the options page
   renders, **Then** the page shows the pre-check state of each site.
2. **Given** one site holds no verified pre-check, **When** the operator opens
   the confirmation page, **Then** the portal disables the confirmation input.
3. **Given** every site holds a verified pre-check, **When** the operator opens
   the confirmation page, **Then** the portal enables the confirmation input.
4. **Given** a capture reports a partial result, **When** the page renders,
   **Then** the page names the missing sections.

### User Story 4 - Set the Organization Upgrade Options (Priority: P1)

The operator sets the firmware version, the strategy, and the schedule. The
portal validates the values before the confirmation step.

**Why this priority**: The Mist cloud rejects an invalid body. Early validation
gives the operator a clear message instead of a cloud error.

**Independent test**: A unit test sends each invalid option to `OrgUpgradeBody`.
Each call raises `ValueError` with a plain message.

**Acceptance scenarios**:

1. **Given** the operator opens `/upgrade/org/options`, **When** the page
   renders, **Then** the page lists every selected site with a device count.
2. **Given** the operator sets the strategy `canary`, **When** the operator
   sends phases that do not end at 100, **Then** the portal refuses the value.
3. **Given** the operator sets the strategy `big_bang`, **When** the operator
   sends a maximum failure percentage, **Then** the portal refuses the
   combination.
4. **Given** the operator sends an empty firmware version, **When** the portal
   validates the body, **Then** the portal refuses the value.
5. **Given** the operator sends a valid body, **When** the portal stores it,
   **Then** the portal redirects to `/upgrade/org/confirm`.

### User Story 5 - Confirm With a Typed Word (Priority: P1)

The confirmation page shows the scope and the risk. The operator types the word
`CONFIRM`. The portal then enables the submit control.

**Why this priority**: An organization job can interrupt service at many sites.
The typed word proves operator intent.

**Independent test**: A test posts the submit request without the word. The
portal refuses the request and sends no cloud call.

**Acceptance scenarios**:

1. **Given** the confirmation page renders, **When** the operator reads it,
   **Then** the page names the organization, the site count, and the device
   count.
2. **Given** the operator types `confirm` in lower case, **When** the gate runs,
   **Then** the submit control stays disabled.
3. **Given** the operator types `CONFIRM`, **When** the gate runs, **Then** the
   portal enables the submit control.
4. **Given** a request arrives without the exact word, **When** the route reads
   the body, **Then** the route answers HTTP 400 and calls no Mist operation.
5. **Given** the operator leaves the page, **When** the operator returns,
   **Then** the page clears the input and disables the control again.

### User Story 6 - Submit One Organization Job (Priority: P1)

The portal calls `upgradeOrgDevices` one time. The portal stores the returned
job identifier. The portal never repeats an uncertain write.

**Why this priority**: A repeated write can start a second upgrade. A second
upgrade doubles the risk to the network.

**Independent test**: A stand-in SDK records each call. The test proves one call
for one submission, even after a transport error.

**Acceptance scenarios**:

1. **Given** a valid body, **When** the route submits the job, **Then** the
   portal calls `upgradeOrgDevices` exactly one time.
2. **Given** the session permits SDK retries, **When** the service checks the
   session, **Then** the service refuses the write.
3. **Given** the cloud answers HTTP 200 with a job identifier, **When** the
   portal reads the answer, **Then** the portal stores the identifier.
4. **Given** the cloud answers HTTP 200 with a malformed body, **When** the
   portal reads the answer, **Then** the portal records an error and no job.
5. **Given** the transport raises an error, **When** the route handles it,
   **Then** the route reports an uncertain result and starts no second write.

### User Story 7 - Watch the Job and Cancel It (Priority: P2)

The progress page shows the job state and the state of each site entry. The
operator can request a cancellation.

**Why this priority**: The operator needs a live view and one stop control. The
view must not hide a failed device.

**Independent test**: A fake service returns a job with three site entries. The
page renders one row for each entry.

**Acceptance scenarios**:

1. **Given** a stored job identifier, **When** the browser polls the status
   path, **Then** the answer holds the job state and the site entries.
2. **Given** the job reports failed devices, **When** the page renders, **Then**
   the page counts the failed devices and names them.
3. **Given** the operator requests a cancellation, **When** the portal calls
   `cancelOrgDeviceUpgrade`, **Then** the portal reports a best effort result.
4. **Given** the cloud answers the cancellation with an empty body, **When** the
   portal reads the answer, **Then** the portal does not claim a rollback.
5. **Given** the cloud does not answer, **When** the poll fails, **Then** the
   page keeps the last known state and names the failure.

### User Story 8 - Capture the Post-Check and Compare (Priority: P2)

The portal captures a post-check for each site after the job settles. The
operator opens a comparison for each site.

**Why this priority**: The comparison proves the outcome. A green job state
alone does not prove a healthy site.

**Independent test**: A fake comparison service returns a difference set for one
site. The review page lists that difference set.

**Acceptance scenarios**:

1. **Given** the job reaches a final state, **When** the portal starts the
   post-check, **Then** the portal captures each selected site.
2. **Given** both captures exist for one site, **When** the operator opens the
   comparison, **Then** the page shows the difference set.
3. **Given** one post-check fails, **When** the review page renders, **Then**
   the page names that site and keeps the other comparisons.
4. **Given** the operator exports a comparison, **When** the export runs,
   **Then** the file holds both capture identifiers.

### User Story 9 - Hold a Lock for Every Selected Site (Priority: P2)

The portal holds a site lock for each selected site. The portal refuses the
submission when another operator holds one of those sites.

**Why this priority**: Two upgrades at one site can corrupt a comparison. The
lock prevents that overlap.

**Independent test**: A fake lock store reports one locked site. The submit
route then answers HTTP 409 and names the holder.

**Acceptance scenarios**:

1. **Given** the operator continues from the site picker, **When** the portal
   requests the locks, **Then** the portal requests one lock for each site.
2. **Given** another operator holds one site, **When** the portal reads the
   locks, **Then** the portal answers HTTP 409 and names the holder.
3. **Given** the lock store does not answer, **When** the portal reads the
   locks, **Then** the portal answers HTTP 503 and refuses the write.
4. **Given** the job reaches a final state, **When** the portal finishes,
   **Then** the portal releases every lock that it holds.
5. **Given** the browser stops the heartbeat, **When** a lock expires, **Then**
   the portal marks the run as unsafe to continue.

### Edge Cases

- The operator changes the mode after a site selection. The portal clears the
  stale site set.
- The operator selects one site in multi-site mode. The portal keeps the
  organization contract and does not switch to the site contract.
- The organization holds no site. The site picker shows an empty state.
- The cloud returns a job identifier that differs from the requested one. The
  portal records an error and does not replace the known identity.
- The firmware version does not exist for a model. The cloud reports the failure
  for each device, and the portal shows the failed list.
- The browser loses the session during a poll. The poll receives HTTP 401 and
  the page stops.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST ask for the upgrade mode after the organization
  choice and before the site choice.
- **FR-002**: The portal MUST accept the two modes `single_site` and
  `multi_site` only.
- **FR-003**: The portal MUST store the mode in the signed browser session under
  `selected_upgrade_mode`.
- **FR-004**: The portal MUST store the site identifiers in
  `OperatorSession.selected_site_ids`.
- **FR-005**: The portal MUST clear the server-side site set when the operator
  changes the organization or the mode.
- **FR-006**: The portal MUST keep the single-site flow and its current paths
  without a change.
- **FR-007**: The portal MUST serve `/upgrade/org/options` with the template
  `upgrade/org_options.html`.
- **FR-008**: The portal MUST serve `/upgrade/org/confirm` with the template
  `upgrade/org_confirm.html`.
- **FR-009**: The portal MUST serve `/upgrade/org/jobs/<upgrade_id>` with the
  template `upgrade/org_progress.html`.
- **FR-010**: The portal MUST validate the request body with `OrgUpgradeBody`
  before the cloud write.
- **FR-011**: The portal MUST call `upgradeOrgDevices` for a submission.
- **FR-012**: The portal MUST call `getOrgDeviceUpgrade` for a status read.
- **FR-013**: The portal MUST call `listOrgDeviceUpgrades` for the job history of
  one organization.
- **FR-014**: The portal MUST call `cancelOrgDeviceUpgrade` for a cancellation.
- **FR-015**: The portal MUST set `device_type` to `ap` for every organization
  job.
- **FR-016**: The portal MUST set `all_sites` to false and MUST name each site
  identifier.
- **FR-017**: The portal MUST show the pre-check state of each selected site on
  the options page.
- **FR-018**: The portal MUST refuse the submission when a selected site holds
  no verified pre-check.
- **FR-019**: The portal MUST show the organization name, the site count, and
  the device count on the confirmation page.
- **FR-020**: The portal MUST require the exact text `CONFIRM` before a
  submission.
- **FR-021**: The portal MUST render the job state and every site entry on the
  progress page.
- **FR-022**: The portal MUST report the failed device list without a derived
  summary state.
- **FR-023**: The portal MUST start a post-check for each selected site after
  the job reaches a final state.
- **FR-024**: The portal MUST offer a comparison of the pre-check and the
  post-check for each site.
- **FR-025**: The portal MUST hold one site lock for each selected site during
  the job.
- **FR-026**: The portal MUST release every lock when the run ends.
- **FR-027**: The portal MUST record the mode, the organization, the site set,
  and the job identifier in the run record.
- **FR-028**: The portal MUST write an audit entry for every organization write.

### Safety Requirements

- **SR-001**: The portal MUST NOT retry an upgrade write after an uncertain
  answer.
- **SR-002**: The portal MUST use a session with SDK retries disabled for every
  write.
- **SR-003**: The portal MUST refuse a write when the transport permits
  retries.
- **SR-004**: The portal MUST NOT treat HTTP 200 as proof of a completed
  upgrade.
- **SR-005**: The portal MUST NOT claim that a cancellation reverses a completed
  upgrade.
- **SR-006**: The portal MUST refuse a write when the lock store does not
  answer.
- **SR-007**: The portal MUST refuse a write when another operator holds a
  selected site.
- **SR-008**: The portal MUST redact the API token in every log line and every
  error message.
- **SR-009**: The portal MUST show a warning that names the exact consequence
  before the submission.
- **SR-010**: The portal MUST record an error instead of an empty job when the
  cloud sends a malformed answer.

### API Requirements

- **API-001**: The portal MUST use `mistapi.api.v1.orgs.devices` for every
  organization upgrade operation.
- **API-002**: The portal MUST send the body fields that `OrgUpgradeBody`
  supports and no other field.
- **API-003**: The portal MUST keep the site operations of the single-site flow
  without a change.
- **API-004**: The portal MUST NOT call the Mist HTTP endpoints directly when a
  `mistapi` operation exists.
- **API-005**: The portal MUST surface a cloud error with the same error
  envelope that the other routes use.
- **API-006**: The portal MUST read the job identifier from the `id` field of
  the answer.

### UX Requirements

- **UX-001**: The organization pages MUST use the classes `portal-card`,
  `portal-table`, and `portal-button` from `portal.css`.
- **UX-002**: The mode picker MUST use the same bubble control group as the
  other option groups.
- **UX-003**: The pages MUST name the lock state in words and not by color
  alone.
- **UX-004**: The pages MUST carry a `data-testid` attribute on every control
  that a test drives.
- **UX-005**: The portal MUST NOT add a second color system for the
  organization pages.
- **UX-006**: The confirmation page MUST show the danger style that the
  single-site page uses.

### Test Requirements

- **TR-001**: Every unit test and contract test MUST run offline.
- **TR-002**: The tests MUST use the socket block in `tests/conftest.py`.
- **TR-003**: The tests MUST use a stand-in SDK instead of a live session.
- **TR-004**: A test MUST prove one cloud write for one submission.
- **TR-005**: A test MUST prove that a refused body starts no cloud call.
- **TR-006**: A test MUST prove that the route refuses a write without the exact
  confirmation word.
- **TR-007**: A test MUST prove that a locked site blocks the submission.

## Key Entities

- **UpgradeMode**: the text `single_site` or `multi_site` in the browser
  session.
- **OrganizationChoice**: the organization identifier under `selected_org_id`.
- **SiteSelection**: the ordered site identifiers in `OperatorSession.selected_site_ids`.
- **OrgUpgradeBody**: the validated request body for the cloud write.
- **OrgUpgradeResult**: the outcome record with the organization, the job
  identifier, the HTTP status, the data, and the error.
- **RunRecord**: the stored run document in the `upgrade_runs` collection.
- **CaptureRecord**: the pre-check document or the post-check document of one
  site.
- **SiteLockRecord**: the lock grant under the session key `site_lock_records`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The operator reaches `/upgrade/org/options` from `/select/site`
  without an HTTP 404 answer.
- **SC-002**: The single-site tests pass without a change.
- **SC-003**: A submission produces exactly one call to `upgradeOrgDevices`.
- **SC-004**: A submission without the word `CONFIRM` produces no cloud call.
- **SC-005**: The progress page shows one row for each site entry of the job.
- **SC-006**: The review page opens a comparison for each selected site.
- **SC-007**: Every new test runs offline in under 30 seconds.
- **SC-008**: Every changed Markdown file scores 80 or more with the STE linter.

## Assumptions

- **A-001**: The signed browser session already carries the organization and the
  operator identity.
- **A-002**: The operator holds the privilege to write firmware in the chosen
  organization.
- **A-003**: The lock store and the capture store are reachable during a run.
- **A-004**: The selected sites hold access points that accept the chosen
  firmware.
- **A-005**: The Mist cloud keeps the organization job record for a later read.

## Risks

### Risk 1: A repeated write starts a second upgrade

The SDK retries a POST request after HTTP 429 by default. A retry can start a
second organization job.

**Countermeasure**: `OrgUpgradeSession` sets `_MAX_429_RETRIES` to zero.
`OrgUpgradeService._check_write_session` refuses a session that permits retries.
The transport adapter must also permit no retry.

### Risk 2: The documentation claims more device families than the endpoint verifies

The endpoint description names access points only. The schema enumeration also
names switches and gateways.

**Countermeasure**: The portal sends `device_type` as `ap` only. `OrgUpgradeBody`
raises `ValueError` for any other value. A later change needs a separate safety
review.

### Risk 3: An empty job looks like a success

A malformed answer with HTTP 200 can produce a record with no target.

**Countermeasure**: `_OrgUpgradeResponse.normalize` validates the answer. It
records an error instead of an empty job.

### Risk 4: A lock gap permits two upgrades at one site

An operator can select a site that another operator already holds.

**Countermeasure**: The portal reads the lock of every selected site before the
write. A locked site or an unreachable store blocks the write.

### Risk 5: A partial pre-check hides a later regression

A capture with missing sections gives a weak baseline.

**Countermeasure**: The options page shows the pre-check state of each site. The
confirmation page blocks the write until every site holds a verified pre-check.

### Risk 6: A cancellation gives false comfort

The cancel operation stops scheduled devices only.

**Countermeasure**: The pages state that a cancellation does not restore an
upgraded device. The portal reports a best effort result.

### Risk 7: A large site set exceeds the operator attention

One job can touch hundreds of access points.

**Countermeasure**: The confirmation page names the site count and the device
count. The page shows a warning with the exact consequence.

## Verified API Conflicts

The table records each conflict between the documentation, the schema, and the
code. Each row states the decision for this feature.

| Conflict | Source A | Source B | Decision |
| - | - | - | - |
| Device families | The description says "Only supported for Access Points upgrades" | The `device_type` enumeration names `ap`, `gateway`, and `switch` | Send `ap` only. Do not claim switch support or gateway support. |
| SDK module | The Markdown pages name `mistapi.api.v1.utilities.upgrade` | The code imports `mistapi.api.v1.orgs.devices` | Use `mistapi.api.v1.orgs.devices`, because the code path runs today. |
| Answer identifier | The organization answer names `id` | `src/firmware/upgrade_service.py` prefers `upgrade_id` | Read `id` for the organization job. Keep `upgrade_id` for the site job. |
| Peer cluster size | The documentation gives the default 10 | `src/firmware/org_ap_upgrader.py` gives the default 5 | Omit the field. The cloud default then applies. |
| Schedule field | The schema marks `start_time` as deprecated | `OrgUpgradeBody` accepts `start_time` as an epoch integer | Keep `start_time` for now. Record `start_datetime` as later work. |
| Body shape | The site schema uses `version` and `device_ids` | The organization schema uses `versions` and `site_ids` | Use the organization schema. Never send the site fields. |

## Non-Goals

- **NG-001**: Do not build a React application or any JavaScript build step.
- **NG-002**: Do not replace the single-site flow.
- **NG-003**: Do not upgrade switches with the organization endpoint.
- **NG-004**: Do not upgrade gateways with the organization endpoint.
- **NG-005**: Do not add SSR upgrades in the first implementation.
- **NG-006**: Do not add Mist Edge upgrades in the first implementation.
- **NG-007**: Do not use the `all_sites` shortcut.
- **NG-008**: Do not add an automatic retry for any write.
- **NG-009**: Do not add a new color system or a second design language.
- **NG-010**: Do not call the Mist HTTP API without the `mistapi` SDK.

## Implementation Anchors

- `src/upgrade_portal/app/routes/select.py`
- `src/upgrade_portal/app/routes/upgrade.py`
- `src/upgrade_portal/app/routes/org_upgrade.py`
- `src/upgrade_portal/app/routes/capture.py`
- `src/upgrade_portal/app/routes/review.py`
- `src/upgrade_portal/app/factory.py`
- `src/upgrade_portal/app/assets/templates/select/orgs.html`
- `src/upgrade_portal/app/assets/templates/select/mode.html`
- `src/upgrade_portal/app/assets/templates/select/sites.html`
- `src/upgrade_portal/app/assets/templates/upgrade/options.html`
- `src/upgrade_portal/app/assets/templates/upgrade/confirm.html`
- `src/upgrade_portal/app/assets/templates/upgrade/progress.html`
- `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`
- `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html`
- `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html`
- `src/upgrade_portal/app/assets/static/js/portal.js`
- `src/upgrade_portal/app/wiring.py`
- `src/upgrade_portal/runtime/runs.py`
- `src/upgrade_portal/runtime/lock.py`
- `src/firmware/upgrade_service.py`
- `src/firmware/org_upgrade_service.py`
- `src/firmware/org_upgrade_body.py`

## Related Documents

| Document | Purpose |
| - | - |
| `plan.md` | The phases and the service seams |
| `research.md` | The verified cloud contract |
| `data-model.md` | The entities and the states |
| `contracts/api-contract.md` | The HTTP paths and the SDK calls |
| `contracts/ui-contract.md` | The templates and the test identifiers |
| `tasks.md` | The ordered work |
| `checklists/requirements.md` | The grade of the result |
