# Implementation Plan: Readable Maps Title

**Branch**: `jmorrison-juniper-map-title-contrast` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: The specification for issue #3365.

## Summary

Read the map card text color with `getComputedStyle`.
Give that color to the Plotly layout font.
Update an existing plot when the theme stylesheet finishes loading.
Keep the image, traces, viewing range, and map selection unchanged.

## Technical Context

**Language/Version**: Existing browser JavaScript and Python 3.13.

**Primary Dependencies**: The shipped Plotly and Bootstrap files, Flask, pytest, and Playwright.
This repair adds no dependency.

**Storage**: The existing browser theme preference remains unchanged.
Tests use temporary directories.

**Testing**: Chromium journeys, offline map route checks, template contracts, and the repository quality ratchet.

**Target Platform**: Existing desktop and mobile browsers.

**Project Type**: The existing Flask web portal.

**Performance Goals**: Update the font without a map data request or another image download.

**Constraints**: Use actual computed colors.
Wait for the stylesheet load event.
Do not change production stores, credentials, APIs, or deployment settings.

**Scale/Scope**: One map template, two regression test modules, one release fragment, the related README description, and this issue's specification.

## Constitution Check

The repair preserves input handling, API behavior, database keys, and destructive-operation safeguards.
The app owns the branch, so the workflow does not create or switch a branch.
The repository Git extension disables automatic commits.
The final commit follows the authoritative Git workflow and includes the required co-author trailer.

The template already contains long JavaScript functions.
This repair changes only the layout font and the completion callback.
It adds one bounded theme-update function.
A separate template cleanup can split the existing long functions.
This issue does not perform that unrelated cleanup.

The test directories already exceed the five-item hierarchy limit.
The isolated regression modules use the existing test layout.
A separate test-layout cleanup can group the map tests.
No new production Python package, module, or class enters that hierarchy.

The required local validation precedes the only initial push.
Every required check and CodeQL must pass before the squash merge.
The exact merge revision receives another local browser and contract run.
The user does not authorize a production deployment or production stores.

## Project Structure

### Documentation

```text
specs/3365-map-title-contrast/
  spec.md
  plan.md
  tasks.md
  checklists/requirements.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/ui.md
```

### Source Code

```text
web_portal/templates/map_viewer.html
tests/e2e/test_map_title_contrast.py
tests/unit/web_portal/test_map_title_theme.py
changelog.d/issue-3365-map-title-contrast.md
README.md
```

**Structure Decision**: Keep the repair beside the existing map template and regression tests.
Reuse the existing simulated map server and floor plan fixture.
Do not edit shared theme code or shared test fixtures.
The generated screenshots remain under the browser runner's controlled output.
The light and dark proof images enter this issue's `design/evidence/` directory.

## Implementation Steps

1. Add the actual-color browser measurement and its offline decision checks.
2. Run the dark-theme journey against the unchanged template to prove the defect.
3. Set `layout.font.color` from the map card text color.
4. Add a stylesheet `load` listener that calls `Plotly.relayout` on an existing plot.
5. Synchronize the font after `Plotly.newPlot` completes, because an image can delay completion.
6. Run the related map journeys and local quality checks.
7. Add the release fragment and complete the SpecKit consistency analysis.

## Workflow Execution

The specification, plan, task generation, implementation, and analysis use the repository SpecKit templates.
The explicit feature directory is `specs/3365-map-title-contrast`.
PowerShell is unavailable on this host.
The app controls the branch, so the branch creation hook cannot run here.
The artifacts retain the complete workflow evidence without changing `.specify/feature.json` or shared agent instructions.

## Complexity Tracking

| Existing limitation | Reason for the narrow scope | Separate repair |
| - | - | - |
| Long JavaScript map functions | The defect concerns the layout font and theme timing only. | Split the map renderer in a dedicated refactor. |
| Large test directories | The user requires isolated browser and offline regression coverage. | Group map tests in a dedicated test-layout refactor. |

## SpecKit Consistency Analysis

The analysis checked the specification, plan, tasks, implementation, and local results.
All eight functional requirements have implementation tasks and measured evidence.
All five success criteria have corresponding browser or offline checks.
No requirement ambiguity, duplicate requirement, or missing behavior remains.
The workflow and existing hierarchy limitations remain explicit above.

| Requirement | Tasks | Evidence |
| - | - | - |
| FR-001 | T008-T010 | Initial and saved theme titles use the actual card text color. |
| FR-002 | T005-T010 | The dark and light titles exceed 4.5:1 without rounding. |
| FR-003 | T011-T013 | Both theme-change directions, a held stylesheet, and a pending image pass. |
| FR-004 | T011-T012 | The zoomed view, image, traces, and selection remain unchanged. |
| FR-005 | T013-T015 | Image status notes and both original late-answer journeys pass. |
| FR-006 | T005, T010 | The browser reads the actual SVG fill and actual card background. |
| FR-007 | T006-T007 | The original defect, near-threshold ratio, invalid colors, and missing inputs fail. |
| FR-008 | T005, T015 | Tests use the simulated cloud and controlled artifact paths without production stores. |
