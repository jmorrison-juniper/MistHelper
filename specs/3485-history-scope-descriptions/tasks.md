# Tasks: History scope descriptions

**Input**: The specification and design files in `specs/3485-history-scope-descriptions/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), and [history-scope.md](contracts/history-scope.md).

**Tests**: The user requires unit, real route, and Chromium evidence.

**Organization**: Complete the site descriptions first.
Then verify organization descriptions and unchanged history behavior.

## Phase 1: Setup

- [x] T001 Claim issue #3485 and record the exact reservation in `specs/3485-history-scope-descriptions/.spec-context.json`. (delivered: specs/3485-history-scope-descriptions/.spec-context.json)
- [x] T002 Complete the issue-owned specification and design in `specs/3485-history-scope-descriptions/plan.md`. (delivered: specs/3485-history-scope-descriptions/plan.md)

## Phase 2: Foundational

- [x] T003 Restore missing tools from `requirements.txt` and `requirements-dev.txt` with the existing worktree bootstrap. (delivered: .venv/bin/python)
- [x] T004 Verify the existing scope and organization contracts before changing `src/upgrade_portal/app/routes/review.py`. (delivered: tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py)

The starting revision passed 270 existing scope and organization cases.
The Bash plan script returned code 127 because it is absent.
The plan records the file-only workflow.

## Phase 3: User Story 1 - Site history (Priority: P1)

**Goal**: Correct all nine descriptions for an empty site with populated other sites.

**Independent Test**: Render the real route with existing synthetic query inputs.
Verify each complete note, caption, and empty statement.

- [x] T005 [P] [US1] Add named and unnamed site text cases. (delivered: tests/unit/upgrade_portal/test_history_card_scope.py)
- [x] T006 [P] [US1] Prove the original rendered empty-site failure across all nine descriptions. (delivered: tests/contract/upgrade_portal/test_history_card_scope_routes.py)
- [x] T007 [US1] Add the bounded description record and card scope. (delivered: src/upgrade_portal/app/history_descriptions.py)
- [x] T008 [US1] Wire validated scope fields into the existing history context. (delivered: src/upgrade_portal/app/routes/review.py)
- [x] T009 [US1] Print settled descriptions and stable note identifiers. (delivered: src/upgrade_portal/app/assets/templates/review/history.html)
- [x] T010 [US1] Verify stored-name escaping and ignored query names. (delivered: tests/contract/upgrade_portal/test_history_card_scope_routes.py)

## Phase 4: User Story 2 - Organization history (Priority: P1)

**Goal**: Name the selected organization without adopting a site's name.

**Independent Test**: Render populated and empty organization pages.
Verify all notes, captions, and empty statements.

- [x] T011 [US2] Add organization text cases. (delivered: tests/unit/upgrade_portal/test_history_card_scope.py)
- [x] T012 [US2] Pin complete organization descriptions and empty states. (delivered: tests/contract/upgrade_portal/test_history_card_scope_routes.py)
- [x] T013 [US2] Verify site and organization Chromium journeys without a skip. (delivered: tests/e2e/upgrade_portal/test_history_card_scope_journey.py)

## Phase 5: User Story 3 - Existing behavior (Priority: P2)

**Goal**: Preserve readers, identifiers, totals, page bounds, attribution, and access decisions.

**Independent Test**: Repeat existing contracts and inspect actual query evidence.

- [x] T014 [US3] Verify exact identifiers, totals, query binds, and later empty pages. (delivered: tests/contract/upgrade_portal/test_history_card_scope_routes.py)
- [x] T015 [US3] Verify unchanged authentication and failure responses. (delivered: tests/contract/upgrade_portal/test_history_card_scope_routes.py)
- [x] T016 [US3] Confirm unchanged reader bodies and the complete existing scope class. (delivered: src/upgrade_portal/app/routes/review.py)

## Phase 6: Local completion

- [x] T017 Add the unique release note. (delivered: changelog.d/issue-3485-history-scope-descriptions.md)
- [x] T018 Repeat the full affected matrix and all configured gates after extraction. (delivered: specs/3485-history-scope-descriptions/quickstart.md)
- [x] T019 Resolve C1 through the bounded extraction and verify requirement coverage. (delivered: specs/3485-history-scope-descriptions/checklists/requirements.md)
- [x] T020 Record exact post-extraction local results and remaining publication limits. (delivered: specs/3485-history-scope-descriptions/.spec-context.json)
- [x] T021 Refresh the native-owner journey and verify the complete current-base collection, negative guards, and local checks. (delivered: tests/e2e/upgrade_portal/test_history_card_scope_journey.py)
- [x] T022 Correct the shared audit assumption with exact native states, explicit decision trials, and complete 603-case execution. (delivered: tests/e2e/upgrade_portal/test_history_card_scope_journey.py)

The parent grants sole publication and delivery on `92dc5d3ebf5fa6d2b9ddba536b5c3bc6cd4ca232`.
The session task records track protected publication and exact merged-main verification separately.
Do not infer a different base from a later observed revision.

## Dependencies & Execution Order

T001 precedes T002.
T003 and T004 precede every implementation task.
T005 and T006 can proceed independently after the design.
T006 must show the original failure before T007 through T009.
T008 requires T007 and precedes every post-extraction verification.
T010 through T016 require the implemented descriptions.
T018 requires all dedicated tests and the release note.
T019 and T020 require the local results.
T021 requires the explicit refresh grant and repeats all affected checks after the rebase.
T022 requires the completed full-scope failure and the parent's bounded corrective authority.
The correction preserves the original 600 cases and all 603 current case identifiers.

## Parallel Opportunities

The initial unit and route test files have no shared edit.
After implementation, static gates can run independently from focused browser checks.
Do not run parallel tests against the same process-owned browser store.

## Implementation Strategy

Write the failing real route case first.
Keep the scope and template changes together.
Verify all three stories before the local commit.
Report the clean local commit to the parent without publication.
