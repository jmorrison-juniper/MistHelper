# Implementation Plan: Strategy Failure Limit

**Branch**: `jmorrison-juniper-strategy-failure-limit-controls`

**Date**: 2026-10-02

**Spec**: [spec.md](spec.md)

**Initial base**: `5d38898af5639e90715ec57eb8d48d2985e1acf8`

## Summary

Add the existing strategy rule to the group for the maximum failure percentage in `upgrade/org_options.html`.
Use one template expression to set its initial hidden and disabled attributes.
Keep shared JavaScript and all server policy unchanged.

## Technical Context

**Language/Version**: Python 3.13.13, Jinja, and unchanged JavaScript.

**Primary Dependencies**: Existing Flask, pytest, and Playwright requirements.

**Storage**: Process-owned test records only. No real cloud or persistent store.

**Testing**: Dedicated unit, template contract, and actual Chromium journeys.

**Target Platform**: The current portal on desktop and narrow viewports.

**Project Type**: An existing web application.

**Performance Goals**: No additional network request or visibility handler.

**Constraints**: Template-only product content. No firmware start, publication, or shared fixture edit.

**Scale/Scope**: One existing control and four strategies.

## Constitution Check

The change adds no production class, method, API surface, or schema.
Existing template and test parents exceed the five-child limit.
Dedicated nested test directories keep new feature code separate without restructuring shared files.
A separately authorized maintenance change can address existing hierarchy debt.
New helpers must remain necessary for direct contract or browser evidence.

The app owns the branch name.
Current Git instructions require Conventional Commits and the Copilot App trailer.
The parent forbids publication and deployment before an explicit verified-base grant.
This local preparation does not authorize a branch change or a deployment.

## Project Structure

### Documentation (this feature)

```text
specs/3326-strategy-failure-limit/
  spec.md
  plan.md
  tasks.md
  contracts/ui.md
```

### Source Code (repository root)

```text
src/upgrade_portal/app/assets/templates/upgrade/org_options.html
tests/unit/upgrade_portal/strategy_failure_limit/
tests/contract/upgrade_portal/strategy_failure_limit/
tests/e2e/upgrade_portal/strategy_failure_limit/
changelog.d/issue-3326-strategy-failure-limit.md
```

**Structure Decision**: Keep the product repair inside the existing failure-field group and its initial-state expression.
Shared JavaScript, routes, stores, fixtures, authentication, styles, and the single-site template remain read-only.
Dependencies, exclusions, baselines, instructions, README, and CHANGELOG also remain read-only.

## Research and Design Decisions

The live issue is open and originally held no assignee or comment.
The complete paginated scan found zero open pull requests and therefore zero conflicting PR paths.
The authenticated account is `jmorrison-juniper`.
The claim reserves the complete feature-owned set.

The original field had no strategy metadata.
`updateOrgAdvancedVisibility` already reads `data-org-requires-strategy`.
`setOrgGroupVisibility` hides the group and disables its controls without clearing their values.

`orgFormBody` builds the save JSON from FormData, which omits disabled controls.

`_base_request_options` already omits the percentage for Big bang.
The feature aligns the page with that policy and does not redefine it.

## Tool and Hook Limitations

The current SpecKit templates and agent procedures supplied the artifact structure.
`pwsh -NoProfile -File .specify/scripts/powershell/setup-plan.ps1 -Json` failed because `pwsh` is absent.
The branch hook would replace the app-managed branch and change shared `.specify` state.
The feature-only equivalent writes the specification, plan, tasks, and UI contract directly.
No shared context file, governance record, or optional commit hook changes.
Read-only requirement-to-test analysis completes the local workflow after implementation.

The first Python 3.13 test command failed because `pytest` was absent.
The standard bootstrap then failed in `ensurepip` with SIGABRT, as described in issue #3701.
UV recreated only the ignored `.venv` of this worktree with seeds, copy mode, and system certificates.
Both unchanged requirement files supplied the restored packages.
No bootstrap source or dependency manifest changed.

## Validation and Local Handoff

Preserve a real current-page red browser result before the template edit.
Render the actual template before JavaScript for all four saved strategies.
Use the actual controller, form, script, and save route for browser evidence.
Require process ownership, native required-field behavior, exact payloads, and zero SDK/start counts.
Use counted direct negative controls for an absent rule and an enabled hidden field.

Collect the complete CI test roots before selecting the affected browser tests.
Run adjacent existing organization options and advanced strategy journeys without fixture or marker changes.
Run applicable syntax, Ruff, Black, type, Bandit, complexity, and test-quality checks.
Keep required input preflight and committed-scope test-quality checks in their documented order.
Explicitly measure feature tests if the analyzer excludes a module through an SDK import.
Record baseline findings and unavailable capabilities separately from acceptance evidence.

Prepare the complete 23-item PR template as an offline session artifact with exact commands and results.
Commit only owned paths. Never amend.
Verify the full local SHA, clean relevant index and worktree, limited product diff, and resource cleanup.
Report the local receipt to the parent at position 40.
Do not push, create a PR, merge, dispatch a workflow, or claim delivery completion.

## Complexity Tracking

The repair needs no new visibility handler, wrapper, alias, compatibility path, or CSS rule.
The feature does not change firmware options, guards, timeouts, confirmations, version choices, or active runs.
Any required expansion outside the reserved paths must reach the parent before an edit.

## Verified Local Evidence

The product diff changes one template with six added lines and two removed lines.
The red Chromium case found the Big bang input visible, enabled, and required.
Its FormData held `17`, and its rectangle measured 1198 by 38 pixels.

The full CI collection found 30,930 tests and ran 177 selected tests.
All 177 tests passed.
Three existing collection warnings remain unchanged.
The 80 dedicated browser cases used the package name `MistHelper.tests.e2e.upgrade_portal.strategy_failure_limit.test_journey`.
The snapshot and worktree held identical bytes for all 11 product and Python test files.

The browser recorded 148 field measurements in both current themes.
The viewports measured 1280 by 900 pixels and 390 by 844 pixels.
Visible fields measured 1198 or 324 pixels wide and 38 pixels high.
Hidden fields measured zero pixels in both directions.

The actual traces held 16 accepted saves and four target refusals.
Canary, RRM, and Serial posted `max_failure_percentage="23"`.
Big bang omitted the key.
The run held 16 process-owned plans, zero SDK calls, and zero firmware-start callbacks.
Each of the 80 owned server listeners stopped, and no owner record remained.

The complete hashed runtime closure covered 105 packages at their installed versions.
The strict audit found zero skipped packages and zero known vulnerabilities.
The standard audit failed in temporary `ensurepip` with SIGABRT.
The hashed audit used `--require-hashes --no-deps --disable-pip --strict` instead.
The Git-only development tools do not belong to this runtime closure and have no package-index audit coverage.

The unchanged quality baseline accepted 725 findings across 1005 discovered files.
The complete gate found zero new findings and zero parse errors.
The dedicated scan analyzed all four new test modules and found zero findings.
The input preflight read and validated all six required files.

STE coverage remains partial because `data/ste_dictionary.json` is unavailable.
No dependency manifest, quality baseline, exclusion, or shared instruction changed.
No live firmware evidence or human review approval belongs to this local preparation.
The publication owner must apply any required firmware-evidence review after the parent's grant.
