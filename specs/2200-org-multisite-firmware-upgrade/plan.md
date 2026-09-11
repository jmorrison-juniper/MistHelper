# Implementation Plan: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Status**: In planning
**Specification**: `spec.md`
**Application**: `src/upgrade_portal` (Flask, Jinja, plain JavaScript)

## Summary

The portal adds an organization scope to the existing upgrade flow. The operator
picks many sites in one organization. The portal sends one job to the Mist cloud
through `upgradeOrgDevices`. The job upgrades access points only.

The plan reuses the current pages, the current session, and the current safety
gates. The plan adds one route lane, one wiring seam, and one status view.

## Technical Context

| Item | Value |
| - | - |
| Language | Python 3.13 or newer |
| Web framework | Flask with Jinja templates |
| Browser code | One plain JavaScript file, no build step |
| Cloud SDK | `mistapi` 0.59 or newer |
| Storage | The capture store in `src/upgrade_portal/capture/store.py` |
| Run collection | `upgrade_runs` |
| Test runner | `pytest` |
| Linters | `ruff` for Python, `tools.ste_linter` for Markdown |
| Network in tests | Blocked by `tests/conftest.py` |

## Constitution Check

| Principle | Effect on this plan |
| - | - |
| Five-item rule | Each new view function stays under 25 lines. Helpers hold the detail. |
| Class-based architecture | `OrgUpgradeService` holds the cloud calls. The routes hold no cloud code. |
| Safety first | The typed word `CONFIRM` gates every write. The portal validates every input. |
| Deployment pipeline | The implementation phase runs the pipeline. This specification phase does not. |
| Logging | Each action writes an information line before it and a debug line after it. |
| Inline comments | Every new line carries a comment that states the reason. |
| Action logging | Every cloud call and every store write carries a log pair. |

## Project Structure

### Documentation for this feature

```text
specs/2200-org-multisite-firmware-upgrade/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── api-contract.md
    └── ui-contract.md
```

### Source code

```text
src/upgrade_portal/
├── app/
│   ├── factory.py                      # Registers the blueprints
│   ├── wiring.py                       # Holds the service seams
│   ├── routes/
│   │   ├── select.py                   # Organization, mode, and site pages
│   │   ├── upgrade.py                  # Run, options, confirm, progress
│   │   ├── org_upgrade.py              # The organization lane, already present
│   │   ├── capture.py                  # Pre-check and post-check
│   │   └── review.py                   # History and comparison
│   └── assets/
│       ├── templates/
│       │   ├── select/{orgs,mode,sites}.html
│       │   └── upgrade/{options,confirm,progress}.html
│       │   └── upgrade/{org_options,org_confirm,org_progress}.html
│       └── static/js/portal.js
├── runtime/
│   ├── runs.py                         # Run record and status view
│   └── lock.py                         # Site lock rules
└── capture/store.py                    # Persistence

src/firmware/
├── upgrade_service.py                  # Plan and submit helpers
├── org_upgrade_service.py              # Organization job service
└── org_upgrade_body.py                 # Request body rules
```

## Phase 1: Close the Gaps in the Route Lane

### Goal

The route lane already exists. `src/upgrade_portal/app/routes/org_upgrade.py`
serves seven paths. `factory.py` registers the blueprint `org_upgrade`.

This phase adds the missing guards, the missing history path, and the missing
counts.

### The current paths

| Method and path | View function |
| - | - |
| `GET /upgrade/org/options` | `options_page` |
| `POST /api/org-upgrades/options` | `save_options` |
| `GET /upgrade/org/confirm` | `confirm_page` |
| `POST /api/org-upgrades` | `submit_upgrade` |
| `GET /upgrade/org/jobs/<upgrade_id>` | `job_page` |
| `GET /api/org-upgrades/<upgrade_id>` | `upgrade_status` |
| `POST /api/org-upgrades/<upgrade_id>/cancel` | `cancel_upgrade` |

### The new path

Add `GET /api/org-upgrades` with the view function `job_history`. The handler
calls `listOrgDeviceUpgrades`. The operator reads it after an uncertain answer.

### The current guards

`active_context()` checks three items today:

1. The session holds an organization.
2. The mode equals `multi_site`.
3. The site set holds at least one site.

`identity.require_session` guards every route.

### The new guards

Add two guards before every write:

4. The portal holds a live lock for every selected site.
5. Every selected site holds a verified pre-check.

### Site count status

`status_summary` reads the target arrays inside each site upgrade entry. It sums
the total, upgraded, and failed values across all selected sites.

### Refusal codes

The lane already uses `json_error` from `factory.py`. That helper builds a flat
shape with `code`, `message`, and optional `details`.

| Code | Status | Reason |
| - | - | - |
| `multi_site_mode_required` | 400 | Present today. |
| `sites_not_chosen` | 400 | Present today. |
| `org_upgrade_options_invalid` | 400 | Present today. |
| `confirmation_required` | 400 | Present today. |
| `org_upgrade_submission_failed` | 502 or 503 | Present today. |
| `org_upgrade_status_failed` | 502 | Present today. |
| `org_upgrade_cancel_failed` | 400, 502, or 503 | Present today. |
| `precheck_missing` | 409 | New. |
| `site_locked` | 409 | New. |
| `lock_store_unreachable` | 503 | New. |
| `lock_lost` | 409 | New. |

## Phase 2: The Service Seam

### Goal

Keep one replaceable service object. A test replaces it without a network.

### The current seam

`upgrade_service()` reads `current_app.config` under the key
`ORG_UPGRADE_SERVICE`. The default is the class `OrgUpgradeService`. A test can
inject a stand-in through the Flask config.

That seam works. `wiring.py` needs no installer for the class itself.

### The write session

`current_cloud_session()` returns `identity.current_session().cloud_session`.
Each portal sign-in sets `_MAX_429_RETRIES` to zero. The default transport
adapters also permit zero retries. `OrgUpgradeService._check_write_session`
checks both conditions before each write.

### Rule

Warning: do not enable a retry on this session. A repeated write can start a
second upgrade job.

## Phase 3: Options and Validation

### Goal

Collect the firmware version, the strategy, and the schedule. Refuse an invalid
combination before the confirmation step.

### Work

`save_options` already reads the form body or the JSON body. It maps the form
fields to the request shape of `OrgUpgradeBody`:

| Form field | Body field | Note |
| - | - | - |
| `version` | `versions[0].version` | The handler sets `firmware_type` to `ap`. |
| `strategy` | `strategy` | One of `big_bang`, `canary`, `rrm`, `serial`. |
| `canary_phases` | `canary_phases` | The handler splits the text on commas. |
| `max_failure_percentage` | `max_failure_percentage` | An integer from 0 to 100. |
| `start_time` | `start_time` | The handler reads an ISO 8601 text and stores an epoch integer. |

The handler calls `OrgUpgradeBody.build`. A `ValueError` becomes an
`org_upgrade_options_invalid` refusal with the message of the error.

The handler stores the body under the session key `org_upgrade_options`.

### The remaining work

Add a `force` field to the form, because `OrgUpgradeBody` accepts it.

Add a `serial` option to the strategy group, because `OrgUpgradeBody` accepts
four strategies and the page offers three.

Move the stored body from the session to the run record. The run must recover
its options after a worker restart.

### Device counts

The options page shows a device count for each site. `build_site_rows` supplies
that count today. Add a pre-check column beside it.

## Phase 4: The Typed Confirmation

### Goal

Prove operator intent before the write.

### Work

`upgrade/org_confirm.html` already holds a confirmation input. The field name is
`confirmation`, and `submit_upgrade` reads the same name. The two agree today.

The single-site page uses `confirm`. Align the two names in a later change, and
keep one server helper for both pages.

Add the attributes `data-confirm-word`, `data-confirm-target`, and
`data-confirm-hint-for` to the input. `portal.js` already reads these attributes
in `applyConfirmGate`. The browser gate then needs no new JavaScript.

Set the `disabled` attribute on the start button in the markup. The gate removes
it only after an exact match.

`submit_upgrade` already compares the text to `CONFIRM` with an exact match. The
handler trims no whitespace and changes no case.

The cancel control uses the word `CANCEL` in the same field.

### Rule

Warning: do not enable the submit control in the template, because a browser can
then start every upgrade. The browser gate and the server check must both run.

## Phase 5: Submission and Polling

### Goal

Send one write. Read the result without a derived state.

### Work

`submit_upgrade` runs these steps today:

1. Read the field `confirmation` and compare it to `CONFIRM`.
2. Read the organization, the site set, and the stored options.
3. Call `OrgUpgradeService.submit` one time.
4. Store the job identifier under the session key `org_upgrade_last_job`.
5. Answer with the progress path.

Add these steps:

6. Run the lock guard and the pre-check guard before the write.
7. Write an audit entry with the organization, the site set, and the answer.
8. Store the job identifier in the run record, not in the session alone.

`upgrade_status` calls `OrgUpgradeService.status`. The handler returns the job
data and the site entries. The handler adds no summary state.

`portal.js` reloads the organization progress page on the configured interval.
The page route reads `GET /api/org-upgrades/<upgrade_id>` data through the
service. A later in-place painter can replace the full-page reload.

### No hidden retry

The service never repeats a write. `submit_upgrade` answers HTTP 503 with
`org_upgrade_submission_failed` after an unknown outcome. The message asks the
operator to reconcile the job history first.

Add the history path `GET /api/org-upgrades`. It calls `listOrgDeviceUpgrades`.
The operator uses it to find a job that the portal did not record.

## Phase 6: Locks Across Many Sites

### Goal

Hold one lock for each selected site. Release every lock at the end.

### Work

`select.choose_sites` requests one lock for each selected site. The portal uses
the existing path `POST /api/sites/<site_id>/lock`. The portal stores each grant
under the session key `site_lock_records`.

The portal releases every lock when one request fails. A partial lock set must
never start a job.

`portal.js` beats every held lock. The function `startLockBeat` takes one region
today. Extend the banner to hold a list of site identifiers. The beat then posts
one heartbeat for each site.

### Refusal

The submit guard reads every lock again before the write. A stale grant or a
different holder gives a `site_locked` refusal.

## Phase 7: Post-Checks and Comparison

### Goal

Prove the outcome for each site.

### Work

A watcher reads the job state. The watcher starts a post-check for each selected
site when the job reaches a final state. The watcher reuses
`POST /api/runs/<run_id>/capture/start`.

The review lane already serves `/compare` and `POST /api/comparisons`. The
organization progress page adds one link for each site. Each link opens the
comparison of the pre-check and the post-check of that site.

A failed post-check marks one site only. The other comparisons stay available.

## Phase 8: Tests

### Goal

Prove every rule offline.

### Work

| Suite | Path | Purpose |
| - | - | - |
| Contract | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | The lane behavior, already present with seven tests |
| Unit | `tests/unit/upgrade_portal/test_org_upgrade_service.py` | The cloud contract, already present |
| Unit | `tests/unit/upgrade_portal/test_org_upgrade_guards.py` | The lock guard and the pre-check guard |
| Unit | `tests/unit/firmware/test_org_upgrade_body.py` | The body rules |
| End to end | `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` | The whole flow with stand-ins |

Every suite uses the socket block in `tests/conftest.py`. Every suite uses a
stand-in SDK. No suite reads a credential.

The two present suites give 180 passing tests today. Keep them green.

## Complexity Tracking

| Item | Reason | Simpler choice that fails |
| - | - | - |
| A separate route module | `upgrade.py` already holds 121 KB. A separate lane keeps each file readable. | Adding the routes to `upgrade.py` breaks the five-item rule. |
| A separate cloud session | The SDK retries a POST request by default. | A shared session can start a second job. |
| A separate service class | The site service collapses the site entries of the answer. | Reuse loses the result of each site. |

## Risks and Countermeasures

| Risk | Countermeasure |
| - | - |
| A repeated write starts a second job | Disable SDK retries and transport retries. Refuse a session that permits them. |
| The endpoint supports fewer families than the schema claims | Send `device_type` as `ap` only. |
| A malformed answer looks like an empty success | `_OrgUpgradeResponse.normalize` records an error instead. |
| A partial lock set permits a conflict | Release every lock when one request fails. |
| A weak pre-check hides a regression | Block the write until every site holds a verified pre-check. |
| A cancellation gives false comfort | State that a cancellation does not restore an upgraded device. |
| A wrong count hides a live device | Read the target counts from each site entry. |

## Verification Checklist

- The single-site flow keeps every current path.
- The seven present routes keep their behavior.
- The history path answers with the job list.
- A submission calls `upgradeOrgDevices` exactly one time.
- A submission without the exact word calls no cloud operation.
- A locked site gives HTTP 409.
- An unreachable lock store gives HTTP 503.
- The progress page shows one row for each site entry.
- The progress page shows a true device count.
- The browser gate disables the start button until the exact word.
- Every new test runs offline.
- Every changed Markdown file scores 80 or more.

## Rollout

The mode picker and the route lane already ship together. Add the guards before
the next release. A job without a lock and without a baseline gives the operator
no proof of a safe result.

Ship the first release with access points only. Add a later feature for
switches, for gateways, for SSR routers, and for Mist Edge devices. Each family
needs its own safety review and its own endpoint check.
