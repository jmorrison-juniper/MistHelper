# Feature Specification: Issue 1772 test-quality triage

**Feature Branch**: `chore/1772-test-quality`

**Created**: 2026-09-15

**Status**: Ready for review

**Input**: User description: "Triage issue #1772, re-measure the test-quality findings, repair the high-severity set, and defer the rest with issues."

## User Scenarios & Testing

### User Story 1 - Re-measure current findings (Priority: P1)

A maintainer needs a current analyzer result after issue #1768 changed analyzer coverage reporting.

**Why this priority**: The original 1,596 total and 35 high-severity counts are obsolete.

**Independent Test**: Run `python -m tools.test_quality_analyzer` and compare the report with the original issue counts.

**Acceptance Scenarios**:

1. **Given** the branch starts from current `origin/main`, **When** the analyzer runs, **Then** it reports the current total and severity counts.
2. **Given** the analyzer skips Mist API tests, **When** the report is read, **Then** each skipped file has a reason.

---

### User Story 2 - Repair the high-severity set (Priority: P1)

A maintainer needs high-severity findings to describe tests that can hide defects, not pytest infrastructure.

**Why this priority**: A high-severity false positive hides the important unmeasured-green defects described by issues #2654 and #2689.

**Independent Test**: Run the regression test for pytest helper roots, then rerun the analyzer.

**Acceptance Scenarios**:

1. **Given** a pytest root contains fixtures and helpers, **When** the CLI runs, **Then** it does not report `untested_public_function` for that root.
2. **Given** analyzer fixture roots model source-under-test files, **When** detector meta-tests run, **Then** `UntestedDetector` still reports bad fixtures.

---

### User Story 3 - Defer remaining groups with clear ownership (Priority: P2)

A maintainer needs each remaining rule group to have one follow-up issue.

**Why this priority**: The remaining 2,569 findings are too large for one safe pull request.

**Independent Test**: Read `specs\1772-test-quality\triage.md` and confirm each rule group has a decision and issue number.

**Acceptance Scenarios**:

1. **Given** the triage table lists a remaining rule group, **When** a reader checks the Follow-up column, **Then** it names an issue number.
2. **Given** a future maintainer repairs one group, **When** they open its issue, **Then** it states the group count and acceptance criteria.

### Edge Cases

- If issue #1768 exposes skipped files, state that the measurement is incomplete for those files.
- If the analyzer fixture corpus runs through the CLI, preserve its `untested_public_function` signal.
- If a high-severity finding points to pytest infrastructure, repair the analyzer instead of changing the baseline.

## Requirements

### Functional Requirements

- **FR-001**: The triage MUST record current total, severity, skipped-file, parse-error, and stale-baseline counts.
- **FR-002**: The triage MUST compare current counts with the original 1,596 total and 35 high-severity counts.
- **FR-003**: The analyzer MUST not run `UntestedDetector` on real pytest roots as source-under-test roots.
- **FR-004**: The analyzer MUST keep `UntestedDetector` behavior for synthetic analyzer fixture roots.
- **FR-005**: Each remaining rule group MUST have a decision and one follow-up issue number.
- **FR-006**: The pull request MUST not edit `CHANGELOG.md` or frozen vendor documentation.

### Key Entities

- **Analyzer report**: JSON and Markdown output from `tools.test_quality_analyzer`.
- **Triage decision**: A rule and severity group with a count, decision, reason, and follow-up.
- **High-severity decision**: One original high finding with its file, line, function, classification, and decision.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The pre-repair analyzer run records 2,693 findings, 124 high-severity findings, 28 skipped files, and zero parse errors.
- **SC-002**: The post-repair analyzer run records 2,569 findings, zero high-severity findings, 28 skipped files, and zero parse errors.
- **SC-003**: The regression test `test_pytest_helper_root_does_not_emit_untested_public_function` passes.
- **SC-004**: Each of the 16 remaining medium-severity rule groups has a follow-up issue.

## Assumptions

- The triage is the deliverable. This pull request does not attempt a 2,569-finding repair sweep.
- The 28 skipped Mist API files remain unmeasured by the default analyzer run.
- Synthetic analyzer fixtures can keep using test roots as source-under-test data.
