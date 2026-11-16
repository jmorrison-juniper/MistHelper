---
description: "Tasks for native Windows timeout acceptance"
---

# Tasks: Native Windows Timeout Acceptance

**Input**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Organization**: Tasks follow User Story 1, which provides the only user-facing outcome.

## Phase 1: Setup

No project initialization or dependency changes are required.

## Phase 2: Foundational

No shared infrastructure changes are required.

## Phase 3: User Story 1 - Verify the Timeout Guard on Windows (Priority: P1)

**Goal**: Provide trustworthy, optional acceptance evidence from native Windows without changing the existing timeout test.

**Independent Test**: The contract test accepts the valid workflow and rejects an invalid trigger. The existing module passes locally. A coordinator-approved Windows run remains pending.

### Tests

- [X] T001 [US1] Add contract tests in `tests/guardrails/e2e_timeout_budget/test_windows_timeout_budget_workflow.py`. Check non-main push filters, read-only permissions, credential-free checkout, native Windows, Python, seven tests, and zero skips, errors, or failures. Run the extracted JUnit validator against valid and invalid reports, including each missing count field, unreadable files, and malformed files. Add a mutation case that rejects an unapproved trigger.

### Implementation

- [X] T002 [US1] Add `.github/workflows/windows-timeout-budget.yml`. Trigger it only on filtered non-main pushes. Use bounded Windows execution, existing action versions, read-only permissions, credential-free checkout, runtime confirmation, and JUnit validation. Keep `tests/guardrails/e2e_timeout_budget/test_timeout_budget.py` unchanged.
- [X] T003 [P] [US1] Add `changelog.d/issue-4777-windows-timeout-acceptance.md` with one `###` heading and one issue #4777 bullet.

### Local Validation

- [X] T004 [US1] Run the workflow contract tests. Verify trigger rejection and require the extracted JUnit validator to accept only seven clean results with every count field present.
- [X] T005 [US1] Run the full timeout-budget test module and verify all seven tests pass.
- [X] T006 [US1] Run the applicable Ruff, Black, compile, and STE checks for the new test and documentation.
- [X] T007 [US1] Confirm the existing timeout test, protected CI files, dependency files, settings, and `.specify/feature.json` remain unchanged.

### Native Acceptance

- [X] T008 [US1] Run the workflow on an approved non-main push. Verify seven tests pass with zero skips, errors, or failures.

**Verified run**:

- URL: https://github.com/jmorrison-juniper/MistHelper/actions/runs/43806539826
- Tested commit: `2fbfe2e9a9392f168d20726ccfd3fc965ad1ac00`.
- Environment: Windows Server 2025 and CPython 3.15.2.
- Pytest result: `7 passed, 1 warning`.
- Validator result: `Native Windows tests: 7 collected, 0 skipped, 0 failures, 0 errors`.

**Pending**: Quality Gates, CodeQL, STE compliance, and Conventional Commits PR title checks await the pull request.

**Not applicable**: UI, container, and menu checks. This change alters none of them.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: No setup tasks are required.
- **Foundational**: No foundational tasks are required.
- **User Story 1**: T001 precedes T002. T003 is independent. T004 through T007 require the implementation. T008 requires coordinator approval and a real non-main push.

### User Story Dependencies

- **User Story 1 (P1)**: No other story is required.

### Parallel Opportunities

- T003 can run independently from T001 and T002.
- After T002, T004 and T005 can run separately. Do not treat either local result as native Windows acceptance.

## Implementation Strategy

Complete User Story 1 as the MVP. First add the failing workflow contract, then add the optional workflow and changelog fragment. Run local validation and preserve native acceptance as unchecked until coordinator approval and a successful Windows run.
