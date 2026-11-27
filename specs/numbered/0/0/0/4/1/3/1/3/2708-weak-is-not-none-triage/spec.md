# Feature Specification: Test quality: triage weak_is_not_none findings

**Feature Branch**: `chore/2708-weak-is-not-none-triage`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #2708, "Test quality: triage weak_is_not_none findings". The issue is open. Its labels are chore, tests, in-progress, testing, priority:P3, and severity:medium.

## Background

Issue #2708 follows issue #1772. The issue asks for a triage of each `weak_is_not_none` finding. It asks for a repair of the tests or the analyzer rule for that group. The rule flags each assert statement of the form `assert x is not None`. Source: `.venv/Lib/site-packages/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py` line 310 (local, installed analyzer 0.6.4).

On remote main, commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, the baseline holds 84 entries for this rule. A per-line check finds 65 weak guards still present and 19 entries stale. The analyzer did not run for this record. Design/research.md lists that gap under Unverified.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify every baseline entry (Priority: P1)

A maintainer reads one complete list. Each of the 84 baseline entries has one category, one task, and one evidence row.

**Why this priority**: No repair can prove the group is done without a complete list.

**Independent Test**: Count the entries in tasks.md and the rows in the remote table of design/research.md. The rule entries total 84 in both places.

**Acceptance Scenarios**:

1. **Given** the baseline on main, **When** triage completes, **Then** each entry appears under exactly one task.
2. **Given** an entry with an open owner, **When** triage completes, **Then** the entry names the owner and the release condition.

---

### User Story 2 - Repaired guards fail on broken behavior (Priority: P1)

A reviewer sees that each repaired line rejects a controlled wrong value. The wrong value exists only in test memory.

**Why this priority**: A guard that cannot fail gives no protection.

**Independent Test**: Run the affected test with one controlled wrong value. The original line passes it. The repaired line fails it.

**Acceptance Scenarios**:

1. **Given** a repaired weak guard, **When** the guarded value changes in memory, **Then** the test fails at the repaired line.
2. **Given** a repaired line, **When** the file is searched, **Then** that line holds no `is not None` assert statement.

---

### User Story 3 - Lower the count without losing scope (Priority: P2)

A maintainer sees the count fall. No rule, config value, exclusion, marker, or test scope changes to make the count fall.

**Why this priority**: Earlier work reduced counts by removing scope. The issue records that failure.

**Independent Test**: The gate summary reports zero new findings after each slice. The baseline diff adds no entry.

**Acceptance Scenarios**:

1. **Given** a slice, **When** the gate runs, **Then** the gate reports zero new findings.
2. **Given** a stale entry, **When** the analyzer confirms its absence, **Then** the entry leaves the baseline in the same slice.

---

### User Story 4 - Held files wait for their owners (Priority: P2)

A contributor does not edit a file that an open issue or pull request reserves. Each hold names its owner.

**Why this priority**: Two changes to one file conflict and can lose work.

**Independent Test**: Each held file appears in a hold task with its owner and release condition.

**Acceptance Scenarios**:

1. **Given** a file under an open reservation, **When** a slice selects it, **Then** the slice removes the file from its scope.

---

### User Story 5 - Reuse preserved work only after review (Priority: P3)

A contributor reads each preserved candidate as evidence. The contributor derives each repair again from main.

**Why this priority**: Preserved candidates are not on main and have no reviewed proof.

**Independent Test**: Each slice names the source of its repair. A slice that copies a candidate blob fails review.

**Acceptance Scenarios**:

1. **Given** a preserved candidate, **When** a slice uses it, **Then** the slice cites its derivation from main.

---

### Edge Cases

- A repaired line changes the line count of its file. Each later finding in that file moves. The gate then reports moved findings as new. The baseline update must record only that shift.
- Main moves during a slice. The slice rebases on main. It rechecks each repaired line before push.
- The analyzer reports a finding that the triage marks stale. The analyzer result controls. The baseline entry stays until the analyzer confirms its absence.
- A compose-gated test skips without running services. The record does not count that skip as a pass.
- An open pull request changes a file in a slice. The slice waits for that pull request. Pull request #4208 changes `tests/guardrails/test_src_public_symbol_preservation.py`, a stale entry in this record.
- A preserved candidate matches a wanted repair. The slice does not copy its blob.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST classify each baseline entry for `weak_is_not_none` on main into one category.
- **FR-002**: Each repaired finding MUST replace its weak guard with one exact check on the same line.
- **FR-003**: A repair MUST keep the file line count unchanged, unless the baseline update records each shift.
- **FR-004**: Each repaired guard MUST fail for one controlled wrong value. The pull request body MUST record that result.
- **FR-005**: The record MUST NOT lower the count by changing a rule, a config value, an exclusion, a marker, or test scope.
- **FR-006**: A stale entry MUST leave the baseline only after the analyzer confirms its absence on main.
- **FR-007**: The baseline MUST change only through the documented analyzer command. The diff MUST be reviewed.
- **FR-008**: A slice MUST NOT edit a file that an open issue or pull request reserves.
- **FR-009**: Each slice pull request MUST close its own child issue and MUST contain `Part of #2708`. Only the final slice MUST contain `Closes #2708`.
- **FR-010**: Each changed test line MUST carry an inline comment. Each new assertion message MUST use ASCII characters.
- **FR-011**: Each slice MUST run each applicable local gate before push. The pull request body MUST list each result.
- **FR-012**: Slices MUST merge one at a time. Each slice MUST rebase on current main before its checks run.
- **FR-013**: Each claim about a commit, branch, or blob MUST cite GitHub evidence. Local-only evidence MUST carry the label "local only".

### Key Entities

- **Baseline entry**: One `weak_is_not_none` row in `.github/test-quality-baseline.json`. Its identity has five fields. The line number is one field.
- **Weak guard**: One assert statement of the form `assert x is not None`.
- **Slice**: One pull request that repairs one group of files. Slices merge one at a time.
- **Hold**: One reservation by an open issue or pull request. A hold blocks edits to its file.

### Mist Cloud Transport Requirements

Not applicable. The record adds no Mist REST request and no transport. The registry test in `mist-ops-platform/tests/unit/mist/test_registry_validation.py` checks module resolution only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 84 of 84 baseline entries have one category and one remote row.
- **SC-002**: After the last slice, no repaired line holds an assert `is not None` statement.
- **SC-003**: Each slice reports zero new findings in the gate summary.
- **SC-004**: Each hold names its owner and its release condition.
- **SC-005**: Each slice pull request passes the `test_quality_gate` check on its final commit.

## Assumptions

- Main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` is the base of the first slice. Later slices rebase on newer main commits.
- The analyzer comes from the `misthelper-devtools` package. `requirements-dev.txt` line 197 pins it.
- The repository venv runs the local gates on Windows. `documentation/development-setup.md` line 40 describes the venv bootstrap.
- Test-only changes add no changelog fragment. Design/research.md decision D-12 records that choice.

## Clarifications

### Session 2026-11-26

- Q: Which findings form the scope? A: The 84 baseline entries on main. The 2026-11-10 report with 67 entries is stale. Decision D-1.
- Q: Which analyzer command applies? A: The documented gate command. The issue command `python -m tools.test_quality_analyzer` has no target on main. Decision D-8.
- Q: Which closing keyword applies? A: Each slice closes its own child issue and names `Part of #2708`. The final slice closes `#2708`. Decision D-9.
- Q: Do slices merge in parallel? A: No. One slice merges at a time. Decision D-10.

## Non-Goals

- No change to analyzer logic, rule names, or config keys. The analyzer lives in the external `misthelper-devtools` package.
- No repair of root-logger isolation. Issue #4728 tracks that defect.
- No change to the credential session design. Issue #3714 tracks that design.
- No change to other rule groups, such as `weak_zero_assertions` in issue #2711.
- No production code change.
