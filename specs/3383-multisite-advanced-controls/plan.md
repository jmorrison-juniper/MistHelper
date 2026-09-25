# Implementation Plan: The multi-site options page offers each advanced control

**Issue**: #3383 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Technical context

- Python 3.13, Flask, and Jinja for the portal on port 8056.

- `portal.js` for the visibility rules of the multi-site form.

- pytest for the unit and contract tests. Playwright with Microsoft Edge for
  the browser journey.

- No new dependency and no schema change of the run store.

## The changed files

| File | The change |
| - | - |
| `src/upgrade_portal/upgrade/org_advanced_options.py` | New. `OrgAdvancedOptions` reads, passes on, and shows the advanced values. `OrgAdvancedRules` holds the two rules of the multi-site plan. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | Read the advanced values, give them to the mapper, apply the rules, and show the values. |
| `src/upgrade_portal/upgrade/options.py` | Add the label and the rule of each new control to `ORG_OPTION_HELP`. |
| `src/firmware/upgrade_service.py` | Make the canary rule and the access point rule public. |
| `src/firmware/aggregate_upgrade_service.py` | Build the access point child with the shared rules, and refuse the stable build. |
| `src/firmware/org_upgrade_body.py` | Accept and check the nine access point fields. |
| `src/upgrade_portal/app/assets/templates/upgrade/org_options.html` | Add the advanced controls. |
| `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html` | Add the advanced summary. |
| `src/upgrade_portal/app/assets/static/js/portal.js` | Show each control only when its rule allows it. |

## The data flow

1. The browser posts each visible control. A hidden control is disabled, so it
   posts no value.

2. `read_options` keeps each advanced value that is not empty. It reads them
   only for a request that names the device types.

3. `_site_option_body` gives the values to the single-site mapper for each
   site. The mapper refuses a bad value with the field name.

4. `_aggregate_saved_options` applies the two multi-site rules. Then the
   aggregate service builds each child.

5. The access point child uses the shared canary rule and access point rule.
   Each switch child and each gateway child uses the site body builder.

6. At the start, `OrgUpgradeBody.build` checks the access point child again.

7. The confirm page reads the stored body of each child. It lists an advanced
   value only when a child body carries that field.

## The test strategy

- Contract tests post each field through the route and read the options that
  reach the aggregate boundary.

- A parity contract test maps each advanced control of the single-site page to
  a control of the multi-site page.

- Unit tests prove the organization body rules and the access point child
  fields. One unit test compares the access point child with the site body.

- A browser journey sets each control, reads the confirm page, and goes Back.

## Project rules

- Each function stays within five parameters and 25 lines.

- Each new line of code carries an inline comment and the action logs.

- The text of the page, the messages, and the documents follows STE.
