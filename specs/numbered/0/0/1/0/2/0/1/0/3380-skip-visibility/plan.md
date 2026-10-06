# Implementation Plan: Browser Skip Visibility

**Branch**: `jmorrison-juniper-fix-3380-skip-visibility` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Issue**: #3380

**Input**: The approved specification and its 16-site implementation manifest.

## Summary

Add one static AST guard before any browser-test repair.
The first guard run must fail with exactly 16 findings.
Each finding must name the file, source location, and missing-content condition.

Replace only the 16 approved UI-loss or seeded-data skips with explicit failures.
Keep browser capability skips and all other skip categories unchanged.
Update the capture click walk to use the AP, switch, and gateway version selectors.
Require each selector to be visible and to contain a real version option.
Preserve both confirm-page checks and the browser-driven History return.

Production code, shared fixtures, shared seeded-data fixtures, and unrelated tests remain unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing pytest, pytest-playwright, Playwright sync API, and Python `ast`.
The change adds no dependency.

**Storage**: Existing isolated browser-test stores only.
The change adds no schema, persistence, or seeded-data format.

**Testing**: One static guard test and the existing focused E2E modules.
Run browser validation with Microsoft Edge through `--browser-channel msedge`.

**Target Platform**: Windows 11, macOS, and Linux for static checks.
The focused browser evidence uses the repository-supported Edge configuration.

**Project Type**: Existing Python CLI and web portal test suite.

**Performance Goals**: The AST guard parses ten fixed Python files once.
The browser changes add no polling loop and no product request.

**Constraints**: Repair exactly 16 approved statements.
Keep genuine browser capability skips.
Do not change production code or shared fixtures.
Do not edit `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.

**Scale/Scope**: One new guard file and ten existing E2E files.
No product model, API contract, or interface changes apply.

## Constitution Check

The review uses `.specify/memory/constitution.md`, version 1.5.0.

| Principle | Pre-design decision | Post-design decision |
| --- | --- | --- |
| I. Five-Item Rule | Keep the repair in existing E2E modules. Add one focused guard module. | Pass. The design adds no product hierarchy and no helper package. |
| II. Class-Based Architecture | Add no production abstraction or wrapper. Keep test helpers in their current owners. | Pass. The design changes assertions and one static guard only. |
| III. Safety-First | Convert false-success skips into named failures. Preserve genuine capability skips. | Pass. Missing required UI or data cannot report success. |
| IV. Deployment Pipeline | Run each applicable local gate. Record the red-first and green results. | Pass by design. Delivery remains a later implementation step. |
| V. Observability | Make each failure name the absent row, control, option, comparison, record, or link. | Pass. The test output identifies the failed precondition. |
| VI. Inline Comments | Preserve the repository comment style in each changed test block. | Pass by design. New executable lines require cause and purpose comments. |
| VII. Action Logging | Add no product action. Use guard logging for scan scope and result counts. | Pass. The guard reports its measured files, sites, and findings. |

The pre-design and post-design checks pass.
The design adds no justified constitution violation.
The design does not require research, a data model, a quickstart, or a contract.

## Project Structure

### Documentation for This Feature

```text
specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/
|-- spec.md
`-- plan.md
```

Do not create `research.md`, `data-model.md`, `quickstart.md`, or `contracts/`.
This change adds no product model or interface.

### Approved Implementation Manifest

```text
tests/
|-- guardrails/
|   `-- test_e2e_skip_visibility.py
`-- e2e/
    |-- web_portal/
    |   `-- test_operations_panel_workflow.py
    `-- upgrade_portal/
        |-- test_browser_token_signin.py
        |-- test_capture.py
        |-- test_comparison.py
        |-- test_history.py
        |-- test_signin.py
        |-- test_site_selection.py
        |-- test_stop.py
        |-- test_two_operators.py
        `-- test_run_controls/
            `-- test_existing.py
```

The implementation must not add a production file or shared fixture to this manifest.
The implementation must not add another E2E file.
The implementation must not change a skip category outside the 16 approved sites.

## Approved Repair Inventory

This table is the implementation manifest.
Keep every identifier, file, and missing condition.

| ID | Test file | Missing condition that must fail |
| --- | --- | --- |
| R-01 | `tests/e2e/web_portal/test_operations_panel_workflow.py` | No accordion category reveals an operation row |
| R-02 | `tests/e2e/upgrade_portal/test_browser_token_signin.py` | No element matches the required row prefix |
| R-03 | `tests/e2e/upgrade_portal/test_capture.py` | The site picker has no site row |
| R-04 | `tests/e2e/upgrade_portal/test_capture.py` | A required type version control is absent or has no real option |
| R-05 | `tests/e2e/upgrade_portal/test_comparison.py` | A required comparison table has no row |
| R-06 | `tests/e2e/upgrade_portal/test_comparison.py` | The expected comparison does not render |
| R-07 | `tests/e2e/upgrade_portal/test_comparison.py` | The picker has no stored-capture option |
| R-08 | `tests/e2e/upgrade_portal/test_history.py` | The site picker has no site row |
| R-09 | `tests/e2e/upgrade_portal/test_history.py` | The seeded store has no history row |
| R-10 | `tests/e2e/upgrade_portal/test_history.py` | A required previous-page control has no link |
| R-11 | `tests/e2e/upgrade_portal/test_signin.py` | No element matches the required row prefix |
| R-12 | `tests/e2e/upgrade_portal/test_site_selection.py` | No element matches the required row prefix |
| R-13 | `tests/e2e/upgrade_portal/test_site_selection.py` | The inventory table has no row |
| R-14 | `tests/e2e/upgrade_portal/test_stop.py` | The site picker has no site row |
| R-15 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | The site picker has no site row |
| R-16 | `tests/e2e/upgrade_portal/test_two_operators.py` | The site picker has no site row |

## Phase 0: Red-First Static Guard

Complete this phase before any E2E repair.

1. Add `tests/guardrails/test_e2e_skip_visibility.py`.
2. Store the 16 approved records as immutable guard data.
3. Give each record its ID, repository path, owning function, and stable message fragment.
4. Parse each source file with `ast.parse`.
5. Locate the approved condition by its owner and message fragment.
6. Report a finding when the matched call target is `pytest.skip`.
7. Fail if an approved site cannot be located.
8. Print the number of examined sites and the number of findings.
9. Include the repair ID, path, line, and condition in each finding.
10. Add an in-memory negative test that proves one forbidden skip fails.
11. Add an in-memory positive test that proves an explicit failure passes.
12. Add an input-failure test that proves an absent approved site fails.

Run the guard before an E2E edit:

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\test_e2e_skip_visibility.py
```

The first repository scan must fail.
Its proof line must report 16 examined sites and 16 findings.
Capture the complete failing output in the implementation record.
Do not weaken the guard or change its manifest after this red result.

## Phase 1: Convert the Approved Skips

Change each approved `pytest.skip` call to an explicit failure.
Use `raise AssertionError(...)` when a helper must stop and return a typed value.
Use an assertion when the value can remain in the current block.

Keep each existing cause in the failure text.
Name the missing selector, row prefix, table, comparison, capture, site, or page link.
Do not use a generic message such as `required data is missing`.

Do not change these categories:

- A missing Playwright package, browser binary, or browser fixture.
- A browser launch failure that states the unavailable capability.
- A browser server capability that prevents the test from starting.
- Any nonapproved lock, conflict, store, timeout, or run-state skip.

After all 16 repairs, rerun the guard.
The proof line must report 16 examined sites and zero findings.

## Phase 2: Repair the Capture Click Walk

Remove `VERSION_SELECT_ALL_ID` from `test_capture.py`.
Add one ordered tuple with these live selectors:

1. `upgrade-version-select-ap`
2. `upgrade-version-select-switch`
3. `upgrade-version-select-gateway`

For each selector:

1. Resolve the control by `data-testid`.
2. Require the control to be visible.
3. Require more than the empty prompt option.
4. Fail with the selector identifier when the control is absent.
5. Fail with the selector identifier when no real option exists.
6. Select the first real option at index 1.

Keep the existing save click.
Keep the first confirm-page URL and input checks.
Keep the History link click and run selection.
Keep the confirm link click and second confirm-page checks.
Do not replace a browser action with an API call.

## Phase 3: Focused Validation

Set strict browser mode for each browser run:

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
```

Run the static guard:

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\test_e2e_skip_visibility.py
```

Expected result: the guard passes with 16 examined sites and zero findings.

Run the capture click walk alone:

```powershell
python -m pytest tests\e2e\upgrade_portal\test_capture.py::TestUpgradeJourney::test_walk_from_the_site_list_reaches_the_confirm_page --browser-channel msedge -q -rs
```

Expected result: one pass and zero skips.
The test must reach both confirm-page visits through browser actions.

Run the ten affected modules:

```powershell
python -m pytest `
  tests\e2e\web_portal\test_operations_panel_workflow.py `
  tests\e2e\upgrade_portal\test_browser_token_signin.py `
  tests\e2e\upgrade_portal\test_capture.py `
  tests\e2e\upgrade_portal\test_comparison.py `
  tests\e2e\upgrade_portal\test_history.py `
  tests\e2e\upgrade_portal\test_signin.py `
  tests\e2e\upgrade_portal\test_site_selection.py `
  tests\e2e\upgrade_portal\test_stop.py `
  tests\e2e\upgrade_portal\test_run_controls\test_existing.py `
  tests\e2e\upgrade_portal\test_two_operators.py `
  --browser-channel msedge -q -rs
```

Expected result: each affected test passes with zero missing-content skips.
Any remaining skip must name a genuine browser capability.

## Applicable Repository Gates

Run each command in the isolated `.venv`.
Stop at the first failure and repair its cause.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src\ MistHelper.py wsgi.py scripts\mist_ideas_analyzer_pkg\__init__.py scripts\mist_ideas_distiller_v2_pkg\__init__.py --config-file pyproject.toml
python -m pytest tests\guardrails
bandit -c pyproject.toml -r . -q
radon cc src\ MistHelper.py wsgi.py scripts\analyze_marvis_pcap.py scripts\probe_zscaler_endpoints.py tests\unit\utils\test_zscaler_catalogue.py -j | complexity-gate --max 10
vulture src\ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src\ wsgi.py web_portal
interrogate src\ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
```

After the implementation commit, run the required test-quality comparison:

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
git rev-parse --verify "origin/${BASE_REF}^{commit}"
test-quality-analyzer --gate `
  --config .github\test-quality-config.toml `
  --baseline .github\test-quality-baseline.json `
  --changed-from "origin/$BASE_REF" `
  --full-gate-path .github\workflows\ci.yml `
  --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

Run the full E2E folder when the focused modules pass:

```powershell
python -m pytest tests\e2e\upgrade_portal --browser-channel msedge -q -rs
```

Record the pass, fail, and skip counts.
Each skip must state a genuine browser capability.

## Scope Verification

Before delivery, inspect the complete diff.
The diff must contain only the approved implementation manifest and the issue release-note fragment.
The release-note fragment is required during implementation, but it is not part of this planning-only change.

Confirm these exclusions:

- No file under `src/` changed.
- No shared fixture changed.
- No shared seeded-data fixture changed.
- `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` did not change.
- No timeout, marker, order rule, or unrelated assertion changed.
- No nonapproved `pytest.skip` changed.
- No direct API cleanup replaced a browser step.

## Design Completion

No technical clarification remains.
The static guard provides the required red-first proof.
The approved manifest fixes all 16 false-success sites.
The capture walk uses the three live type selectors.
The validation matrix proves focused behavior and repository quality.
