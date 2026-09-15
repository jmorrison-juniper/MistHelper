---
description: "Task list for feature 2654-guard-proof"
---

# Tasks: Guard Proof Enforcement

**Input**: Design documents from `specs\2654-guard-proof\`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Required by issue #2654. A negative test must prove that the
enforcement rejects a guard that measures nothing.

**Organization**: Tasks are ordered by dependency. Each path is relative to the
repository root.

## Phase 1: Setup

**Purpose**: Confirm the issue evidence and the repository rule sources.

- [X] T001 Read issues #2654, #1924, and #2689 with comments.
- [X] T002 Read `.github\copilot-instructions.md`,
  `.github\instructions\coding-standards.instructions.md`,
  `.github\instructions\git-flow-multi-agent.instructions.md`, and
  `.specify\memory\constitution.md`.
- [X] T003 Create the isolated worktree `..\MistHelper-2654-guard-proof` from
  `origin\main`.
- [X] T004 Bootstrap the worktree and confirm `mistapi` 0.64.0.
- [X] T005 Run pytest collection and confirm zero collection errors.

## Phase 2: Specification

**Purpose**: Record the contract before implementation.

- [X] T006 Create `specs\2654-guard-proof\spec.md`.
- [X] T007 Create `specs\2654-guard-proof\plan.md`.
- [X] T008 Create `specs\2654-guard-proof\tasks.md`.

## Phase 3: Enforcement

**Purpose**: Add a gate that blocks a new guard that measures nothing.

- [X] T009 Add `tools\guard_proof_audit.py` with `GuardProofAuditor`.
- [X] T010 Add `GuardProofCli` so the audit can run from the command line.
- [X] T011 Baseline the known SDK compatibility finding to issue #2689.

## Phase 4: Tests

**Purpose**: Prove both the failing path and the environmental skip path.

- [X] T012 Add a negative test in `tests\guardrails\test_guard_proof_audit.py`
  that creates an all-skipped guard in memory and asserts rejection.
- [X] T013 Add positive tests for `pytest.importorskip` and
  `pytest.mark.skipif` in `tests\guardrails\test_guard_proof_audit.py`.
- [X] T014 Add a repository test that blocks active findings and reports the
  known issue #2689 finding.

## Phase 5: Documentation

**Purpose**: Make the rule visible where contributors and agents read it.

- [X] T015 Add the guard proof rule to
  `.github\instructions\git-flow-multi-agent.instructions.md`.
- [X] T016 Add the guard proof checklist item to
  `.github\PULL_REQUEST_TEMPLATE.md`.
- [X] T017 Add the contributor rule to `documentation\CONTRIBUTING-MistHelper.md`.
- [X] T018 Add the agent rule to `.github\copilot-instructions.md`.
- [X] T019 Add `changelog.d\issue-2654-guard-proof.md`.

## Phase 6: Validation and Pull Request

**Purpose**: Prove the change locally and then open the pull request.

- [X] T020 Run `python -m ruff check .`.
- [X] T021 Run `python -m black --check .`.
- [X] T022 Run the project mypy command from the issue.
- [X] T023 Run `python -m pytest tests\guardrails\test_guard_proof_audit.py -v`.
- [X] T024 Run `python -m tools.guard_proof_audit --include-known`.
- [ ] T025 Commit, push, open the pull request, and wait for required checks.
