# Feature Specification: W0706 try-except-raise handlers in MistHelper.py

**Feature Branch**: `chore/4132-w0706-try-except-raise`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4132. Pylint reports W0706 for except handlers that only re-raise in `MistHelper.py`.

## Terms

- **Re-raise-only handler**: An except handler whose only statement is a bare `raise`.
- **Stop signal**: The exception `KeyboardInterrupt` or `SystemExit`.
- **Touched function**: A function that this change edits.
- **Guard test**: A test that fails when the repository rule breaks.

## Clarifications

### Session 2026-11-26

- Q: Which handlers does the issue name? A: The issue names eight line numbers from commit `61505c611`. Main holds seven re-raise-only handlers. The eighth handler is absent from main.
- Q: What does the issue caution require? A: Check the handler that follows each block. Keep a handler when a later broad handler catches a stop signal.
- Q: Which exceptions must still reach the operator? A: `KeyboardInterrupt` and `SystemExit`. Both derive from `BaseException`, so `except Exception` never catches them.
- Q: Can a pylint comment suppress the finding? A: No. `AGENTS.md` and the constitution forbid suppressing a legitimate finding.
- Q: Does the change need a changelog fragment? A: Yes. The constitution requires one fragment for each change. It governs over the changelog README.
- Q: Where do the new tests go? A: In the existing narrow-except test module. A new file in `tests/unit/` adds a child to a folder that already exceeds five children.
- Q: Does a CI gate read `MistHelper.py` for this rule? A: No. The CI pylint job scans `src/` only. A guard test enforces the rule instead.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pylint reports no W0706 finding (Priority: P1)

A maintainer runs pylint on `MistHelper.py`. The run reports no `try-except-raise` message. Each removed handler re-raised a stop signal that no later handler caught.

**Why this priority**: The lint finding is the issue scope. The lint baseline stays clean after this change.

**Independent Test**: Run `python -m pylint MistHelper.py` and the guard test in `tests/unit/test_issue_1709_narrow_except.py`. Both report zero findings.

**Acceptance Scenarios**:

1. **Given** main with seven re-raise-only handlers, **When** the change merges, **Then** pylint reports no W0706 line for `MistHelper.py`.
2. **Given** a later edit adds a re-raise-only handler, **When** the guard test runs, **Then** the test fails and names the line.

### User Story 2 - The operator stop path behaves the same (Priority: P1)

An operator presses Ctrl+C, or a menu calls `sys.exit`. The program stops at the same point with the same exit code. An ordinary error still reaches its existing handler.

**Why this priority**: The stop path protects the operator and unattended runs. The issue requires unchanged behavior.

**Independent Test**: Run the new stop-path, ordinary-error, `__main__`, and logging tests. All 18 new cases pass.

**Acceptance Scenarios**:

1. **Given** a menu function raises `SystemExit(3)`, **When** the test harness runs it, **Then** `SystemExit(3)` reaches the caller and no failure line prints.
2. **Given** a menu function raises `RuntimeError`, **When** the test harness runs it, **Then** the existing failure handler records the failure.
3. **Given** the `__main__` block receives `KeyboardInterrupt`, **When** the program stops, **Then** the process exit code remains 130.

### User Story 3 - A reviewer verifies the change from the record (Priority: P2)

A reviewer reads this record and the pull request diff. Each removed handler appears with its main line number, its function, and its test.

**Why this priority**: Clear evidence shortens review and keeps the lint change auditable.

**Independent Test**: Compare the change map in `plan.md` with the pull request diff. Each handler pair appears once.

**Acceptance Scenarios**:

1. **Given** the pull request diff, **When** the reviewer compares it with `plan.md`, **Then** the seven handler pairs match the change map exactly.
2. **Given** the changelog guard, **When** it reads the fragment, **Then** the guard accepts the file name and the change type.

### Edge Cases

- A stop signal reaches a later broad handler. None of the seven try statements has a later `except BaseException` handler.
- Caution: a later `except BaseException` handler below a removed handler catches stop signals. Reviewers must reject such an edit.
- A try statement loses every handler. No try statement does, because each keeps an `except Exception` handler.
- The `__main__` try statement has a `finally` clause. The clause still runs when `SystemExit` propagates.
- The `args` global is missing when `_fast_mode_from_cli_args` runs. The function still returns `False`, as before.
- Line citations below the first removed handler drift. Citations outside this change keep their old numbers.
- The issue line numbers are stale. Every edit uses the line numbers from main.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST remove the seven re-raise-only handler pairs from `MistHelper.py`.
- **FR-002**: The change MUST keep each `except Exception` handler that follows a removed handler.
- **FR-003**: Each stop signal MUST propagate from each touched function with the same type and code.
- **FR-004**: The `__main__` block MUST keep its `KeyboardInterrupt` handler, its exit code 130, and its `finally` clause.
- **FR-005**: A guard test MUST fail when `MistHelper.py` holds a re-raise-only handler.
- **FR-006**: Pylint MUST report zero `try-except-raise` messages for `MistHelper.py`.
- **FR-007**: The change MUST NOT add a suppression comment for the finding.
- **FR-008**: Each touched function MUST carry inline comments and the action logging that the repository rules require.
- **FR-009**: The change MUST add one changelog fragment with one heading and one change-type bullet.
- **FR-010**: The change MUST keep every module-level name and every menu reference unchanged.
- **FR-011**: Each new Markdown file MUST score 80 or above in the STE gate. The change MUST NOT edit `CHANGELOG.md`.
- **FR-012**: The pull request MUST close issue 4132 and pass each required CI check. It MUST carry no `auto-merge` label before human review.

### Key Entities

Not applicable. The change holds no data entity. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pylint reports zero `try-except-raise` lines for `MistHelper.py`, down from seven.
- **SC-002**: The guard test reports zero offenders and states the number of handlers it examined.
- **SC-003**: All 18 new cases in the narrow-except test module pass.
- **SC-004**: Each applicable local gate in `tasks.md` reports its expected result.
- **SC-005**: Every required CI check passes on the pull request head commit.

## Assumptions

- Main and local HEAD hold the same `MistHelper.py` content. Both blobs equal `98d7828479ded6bc4c83d15e0c1847171cfbfd49`.
- No open pull request changes `MistHelper.py`. The open pull request list held seven items on 2026-11-26.
- Pylint 4.1.4 applies the rule shown in the local pylint source. The pin appears in `requirements-dev.txt`.
- Python 3.15 keeps `KeyboardInterrupt` and `SystemExit` as direct `BaseException` subclasses.

## Out of Scope

- Other pylint messages in `MistHelper.py`.
- Adding `MistHelper.py` to the CI pylint job.
- Updating historical line citations in documents and in `src/` comments.
- Removing the stray `# hi` comment at line 8372. This is a separate defect.
- Reducing the direct-child debt of `changelog.d/` and `tests/unit/`.
