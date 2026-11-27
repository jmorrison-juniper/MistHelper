# Feature Specification: Weak zero-assertion triage

**Feature Branch**: `chore/2711-weak-zero-assertions` (planning). Each slice uses `test/2711-<slice-slug>`.

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #2711, "Test quality: triage weak_zero_assertions findings". The issue reports 876 medium findings from the 2026-09-15 analyzer run. Its triage decision is "real defect, repair later".

## Clarifications

### Session 2026-11-26

- Q: Which analyzer decides the test-quality gate?
  A: The commit pinned in `requirements-dev.txt` line 197, `misthelper-devtools` commit `2239e7bd`, version 0.6.4. Older reports in the issue comments do not decide the gate.
- Q: Is `python -m tools.test_quality_analyzer` the acceptance command?
  A: No. The `tools` module is absent on `main`. Use `test-quality-analyzer` from the local gates table.
- Q: Does the gate fail on `main` with 18 new findings, as comment 167 reports?
  A: No, under the pinned analyzer. The pinned gate passed on `main` commit `f03c6c9`. The 18 entries are shifted baseline entries that an older analyzer flags.
- Q: Which test paths does the work use?
  A: The current tree paths on `main`. Paths in older comments are stale after the relocation in pull request #4358.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore a baseline that matches the analyzer (Priority: P1)

A maintainer runs the full test-quality gate. The baseline lists 557 `weak_zero_assertions` entries. Of these, 313 entries no longer match a finding. The maintainer needs a baseline that lists only current findings.

**Why this priority**: A stale baseline hides which entries still need work. It also makes each later change look like a new finding.

**Independent Test**: Run the full gate after one serial baseline change. The gate reports zero new findings. The weak-zero entry count equals the count of current findings.

**Acceptance Scenarios**:

1. **Given** the pinned analyzer and the 557-entry baseline, **When** the analyzer rewrites the baseline, **Then** only `weak_zero_assertions` entries change.
2. **Given** the rewritten baseline, **When** the full gate runs, **Then** the gate reports zero new findings.
3. **Given** a baseline entry for a missing test file, **When** the rewrite runs, **Then** that entry is removed.

---

### User Story 2 - Repair tests that assert nothing (Priority: P2)

A reviewer finds 115 test functions with no assertion construct in the test body. The repair adds behavior checks to each test. A mutation control proves that each repaired test fails when the guarded behavior breaks.

**Why this priority**: These tests pass without checking any result. They add coverage without evidence.

**Independent Test**: Apply one in-memory mutation to the code under test. The repaired test fails. The same test passes on the unmodified code.

**Acceptance Scenarios**:

1. **Given** a repaired test, **When** the mutation control runs, **Then** the test fails with an assertion error.
2. **Given** the unmodified code, **When** the repaired test runs, **Then** the test passes.
3. **Given** a repaired slice, **When** the changed-from gate runs, **Then** the gate reports zero new findings.

---

### User Story 3 - Route detector gaps to the analyzer owner (Priority: P2)

A reviewer finds 129 entries where a valid assertion exists, but the pinned analyzer does not count it. These entries use mock call-count methods, Playwright `expect`, or assertion helpers. The owner of `misthelper-devtools` must change the detector. MistHelper keeps these entries until the pin changes.

**Why this priority**: Rewriting these tests would weaken them or add redundant checks.

**Independent Test**: The upstream issue lists each detector-gap family, its count, and one example. No MistHelper test changes for these families.

**Acceptance Scenarios**:

1. **Given** a detector-gap entry, **When** the reviewer reads the test, **Then** the test contains a real assertion that the detector misses.
2. **Given** the upstream issue, **When** a maintainer reads it, **Then** it names each family with its count.

### Edge Cases

- A test calls a helper that holds the assertions. The helper body is read before the entry receives a disposition. A helper name alone is not evidence.
- A repaired test adds lines above a flagged test. The flagged test shifts to a new line. Its baseline entry then looks new. The same serial pull request re-keys that entry.
- A test uses a fixture that holds assertions. The fixture body is read before the entry receives a disposition.
- A test file moves to a new path. The baseline entry for the old path becomes stale. The new path receives the disposition.
- A test uses Playwright `expect`. The analyzer does not count the call. The entry belongs to the detector-gap family.
- A pull request adds `Closes #2711` before the final acceptance. The merge closes the umbrella issue, as it did for pull request #4515.
- A preserved branch overlaps a current file. The branch is not integrated until its owner gives a file handoff.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The work MUST use the pinned `misthelper-devtools` analyzer as the only gate authority.
- **FR-002**: The work MUST assign each baseline `weak_zero_assertions` entry to exactly one disposition.
- **FR-003**: The work MUST remove stale baseline entries only through the analyzer write command with the full-suite scope.
- **FR-004**: The work MUST repair each zero-construct test with behavior assertions. The repair MUST add no redundant or placeholder assertion.
- **FR-005**: Each repaired test MUST have an in-memory mutation control. The control MUST fail the repaired test and pass on unmodified code.
- **FR-006**: Detector-gap entries MUST route to the `misthelper-devtools` owner. MistHelper MUST NOT rewrite those tests or suppress those findings.
- **FR-007**: Each helper-based case MUST have its helper body read before disposition.
- **FR-008**: The work MUST use current tree paths. Each stale comment path MUST appear in the analysis as stale.
- **FR-009**: Each slice pull request MUST use `Part of #2711` in its body. Only the final pull request MAY use a closing keyword.
- **FR-010**: The work MUST check file overlap with open pull requests before each slice. It MUST NOT integrate a preserved branch without an owner handoff.
- **FR-011**: Each change MUST pass the local gates that apply to its changed files.
- **FR-012**: Each pull request MUST show a passing test-quality job in CI before merge.
- **FR-013**: The issue MUST stay open until the zero-construct family is empty and the detector-gap family has an upstream owner.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. The change edits test code and one baseline file. No Mist REST or WebSocket request is added, removed, or changed.

### Key Entities *(include if feature involves data)*

- **BaselineEntry**: One analyzer-keyed record in `.github/test-quality-baseline.json`. The key includes the line number.
- **Finding**: One current analyzer result for a test function. It uses the same key as a baseline entry.
- **Disposition**: The class of one entry. Each entry has exactly one of six classes.
- **Slice**: One domain group of test files. One slice equals one pull request.

Details appear in `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After each serial merge, the full-suite gate reports zero new findings.
- **SC-002**: The final baseline holds 129 `weak_zero_assertions` entries. These entries await the detector fix.
- **SC-003**: The count of zero-construct findings reaches zero.
- **SC-004**: Each repaired test has one recorded mutation control. The control fails the repaired test.
- **SC-005**: One upstream issue exists in `misthelper-devtools`. It names the three detector-gap families with their counts.
- **SC-006**: Each pull request passes its local gates and its CI test-quality job.

## Assumptions

- The local `.venv` installs the pinned analyzer. The check in T001 proves the version.
- The implementation agent can run the analyzer and the tests on a local machine.
- The count of 244 current findings holds until the analyzer report confirms it.
- CI runs the full-suite gate on `main` for each manual or push run.
- The owner of `misthelper-devtools` accepts a detector change request.

## Out of Scope

- Changing `misthelper-devtools` code in this repository.
- Changing the devtools pin in `requirements-dev.txt`.
- Changing `.github/test-quality-config.toml` or any rule switch.
- Changing entries for other rules, such as `weak_is_not_none` (#2708) or `weak_bare_assert` (#2707).
- Deleting a test to lower the count.
- Adding a suppression comment, a configuration exclusion, or a fixture marker that hides a finding.
- Integrating preserved branches from comments 159 through 166 without a handoff.
