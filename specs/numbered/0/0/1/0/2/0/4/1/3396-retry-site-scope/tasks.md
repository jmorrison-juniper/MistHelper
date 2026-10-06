# Tasks: Retry Site Scope

**Input**: Design documents in
`specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: The specification requires focused contract tests. Each test must
use fakes and must block external connections.

**Organization**: Tasks follow the three user stories. The work is sequential
because each story edits the same route module and contract test file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel without a file conflict.
- **[Story]**: The task belongs to the named user story.
- Each task names its exact file path.
- Tick a task only after its file or command result is verified.

## Approved Change Boundary

Implementation can change only these files:

- `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
- `tests/contract/upgrade_portal/test_org_child_controls_routes.py`
- `changelog.d/issue-3396-retry-site-scope.md`

Planning records remain under
`specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/`.

Warning: Stop if the correction needs another production file. Report the file
and the reason before any scope expansion.

## Phase 1: Setup

**Purpose**: Confirm the narrow issue boundary before test or production work.

- [X] T001 Compare the issue #3396 specification and plan with the current route and test seams. Stop if any production file other than `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` is necessary.

---

## Phase 2: Foundational Test Isolation

**Purpose**: Make every issue test fail at the call site if code opens an
external connection.

**Critical**: Complete this phase before any user story.

- [X] T002 Add an autouse socket-block fixture to `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Make each network attempt raise before transmission, and keep Mist reads, prechecks, locks, durable storage, and aggregate submission behind existing fakes.
- [X] T003 Verify that `tests/contract/upgrade_portal/test_org_child_controls_routes.py` reads no live credential and uses no Mist, Redis, ArangoDB, or firmware service.

**Checkpoint**: The focused contract file now enforces fake-only execution.

---

## Phase 3: User Story 1 - Confirm the Actual Retry Scope (Priority: P1)

**Goal**: Show only sites that retain planned retry devices after
device-family filtering.

**Independent Test**: Select sites A and B. Clear the only retry family at
site A. Confirm that the page shows one site, one device, and site B prechecks.

### Tests for User Story 1

- [X] T004 [US1] Extend the paired cleared-type tests in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Assert that selection remains A and B, confirmation reports one site and one device, warning scope excludes site A, and confirmation prechecks receive site B only.
- [X] T005 [US1] Confirm the stale result from the read-only issue assessment. The unchanged save stored both selected sites after the switch family was cleared. Record the focused red command and failure in this task after the test exists.

### Implementation for User Story 1

- [X] T006 [US1] Update `confirm_page` in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. For aggregate plans, load the owned durable operation first and use its ordered `site_ids` and aligned `site_names` for validation, counts, warnings, and confirmation prechecks.
- [X] T007 [US1] Preserve legacy access point confirmation, authentication, authorization, and the typed `CONFIRM` control in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.

**Checkpoint**: User Story 1 passes its focused fake-only assertions.

**Red Evidence**: Run
`python -m pytest tests/contract/upgrade_portal/test_org_child_controls_routes.py -k "retry_save_with_a_cleared_type" -q`
against the unchanged production route. The new assertion must fail because
the parent durable scope contains sites A and B. The local red run selected
one test and failed at the `plan["site_ids"] == [SITE_TWO]` assertion.

---

## Phase 4: User Story 2 - Save and Lock the Actual Retry Scope (Priority: P1)

**Goal**: Store, validate, check, and lock only sites that retain planned
retry devices.

**Independent Test**: Save and submit the filtered retry. Verify that the
parent, children, submission prechecks, exact-context check, and locks use site
B only.

### Tests for User Story 2

- [X] T008 [US2] Extend `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Assert that parent `site_ids` equals `[site_b]`, parent `site_names` contains site B only, and every child site identifier belongs to site B.
- [X] T009 [US2] Extend `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Assert that submission prechecks, the initial lock refusal check, acquired locks, and the durable `site_locks` mapping use site B only.
- [X] T010 [US2] Add failure-safety assertions to `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Prove that a site A lock does not block the retry, a site B lock does block it, and stale ownership, nonce, organization, or durable scope stops before any precheck write, lock write, or firmware write.

### Implementation for User Story 2

- [X] T011 [US2] Update `_aggregate_saved_options` in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. Validate all selected rows first, derive unique target site identifiers after retry filtering, and pass only matching rows to `AggregateBuildInput` while preserving selected-site order and names.
- [X] T012 [US2] Update `_load_submission_context` in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. For aggregate plans, load the owned durable operation and use its ordered `site_ids` for lock refusal, prechecks, exact-context validation, lock acquisition, and child submission.
- [X] T013 [US2] Preserve write-enable checks, accountable operator checks, audit timing, lock tokens, compare-and-set writes, retry lineage, idempotency, and durable transaction behavior in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.

**Checkpoint**: User Story 2 passes without a live connection or credential.

---

## Phase 5: User Story 3 - Preserve Selection and Valid Saves (Priority: P2)

**Goal**: Narrow only filtered retries. Keep operator selection and valid save
behavior unchanged.

**Independent Test**: Compare a plain save, a fully targeted retry, a filtered
retry, and an empty retry. Only the filtered retry has a narrower durable
scope.

### Tests for User Story 3

- [X] T014 [US3] Add regression assertions in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Prove that plain multi-site saves retain existing scope and retries retain each selected site that has a planned target.
- [X] T015 [US3] Add edge assertions in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. Prove that duplicate targets create one durable site entry, target order does not replace selected-site order, names remain aligned, and the existing empty-plan refusal writes no operation.

### Implementation for User Story 3

- [X] T016 [US3] Review the retry-only branch in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. Confirm that it does not mutate `selected_site_ids`, change plain-save scope, add a Mist request, add a durable write, or add a top-level production symbol.

The cleared-family scenario supplies the shared submission, precheck, and lock
evidence for each path that removes a site after retry filtering. The
device-left-site scenario independently proves the same saved and confirmed
durable scope.

**Checkpoint**: All three stories pass independently in the focused contract
file.

---

## Phase 6: Release Note, Validation, and Local Commits

**Purpose**: Record the user-visible correction and produce local evidence.
Do not push, open a pull request, run a workflow, or change issue state.

- [X] T017 Create `changelog.d/issue-3396-retry-site-scope.md` with one `###` heading and one `Fixed` bullet. State that filtered retries now confirm, store, check, and lock only planned sites. End the bullet with `Issue #3396.`
- [X] T018 Run `python -m pytest tests/contract/upgrade_portal/test_org_child_controls_routes.py -k "retry_save_with_a_cleared_type" -q` and require a pass.
- [X] T019 Run `python -m pytest tests/contract/upgrade_portal/test_org_child_controls_routes.py -q` and require every fake-only contract test to pass with the socket block active.
- [X] T020 Run `python -m ruff check src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py tests/contract/upgrade_portal/test_org_child_controls_routes.py` and require `All checks passed`.
- [X] T021 Run `python -m black --check src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py tests/contract/upgrade_portal/test_org_child_controls_routes.py` and require no file change.
- [X] T022 Run `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` and require `Success`.
- [X] T023 Run `bandit -c pyproject.toml -r src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py -q` and require no finding.
- [X] T024 Run `radon cc src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py -j | complexity-gate --max 10` and require no block above complexity 10.
- [X] T025 Run `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/spec.md specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/plan.md specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/tasks.md changelog.d/issue-3396-retry-site-scope.md` and require each file to score 80 or higher.
- [ ] T026 Stage planning records only with explicit paths: `git add specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/spec.md specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/plan.md specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/tasks.md`. Commit with subject `docs(spec): define retry site scope`, body `Refs #3396`, and trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
- [ ] T027 Stage implementation files only with `git add src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py tests/contract/upgrade_portal/test_org_child_controls_routes.py changelog.d/issue-3396-retry-site-scope.md`. Commit with subject `fix(upgrade-portal): narrow retry site scope`, body `Refs #3396`, and trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
- [ ] T028 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` after the local commits and require a pass.
- [ ] T029 Run `git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"` and `git rev-parse --verify "origin/main^{commit}"`, then run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. Require `gate: 0 new findings vs baseline`.
- [ ] T030 Run `git status --short` and verify that no feature-owned path remains staged, unstaged, or untracked. Do not stage or change any unrelated path.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependency.
- **Phase 2** depends on Phase 1 and blocks each user story.
- **User Story 1** depends on Phase 2.
- **User Story 2** depends on User Story 1 because both edit the same route flow.
- **User Story 3** depends on User Stories 1 and 2.
- **Phase 6** depends on all selected user stories.

### User Story Dependencies

- **User Story 1** defines the durable confirmation scope.
- **User Story 2** uses the same durable scope for save and submission.
- **User Story 3** proves that the correction does not change valid paths.

### Within Each User Story

- Add the focused test before the production edit.
- Verify that the new assertion can fail.
- Make the narrow route change.
- Run the focused fake-only test.
- Stop if another production file becomes necessary.

## Parallel Opportunities

No implementation task is marked `[P]`. The work shares
`org_upgrade.py` and `test_org_child_controls_routes.py`. Parallel edits can
cause a file conflict or can hide the required red-to-green test order.

## Parallel Example

No safe parallel implementation example exists for this feature. One engineer
must complete the route and focused contract sequence.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1.
3. Run its focused fake-only test.
4. Stop before submission work if the confirmation scope is not exact.

### Incremental Delivery

1. Add exact confirmation scope.
2. Add exact durable and lock scope.
3. Prove preserved selection and valid saves.
4. Add the release note.
5. Run each required local gate.
6. Create the two local commits with explicit-path staging.
7. Stop before any push, pull request, workflow, issue, label, or merge action.

## Notes

- Use no live Mist token or service.
- Keep each socket block active for the full contract file.
- Preserve each destructive safeguard.
- Add no production symbol or dependency.
- Do not use `git add .`, `git add -A`, `git stash`, or a destructive Git command.
