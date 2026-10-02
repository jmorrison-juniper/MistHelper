# Implementation Plan: Maps Site Selection

**Branch**: `jmorrison-juniper-maps-site-selection-race` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: [Specification](spec.md) and [requirements checklist](checklists/requirements.md).

## Summary

Add an independent site-choice counter beside the existing map-view counter.
Advance it before each site change can return, including blank selections.
Capture the occurrence for each request.
Reject stale success and failure continuations before either can alter controls or notifications.
Preserve the existing fetch call, option fields, map rendering, and theme behavior.
Show observable current failures through the existing map placeholder.

## Technical Context

**Language/Version**: Python 3.13.13 and the existing browser JavaScript.

**Primary Dependencies**: Existing Flask, Jinja, Plotly, pytest, Playwright, and Node. No dependency changes.

**Storage**: One page-local integer. No database, schema, persistent state, or migration.

**Testing**: Real Chromium requests to a private threaded local server, actual-script Node execution, and independent observation guards.

**Target Platform**: The existing Maps page on supported hosts.

**Performance Goals**: Constant-time occurrence checks. Zero extra requests, retries, or cancellations.

**Constraints**: The exact eight-file reservation, synthetic records, isolated loopback server, and unchanged production request semantics.

**Scale/Scope**: One existing template block, two issue-owned tests, four specification files, and one release fragment.

## Constitution Check

Use [the project constitution](../../.specify/memory/constitution.md) and the repository's [plan template](../../.specify/templates/plan-template.md).
Use semantic classes for test support.
Keep test functions small and typed.
Use bounded ASCII action logs without response bodies or credentials.
Use rare meaningful comments, as the current request requires.
Do not add a per-line comment sweep.

The production page already uses global JavaScript handlers.
Keep that existing architecture for this narrow race repair.
Do not introduce a wrapper, module, class migration, or unrelated refactor.
The existing directory counts exceed the Five-Item Rule.
This repair does not expand production packages or repair unrelated structural debt.

## Project Structure

### Documentation for this feature

```text
specs/3366-map-site-selection/
|-- spec.md
|-- plan.md
|-- tasks.md
`-- checklists/
    `-- requirements.md
```

### Source code

| Role | Exact owned path |
| - | - |
| Production | `web_portal/templates/map_viewer.html` |
| Browser proof | `tests/e2e/test_map_site_selection_race_journey.py` |
| Offline proof | `tests/unit/web_portal/test_map_site_selection_race.py` |
| Specification | `specs/3366-map-site-selection/spec.md` |
| Checklist | `specs/3366-map-site-selection/checklists/requirements.md` |
| Plan | `specs/3366-map-site-selection/plan.md` |
| Tasks | `specs/3366-map-site-selection/tasks.md` |
| Release note | `changelog.d/issue-3366-map-site-selection.md` |

All temporary artifacts belong below `data/issue-3366/`.
No shared `.specify` state, agent-context file, browser fixture, port policy, or shared record changes.

## Phase 0: Research Decisions

### Selection identity

The existing `mapViewNumber` protects map rendering, not map lists.
A separate `siteChoiceNumber` applies the same current-counter guard pattern.
Site identifier comparison fails for A-B-A.
Reusing `mapViewNumber` incorrectly couples list validity to map changes.
Cancellation cannot prove that a late completion is harmless.

### Current errors

The list route can return an explicit error with `maps: []`.
Transport rejection, failed HTTP status, invalid JSON, or an invalid list must not enable an empty control.
Use the existing placeholder and fixed safe text: `Failed to load floor plans.`.
Validate all list entries before the first option append.
Require each entry's existing fields without adding identifier or dimension restrictions.
Keep valid empty arrays successful.
Do not change backend error conversion.

### Browser and offline evidence

Reuse the existing threaded Werkzeug server pattern and real shipped assets.
Give the new test its own server, operating-system-assigned port, request ledger, and response holds.
Synthetic HTTP responses replace the backend boundary, not the browser's fetch or handlers.
A streamed connection failure provides an actual failed browser request.
Node executes the actual inline script with controlled DOM and promise boundaries.
Expected controls come from independent fixture facts, never the production counter.

## Phase 1: Design and Contracts

1. Advance and capture the site-choice occurrence.
2. Keep the existing blank option reset, disabled control, and `clearMap()` call.
3. If the site is blank, return without a request.
4. Keep the existing map-list URL and single-argument fetch call.
5. Before a success or failure changes state, compare its captured occurrence with the current counter.

Current success preserves option order, identifiers, safe labels, image suffixes, width, and height.
It enables the control after population and selects no map automatically.
An empty array enables only the blank option.
Current failure restores blank, disabled controls and one visible fixed error.
Stale success and failure cause zero state changes.
Existing map-data, image, view-counter, and theme code remain byte-for-byte unchanged.

## Validation Guide

### Red-first proof

Initial source: `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.

Initial template SHA-256: `ac1bd1a420ed6f39b2923368edac2bac902290201459dfe30b65c4fda0efdf5f`.

Hold A's actual request, choose B, complete B, then release A.
Require the exact B-only options and two GET requests.
Record the defect-specific assertion failure before any production edit.
Also prove the original offline A-B, A-B-A, and A-blank-A contamination.

### Behavior and guard matrix

Cover stale success and failure while the latest choice is pending, successful, failed, blank, or repeated.
Cover current connection failure, HTTP 4xx and 5xx, invalid JSON, empty body, explicit errors, and invalid lists.
Cover valid empty lists, blank map clearing, and error replacement by a new selection.
Check every option's label, identifier, dimensions, and selected state.
Inspect complete displayed-map state before and after stale responses.
Observe DOM mutations to detect temporary changes.
Require actual completion callbacks through precise Chromium coverage.
Bound each request wait at 15 seconds.

Prove the observation guard rejects contamination, A1 revival, duplicates, wrong enabled state, and error replacement.
Prove missing or unreadable source, control snapshots, and request-order evidence fail.
Print nonzero checked counts.
Reject unexpected remote browser requests.

### Changed-region coverage

Start V8 precise coverage before navigation.
Retain script source, range offsets, and call counts under issue-owned paths.
Map the inline script to the changed template statements.
Require every changed executable statement to run.
Require both current and stale guard outcomes, blank and nonblank choices, success and failure, and empty and nonempty lists.
Fail for missing input, absent ranges, wrong source identity, or zero measured cases.
Python coverage cannot prove browser JavaScript execution.

### Adjacent regressions

Run unchanged `tests/maps/` and the image-route, safe-text, and title-theme unit tests.
Run unchanged `test_map_viewer_image.py` and `test_map_title_contrast.py`.
Those tests preserve images, devices, map-data errors, late completions, zoom, and all four title themes.
Require measured title contrast of at least 4.5:1 without additional requests.

### Required local gates

Read scopes from `.github/workflows/ci.yml` and settings from `pyproject.toml`.
Run full Ruff, full Black, exact CI MYPY_PATHS, configured Bandit, and the unchanged test-quality ratchet.
Run runtime dependency audit, owned Markdown links, and STE.
Retain exact commands, results, checked counts, and unavailable capabilities in [tasks.md](tasks.md).
Do not change settings, suppressions, exclusions, baselines, or dependencies.

Python 3.13.13, Node, timeout support, and actual Chromium are available in this worktree.
The STE dictionary and PowerShell are unavailable.
Report them explicitly without a passing measurement.
Do not manufacture a dictionary or start unapproved services.

Full unrelated test suites and their store-dependent journeys remain remote CI requirements.
The explicit publication release also requires the full CI browser collection locally.
Use its existing isolated process fixture and in-memory records.
Do not provision stores or change shared browser support.
Require all issue and adjacent Maps cases to execute without skips.
Report each pre-existing optional skip by name.
Keep all original required checks active after publication.

## Publication Contract

Complete the local repair, proofs, gates, analysis, and Conventional Commit first.
Stop before push or pull request creation.
Wait for the parent's explicit full verified-main SHA release at position 15 after issue #3353.
An observed main revision, sibling report, or initial SHA is not release authority.
The parent supplied the explicit release on `1a06f1516223a20eef715d91a32255e6219331db`.

After release, rebase onto that verified SHA and read current manifests.
Repeat local proof, push once, and use the original complete pull request template.
Require all quality, title, CodeQL, and strict base checks on the exact head.
Use a protected exact-head squash merge without admin bypass or branch deletion.
Run exact merged-main local proof in this same isolated worktree.
No deployment, firmware, cloud login, production store, or container action is authorized.

## Complexity Tracking

| Existing constraint | Bounded exception | Reason |
| - | - | - |
| Global JavaScript handlers | Keep the existing template handlers. | A class migration increases race risk without improving the requested guard. |
| Large existing directory counts | Add only the two explicitly reserved test files. | Unrelated package restructuring violates the one-issue boundary. |
