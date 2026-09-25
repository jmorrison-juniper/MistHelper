# Tasks: The portal pages use American spelling

**Issue**: #3384 | **Plan**: [plan.md](plan.md)

## Phase 1: Red

- [x] T001 Add `tests/contract/upgrade_portal/test_template_spelling.py` with
  the file guard and the two pattern tests.
- [x] T002 Run the guard on the old templates, and record the red result. The guard read 25
  files and named the five lines of the issue.

## Phase 2: Green

- [x] T003 Change the four lines of `options.html` and the one line of
  `confirm.html`.
- [x] T004 Run the guard tests green. The file gave 3 passed.

## Phase 3: Finish

- [x] T005 Add the release note under `changelog.d/`.
- [x] T006 Run every gate: ruff, black, pydocstyle, interrogate, bandit, radon,
  vulture, the STE lint, and the test quality gate.
- [ ] T007 Rebase onto main after pull request #3385 merges. Run the portal
  suites and the browser suite of the upgrade portal.
- [ ] T008 After the merge, deploy the two templates to port 8056 with a class
  B reload, and read the text in the served files.
