# Data Model: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Language**: Python 3.13 or newer
**Storage**: The capture store in `src/upgrade_portal/capture/store.py`

## 1. Browser Session State

The portal keeps scalar scope values in the signed Flask session. The
server-side `OperatorSession` keeps the multi-site target set.

| Value | Type | Set by | Meaning |
| - | - | - | - |
| `selected_org_id` | `str` | `select.choose_org` | The chosen organization |
| `selected_upgrade_mode` | `str` | `select.choose_mode` | `single_site` or `multi_site` |
| `selected_site_id` | `str` | `select.site_inventory_page` | The single-site target |
| `OperatorSession.selected_site_ids` | `tuple[str, ...]` | `select.choose_sites` | The multi-site target set |
| `site_lock_records` | `dict[str, dict]` | `select.take_site_lock` | One lock grant for each held site |
| `org_upgrade_options` | `dict` | `org_upgrade.save_options` | The validated request body |
| `org_upgrade_last_job` | `dict` | `org_upgrade.submit_upgrade` | The job identifier and the site count |

### Rules

- The portal clears the server-side site set when the operator changes the
  organization.
- The portal clears the server-side site set when the operator changes the mode.
- The portal clears `selected_site_id` when the mode becomes `multi_site`.
- Move `org_upgrade_options` to the run record for durable recovery.

## 2. The Request Body

`src/firmware/org_upgrade_body.py` owns the body rules. The class validates the
input and returns a new dictionary.

```python
body = {
    "all_sites": False,
    "device_type": "ap",
    "site_ids": ["<uuid>", "<uuid>"],
    "versions": [{"firmware_type": "ap", "version": "0.14.29538"}],
    "strategy": "canary",
    "start_time": 1789000000,
    "canary_phases": [1, 10, 50, 100],
    "max_failure_percentage": 5,
}
```

### Field rules

| Field | Type | Rule | Failure message |
| - | - | - | - |
| `all_sites` | `bool` | Always false | The all_sites field must be false. |
| `device_type` | `str` | Always `ap` | The organization upgrade supports AP devices only. |
| `site_ids` | `list[str]` | Nonempty, unique, UUID | The site_ids field must not contain duplicate sites. |
| `versions` | `list[dict]` | Exactly one AP record | The AP upgrade needs exactly one versions record. |
| `versions[0].version` | `str` | Nonempty, printable, no space | Each versions record needs a nonempty version string without whitespace. |
| `versions[0].force` | `bool` | Optional | The force field in a versions record must be a boolean. |
| `strategy` | `str` | `big_bang`, `canary`, `rrm`, `serial` | The strategy field must be big_bang, canary, rrm, or serial. |
| `start_time` | `int` | 0 to 2147483647 | The start_time field must be an integer from 0 to 2147483647. |
| `canary_phases` | `list[int]` | Increasing, ends at 100, canary only | The canary_phases percentages must increase and end at 100. |
| `max_failure_percentage` | `int` | 0 to 100, never with `big_bang` | The max_failure_percentage field cannot use the big_bang strategy. |

The class rejects any other field with this message: "The upgrade request
contains an unsupported field."

## 3. The Cloud Result

`src/firmware/org_upgrade_service.py` returns a frozen dataclass.

```python
@dataclass(frozen=True, slots=True)
class OrgUpgradeResult:
    org_id: str
    upgrade_id: str | None
    raw_status: int
    data: Mapping[str, object]
    error: str | None
```

### Rules

- The field `raw_status` holds zero when the answer carries no valid HTTP code.
- The field `data` holds a detached copy of the answer and the `upgrades` array.
- The field `error` holds a message for a failed request or a malformed answer.
- A valid answer with HTTP 200 sets `error` to `None`.
- The service reads the job identifier from the `id` field.

## 4. The Job Answer

The cloud answer holds one entry for each site job.

```json
{
  "id": "33333333-3333-3333-3333-333333333333",
  "status": "upgrading",
  "upgrades": [
    {
      "id": "44444444-4444-4444-4444-444444444444",
      "site_id": "11111111-1111-1111-1111-111111111111",
      "status": "upgrading",
      "start_time": 1789000000,
      "targets": {
        "total": 12,
        "scheduled": ["000000000001"],
        "downloading": [],
        "downloaded": [],
        "download_requested": [],
        "reboot_in_progress": [],
        "rebooted": [],
        "upgraded": ["000000000002"],
        "failed": [],
        "skipped": []
      }
    }
  ]
}
```

### Rules

- The portal keeps every array, even an empty array.
- The portal keeps an absent field absent. The portal adds no default.
- The portal derives no final state from the arrays.
- The portal counts the failed array and shows the count.

## 5. The Run Record

`src/upgrade_portal/runtime/runs.py` owns the run model. The store writes the
record to the `upgrade_runs` collection.

### Current fields

`RunRecordBuilder.REQUIRED_FIELDS` names these keys:

`_key`, `run_id`, `schema_version`, `org_id`, `org_name`, `site_id`,
`site_name`, `actor_email`, `browser_id`, `created_at`, `updated_at`, `state`,
`tier`, `targets`, `options`, `phases`, `stop_request`, `pre_capture_id`,
`post_capture_id`, `error`.

### New fields for this feature

| Field | Type | Meaning |
| - | - | - |
| `upgrade_mode` | `str` | `single_site` or `multi_site` |
| `site_ids` | `list[str]` | The selected sites, in the operator order |
| `org_upgrade_id` | `str` | The job identifier from the cloud |
| `org_upgrade_body` | `dict` | The validated request body |
| `pre_capture_ids` | `dict[str, str]` | One pre-check identifier for each site |
| `post_capture_ids` | `dict[str, str]` | One post-check identifier for each site |
| `site_lock_ids` | `dict[str, str]` | One lock token for each site |

### Rules

- The record always holds the explicit mode. The portal never derives the mode
  from the site count.
- A multi-site record keeps `site_id` empty and fills `site_ids`.
- A single-site record keeps `site_ids` empty and fills `site_id`.
- The record keeps the request body, so an audit can replay the scope.

## 6. The Run States

`RunState` in `runtime/runs.py` names seventeen values.

| Value | Meaning |
| - | - |
| `created` | The portal made the record. |
| `pre_capture_running` | A pre-check runs. |
| `pre_capture_done` | Every pre-check finished. |
| `awaiting_confirmation` | The portal waits for the typed word. |
| `upgrade_submitting` | The portal sends the write. |
| `upgrade_running` | The cloud runs the job. |
| `settling_gateways` | The gateway phase settles. |
| `settling_switches` | The switch phase settles. |
| `settling_aps` | The access point phase settles. |
| `settling_clients` | The client phase settles. |
| `post_capture_running` | A post-check runs. |
| `post_capture_done` | Every post-check finished. |
| `complete` | The run finished. |
| `stopping` | The operator asked for a stop. |
| `stopped` | The run stopped. |
| `failed` | The run failed. |
| `cancelled` | The operator cancelled the run. |

An organization run uses `settling_aps` only, because the job upgrades access
points only. The other settle states stay unused in this mode.

`PHASE_ORDER` holds `("gateways", "switches", "aps", "clients")`. `PhaseState`
holds `pending`, `waiting`, `settled`, `skipped`, and `failed`. An organization
run marks the gateway phase, the switch phase, and the client phase as
`skipped`.

## 7. The Status View

`RunStatusView.build` returns these keys today:

`run_id`, `state`, `phase_order`, `phases`, `targets`, `stop_request`,
`pre_capture_id`, `post_capture_id`, `message`, and an optional `lock`.

`org_upgrade.status_summary` returns these keys today:

`status`, `current_phase`, `total`, `upgraded_count`, `failed_count`, and
`site_upgrades`.

`status_summary` reads each nested target object and sums its device counts.

The planned run record adds these keys:

| Key | Type | Meaning |
| - | - | - |
| `upgrade_mode` | `str` | Always `multi_site` |
| `site_count` | `int` | The number of selected sites |

Each entry of `site_upgrades` adds `site_name`, `total`, `upgraded`, `failed`,
`pre_capture_id`, and `post_capture_id`.

## 8. The Site Lock Record

`select.py` stores one grant for each held site under `site_lock_records`.

| Field | Type | Meaning |
| - | - | - |
| `site_id` | `str` | The held site |
| `lock_token` | `str` | The grant token |
| `holder` | `str` | The operator address |
| `expires_at` | `str` | The expiry time |

The three lock states are `free`, `locked`, and `unknown`. The site picker shows
`Unknown` when the store does not answer, because a free site and an unreadable
site both give an empty holder.

## 9. Entity Relations

- One organization holds many sites.
- One run holds one mode.
- One multi-site run holds one organization and many sites.
- One multi-site run holds one cloud job.
- One cloud job holds one site job for each selected site.
- One site holds one pre-check and one post-check for each run.
- One site holds one lock at a time.

## 10. Validation Rules

The portal applies these rules in order:

1. The mode must equal `multi_site` for every organization path.
2. The site set must hold at least one site.
3. The site set must hold unique UUID strings.
4. Every site must belong to the chosen organization.
5. Every site must hold a verified pre-check.
6. Every site must hold a live lock for this operator.
7. The body must pass `OrgUpgradeBody.build`.
8. The confirmation field must equal `CONFIRM` exactly. The field name is
   `confirmation` in the organization lane.

A failure at any step gives a refusal. The portal then calls no cloud
operation.

## 11. Persistence Rules

- The store writes the run record before the cloud write.
- The store writes the job identifier after the cloud answer.
- The store keeps the request body for the audit trail.
- The audit logger masks the API token in every entry.
- A malformed cloud answer writes an error field and no job identifier.
