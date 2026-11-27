# Feature Specification: C0103 naming exceptions in MistHelper.py

**Feature Branch**: `chore/4130-c0103-invalid-names`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Lint: C0103 invalid-name -- 29 names do not match the naming style in 2 files" (GitHub issue #4130)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The named files pass the C0103 check (Priority: P1)

A maintainer runs pylint with the C0103 check on the two named files. The run reports no naming finding.

**Why this priority**: This is the expected outcome of issue #4130. The lint debt stays open until this check passes.

**Independent Test**: Run the pylint command in `design/quickstart.md`. The JSON output contains no message for either file.

**Acceptance Scenarios**:

1. **Given** the change is applied, **When** pylint checks `web_portal/services/operation.py`, **Then** it reports zero C0103 messages.
2. **Given** the change is applied, **When** pylint checks `MistHelper.py`, **Then** it reports zero C0103 messages.

---

### User Story 2 - Runtime behavior and module names stay unchanged (Priority: P1)

A reviewer reads the diff. The diff adds comments and one configuration key. It renames no module-level name.

**Why this priority**: The symbol gate and the string-keyed bootstrap need the current names. A rename breaks imports and tests.

**Independent Test**: Run the symbol gate and the targeted test modules listed in `design/quickstart.md`. Each command passes.

**Acceptance Scenarios**:

1. **Given** the diff, **When** `symbol-diff` checks `MistHelper.py`, **Then** it prints `symbol_diff: no module-level name changed` and exits with code 0.
2. **Given** the diff, **When** the targeted test modules run, **Then** no test fails.

---

### User Story 3 - Each exception is reviewed and bounded (Priority: P2)

A reviewer finds each kept name and its reason in one place. A guard test fails when an unreviewed exception appears.

**Why this priority**: A pragma can hide a future finding. A fixed count keeps the remaining lint debt visible.

**Independent Test**: Run the three guard test cases. Each case passes on the final tree.

**Acceptance Scenarios**:

1. **Given** a new `invalid-name` pragma, **When** the guard counts the pragmas, **Then** the count differs from 24 and the guard fails.
2. **Given** the module-name rule, **When** the guard tests two names, **Then** it accepts `MistHelper` and rejects `Mist_Helper`.

### Edge Cases

- A new module-level name appears in `MistHelper.py`: the symbol gate reports an added name, and the guard count changes.
- Pylint does not report a predicted name: its pragma has no effect. Task T009 removes that pragma.
- Remote `main` moves before the pull request opens: rebase the branch, then rerun task T009.
- Another open pull request changes `MistHelper.py` during the work: stop and wait. `MistHelper.py` is a hot file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST keep `web_portal/services/operation.py` free of C0103 findings.
- **FR-002**: The change MUST leave `MistHelper.py` free of C0103 findings under pylint 4.1.4.
- **FR-003**: The change MUST keep the file name `MistHelper.py`.
- **FR-004**: The change MUST keep every module-level name, function name, and class name unchanged.
- **FR-005**: The change MUST allow the module name `MistHelper` only through `module-rgx` in `[tool.pylint.basic]`.
- **FR-006**: Each kept name MUST carry one `invalid-name` pragma on its flagged line, with a reason.
- **FR-007**: The change MUST add no executable statement and no behavior change.
- **FR-008**: A guard test MUST check zero findings, the pragma count, and the module-name rule.
- **FR-009**: The change MUST add one changelog fragment under `changelog.d/`.
- **FR-010**: The change MUST track each deferred rename in a follow-up issue.
- **FR-011**: The change MUST pass each applicable local gate and record each result.
- **FR-012**: The change MUST confirm that no open pull request changes the same files before the pull request opens.

### Key Entities *(include if feature involves data)*

Not applicable: this change adds no data entity. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pylint reports 0 C0103 messages for both named files.
- **SC-002**: `symbol-diff` reports no module-level name change for `MistHelper.py` and exits with code 0.
- **SC-003**: The three guard test cases pass.
- **SC-004**: `MistHelper.py` contains exactly 24 `invalid-name` pragma lines.
- **SC-005**: The two targeted test modules report zero failures.

## Assumptions

- The base commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main`. It stays the base until the pull request opens.
- The `.venv` interpreter runs pylint 4.1.4, the version that `pyproject.toml` pins.
- The change runs on Windows 11. The same code runs in the Linux container.
- The predicted findings use pylint 4.1.4 source logic. Task T002 records the actual output.

## Out of Scope

- Renaming any module-level name, the module file, or a method name.
- Redesigning the optional-dependency bootstrap or the fallback classes.
- Changing the CI pylint scope in `.github/workflows/ci.yml`.
- Other pylint messages in `MistHelper.py`.
- Repairing the rule conflict in `changelog.d/README.md`.
- Removing the legacy private globals in `MistHelper.py`.

## Clarifications

### Session 2026-11-26

- Q: Is `web_portal/services/operation.py` still open? A: No. PR #4662 merged on 2026-11-09 at commit `a71078c3e96dd46dd9a10b64fb5e7654a6fc895b`.
- Q: Do the line numbers in the issue still apply? A: No. Commit `61505c611` is absent on the remote. PR #4607 changed `MistHelper.py` after the last recorded run.
- Q: Keep or rename `MistHelper.py`? A: Keep the name. See decision D-1 in `design/research.md`.
- Q: Rename the flagged module-level names? A: No. The symbol gate fails on any lost or added name. See decision D-2.
- Q: Does any open pull request change the target files? A: No. The check ran on 2026-11-26.
