# Implementation Plan: Per-Type Upgrade Version Defaults

## Summary

The portal will calculate one safe firmware target for each access point,
switch, and gateway type. A typed selector will use returned availability data,
normalize exact version values, find the common candidates, and select the
highest numeric candidate unless a compatible type override applies.

The options page will replace the global control with three type controls. The
save path will read current inventory and availability again before it writes a
plan. It will reject unknown, cross-type, unavailable, and incompatible
targets. The save path will not invoke the upgrade driver. The existing
confirmation page will remain the only path that can start an upgrade.

## Project Structure

```text
src/upgrade_portal/
├── upgrade/options.py
├── app/routes/upgrade.py
└── app/assets/
    ├── templates/upgrade/options.html
    └── static/js/portal.js
deploy/.env.example
documentation/upgrade_capture_portal.md
tests/
├── unit/upgrade_portal/test_upgrade_options.py
├── contract/upgrade_portal/test_upgrade_options.py
└── e2e/upgrade_portal/test_upgrade.py
```

**Structure Decision:** Keep compatibility selection in `options.py`, retain
the route as the read and write boundary, and keep the browser code limited to
its defined UI contract.

## Constitution Check

| Principle | Assessment | Plan response |
| --- | --- | --- |
| I. Five-Item Rule | PASS | Put typed selection rules in a focused class with small helpers and bounded method inputs. |
| II. Class-Based Architecture | PASS | Add the new selection behavior to a semantically named class instead of new wrapper functions. |
| III. Safety-First | PASS | Validate current inventory and returned availability before persistence. Keep `CONFIRM` as the start gate. |
| IV. Full Deployment Pipeline | PASS | Run syntax, focused tests, lint, formatting, and the required deployment workflow during implementation. |
| V. Observability & Logging | PASS | Log safe selection and rejection summaries without values that can expose secrets. |
| VI. Inline Comments | PASS | Add same-line rationale comments to every generated or changed executable line and its changed block. |
| VII. Action Logging | PASS | Add `info` before meaningful selection and validation work and `debug` after it. |

## Phase 0: Research

See [research.md](research.md). The current portal already separates the
options view, save path, and start path. The plan extends those boundaries
without adding a firmware write to discovery or validation.

## Phase 1: Design

See [data-model.md](data-model.md) for the type candidate and selection
records. See [contracts/http-api.md](contracts/http-api.md) and
[contracts/ui-testids.md](contracts/ui-testids.md) for the saved-body and UI
contracts.

## Implementation Steps

1. Add a typed compatibility selector in `src/upgrade_portal/upgrade/options.py`.
   Group eligible inventory by `ap`, `switch`, and `gateway`. Normalize returned
   version values, intersect the values for every eligible device, and rank
   numeric components. Read `CAPTURE_DEFAULT_AP_VERSION`,
   `CAPTURE_DEFAULT_SWITCH_VERSION`, and `CAPTURE_DEFAULT_GATEWAY_VERSION`.
   Use an override only when it is an exact compatible candidate.
2. Extend the options view and route rendering in
   `src/upgrade_portal/upgrade/options.py` and
   `src/upgrade_portal/app/routes/upgrade.py`. Supply per-type candidates,
   defaults, and empty-candidate warnings while retaining saved choices.
3. Change `src/upgrade_portal/app/assets/templates/upgrade/options.html` and
   `src/upgrade_portal/app/assets/static/js/portal.js`. Replace the global
   control with the three fixed type controls. Apply each selection only to
   devices of that type that offer that exact version. Preserve individual
   device controls and the existing save action.
4. Change save validation in `src/upgrade_portal/upgrade/options.py`. Read
   current inventory and model availability during each save. Reject a target
   that is unknown, from another type, unavailable, or not common to the type.
   Do not modify the run record when validation fails.
5. Document the three optional settings in `deploy/.env.example` and
   `documentation/upgrade_capture_portal.md`. State that each setting requires
   an exact returned compatible version and otherwise uses the safe default.
6. Add unit tests for eligibility, normalization, numeric ordering, common-set
   selection, valid and invalid overrides, no-common-candidate warnings, and
   stale save data. Add route contract tests for rejected saves and unchanged
   records. Update browser tests for the three controls and the removed global
   control. Assert that options reads and saves never call the upgrade launcher.

## Post-Design Constitution Check

| Principle | Assessment | Plan response |
| --- | --- | --- |
| I. Five-Item Rule | PASS | The selector class and route boundary keep new logic small and local. |
| II. Class-Based Architecture | PASS | The new compatibility logic has one class owner. |
| III. Safety-First | PASS | Discovery and validation remain read-only. The typed confirmation stays required. |
| IV. Full Deployment Pipeline | PASS | The implementation task includes the required verification and deployment gates. |
| V. Observability & Logging | PASS | The plan includes safe action logging. |
| VI. Inline Comments | PASS | The implementation task requires compliant inline comments. |
| VII. Action Logging | PASS | The implementation task requires logs before and after meaningful actions. |
