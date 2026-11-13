# Tasks: Locked Dependency Exports

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), and the design files under `design/`.

**Tests**: Use the existing dependency guards. Do not add a test that duplicates the generated-export comparison.

**Organization**: Tasks follow User Story 1 because the specification defines one independently testable user story.

## Phase 1: Setup

**Purpose**: Confirm the project limits and locked source.

- [x] T001 Review package limits in `pyproject.toml` and package records in `uv.lock`.

---

## Phase 2: Foundational

**Purpose**: Verify the lock before package upgrades.

- [x] T002 Run `uv lock --check` against `pyproject.toml` and `uv.lock`.

---

## Phase 3: User Story 1 - Install compatible dependencies (Priority: P1)

**Goal**: Keep locked runtime and development requirements consistent across supported platforms.

**Independent Test**: Compare both requirements files with fresh exports, then run the dependency guards.

### Implementation

- [x] T003 [US1] Upgrade `markdown-it-py`, `openai`, and `simplejson` within project limits in `uv.lock`.
- [x] T004 [P] [US1] Generate the runtime export in `requirements.txt` from `uv.lock`.
- [x] T005 [P] [US1] Generate the development export in `requirements-dev.txt` from `uv.lock`.
- [x] T006 [US1] Verify both exports and locked versions with `tests/guardrails/test_dependency_export.py`, `tests/guardrails/test_dependency_lock_file.py`, and `tests/guardrails/test_dependency_declaration_parity.py`.
- [x] T007 [US1] Audit runtime package versions in `requirements.txt` with `pip-audit`.

**Checkpoint**: Both exports match the lock, preserve platform markers, and pass dependency checks.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Verify the final files before commit.

- [x] T008 Confirm `git diff --check` passes for `uv.lock`, `requirements.txt`, and `requirements-dev.txt`.

---

## Phase 5: Merge and Deployment

**Purpose**: Merge the verified dependency update and complete the authorized deployment.

- [ ] T009 Commit the verified dependency exports and specification files with a Conventional Commit message.
- [ ] T010 Rebase the feature branch on `origin/main` and rerun the dependency checks.
- [ ] T011 Push the feature branch and open a pull request from the repository template that closes issue #4785.
- [ ] T012 Wait for required CI and CodeQL checks, then obtain required human review.
- [ ] T013 Merge the pull request in the serial merge slot after all required checks and reviews pass.
- [ ] T014 Verify the post-merge image build and confirm its revision label matches the merge commit.
- [ ] T015 Deploy the image to the approved production target and verify service health. Stop if target or access details are missing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: T001 has no prerequisites.
- **Foundational**: T002 depends on T001.
- **User Story 1**: T003 depends on T002. T004 and T005 depend on T003.
- **Polish**: T008 depends on T006 and T007.
- **Merge and Deployment**: T009 depends on T008. T010 depends on T009. T011 depends on T010. T012 depends on T011. T013 depends on T012. T014 depends on T013. T015 depends on T014 and the production target details.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on the lock check. It has no dependency on another story.

### Parallel Opportunities

- T004 and T005 can run in parallel after T003 because they write different files from the same lock.

## Parallel Example: User Story 1

```text
Task: Generate requirements.txt from uv.lock.
Task: Generate requirements-dev.txt from uv.lock.
```

## Implementation Strategy

### MVP First

Complete User Story 1. Run the export guards and dependency audit before commit.

### Incremental Delivery

Update the lock first, regenerate both exports, then run the focused checks.
Commit and merge only after local checks pass. Deploy only after the post-merge image matches the merge commit and the production target is confirmed.
