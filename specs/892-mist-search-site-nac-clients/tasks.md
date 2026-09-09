# Tasks: searchSiteNacClients

**Input**: [spec.md](./spec.md) and [plan.md](./plan.md)  
**Branch**: `feat/1400-search-site-nac-clients`

## Phase 1: Setup

- [X] T001 Confirm menu 258 avoids the proposed menu sequence.
- [X] T002 Confirm the existing primary-key and Arango mappings.

## Phase 2: Implementation

- [X] T003 Add `searchSiteNacClients` to the site search exporter bindings.
- [X] T004 Register menu 258 in `MistHelper.py`.
- [X] T005 Register menu 258 as `interactive_safe`.
- [X] T006 Add focused endpoint binding tests.

## Phase 3: Documentation

- [X] T007 Update the README operation count and menu description.
- [X] T008 Add the CHANGELOG entry for issue #1400.
- [X] T009 Regenerate the menu reference and highlights.

## Phase 4: Validation and Delivery

- [X] T010 Run focused tests and quality checks.
- [X] T011 Commit and push the feature branch.
- [X] T012 Open PR #2390 that closes #1400.
- [ ] T013 Merge after required checks pass, if policy permits. Blocked: PR #2390 currently has `mergeable_state=dirty`; resolve the base-branch conflict, push the resolution, then merge.
