# Tasks: Endpoint family per-choice prompts

**Input**: Design documents from `specs/3256-family-prompts/`

## Phase 1: Setup

- [x] T001 Read issue #3256 and the fleet charter. (delivered: specs/3256-family-prompts/spec.md)
- [x] T002 Create the worktree from current `origin/main`. (delivered: specs/3256-family-prompts/plan.md)
- [x] T003 Post the SpecKit start comment on #3256. (delivered: data/issue-3256-comments/start.md)

## Phase 2: Implementation

- [x] T004 Add endpoint family option metadata in `web_portal/services/operation.py`. (delivered: web_portal/services/operation.py)
- [x] T005 Change menus 263 through 268 from `cli_only` to dynamic interactive rows. (delivered: web_portal/services/operation.py)
- [x] T006 Add dynamic parameter rendering to `web_portal/static/js/operations.js`. (delivered: web_portal/static/js/operations.js)
- [x] T007 Preserve prompt answer order in `collectInputAnswers()`. (delivered: web_portal/static/js/operations.js)

## Phase 3: Tests

- [x] T008 Update `tests/unit/web_portal/test_portal_required_answers.py` for the six endpoint family rows. (delivered: tests/unit/web_portal/test_portal_required_answers.py)
- [x] T009 Prove the guard fails before the implementation. (delivered: data/issue-3256-guard-red.txt)
- [x] T010 Prove the guard passes after the implementation. (delivered: data/issue-3256-guard-green.txt)

## Phase 4: Verification

- [x] T011 Run py_compile, ruff, black, pytest, and the test quality analyzer. (delivered: specs/3256-family-prompts/quickstart.md)
- [x] T012 Start the private portal on port 9606. (delivered: data/issue-3256-browser-check.py)
- [x] T013 Verify one operation in each menu 263 through 268 through the browser. (delivered: data/issue-3256-screenshots/results.json)
- [x] T014 Add the release note fragment. (delivered: changelog.d/issue-3256-family-prompts.md)
- [x] T015 Open a pull request without the auto-merge label. (delivered: #3284)
