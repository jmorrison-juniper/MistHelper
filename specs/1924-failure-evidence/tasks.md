# Tasks: Failure Evidence Erasure Audit

**Input**: Design documents from `/specs/1924-failure-evidence/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: Guard tests and local quality gates are required.

## Phase 1: Setup

- [x] T001 Read issue #1924 and spawned issues #2632, #2654, #2689, #2717, and #2736. (delivered: specs/1924-failure-evidence/spec.md)
- [x] T002 Create worktree `MistHelper-1924-evidence` from `origin/main`. (delivered: local worktree)
- [x] T003 Verify `mistapi` 0.64.0 and collect 16619 tests with zero errors. (delivered: local command output)

## Phase 2: Inventory

- [x] T004 Run `tools.guard_proof_audit` after analyzer metric generation. (delivered: specs/1924-failure-evidence/inventory.md)
- [x] T005 Count broad-handler, success-report, retry, fallback, and default candidates. (delivered: specs/1924-failure-evidence/inventory.json)
- [x] T006 Record `MistHelper.py` findings without editing `MistHelper.py`. (delivered: specs/1924-failure-evidence/inventory.md)

## Phase 3: Repair

- [x] T007 Add upper bounds to runtime dependency manifests. (delivered: requirements.txt and pyproject.toml)
- [x] T008 Extend `GuardProofAuditor` with dependency upper-bound checks. (delivered: tools/guard_proof_audit.py)
- [x] T009 Add negative tests for unbounded and zero dependency input. (delivered: tests/guardrails/test_guard_proof_audit.py)

## Phase 4: Deferral

- [x] T010 File follow-up issue #2750 for broad handlers. (delivered: GitHub issue #2750)
- [x] T011 File follow-up issue #2751 for early success reports. (delivered: GitHub issue #2751)
- [x] T012 File follow-up issue #2752 for hidden first failures. (delivered: GitHub issue #2752)
- [x] T013 File follow-up issue #2753 for code defaults. (delivered: GitHub issue #2753)

## Phase 5: Validation

- [ ] T014 Run local quality gates and targeted tests. (delivered after command output is collected)
- [ ] T015 Open the pull request and watch required checks. (delivered after pull request creation)
- [ ] T016 Merge after CodeQL and required checks pass. (delivered after branch protection allows merge)
