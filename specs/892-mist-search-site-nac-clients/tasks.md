# Tasks: searchSiteNacClients

**Input**: [spec.md](./spec.md) and [plan.md](./plan.md)  
**Branch**: `feat/1400-search-site-nac-clients`

## Phase 1: Setup

- [X] T001 Confirm menu 257 avoids the active menu conflicts (248-256 claimed by concurrent PRs).
- [X] T002 Confirm the existing primary-key and Arango mappings.

## Phase 2: Implementation

- [X] T003 Add `searchSiteNacClients` to the site search exporter bindings.
- [X] T004 Register menu 257 in `MistHelper.py`.
- [X] T005 Register menu 257 as `interactive_safe`.
- [X] T006 Add focused endpoint binding tests.

## Phase 3: Documentation

- [X] T007 Update the README operation count and menu description.
- [X] T008 Add the CHANGELOG entry for issue #1400.
- [X] T009 Regenerate the menu reference and highlights.

## Phase 4: Validation and Delivery

- [X] T010 Run focused tests and quality checks.
- [X] T011 Commit and push the feature branch.
- [X] T012 Open PR #2390 that closes #1400.
- [X] T013 Merge after required checks pass. Rebased onto `main` after menus
      254-256 landed, moved this feature to the next free number (257), and
      re-ran the full guardrail suite before merge.
