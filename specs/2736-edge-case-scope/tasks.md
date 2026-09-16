# Tasks: Edge-Case Detector Scope

**Input**: Design documents from `specs/2736-edge-case-scope/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: The issue requires detector tests, audit tests, analyzer runs, and the
full non-e2e suite.

## Phase 1: Setup

- [x] T001 Read issue #2736, pull request #2734, issue #2654, and repository
  instructions. (delivered: issue and instruction review)
- [x] T002 Create the isolated worktree
  `..\MistHelper-2736-edge-scope` from `origin/main`. (delivered: worktree)
- [x] T003 Verify the virtual environment uses `mistapi` 0.64.0 and collects
  16613 tests. (delivered: local collection output)

---

## Phase 2: Specification

- [x] T004 Create `specs/2736-edge-case-scope/spec.md` from the specification
  template. (delivered: specs/2736-edge-case-scope/spec.md)
- [x] T005 Create `specs/2736-edge-case-scope/plan.md` from the plan template.
  (delivered: specs/2736-edge-case-scope/plan.md)
- [x] T006 Create `specs/2736-edge-case-scope/tasks.md` from the tasks
  template. (delivered: specs/2736-edge-case-scope/tasks.md)

---

## Phase 3: Detector Scope

- [x] T007 Replace the opt-in marker in
  `tools/test_quality_analyzer/detection/missing_edge_case.py` with inferred
  applicability. (delivered: tools/test_quality_analyzer/detection/missing_edge_case.py)
- [x] T008 Preserve support-call exclusions and status-code exclusions from pull
  request #2734. (delivered: tools/test_quality_analyzer/detection/missing_edge_case.py)
- [x] T009 Update edge-case detector fixtures and unit tests so they prove
  annotation, name, optional, and status-code behavior. (delivered:
  tests/tools/test_quality_analyzer/test_meta_fixtures.py)

---

## Phase 4: Scope Metrics and Audit

- [x] T010 Add detector metrics to the analyzer report model and JSON schema.
  (delivered: tools/test_quality_analyzer/detection/types.py)
- [x] T011 Print and write the `MissingEdgeCaseDetector.inspected_modules`
  metric during analyzer runs. (delivered: tools/test_quality_analyzer/__main__.py)
- [x] T012 Extend `tools/guard_proof_audit.py` so zero inspected modules fail
  when an analyzer report is supplied. (delivered: tools/guard_proof_audit.py)
- [x] T013 Add a negative guardrail test for a zero-scope analyzer rule.
  (delivered: tests/guardrails/test_guard_proof_audit.py)

---

## Phase 5: Release and Validation

- [x] T014 Add the issue #2736 release-note fragment. (delivered:
  changelog.d/issue-2736-edge-case-scope.md)
- [ ] T015 Run all local gates from issue #2736.
- [ ] T016 Re-measure missing-edge-case counts and sample ten findings.
- [ ] T017 Push the branch, open the pull request, and wait for required checks.
- [ ] T018 Decide whether issues #2696 through #2699 must reopen after merge.
