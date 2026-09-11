# API Contract: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Scope**: The portal HTTP paths and the Mist cloud operations
**Device family**: Access points only

## 1. The Mist Cloud Operations

The portal reaches the cloud through the `mistapi` SDK. The portal never calls
the Mist HTTP endpoints directly.

| Purpose | SDK operation | HTTP method and path |
| - | - | - |
| Submit a job | `upgradeOrgDevices` | `POST /api/v1/orgs/{org_id}/devices/upgrade` |
| List the jobs | `listOrgDeviceUpgrades` | `GET /api/v1/orgs/{org_id}/devices/upgrade` |
| Read one job | `getOrgDeviceUpgrade` | `GET /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` |
| Cancel one job | `cancelOrgDeviceUpgrade` | `POST /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}/cancel` |

The import path is `mistapi.api.v1.orgs.devices`.

The local Markdown pages name `mistapi.api.v1.utilities.upgrade`. That path is
wrong for this repository. Use `mistapi.api.v1.orgs.devices`, because the live
code uses it.

## 2. The Device Family Rule

The endpoint description reads: "Upgrade Multiple Sites (Only supported for
Access Points upgrades)".

The portal therefore sends `device_type` as `ap`. The portal claims no switch
support. The portal claims no gateway support.

The schema enumeration also names `gateway` and `switch`. The description wins,
because it states the verified behavior.

Warning: do not send another device type, because an unverified family can leave
a switch or a gateway in an unknown firmware state.

SSR routers use `mistapi.api.v1.orgs.ssr`. Mist Edge uses its own operations.
Both families stay out of this feature.

## 3. The Request Body

`src/firmware/org_upgrade_body.py` builds every body. The class accepts eight
fields.

```json
{
  "all_sites": false,
  "device_type": "ap",
  "site_ids": [
    "11111111-1111-1111-1111-111111111111",
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  ],
  "versions": [
    {
      "firmware_type": "ap",
      "version": "0.14.29538"
    }
  ],
  "strategy": "canary",
  "start_time": 1789000000,
  "canary_phases": [1, 10, 50, 100],
  "max_failure_percentage": 5
}
```

### Rules

| Rule | Effect |
| - | - |
| `all_sites` is always false | The portal names every site. |
| `device_type` is always `ap` | The portal upgrades access points only. |
| `site_ids` holds unique UUID strings | A duplicate site raises `ValueError`. |
| `versions` holds exactly one record | Two records could name conflicting firmware. |
| `strategy` is one of four values | The values are `big_bang`, `canary`, `rrm`, `serial`. |
| `canary_phases` needs the canary strategy | Another strategy raises `ValueError`. |
| `max_failure_percentage` rejects `big_bang` | The big bang strategy has no failure gate. |
| Any other field raises `ValueError` | A silent drop could change the target set. |

The portal omits `p2p_cluster_size`. The documentation and the older code give
different defaults, so the portal claims no value.

The portal keeps `start_time` for the first release. The schema marks it
deprecated and offers `start_datetime`. Record that move as later work.

## 4. The Cloud Answer

### Submit answer

```json
{
  "id": "33333333-3333-3333-3333-333333333333",
  "status": "created",
  "upgrades": [
    {
      "id": "44444444-4444-4444-4444-444444444444",
      "site_id": "11111111-1111-1111-1111-111111111111",
      "status": "created",
      "targets": {
        "total": 12,
        "scheduled": ["000000000001"],
        "upgraded": [],
        "failed": []
      }
    }
  ]
}
```

### Rules

- The job identifier sits in the `id` field.
- The portal keeps every array, even an empty array.
- The portal adds no default for an absent field.
- The portal derives no final state.
- A malformed answer with HTTP 200 gives an error, not an empty job.
- A cancel answer can hold an empty body. HTTP 200 confirms the request only.

## 5. The Portal HTTP Paths

### The current paths

`src/upgrade_portal/app/routes/org_upgrade.py` serves these paths today. The
blueprint name is `org_upgrade`.

| Method and path | View function | Success status |
| - | - | - |
| `GET /upgrade/org/options` | `options_page` | 200 |
| `POST /api/org-upgrades/options` | `save_options` | 200 or 303 |
| `GET /upgrade/org/confirm` | `confirm_page` | 200 |
| `POST /api/org-upgrades` | `submit_upgrade` | 200 or 303 |
| `GET /upgrade/org/jobs/<upgrade_id>` | `job_page` | 200 |
| `GET /api/org-upgrades/<upgrade_id>` | `upgrade_status` | 200 |
| `POST /api/org-upgrades/<upgrade_id>/cancel` | `cancel_upgrade` | 200 |

### The new path

| Method and path | View function | Success status |
| - | - | - |
| `GET /api/org-upgrades` | `job_history` | 200 |

That path calls `listOrgDeviceUpgrades`. The operator uses it after an uncertain
answer.

### Existing paths that this feature uses

| Method and path | Purpose |
| - | - |
| `GET` and `POST /select/org` | Pick the organization |
| `GET` and `POST /select/mode` | Pick the mode |
| `GET` and `POST /select/site` | Pick the sites |
| `GET /api/orgs/<org_id>/sites` | List the sites |
| `POST /api/sites/<site_id>/lock` | Take one site lock |
| `POST /api/sites/<site_id>/lock/heartbeat` | Keep one site lock |
| `DELETE /api/sites/<site_id>/lock` | Release one site lock |
| `POST /api/runs/<run_id>/capture/start` | Start a capture |
| `GET /api/captures/<capture_id>/status` | Read a capture |
| `POST /api/comparisons` | Start a comparison |

## 6. The Submit Request

```http
POST /api/org-upgrades
Content-Type: application/x-www-form-urlencoded

confirmation=CONFIRM&csrf_token=<token>
```

The body carries the confirmation word only. The route reads the organization
from `selected_org_id`, the sites from `OperatorSession.selected_site_ids`, and the options from
`org_upgrade_options`.

The field name is `confirmation`. The single-site page uses `confirm`. Align the
two names in a later change, and keep one server helper for both.

### Answer

A browser form post receives a redirect to the progress page. A JSON client
receives this body:

```json
{
  "next": "/upgrade/org/jobs/33333333-3333-3333-3333-333333333333"
}
```

### The cancel request

```http
POST /api/org-upgrades/<upgrade_id>/cancel
Content-Type: application/json

{"confirmation": "CANCEL"}
```

The cancel word is `CANCEL`. The answer holds `upgrade_id` and
`cancel_requested`.

## 7. The Status Answer

`GET /api/org-upgrades/<upgrade_id>` answers with this shape today:

```json
{
  "upgrade_id": "33333333-3333-3333-3333-333333333333",
  "status": "upgrading",
  "current_phase": null,
  "total": 24,
  "upgraded_count": 8,
  "failed_count": 1,
  "site_upgrades": [
    {
      "site_id": "11111111-1111-1111-1111-111111111111",
      "id": "44444444-4444-4444-4444-444444444444",
      "status": "upgrading"
    }
  ]
}
```

### Status calculation

`status_summary` reads the target arrays from each site upgrade. It sums the
totals across all entries. Each normalized `site_upgrades` entry includes these
keys:

| Key | Type | Meaning |
| - | - | - |
| `site_name` | `str` | The readable site name |
| `total` | `int` | The target count of that site |
| `upgraded` | `int` | The upgraded count of that site |
| `failed` | `int` | The failed count of that site |
| `pre_capture_id` | `str` | The baseline capture |
| `post_capture_id` | `str` | The proof capture |

### Rules

- The field `status` holds the cloud text without a change.
- The field `failed_count` counts the failed arrays of every site job.
- The field `post_capture_id` stays null until the post-check finishes.
- The answer names no derived final state.

## 8. The Refusal Envelope

Every refusal uses `json_error` from `factory.py`. That helper builds one flat
shape.

```json
{
  "code": "site_locked",
  "message": "Another operator holds this site.",
  "details": {
    "site_id": "11111111-1111-1111-1111-111111111111",
    "holder": "operator@example.com"
  }
}
```

### The current codes

| Code | Status | Condition |
| - | - | - |
| `multi_site_mode_required` | 400 | The session mode is not `multi_site`. |
| `sites_not_chosen` | 400 | The site set is empty. |
| `org_upgrade_options_invalid` | 400 | `OrgUpgradeBody` raised `ValueError`. |
| `confirmation_required` | 400 | The body holds no exact word. |
| `org_upgrade_submission_failed` | 502 or 503 | The cloud answered an error, or the outcome is unknown. |
| `org_upgrade_status_failed` | 502 | The status read failed. |
| `org_upgrade_cancel_failed` | 400, 502, or 503 | The cancel request failed. |

### The new codes

| Code | Status | Condition |
| - | - | - |
| `precheck_missing` | 409 | One site holds no verified pre-check. |
| `site_locked` | 409 | Another operator holds a selected site. |
| `lock_store_unreachable` | 503 | The lock store does not answer. |
| `lock_lost` | 409 | The grant expired during the run. |

## 9. Write Safety

| Rule | Reason |
| - | - |
| The session sets `_MAX_429_RETRIES` to zero | The SDK retries a POST request after HTTP 429. |
| The transport adapter permits zero retries | A transport retry can also repeat the write. |
| The service refuses a session that permits retries | A call count alone cannot prove one request. |
| The portal never repeats a write | A repeat can start a second upgrade job. |
| The portal validates the body twice | A caller cannot change a preview body. |

Warning: do not add an automatic retry, because a second write can start a
second upgrade job at every selected site.

After an uncertain answer, the operator reads `GET /api/org-upgrades`. That read
shows a job that the portal did not record.

## 10. Contract Rules

- The portal calls one cloud operation for each service call.
- The portal writes an audit entry for every write.
- The audit logger masks the API token in every entry.
- The portal keeps the site operations of the single-site flow without a change.
- The portal reads the job identifier from `id` for an organization job.
- The portal reads `upgrade_id` for a site job.
- The status answer always names the mode.
- The run record always holds the explicit mode.
