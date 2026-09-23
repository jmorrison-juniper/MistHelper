# Implementation Plan: Multi-site options form repair

## Design

The route keeps the saved option values in the view model. The template renders the same state on first paint. The browser updates visibility after each family or strategy change and disables hidden controls.

## Files

- src/upgrade_portal/app/routes/org_upgrade.py
- src/upgrade_portal/app/assets/templates/upgrade/org_options.html
- src/upgrade_portal/app/assets/static/js/portal.js
- src/upgrade_portal/app/assets/static/css/portal.css
- src/upgrade_portal/upgrade/options.py
- tests/contract/upgrade_portal/test_org_upgrade_routes.py
- tests/e2e/upgrade_portal/test_org_options_form.py

## Risks

- A hidden control can still submit if it is not disabled.
- A server-rendered hidden state can drift from the browser update logic.
- A generic option refusal can expose an internal field name.

## Validation

Run the contract and browser tests for the organization upgrade flow. Run py_compile, ruff, black, mypy, and symbol_diff before the commit.
