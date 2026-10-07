---

description: "Tasks for issue #3332 Child 1 phase-watch wording"

---

# Tasks: Clarify the Phase-Watch Submission Boundary

**Input**: Design documents in `specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/phase-watch-wording.md`

**Tests**: The specification requires direct contract assertions, the focused contract test, and the complete upgrade portal end-to-end suite.

**Scope**: Implement GitHub issue #3332 Child 1 wording only. Change no upgrade behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it uses a different file.
- **[Story]**: The task belongs to User Story 1 or User Story 2.
- Add exact command output to the pull request evidence.
- Tick a task only after its result is verified.

## Phase 1: Setup

**Purpose**: Confirm the worktree, scope, environment, and artifact consistency before any implementation edit.

- [x] T001 Confirm the current branch, `git status --short`, and open pull request file overlap for the manifest in `specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/plan.md`.
- [x] T002 Confirm that only the six approved implementation paths and this feature directory can enter the issue #3332 commit in `specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/plan.md`.
- [x] T003 Run `python scripts/bootstrap_worktree.py` only when `.venv/` is absent, then record the Python version and installed test tools for `.`.
- [x] T004 Run `/speckit.analyze` against `specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/` and record the exact consistency result without changing product code.

---

## Phase 2: Foundational Audit

**Purpose**: Recheck every exact old statement before any approved file changes.

**Critical**: Complete this phase before User Story 1 or User Story 2 edits.

- [x] T005 Read and record each exact existing phase-watch boundary statement in `src/interfaces/portals/upgrade_portal/upgrade/driver.py`, `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`, and `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html`.
- [x] T006 Search every file under `tests/` for each exact old statement from T005, including `A phase starts only after the phase before it reports settled.`, and record every path and line.
- [x] T007 Record that `tests/unit/upgrade_portal/test_org_phase_list_parity.py` indirectly asserts the old note through rendered-text equality.

**Checkpoint**: The old-string evidence is complete, and the implementation manifest remains unchanged.

---

## Phase 3: User Story 1 - Understand the Phase-Watch Boundary (Priority: P1) MVP

**Goal**: State when the watch starts, what it observes, and what it does not prove.

**Independent Test**: Render the organization operation page and directly assert the first three canonical strings.

### Tests for User Story 1

- [x] T008 [US1] Add direct literal assertions in the contract test, and replace the obsolete rendered-text equality in `tests/unit/upgrade_portal/test_org_phase_list_parity.py`.

### Implementation for User Story 1

- [x] T009 [P] [US1] Replace the false ordered-submission promise with the first three canonical strings in `src/interfaces/portals/upgrade_portal/upgrade/driver.py`.
- [x] T010 [P] [US1] Keep the watch read-only and add the first three canonical strings in `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`.
- [x] T011 [P] [US1] Show the first three canonical strings in `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html`.
- [x] T012 [US1] Confirm the wording in `src/interfaces/portals/upgrade_portal/upgrade/driver.py` contains no cloud acceptance or device-family order claim.
- [x] T013 [US1] Confirm the wording in `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` defines no firmware write, retry, resume, lock, or durable state behavior.
- [x] T014 [US1] Run the focused contract test in `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` and record the exact pass count.

**Checkpoint**: User Story 1 states one consistent, independently tested submission boundary.

---

## Phase 4: User Story 2 - Respond Safely to an Uncertain Submission (Priority: P2)

**Goal**: Tell the operator not to start another upgrade when a submission result is uncertain.

**Independent Test**: Render the organization operation page and directly assert the exact warning.

### Tests for User Story 2

- [x] T015 [US2] Add one direct literal assertion for the exact warning in `tests/contract/upgrade_portal/test_org_phase_watch_contract.py`.

### Implementation for User Story 2

- [x] T016 [US2] Add `Warning: If a submission result is uncertain, do not start another upgrade. A second upgrade can target the same devices.` to `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html`.
- [x] T017 [US2] Confirm the warning in `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html` defines no recovery, timeout, retry, or resume instruction.

**Checkpoint**: User Story 2 gives one direct warning and adds no behavior rule.

---

## Phase 5: Release Note and Wording Contract

**Purpose**: Publish the wording change and prove one exact wording authority.

- [x] T018 Create `changelog.d/issue-3332-phase-watch-wording.md` with the approved heading, the `Changed` bullet, and issue #3332.
- [x] T019 Confirm that the contract test and the parity test assert the canonical multi-site note.
- [x] T020 Search all files under `tests/` for every old statement recorded in T005 and confirm no obsolete boundary assertion remains.
- [x] T021 Review `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` and confirm it renders the page, normalizes whitespace, and directly asserts all four literal strings.
- [x] T022 Review the six approved implementation files against `specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/contracts/phase-watch-wording.md`.

---

## Phase 6: Focused Tests and Applicable Gates

**Purpose**: Run each local gate that applies to the Python, Jinja, test, changelog, and Spec Kit changes.

- [x] T023 Run `python -m pytest tests\contract\upgrade_portal\test_org_phase_watch_contract.py -q` and record the exact result for `tests/contract/upgrade_portal/test_org_phase_watch_contract.py`.
- [x] T024 Run `python -m pytest tests\e2e\upgrade_portal -q` and record the complete browser-suite count.
- [x] T025 Run `python -m py_compile` on both changed source modules and both changed test modules.
- [x] T026 Run `python -m ruff check .` and `python -m black --check --diff .` from `.` and record both exact results.
- [x] T027 Run `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`.
- [x] T028 Confirm that the full coverage gate does not apply because this change adds no executable behavior.
- [x] T029 Confirm that the safe menu sweep does not apply because this change edits no menu operation.
- [x] T030 Confirm that the complexity gate does not apply because this change edits no executable block.
- [x] T031 Run `python -m bandit -c pyproject.toml -r src/interfaces/portals/upgrade_portal -q` from `.`.
- [x] T032 Confirm that the dependency audit does not apply because this change edits no dependency file.
- [x] T033 Run `pylint src/ --fail-under=9.5` and `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` from `.`.
- [x] T034 Run `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v` from `.`.
- [x] T035 Run the changelog fragment, process folder, and Spec Kit route guards for the changed artifacts.
- [x] T036 Run the test-quality preflight in `tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` with `python -B -m pytest -p no:cacheprovider -s -q`.
- [x] T037 Run `symbol-diff --base origin/main` for `src/interfaces/portals/upgrade_portal/upgrade/driver.py` and `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`.
- [x] T038 Run `ste-linter --config .ste-linter.toml --min-score 80` on every Markdown file in `specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/` and `changelog.d/issue-3332-phase-watch-wording.md`.
- [x] T039 Run `git diff --check` and inspect the word diff for the six approved implementation paths and the feature directory.
- [x] T040 Search the complete diff for settle timeout, reachability, retry, resume, firmware order, lock, and durable state changes, then reject any behavior change.

**Checkpoint**: Each applicable local gate passes before the commit.

---

## Phase 7: Commit, Rebase, One Push, and Ready Pull Request

**Purpose**: Deliver one reviewed branch update with exact evidence and no draft pull request.

- [x] T041 Build the final manifest from committed, staged, unstaged, and feature-owned untracked paths, then confirm no unrelated path will enter the commit.
- [x] T042 Stage only the six approved implementation paths and the feature directory with explicit `git add` paths.
- [x] T043 Amend the existing commit with subject `docs(upgrade): clarify the phase-watch submission boundary`, body `Closes #3332`, and the required `Co-authored-by` trailer.
- [x] T044 Fetch `origin/main` without tags and rebase the committed branch onto `origin/main`; stop if another change owns a conflicting approved file.
- [x] T045 Rerun T019 through T040 after the rebase and record each exact post-rebase result against the same paths.
- [x] T046 Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`.
- [x] T047 Confirm that the test-quality result for both changed test files states `gate: 0 new findings vs baseline`.
- [ ] T048 Confirm the branch has no earlier push for this implementation, then run one `git push --force-with-lease origin jmorrison-juniper-docs-3332-phase-watch-boundary`.
- [ ] T049 Create a ready pull request to `main` with no draft option, title `docs(upgrade): clarify the phase-watch submission boundary`, and `.github/PULL_REQUEST_TEMPLATE.md`.
- [ ] T050 Preserve every heading, comment, checklist item, and order from `.github/PULL_REQUEST_TEMPLATE.md`, then add `Closes #3332`, the exact manifest, and each command result.
- [ ] T051 Run `gh pr view --json number,title,isDraft,baseRefName,headRefName,mergeable,reviewDecision,url` and verify `isDraft` is `false`, base is `main`, and the head is the issue branch.
- [ ] T052 Run `gh pr checks --watch`, record every required check and CodeQL result, and confirm the pull request has no `auto-merge` label.
- [ ] T053 Report the exact commit SHA, rebase base SHA, single push command, pull request URL, `isDraft: false`, changed paths, test counts, gate results, and exclusions.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: No dependency.
- **Foundational Audit**: Depends on Setup and blocks all edits.
- **User Story 1**: Depends on the Foundational Audit.
- **User Story 2**: Depends on User Story 1 because both stories edit the phase card and contract test.
- **Release Note and Wording Contract**: Depends on both user stories.
- **Focused Tests and Applicable Gates**: Depends on the complete implementation manifest.
- **Delivery**: Depends on every local gate passing.

### User Story Dependencies

- **User Story 1 (P1)**: The MVP can complete after the pre-edit audit.
- **User Story 2 (P2)**: It depends on User Story 1 file edits, but its warning remains independently testable.

### Delivery Dependencies

```text
T001-T007 -> T008-T014 -> T015-T017 -> T018-T022
T018-T022 -> T023-T040 -> T041-T043 -> T044
T044 -> T045-T047 -> T048 -> T049-T053
```

The only push is T048. Do not push before T048 or after T048.

---

## Parallel Opportunities

- T009, T010, and T011 can run in parallel after T008 defines the direct test contract.
- Independent gate commands can run in parallel only when they do not write shared coverage or test artifacts.
- Do not run T024 and T028 in parallel because both can use shared portal test resources.
- Do not run any delivery task in parallel with a file edit or validation command.

## Parallel Example: User Story 1

```text
Task T009: Update the driver wording in src/interfaces/portals/upgrade_portal/upgrade/driver.py.
Task T010: Update the organization watch wording in src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py.
Task T011: Update the phase card wording in src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html.
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and the Foundational Audit.
2. Complete User Story 1.
3. Run the focused contract test.
4. Confirm that the three boundary statements are exact.
5. Continue to User Story 2 only after the MVP passes.

### Incremental Delivery

1. Establish the old-string evidence before edits.
2. Correct the shared phase-watch boundary.
3. Add the uncertain-submission warning.
4. Add the release note and exact contract assertions.
5. Run every applicable gate.
6. Commit, rebase, rerun the gates, and push one time.
7. Create a ready pull request and report exact evidence.

## Scope Guard

- Do not change settle timeout behavior.
- Do not change reachability behavior.
- Do not add retry behavior.
- Do not change resume behavior.
- Do not change firmware submission order or firmware writes.
- Do not change locks.
- Do not add or change durable state behavior.
- Do not add or change route behavior.
- Do not edit a product or test file outside the approved six-file manifest.
