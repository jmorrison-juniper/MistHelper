---
description: "Task list for pytest coverage gate headroom"
---

# Tasks: Pytest Coverage Gate Headroom

**Input**: Design documents from `/specs/2650-coverage-gate/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: Included. The feature requires a contract test that reads the workflow file.

**Execution rule**: Run tasks in order. Do not edit `MistHelper.py`.

## Phase 1: Evidence and Scope

**Purpose**: Measure the problem and confirm the safe file set.

- [x] T001 Read issue #2650 and add the `in-progress` label. (delivered: GitHub issue #2650)
- [x] T002 Create the isolated worktree `MistHelper-2650-coverage-gate` from `origin/main`. (delivered: worktree)
- [x] T003 Read the repository instructions and the SpecKit constitution. (delivered: `.github/instructions/git-flow-multi-agent.instructions.md`)
- [x] T004 Measure recent CI coverage job duration across multiple runs. (delivered: `specs/2650-coverage-gate/spec.md`)
- [x] T005 Check open pull requests for file overlap. (delivered: command output)

## Phase 2: SpecKit Artifacts

**Purpose**: Record the contract before the implementation.

- [x] T006 Create `specs/2650-coverage-gate/spec.md`. (delivered: `specs/2650-coverage-gate/spec.md`)
- [x] T007 Create `specs/2650-coverage-gate/plan.md`. (delivered: `specs/2650-coverage-gate/plan.md`)
- [x] T008 Create `specs/2650-coverage-gate/tasks.md`. (delivered: `specs/2650-coverage-gate/tasks.md`)

## Phase 3: Contract Test

**Purpose**: Make the workflow split persistent.

- [x] T009 Add `CoverageGateWorkflow` to read `.github/workflows/ci.yml`. (delivered: `tests/contract/test_pytest_coverage_gate.py`)
- [x] T010 Add contract checks for the shard matrix, hidden artifact upload, final job name, and combine command. (delivered: `tests/contract/test_pytest_coverage_gate.py`)
- [x] T011 Run the new contract test. (delivered: `tests/contract/test_pytest_coverage_gate.py`)

## Phase 4: Workflow Repair

**Purpose**: Move the long serial work into parallel shards.

- [x] T012 Replace the serial root coverage job with a `pytest_coverage_shards` matrix. (delivered: `.github/workflows/ci.yml`)
- [x] T013 Keep the final job identifier `pytest` and job name `pytest (coverage gate)`. (delivered: `.github/workflows/ci.yml`)
- [x] T014 Combine shard coverage data and enforce `COVERAGE_THRESHOLD` once. (delivered: `.github/workflows/ci.yml`)

## Phase 5: Validation and Delivery

**Purpose**: Prove the change and deliver the pull request.

- [x] T015 Run Ruff, Black, mypy, the contract test, and the final duration measure. (delivered: local gate output)
- [x] T016 Add the release-note fragment `changelog.d/issue-2650-coverage-gate.md`. (delivered: `changelog.d/issue-2650-coverage-gate.md`)
- [ ] T017 Commit the change, push the branch, and open the pull request.
- [ ] T018 Watch required checks, repair failures, and add `auto-merge` only after all required checks pass.
