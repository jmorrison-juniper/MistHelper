# Tasks: Sign-in credential layout

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [presentation contract](contracts/presentation.md).
**Issue**: [#3295](https://github.com/jmorrison-juniper/MistHelper/issues/3295).
**Branch**: `jmorrison-juniper-sign-in-credential-layout`.
**Base**: `5d38898af5639e90715ec57eb8d48d2985e1acf8`.

This file uses the current SpecKit task template through the authorized feature-only equivalent.
PowerShell is absent. The mandatory Git hook did not run successfully.
No shared SpecKit state, branch hook, companion hook, or optional commit hook changed.
The user authorizes implementation and one validated local commit.
Publication remains blocked until the parent grants a full verified-main SHA.

## Phase 1: Setup

- [x] T001 Read the live issue, claim comments, account, and all open-PR pages. Reserve each exact path before edits.
  The claim names app session `10f4fd84-63ac-48ec-a119-2cd59bd172bc` and local session `f7a46f51-5cc9-41f4-88df-d03c7cb15981`.
- [x] T002 Execute feature-only specification and planning with the current templates.
  (delivered: `specs/3295-signin-credential-layout/spec.md`, `specs/3295-signin-credential-layout/plan.md`)
- [x] T003 Restore only this worktree's ignored Python 3.13 environment after the recorded bootstrap failure.

## Phase 2: Foundational prerequisites

- [x] T004 Add process-owned DOM measurements without importing conftest globals.
  (delivered: `tests/e2e/upgrade_portal/issue_3295_signin_support.py`)
- [x] T005 Run real pre-edit Chromium through full `tests/e2e/` collection.
  Preserve the nine required native failures, exact rectangles, inactive FormData state, and actual error-page weight.
  (delivered: session artifact `issue3295-red-native.log` and the later actual error comparison artifacts)

## Phase 3: User Story 1 - Read the token group correctly

- [x] T006 Move the token label, field, and note below the complete mode fieldset.
  (delivered: `src/upgrade_portal/app/assets/templates/auth/signin.html`)
- [x] T007 Add only group spacing and the group's block label.
  (delivered: `src/upgrade_portal/app/assets/static/css/portal.css`)
- [x] T008 Verify exact geometry, accessible name, label focus, and group containment in both native themes.
  Use `tests/contract/upgrade_portal/test_issue_3295_signin_layout.py` and `tests/e2e/upgrade_portal/test_issue_3295_signin_layout.py`.
  Supplemental main assets do not count as native theme coverage.

## Phase 4: User Story 2 - Change modes without losing inputs

- [x] T009 Extend the existing mode callback. Hide and disable only the inactive token.
  (delivered: `src/upgrade_portal/app/assets/static/js/portal.js`, `initBrowserTokenSignIn`)
- [x] T010 Verify keyboard traversal, preserved values, restored validation, and unchanged listener counts.
  Use `tests/unit/upgrade_portal/test_issue_3295_signin_modes.py` and `tests/e2e/upgrade_portal/test_issue_3295_signin_layout.py`.
- [x] T011 Verify zero empty-token requests, one request after ten cycles, clear-before-request, exact refusals, and zero secret exposure.
  Run the existing token-refusal and browser-token journeys unchanged.

## Phase 5: User Story 3 - Read a consistent warning

- [x] T012 Reuse the common bold-prefix rule for danger alerts without changing colors or literal signal words.
  (delivered: `src/upgrade_portal/app/assets/static/css/portal.css`)
- [x] T013 Verify actual sign-in and error prefixes, hidden alerts, escaped messages, adjacent levels, and direct failing controls.
  Run existing prefix tests unchanged. Preserve the dependency-table overflow outside the token group.

## Final Phase: Validation and unpublished handoff

- [x] T014 Run normal and strict full E2E collection. Prove the new module's missing-package behavior.
  Report the unrelated missing-package import fault separately. Do not change its file or the shared harness.
- [x] T015 Run applicable local syntax, Ruff, Black, types, Bandit, quality-input, test-quality, audit, and writing checks.
  Record exact commands, counts, results, and unavailable capabilities in `quickstart.md` and the offline PR draft.

- [x] T016 Verify the source regions and all forbidden paths. Stop every owned browser server and confirm the trail guards.
- [x] T017 Add the unique fragment and preserve all 23 PR checklist items offline.
  (target: `changelog.d/issue-3295-signin-credential-layout.md`)

- [ ] T018 Hold publication at position 38 until the parent grants a full verified-main SHA.
  The local commit and committed-scope receipt belong in the session handoff, not this tracked task record.

## Dependencies & Execution Order

T004 and T005 follow setup. Every source edit follows the real red proof.
US1 and US2 share the token group and its state callback.
US3 changes only the shared prefix selector.

Validation follows all three stories. The local commit follows validation.
The committed-scope check follows the local commit. The parent authorizes no publication task yet.

## Parallel Opportunities

Contract and unit work can run independently of read-only source checks.
Independent quality commands can run together when none changes a required input.
Do not run two browser servers that share a fixture process owner.

## Implementation Strategy

Keep the existing routes, startup rules, transport, messages, and session decisions.
Use the two native upgrade themes for acceptance.
Preserve the measured 400-pixel dependency-table scroll width at a 360-pixel viewport.
Require zero overflow inside the sign-in form and token group.
Do not repair unrelated layout or create another publication window.
