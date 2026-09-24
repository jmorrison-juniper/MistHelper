# Implementation Plan: Multi-site options form repair

## Design

The route keeps the saved option values in the view model. The template renders the same state on first paint. The browser updates visibility after each family or strategy change and disables hidden controls.

Each page reads its own label table. `OPTION_HELP` holds the labels of `options.html`. `ORG_OPTION_HELP` holds the labels of `org_options.html`. The class `OrgOptionRefusal` rebuilds each shared refusal with the multi-site table. It maps a refused target version to the version control of the refused device family. It also refuses a text that holds no whole number before the parser repeats the typed value.

## Files

- src/upgrade_portal/app/routes/org_upgrade.py
- src/upgrade_portal/app/assets/templates/upgrade/org_options.html
- src/upgrade_portal/app/assets/static/js/portal.js
- src/upgrade_portal/app/assets/static/css/portal.css
- src/upgrade_portal/upgrade/options.py
- tests/unit/upgrade_portal/test_option_refusal_message.py
- tests/contract/upgrade_portal/test_org_upgrade_routes.py
- tests/e2e/upgrade_portal/test_org_options_form.py

## Risks

- A hidden control can still submit if it is not disabled.
- A server-rendered hidden state can drift from the browser update logic.
- A generic option refusal can expose an internal field name.
- A label table that serves two pages can drift from one page. The drift test of each table reads one page only. Issue #3273 records that failure.

## Validation

Run the contract and browser tests for the organization upgrade flow. Run py_compile, ruff, black, mypy, and symbol_diff before the commit.
