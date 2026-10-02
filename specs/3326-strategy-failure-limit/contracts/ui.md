# Organization Failure Limit Contract

This contract applies to `/upgrade/org/options` and its existing save at `/api/org-upgrades/options`.
It changes presentation only. The existing server policy remains unchanged.

## Strategy States

| Selected strategy | Visible | Enabled | Required attribute | FormData and save JSON |
| --- | --- | --- | --- | --- |
| `canary` | Yes | Yes | Present | Include `max_failure_percentage` |
| `big_bang` | No | No | Present | Omit `max_failure_percentage` |
| `rrm` | Yes | Yes | Present | Include `max_failure_percentage` |
| `serial` | Yes | Yes | Present | Include `max_failure_percentage` |

The initial server render must match this table before the script runs.
The existing group rule names exactly the three applicable strategy values.
Changing strategies must not clear a valid typed percentage.

## Preserved Field

The field keeps `id="max-failure-percentage"` and `name="max_failure_percentage"`.
Its existing test identifier remains `org-upgrade-max-failures`.
Its label remains `Maximum failure percentage`.
Its type remains `number`, with inclusive bounds of 0 through 100.
Its default remains 5. A saved zero and a saved nonzero value remain unchanged.
The required attribute remains present. Disabling the input excludes it from native validation.

## Browser Evidence

Use the shipped template, layout, styles, shared script, form, controller, and save route.
Use controlled cloud and process-owned store seams with no real credential.
Require the `RunOwnerHeaderCheck` decision before workflow assertions.
Record exact SDK and firmware-start callback counts and require zero.
Do not submit the firmware Start form.

Drive the actual four radio selectors.
Measure field and group visibility, enabled state, native validation, and FormData.
Record the actual Review JSON for omission or exact percentage inclusion.
Prove saved initial Big bang and applicable strategies before JavaScript.
Prove repeated switches with a valid edited value.

Measure desktop at 1280 pixels and a narrow viewport with both `magenta` and `default`.
Keep adjacent Canary phases, model-specific version selects, reboot, and Junos controls unchanged.
Keep Review refusal messages, typed confirmation, and native keyboard access unchanged.
Capture screenshots and traces without secrets.

## Negative Controls and Safety

A removed strategy rule must fail a direct guard check.
A hidden but enabled failure input must fail a direct guard check.
Each guard report states the number of checked fields or decisions.
An unreadable template must fail instead of reporting zero successful checks.

All test resources belong to this run and stop before the local handoff.
Shared fixtures, script helpers, JavaScript, CSS, routes, stores, and policy remain read-only.
