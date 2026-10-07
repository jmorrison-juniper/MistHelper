---

description: "Implementation tasks for upgrade portal log redaction"

---

# Tasks: Upgrade Portal Log Redaction

**Input**: Routed design documents from
`specs/numbered/0/0/1/1/2/2/0/0/4050-upgrade-portal-redaction/`

**Prerequisites**: `spec.md`, `plan.md`

**Authorized file boundary**:

- `specs/numbered/0/0/1/1/2/2/0/0/4050-upgrade-portal-redaction/spec.md`
- `specs/numbered/0/0/1/1/2/2/0/0/4050-upgrade-portal-redaction/plan.md`
- `specs/numbered/0/0/1/1/2/2/0/0/4050-upgrade-portal-redaction/tasks.md`
- `src/interfaces/portals/upgrade_portal/app/factory.py`
- `tests/unit/upgrade_portal/test_logging_contract.py`
- `changelog.d/issue-4050-upgrade-portal-redaction.md`

## Phase 1: Measurement and red proof

- [ ] T001 Confirm no open pull request owns an authorized file.
- [ ] T002 Confirm `propagate = False` and identify the package logger.
- [ ] T003 Confirm the filter installation points and logger versus handler behavior.
- [ ] T004 Confirm whether a current call site can carry sensitive exception text.
- [ ] T005 Confirm existing tests pass while the handler remains unprotected.
- [ ] T006 Add a test that uses the installed handler through the real package logger.
- [ ] T007 Assert redaction, preserved ordinary output, context fields, and two examined lines.
- [ ] T008 Run the focused test before product changes and record the failing output.
- [ ] T009 Commit the specification and false-coverage repair.

## Phase 2: Product repair

- [ ] T010 Import the existing `SensitiveFilter` in `factory.py`.
- [ ] T011 Attach `SensitiveFilter` to the portal handler after `RunContextFilter`.
- [ ] T012 Keep `package_logger.propagate = False`.
- [ ] T013 Add `changelog.d/issue-4050-upgrade-portal-redaction.md`.
- [ ] T014 Run the focused test and confirm the same proof is green.

## Phase 3: Validation and publication

- [ ] T015 Run the targeted upgrade portal logging tests.
- [ ] T016 Run Bandit on the upgrade portal package.
- [ ] T017 Run full-tree Ruff and Black.
- [ ] T018 Run the test-quality preflight.
- [ ] T019 Commit the product repair separately.
- [ ] T020 Run the changed-from test-quality gate after the test commit.
- [ ] T021 Rebase onto `origin/main`.
- [ ] T022 Push once with `--force-with-lease`.
- [ ] T023 Create a ready pull request with `Closes #4050`.
- [ ] T024 Apply the `security` label and do not apply `auto-merge`.
- [ ] T025 Confirm the pull request is not a draft.

## Dependencies

- T006 depends on T001 through T005.
- T008 depends on T006 and T007.
- T009 depends on T008.
- T010 through T013 depend on T009.
- T014 through T018 depend on T010 through T013.
- T019 depends on T014 through T018.
- T020 depends on T019.
- T021 through T025 run in order after T020.
