# Tasks: Python optimization skill

**Input**: Design documents from `specs/2394-python-optimization-skill/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Documentation checks and local repository gates are required.

## Phase 1: Setup

**Purpose**: Confirm the worktree, issue, and source rules.

- [x] T001 Read GitHub issue #2394 and its comments.
- [x] T002 Inspect `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-python-optimization-skill`.
- [x] T003 Verify the branch and preserve existing work by continuing the committed worktree.
- [x] T004 Read the repository instructions and constitution.
- [x] T005 Bootstrap the virtual environment and verify `mistapi` version `0.64.0`.

---

## Phase 2: Evidence Verification

**Purpose**: Verify each measurement before the skill cites it.

- [x] T006 Run `tools\bench_performance_overhead.py` and store the raw artifact under `data\performance\`.
- [x] T007 Read pull request #2690 for the coverage-gate before and after measurements.
- [x] T008 Read workflow run `34983706229` for the serial coverage-gate timing.
- [x] T009 Read workflow run `35020159627` for the sharded coverage-gate timing.
- [x] T010 Verify `scripts\benchmarks\bench_flatten_dict.py` exists and uses a synthetic Mist dataset.

---

## Phase 3: Skill Documentation

**Purpose**: Improve the existing skill instead of adding a duplicate.

- [x] T011 Update `.github\skills\optimizing-python\SKILL.md` with MistHelper measurement evidence.
- [x] T012 Update `.github\skills\optimizing-python\references\benchmarking.md` with commands and workflow run sources.
- [x] T013 Update `.github\skills\optimizing-python\references\optimization-checklist.md` with house-rule constraints.
- [x] T014 Update `.github\skills\optimizing-python\references\report-template.md` with required validation evidence.
- [x] T015 Update `.github\skills\optimizing-python\references\installation-and-sources.md` with repository sources.

---

## Phase 4: SpecKit Records

**Purpose**: Record the feature contract and execution order.

- [x] T016 Create `specs\2394-python-optimization-skill\spec.md`.
- [x] T017 Create `specs\2394-python-optimization-skill\plan.md`.
- [x] T018 Create `specs\2394-python-optimization-skill\tasks.md`.

---

## Phase 5: Validation and Delivery

**Purpose**: Prove the change and prepare the pull request.

- [x] T019 Run the STE linter on each written Markdown file.
- [x] T020 Run the required local repository gates.
- [x] T021 Add `changelog.d\issue-2394-python-optimization-skill.md`.
- [ ] T022 Commit, push, open the pull request, and wait for checks.
- [ ] T023 Merge after all checks pass and verify issue closure.

## Dependencies and Execution Order

1. Complete setup before evidence verification.
2. Complete evidence verification before skill documentation.
3. Complete skill documentation before validation.
4. Complete validation before the commit.
5. Complete the pull request checks before merge.
