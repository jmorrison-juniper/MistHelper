# Implementation Plan: Retry, reschedule, and reconciliation for multi-site upgrades

**Issue**: #3247
**Spec**: [spec.md](./spec.md)

## Technical context

- **Language**: Python 3.13, Flask 3, Jinja2, and the vanilla JavaScript of `portal.js`.
- **Store**: The aggregate operation record in `upgrade_runs`. Every change uses the compare-and-set write of `AggregateUpgradeService._cas`.
- **Cloud calls**: The reconciliation reads `listSiteDevicesStats` through `OrgVersionRefresh.read_site`. The retry and the reschedule make no cloud call.
- **New dependency**: None.

## Design

### The model: three modules in `src/upgrade_portal/upgrade/`

Each module reads the durable record only. No module makes a cloud call or a write.

| Module | Class | Job |
| - | - | - |
| `org_retry.py` | `OrgRetrySelection` | Find the retry devices, and build the options that fill the form. |
| `org_retry.py` | `OrgRetryPlan` | Hold one retry plan, and narrow a site inventory to the retry devices. |
| `org_reconcile.py` | `OrgReconcileCheck` | List the uncertain child jobs and the sites to read, and decide each child job from the running versions. |
| `org_child_controls.py` | `OrgScheduleView` | Show the start time on the confirmation page, and report whether the plan accepts a reschedule. |
| `org_child_controls.py` | `OrgControlsView` | Build the `controls` value that the page and the poll share, with one signature text. |

The signed session cookie holds only the operation identifier and the organization of the retry plan. The portal builds the plan again from the durable record on each use. A long device list therefore never enters the cookie. If the record holds no retry device, the plan holds no device, and the save refuses the options.

### The service: `src/firmware/aggregate_upgrade_service.py`

Two public methods use the nested `update` pattern of `record_device_versions`.

- `reschedule(record, store, change)` checks the planned state again inside the compare-and-set. It then sets or removes `start_time` in each child body, and it sets the new reboot moment when the plan holds a reboot delay.
- `reconcile(record, store, evidence)` applies a verdict only when the child job is still uncertain. It stores the readings in `device_versions`, and it computes the aggregate state again.

### The routes: `src/upgrade_portal/app/routes/org_controls.py`

A new blueprint `org_controls_bp` holds four POST routes. The factory registers it after `org_upgrade`.

| Path | Job |
| - | - |
| `/api/org-upgrades/<upgrade_id>/retry` | Store the retry plan, and open the options page. |
| `/api/org-upgrades/options/retry/clear` | Drop the retry plan, and open the options page. |
| `/api/org-upgrades/<upgrade_id>/reconcile` | Read the devices, and settle each proven child job. |
| `/api/org-upgrades/<upgrade_id>/reschedule` | Change the start time of the current plan. |

### The changes to `org_upgrade.py`

- Three helpers become public, so that the new module uses no private name: `owned_saved_operation`, `release_operation_locks`, and `confirmation_value`.
- `record_controls(record)` builds the controls. `_aggregate_record_view` adds them to the page and the poll.
- `options_page` and `_site_option_record` narrow each site inventory when a retry plan applies.
- `_aggregate_saved_options` stores `plan_options` and `retry_of_operation_id`.
- `_submit_aggregate` drops the retry plan after a successful submission.
- `confirm_page` adds the schedule view.

### The session key

`select.py` holds `ORG_UPGRADE_RETRY_KEY`. `clear_org_upgrade_options` drops it, so every change of the organization, the mode, or the site set also drops the retry plan. The key lives in `select.py`, so no import cycle occurs.

### The browser

- `org_progress.html` shows the retry card and the reconciliation card. The region carries `data-org-controls`, which holds the signature.
- `org_options.html` shows the retry banner and the clear button.
- `org_confirm.html` shows the start time and the reschedule form.
- `paintOrgUpgradeStatus` reloads the page when the signature changes. `initOrgUpgradeForms` already sends every form whose action starts with `/api/org-upgrades`.

## Risks

- **The legacy submission path**: A session with saved options and no operation identifier falls through to the path of access points only. The retry plan therefore uses its own session key.
- **The reboot moment**: The save computes the reboot moment from the clock of the save. The reschedule applies the same rule at the moment of the change.
- **A proof that is not a proof**: A forced reinstall leaves the version before equal to the target. The reconciliation then keeps the child job uncertain.

## Test plan

- Unit tests for the model and for the two service methods.
- Contract tests for the four routes, the save filter, the session key rules, and the new record fields.
- Browser tests with screenshots for the retry, the reconciliation, and the reschedule.
