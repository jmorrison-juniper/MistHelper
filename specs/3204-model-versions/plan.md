# Implementation Plan: Multi-site model versions

## Design

The organization page will reuse the device rows that the single-site page uses.
Each row will show a version select with the versions of its model.
The browser will send explicit `mac` and `version_target` pairs.

The route will select the pairs that belong to each site.
The shared option builder will keep the existing model compatibility check.

The aggregate service will keep the organization AP child for one AP version.
If AP versions differ, it will use the existing site planner for those APs.
That planner groups devices by type, gateway family, and target version.

## Files

- `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`
- `src/upgrade_portal/app/assets/static/js/portal.js`
- `src/upgrade_portal/app/routes/org_upgrade.py`
- `src/firmware/aggregate_upgrade_service.py`
- Focused contract, browser, and aggregate service tests

## Risks

- A device select outside the form can be absent from `FormData`.
- A selected address from one site can enter another site record.
- Mixed AP versions can lose explicit device targeting if they use the organization route.
- A return from confirmation can reset device choices.

## Validation

Run the focused contract, browser, and aggregate service tests.
Run py_compile, Ruff, Black, mypy, STE, and the applicable portal test shards.
