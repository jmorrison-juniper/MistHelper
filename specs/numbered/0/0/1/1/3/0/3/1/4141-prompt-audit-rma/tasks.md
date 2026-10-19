# Tasks: Juniper RMA prompt audit

**Input**: [Specification](spec.md), [plan](plan.md), and the `design/` artifacts.

## Phase 1: Setup

- [x] T001 Record the managed specification and design in spec.md, plan.md, and design/. (delivered: spec.md, plan.md, design/research.md)
- [x] T002 Prepare the worktree environment with scripts/bootstrap_worktree.py and reproduce the zero-prompt report. (delivered: design/research.md)

## Phase 2: Foundational

- [ ] T003 Merge the shared traversal prerequisite and update its commit pin in requirements-dev.txt. Blocked: the separate development-tool session failed before execution.

The shared-tool task blocks exemption removal, not independent control-path tests.

## Phase 3: User Story 1 - Detect unanswered prompts

**Goal**: Examine seven menus without exemptions.

**Independent Test**: Compare the audit with exact expected counts for all seven menus.

- [ ] T004 [US1] Add exact prompt-count assertions in tests/unit/web_portal/test_portal_required_controls.py. Blocked: all seven assertions fail against the current shared tool.
- [ ] T005 [US1] Remove the seven exemptions in tests/unit/web_portal/test_portal_required_controls.py only after the repaired audit passes. Blocked by T003 and T004.
- [x] T006 [US1] Preserve and run tests/e2e/web_portal/test_juniper_menus_browser.py. (delivered: tests/e2e/web_portal/test_juniper_menus_browser.py, 18 passed)

## Phase 4: User Story 2 - Count dependent identifiers

**Goal**: Examine every selectable identifier path in order.

**Independent Test**: Test both key choices and deliberately malformed paths.

- [x] T007 [US2] Add ordered dependent-control expansion and both-choice cases in tests/unit/web_portal/test_portal_required_controls.py. (delivered: tests/unit/web_portal/test_portal_required_controls.py)
- [x] T008 [US2] Add missing, extra, misplaced, empty, and mutually exclusive control cases in tests/unit/web_portal/test_portal_required_controls.py. (delivered: tests/unit/web_portal/test_portal_required_controls.py)
- [ ] T009 [US2] Compare each expanded Juniper path with its audited prompt count in tests/unit/web_portal/test_portal_required_controls.py. The delivered tests compare documented browser counts until T003 completes.

## Phase 5: Validation and Delivery

- [ ] T010 Run the applicable local gates and record exact evidence in design/quickstart.md.
- [ ] T011 Add changelog.d/issue-4141-prompt-audit-rma.md and complete analysis.md.
- [ ] T012 Commit, rebase, push, and create the template pull request that closes #4141.
- [ ] T013 Wait for every required check and CodeQL, enable auto-merge, and confirm the merged revision.

The coordinating session directed this work to stop before a completion pull request.
Keep the seven exemptions and current dependency pin until the shared prerequisite becomes available.
The independent work remains on this branch for a later continuation.

## Dependencies and Execution Order

T001 and T002 precede implementation.
T003 and T004 precede T005.
T007 and T008 precede T009.
T005, T006, and T009 precede T010.
T010 and T011 precede T012.
T012 precedes T013.

## Parallel Opportunities

The shared-tool prerequisite can proceed in its separate checkout while the control-path tests proceed here.
Both stories change one test module, so their edits remain sequential in this checkout.

## Implementation Strategy

Prove the current audit limitation first.
Complete the independent control-path comparison next.
Install the merged shared repair, then remove exemptions only after the focused audit passes.
Run the full affected guard and browser suite before the delivery steps.
