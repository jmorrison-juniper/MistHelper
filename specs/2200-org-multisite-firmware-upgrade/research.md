# Research: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Method**: A direct read of the live source, the local OpenAPI file, and the
local API pages. No claim below comes from memory.

## 1. The Live Application

### 1.1 What the portal is

The portal is a Flask application under `src/upgrade_portal`. The server renders
Jinja templates. The browser runs one plain JavaScript file.

`src/upgrade_portal/app/factory.py` registers seven blueprints. The names are
`auth`, `select`, `capture`, `upgrade`, `org_upgrade`, `review`, and
`comparison`.

### 1.2 What the portal is not

The repository holds a directory named `ops-portal`. That directory is not the
live portal. The live portal uses no React, no TypeScript, and no bundler.

An earlier version of this specification named files such as
`ops-portal/src/router.tsx` and `ops-portal/src/hooks/useSession.ts`. Those
anchors were wrong. This version names the real files only.

### 1.3 The real route inventory

`src/upgrade_portal/app/routes/select.py` declares these paths:

| Path | Method | View function |
| - | - | - |
| `/select/org` | GET, POST | `org_page`, `choose_org` |
| `/select/mode` | GET, POST | `mode_page`, `choose_mode` |
| `/select/site` | GET, POST | `sites_page`, `choose_sites` |
| `/select/site/<site_id>` | GET | `site_inventory_page` |
| `/api/sites` | GET | `list_sites` |
| `/api/orgs/<org_id>/sites` | GET | `list_sites` |
| `/api/sites/<site_id>/inventory` | GET | `site_inventory` |
| `/api/sites/<site_id>/lock` | POST, DELETE | `take_site_lock`, `free_site_lock` |
| `/api/sites/<site_id>/lock/heartbeat` | POST | `beat_site_lock` |

`src/upgrade_portal/app/routes/upgrade.py` declares these paths:

| Path | Method | View function |
| - | - | - |
| `/runs/<run_id>` | GET | `run_page` |
| `/runs/<run_id>/options` | GET | `options_page` |
| `/runs/<run_id>/confirm` | GET | `confirm_page` |
| `/api/runs` | POST | `create_run` |
| `/api/sites/<site_id>/runs` | POST | `create_run` |
| `/api/runs/<run_id>/options` | POST | `save_options` |
| `/api/runs/<run_id>/versions` | GET | `run_versions` |
| `/api/runs/<run_id>/start` | POST | `start_run` |
| `/api/runs/<run_id>/status` | GET | `run_status` |
| `/api/runs/<run_id>/retry` | POST | `retry_run` |
| `/api/runs/<run_id>/reschedule` | POST | `reschedule_run` |
| `/api/runs/<run_id>/cancel` | POST | `cancel_run` |
| `/api/runs/<run_id>/stop` | POST | `stop_run` |

### 1.4 The session keys

`select.py` stores `selected_org_id`, `selected_upgrade_mode`, and
`selected_site_id` in the signed session. `OperatorSession.selected_site_ids`
holds the multi-site target set on the server.

`select.py` also stores `site_lock_records`. That key holds one grant for each
held site.

### 1.5 The typed confirmation

`upgrade/confirm.html` sets one Jinja variable near line 74:
`{% set upgrade_confirm_word = 'CONFIRM' %}`.

The input carries `data-confirm-word` and `data-confirm-target`. `portal.js`
compares the typed text to the attribute in `applyConfirmGate`. The script holds
no copy of the word.

`upgrade.py` holds the server check. The body field is `confirm`. The refusal
text is "The start control needs the exact text CONFIRM."

The stop control uses the same field with the word `STOP`.

### 1.6 A naming difference in the two lanes

`upgrade/org_confirm.html` names its input field `confirmation`.
`org_upgrade.submit_upgrade` reads the same name. The two agree.

`upgrade/confirm.html` names its input field `confirm`. `upgrade.start_run`
reads the same name. The two also agree.

The two lanes differ from each other. Align them in a later change, and keep one
server helper for both pages.

### 1.7 The site lock

`src/upgrade_portal/runtime/lock.py` holds the rules. `select.py` calls
`acquire_site_lock`, `refresh_site_lock`, and `release_site_lock`.

`upgrade.py` holds `lock_refusal`. That helper blocks a write in two conditions:
- The store state is `unknown`. The answer is HTTP 503 with
  `lock_store_unreachable`.
- Another actor holds the site. The answer is HTTP 409 with `site_locked`.

The site picker shows three lock states. They are `free`, `locked`, and
`unknown`. The template never shows an unreadable site as free.

### 1.8 No hidden retry

`upgrade.py` holds no automatic resubmission. Retry is an operator action at
`POST /api/runs/<run_id>/retry`. That route accepts a failed run only.

The comment near line 2125 states the rule: "A retry reads a failed run. This run
holds another state, so no retry applies to it."

`org_upgrade_service.py` states the same rule in its module docstring: "The
service never retries an uncertain write."

### 1.9 The offline test rule

`tests/conftest.py` opens with this rule: "Unit tests must run offline with zero
API credentials in under 30 seconds."

`tests/contract/upgrade_portal/conftest.py` holds `FakeMistApi` and
`FakeCaptureStorage`. Both have fixtures with the same names in lower case.

`tests/unit/upgrade_portal/test_org_upgrade_service.py` already blocks every
outbound socket. It uses a stand-in HTTP transport for the SDK retry test.

## 2. The Current Multi-Site Work

### 2.1 What exists

`select.py` already serves the mode picker. The constants near line 95 name the
two modes. `NEXT_AFTER_MULTI_SITE` holds `/upgrade/org/options`.

`select/sites.html` already shows a checkbox for each site in multi-site mode.
The form posts the repeated field `site_ids`.

Three templates already exist under `assets/templates/upgrade`. They are
`org_options.html`, `org_confirm.html`, and `org_progress.html`.

`src/upgrade_portal/app/routes/org_upgrade.py` already serves seven routes. The
blueprint name `org_upgrade` appears in `BLUEPRINT_NAMES` of `factory.py`.

| Method and path | View function |
| - | - |
| `GET /upgrade/org/options` | `options_page` |
| `POST /api/org-upgrades/options` | `save_options` |
| `GET /upgrade/org/confirm` | `confirm_page` |
| `POST /api/org-upgrades` | `submit_upgrade` |
| `GET /upgrade/org/jobs/<upgrade_id>` | `job_page` |
| `GET /api/org-upgrades/<upgrade_id>` | `upgrade_status` |
| `POST /api/org-upgrades/<upgrade_id>/cancel` | `cancel_upgrade` |

`src/firmware/org_upgrade_service.py` holds `OrgUpgradeService`,
`OrgUpgradeSession`, and `OrgUpgradeResult`. `src/firmware/org_upgrade_body.py`
holds `OrgUpgradeBody`.

The service seam is `current_app.config["ORG_UPGRADE_SERVICE"]`. The default is
the class `OrgUpgradeService`. A test injects a stand-in through that key.

Two offline suites already pass. They are
`tests/unit/upgrade_portal/test_org_upgrade_service.py` and
`tests/contract/upgrade_portal/test_org_upgrade_routes.py`. They give 180
passing tests.

### 2.2 What is missing

The lane takes no site lock. `active_context` checks the organization, the mode,
and the site set only.

The lane checks no pre-check. A job can start without a baseline, and the
comparison then has nothing to compare.

The lane starts no post-check and opens no comparison.

The lane serves no history path. `listOrgDeviceUpgrades` has no caller in the
portal.

The progress page offers a refresh link. `portal.js` also reloads the page on
the configured poll interval while the job is not final.

The lane writes no run record. It stores the job identifier under the session
key `org_upgrade_last_job`.

The lane writes no audit entry for the cloud write.

`org_confirm.html` uses the shared `data-confirm-word` browser gate. The server
also checks the exact confirmation word.

The options page and `OrgUpgradeBody` accept `big_bang`, `canary`, `rrm`, and
`serial`.

### 2.3 The status summary

`status_summary` reads `targets` inside each site upgrade entry. It sums the
total, upgraded, and failed values across the entries.

### 2.4 A naming difference

`submit_upgrade` and `org_confirm.html` both use the field `confirmation`. They
agree with each other.

`upgrade.py` and `confirm.html` both use the field `confirm`. They also agree.

The two lanes differ. Align them in a later change, and keep one server helper
for both pages.

`cancel_upgrade` reads the same `confirmation` field and compares it to
`CANCEL`.

## 3. The Mist Cloud Contract

### 3.1 The four operations

| Purpose | Operation | HTTP method and path |
| - | - | - |
| Submit | `upgradeOrgDevices` | `POST /api/v1/orgs/{org_id}/devices/upgrade` |
| History | `listOrgDeviceUpgrades` | `GET /api/v1/orgs/{org_id}/devices/upgrade` |
| Status | `getOrgDeviceUpgrade` | `GET /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` |
| Cancel | `cancelOrgDeviceUpgrade` | `POST /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}/cancel` |

The code imports them from `mistapi.api.v1.orgs.devices`. See
`src/firmware/org_upgrade_service.py` and `src/firmware/firmware_manager.py`.

### 3.2 The verified device family

The endpoint description in `documentation/api/utilities/POST_orgs_org_id_devices_upgrade.md`
line 11 reads: "Upgrade Multiple Sites (Only supported for Access Points
upgrades)". The same text appears in `documentation/mist-api-openapi31yaml.yaml`.

Decision: the portal upgrades access points only. The portal does not claim
switch support. The portal does not claim gateway support.

### 3.3 The documented body fields

The schema names these fields:

`all_sites`, `canary_phases`, `device_type`, `download_strategy`,
`max_failure_percentage`, `max_failures`, `models`, `p2p_cluster_size`,
`p2p_parallelism`, `reboot_at`, `reboot_datetime`, `reboot_strategy`,
`rrm_first_batch_percentage`, `rrm_max_batch_percentage`, `rrm_mesh_upgrade`,
`rrm_node_order`, `rrm_slow_ramp`, `rules`, `site_ids`, `snapshot`,
`start_datetime`, `start_time`, `strategy`, and `versions`.

### 3.4 The supported subset

`OrgUpgradeBody` accepts eight fields only:

| Field | Rule |
| - | - |
| `all_sites` | The value must be false. |
| `device_type` | The value must be `ap`. |
| `site_ids` | A nonempty array of unique UUID strings. |
| `versions` | Exactly one record with `firmware_type` `ap` and a version string. |
| `strategy` | One of `big_bang`, `canary`, `rrm`, `serial`. |
| `start_time` | An integer from 0 to 2147483647. |
| `canary_phases` | Increasing percentages that end at 100. The canary strategy only. |
| `max_failure_percentage` | An integer from 0 to 100. Never with `big_bang`. |

The module docstring states the reason: "Other documented fields need a separate
safety review."

### 3.5 The answer shape

The submit answer holds `id` at the top level. It also holds `upgrades`. Each
entry names one site job with `site_id`, `status`, `id`, and `targets`.

`_OrgUpgradeResponse` checks nine target arrays. They are `download_requested`,
`downloaded`, `downloading`, `failed`, `reboot_in_progress`, `rebooted`,
`scheduled`, `skipped`, and `upgraded`.

The cancel answer can hold an empty body. HTTP 200 confirms the request only.

## 4. Verified Conflicts

### Conflict 1: The device family

The description says access points only. The `device_type` enumeration names
`ap`, `gateway`, and `switch`.

**Resolution**: Trust the description. Send `ap` only. `OrgUpgradeBody` raises
`ValueError` for another value.

### Conflict 2: The SDK module path

The four Markdown pages name `mistapi.api.v1.utilities.upgrade`. The code
imports `mistapi.api.v1.orgs.devices`.

**Resolution**: Use `mistapi.api.v1.orgs.devices`. That import runs today in
`org_upgrade_service.py`, `org_ap_upgrader.py`, and `firmware_manager.py`.

### Conflict 3: The answer identifier

The organization answer names the job `id`. `src/firmware/upgrade_service.py`
prefers `upgrade_id` at line 1208, because the session router answer uses that
name.

**Resolution**: Read `id` for an organization job. Keep `upgrade_id` for the
site job of the single-site flow.

### Conflict 4: The peer cluster default

The documentation gives `p2p_cluster_size` a default of 10.
`src/firmware/org_ap_upgrader.py` line 2723 gives it a default of 5.

**Resolution**: Omit the field. The cloud default then applies, and the portal
claims no value.

### Conflict 5: The schedule field

The schema marks `start_time` and `reboot_at` as deprecated. It offers
`start_datetime` and `reboot_datetime` in ISO 8601 form.

**Resolution**: Keep `start_time` for the first release, because
`OrgUpgradeBody` already validates it. Record the move to `start_datetime` as
later work.

### Conflict 6: The body shape

The site endpoint uses `version` and `device_ids`. The organization endpoint
uses `versions` and `site_ids`.

**Resolution**: Use the organization shape. `OrgUpgradeBody` rejects the site
fields as unsupported.

### Conflict 7: The missing fields in the older code

`src/firmware/org_ap_upgrader.py` builds a body without `device_type`. It also
omits `rules`, `snapshot`, `max_failures`, and the RRM fields.

**Resolution**: The portal does not use that module. The portal uses
`OrgUpgradeBody`, which always sets `device_type`.

## 5. Families Out of Scope

### 5.1 SSR routers

SSR upgrades use `mistapi.api.v1.orgs.ssr`. The operations are `upgradeOrgSsrs`,
`cancelOrgSsrUpgrade`, and `listOrgAvailableSsrVersions`. See
`src/firmware/upgrade_service.py` at lines 47, 186, and 190.

SSR devices form a separate family with separate version rules. The first
implementation excludes them.

### 5.2 Mist Edge

The repository holds Mist Edge cluster operations under `mxclusters` and
`mxedges`. It holds no organization upgrade path for Mist Edge in the inspected
upgrade code.

The first implementation excludes Mist Edge.

## 6. Design Decisions

| Decision | Reason |
| - | - |
| A new route module | `upgrade.py` already holds 121 KB. A new lane keeps each file readable. |
| One service class for the cloud | The routes then hold no SDK import and no retry rule. |
| A separate session for a write | The installed SDK retries a POST request after HTTP 429. |
| No summary state in the status answer | A derived state can hide a failed device. |
| A lock for every selected site | Two upgrades at one site can corrupt a comparison. |
| A pre-check gate for every site | A comparison needs a baseline for each site. |
| The organization schema only | The site fields would change the target set. |

## 7. Open Questions

| Question | Effect | Owner |
| - | - | - |
| Does the cloud limit the site count of one job? | The portal may need a batch rule. | The implementation phase |
| Does the job answer hold a device count for each site? | The confirmation page may need a second read. | The implementation phase |
| How long does the cloud keep a finished job? | The history page may need a local record. | The implementation phase |
| Does `start_datetime` replace `start_time` soon? | A later change to `OrgUpgradeBody`. | The implementation phase |

Answer each question with a live read before the code merges. Record the answer
in this file.
