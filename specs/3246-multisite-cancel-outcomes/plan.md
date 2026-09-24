# Implementation Plan: The cancellation result of a multi-site upgrade

**Issue**: #3246
**Spec**: [spec.md](./spec.md)

## Technical context

- Python 3.13, Flask 3, and Jinja templates.
- The firmware layer is `src/firmware/`. It must not import `src/upgrade_portal/`.
- The view layer is `src/upgrade_portal/upgrade/`. It makes no cloud call and no write.
- The change adds no dependency, no environment variable, and no schema change. The durable record keeps its shape. The AP result of a new cancel adds the three list keys that a site result already holds.

## The current behavior

1. `AggregateUpgradeService.cancel` sends one cancel for each child job. `_cancellation_result` picks the route.
2. `_cancel_device_child` calls `upgrade_service.cancel_upgrade` with the stored `status_data`. The helper sorts each MAC address into three lists.
3. `_cancel_org_child` calls `OrgUpgradeService.cancel`. It stores `status`, `raw_status`, and `message` only. The AP child job has no lists.
4. The progress page renders each result as one text cell in the child table.

## The design

### Part 1. Share the sort rule in the firmware layer

`src/firmware/upgrade_service.py`:

- Rename `_reboot_macs` to `reboot_macs`. The function keeps its rule.
- Replace `_sort_cancel(macs, last_status, status)` with `sort_cancel(macs, writing, status)`. The argument `writing` is the set of normalized MAC addresses that write firmware, or `None` when the portal cannot tell.
- `cancel_upgrade` calls `sort_cancel(macs, reboot_macs(last_status), status)`. The single-site result stays the same.

### Part 2. Sort the AP child job

The new module `src/firmware/org_cancel_sort.py` holds two classes. `OrgRebootLists` reads the reboot lists of the organization answer. `OrgCancelSort` builds the durable result. Two classes keep each class at five methods or fewer.

| Class and method | Purpose |
| - | - |
| `OrgRebootLists.writing(status_data, site_ids)` | Return the MAC addresses that write firmware, or `None`. |
| `OrgRebootLists._site_lists(status_data)` | Return the reboot list of each site, or `None` for a damaged answer. |
| `OrgRebootLists._add_entry(lists, entry)` | Add the list of one site entry, or report a damaged entry. |
| `OrgRebootLists._entry_job(entry)` | Return the site job of one entry. |
| `OrgRebootLists._holds_lists(job)` | Return whether one job holds reboot lists. |
| `OrgCancelSort.result(child, cancel)` | Return the durable result of one AP cancel. |
| `OrgCancelSort._targets(child)` | Return the MAC addresses and the site identifiers of the child job. |

The rules of `writing`:

1. If the stored answer is not a mapping, return `None`.
2. The root covers every site when it holds a `targets` mapping or a `reboot_in_progress` key. A status word alone does not cover a site.
3. Read each entry of `upgrades` and `site_upgrades`. The job is `entry["upgrade"]` when that value is a mapping. Otherwise, the job is the entry.
4. A job holds lists when it holds a `targets` mapping or a `reboot_in_progress` key. A reference entry with `site_id` and `upgrade_id` holds no lists.
5. If one entry of a site holds no lists, the site stays unread.
6. If an entry is damaged, or a list has a shape that `reboot_macs` rejects, return `None`.
7. If a site of the child job stays unread, and the root does not cover it, return `None`.
8. Otherwise, return the union of the root list and each site list.

`AggregateUpgradeService._cancel_org_child` returns `OrgCancelSort.result(child, result)`.

### Part 3. Build the panel rows in the view layer

The new module `src/upgrade_portal/upgrade/org_cancel_outcomes.py` holds two classes. The module `org_child_controls.py` already holds five top-level items, so the new classes need their own module.

- `OrgCancelOutcomes.rows()` returns one row for each child job that holds a result, in the order of the plan.
- `OrgCancelOutcomes.signature()` returns the pairs `child_id:status`, joined with commas.
- `OrgCancelLists.lists()` applies the list rules to one child job.

The list rules, in this order:

1. The stored rule: if the result holds all three lists, copy them.
2. The rule for a child job that never started: the lists stay empty, and the row holds the note of FR-006. This rule applies in three cases.
   - The child state is `not_submitted`.
   - The child state is `planned`, and the operation holds no live submission claim.
   - The child state is `rejected`, and the cloud answered with a status from 400 through 499.
3. The rule for an unsorted result: every target of the child job goes to the writing list, and the row holds the note of FR-007.

A `planned` child job during a live claim can hold a cloud job that the portal did not record. A rejected answer with a 5xx status, or with no client error, can also hide a cloud job. Those cases use the unsorted rule. Issue #3327 tracks the race between a cancel and a live submission.

### Part 4. Show the panel

- `_aggregate_record_view` in `org_upgrade.py` adds `cancel_outcomes`. The page and the poll read the same field.
- `OrgControlsView.build` adds the part `;cancel=<signature>` to the signature.
- `org_progress.html` replaces the old note with the Caution text of FR-013. It adds the panel after the card "Current status".
- `portal.js` keeps its logic. `orgControlsChanged` already loads the page again when the signature changes. The comment names the panel.

## Risk review

| Risk | Control |
| - | - |
| The panel claims that no device writes firmware, and the operator cuts power to a device in mid-write. | The view sorts every device of an unsorted result into the writing list. The service returns `None` for each shape that it cannot read. |
| The rename breaks the single-site stop. | The single-site tests run without a change. |
| The new signature part reloads the page in a loop. | The part changes only when a result is added or changes its word. |
| The firmware layer imports the portal. | `org_cancel_sort.py` imports only `upgrade_service` and `org_upgrade_service`. |
| The contract document names the old private functions. | `specs/1823-upgrade-capture-portal/contracts/upgrade-service.md` adds a section for `reboot_macs` and for `sort_cancel`. |

## Test plan

| Layer | File | Proof |
| - | - | - |
| Unit | `tests/unit/firmware/test_org_cancel_sort.py` | Each branch of `writing` and `result`. |
| Unit | `tests/unit/upgrade_portal/test_upgrade_service_cancel_sort.py` | `sort_cancel` keeps the three single-site rules. |
| Unit | `tests/unit/firmware/test_aggregate_upgrade_service.py` | The AP cancel stores the three lists. |
| Unit | `tests/unit/upgrade_portal/test_org_cancel_outcomes.py` | The three list rules and the signature. |
| Contract | `tests/contract/upgrade_portal/test_org_cancel_outcomes_routes.py` | The page, the poll, and the HTML post. |
| E2E | `tests/e2e/upgrade_portal/test_org_cancel_outcomes_journey.py` | The browser cancel, the lists, and a reload. |

## Constitution check

- The change keeps the five-item rule. Each new class holds five methods or fewer, and each new module holds five top-level items or fewer.
- Each new code line holds an inline comment.
- Each action logs before and after.
- All text obeys STE.
