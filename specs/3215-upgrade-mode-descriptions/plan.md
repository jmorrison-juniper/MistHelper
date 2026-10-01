# Implementation Plan: Upgrade mode descriptions

**Branch**: `jmorrison-juniper-upgrade-mode-descriptions` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: The specification in this directory.

## Summary

Replace only the descriptions in the two selection templates.
Add dedicated offline rendering contracts and an isolated Chromium journey.
Keep every product route and safety control unchanged.

## Technical Context

**Language/Version**: Python 3.13 and Jinja templates.

**Primary Dependencies**: Existing Flask, pytest, pytest-playwright, and pinned development tools.

**Storage**: Existing in-memory test stores only.

**Testing**: Real Flask routes, rendered HTML, and isolated Chromium.

**Target Platform**: The current macOS worktree and the existing Linux CI runner.

**Project Type**: A description repair for the upgrade portal.

**Performance Goals**: No additional cloud request or server operation.

**Constraints**: No product behavior, firmware order, strategy, lock, schema, key, dependency, or baseline changes.

**Scale/Scope**: Two existing templates, two dedicated test modules, five specification files, and one release note.

## Constitution Check

The existing test directories exceed five children.
The source directory contains four selection templates.
Only existing product files change, and no product class or module is added.
The reservation requires two dedicated test modules under the existing fixture structure.
A separate maintenance issue can organize older test modules without delaying this repair.

The new helpers remain small and have explicit types.
Tests replace every cloud and store boundary with existing stand-ins.
The change preserves typed confirmation, CSRF protection, and selection validation.
The parent requires a local commit before any publication grant.
That explicit sequence replaces the older automatic deployment instructions for this task.

## Current Behavior Trace

| Behavior | Current implementation |
| - | - |
| Single-site workflow | `select.site_inventory_page` opens the inventory and its capture link. Run options and confirmation use `/runs/<run_id>/...`. |
| Single-site cloud routes | `upgrade_service._build_plan` selects `upgradeSiteDevices` or `upgradeDevice`. SSR targets use `upgradeOrgSsrs`. |
| Multi-site selection | `select.choose_sites` saves the ordered sites and opens `/upgrade/org/options`. |
| Multi-site cloud routes | `AggregateUpgradeService` creates one AP organization child and the existing site or SSR plans for other targets. |
| Shared pre-check adoption | `org_upgrade.precheck_gate` uses the same adopter as the single-site route. `StandalonePrecheckAdopter` reads the newest verified standalone capture. |
| Missing pre-check captures | `/api/org-upgrades/prechecks/<site_id>` starts the selected site's capture from the confirmation page. |
| Multi-site post-check | `OrgPostCheckStage` takes captures after the phases for sites with accepted writes. Manual mode holds those captures. |
| Comparison | `OrgPostCheckView` exposes `/compare?before=...&after=...` only for a verified post-check with a stored pre-check. |

## Project Structure

The exact reservation contains these files.

```text
src/upgrade_portal/app/assets/templates/select/mode.html
src/upgrade_portal/app/assets/templates/select/sites.html
tests/contract/upgrade_portal/test_mode_descriptions.py
tests/e2e/upgrade_portal/test_mode_descriptions_journey.py
specs/3215-upgrade-mode-descriptions/spec.md
specs/3215-upgrade-mode-descriptions/plan.md
specs/3215-upgrade-mode-descriptions/tasks.md
specs/3215-upgrade-mode-descriptions/implementation.md
specs/3215-upgrade-mode-descriptions/analysis.md
changelog.d/issue-3215-upgrade-mode-descriptions.md
```

## Implementation Sequence

1. Add the dedicated tests.
2. Record red results from the actual rendered false descriptions.
3. Replace the descriptions and add stable identifiers.
4. Run the focused contracts, Chromium journeys, and applicable quality commands.
5. Record the results and commit the exact reserved files.

## Quality Evidence

Run Ruff, Black, the configured type scope, Bandit, the unchanged test quality ratchet, and Markdown link checks.
Measure coverage of the selection routes with the existing selection contracts.
Run the existing typed-confirmation contracts without a cloud write.
Keep every new Chromium case separate from the known adjacent version-options skip.

The configured STE dictionary and the licensed source PDF are absent in this worktree.
A dictionary-free result cannot prove the configured STE gate.
Report that missing capability explicitly unless an authorized dictionary becomes available.

## SpecKit Execution

The prerequisite command failed with `env: pwsh: No such file or directory`.
This worktree has no PowerShell capability.
Use the current specification, plan, and task templates as a file-only equivalent.
Keep the app-managed branch, shared `.specify` files, and agent instructions unchanged.
Record implementation and analysis in this issue's directory only.
