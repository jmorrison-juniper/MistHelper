# Feature Specification: HTTP 4xx Test-Quality Findings

**Feature Branch**: `test/2746-http-4xx-baseline`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #2746, "Test quality: repair remaining missing_fm_http_4xx findings".

## Terms

- **Baseline**: The file `.github/test-quality-baseline.json`.
- **Baseline entry**: One object in the baseline.
- **Analyzer**: The `test-quality-analyzer` command in misthelper-devtools.
- **Pinned analyzer**: misthelper-devtools at commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- **Complete report**: The output of one full analyzer scan that writes a report file.
- **Finding**: One analyzer result in a complete report.
- **Class A entry**: A baseline entry whose test module makes no HTTP request.
- **Class B entry**: A baseline entry whose test module already has a 4xx test. Task T002 confirms that no finding remains.
- **Class C entry**: A baseline entry whose test module has 4xx tests that the analyzer cannot attribute.
- **Absent-file entry**: A baseline entry whose file the scan cannot reach.
- **Upstream repair**: A change in the misthelper-devtools repository.

## Clarifications

### Session 2026-11-26

- Q: Does issue #2746 cover `missing_fm_http_5xx`? A: No. The issue title and body name `missing_fm_http_4xx`. Issue #2747 owns `missing_fm_http_5xx`.
- Q: Which list defines the working set? A: The 38 baseline entries on main. The issue body count of 71 is outdated.
- Q: Does `--prune-baseline` remove class B entries? A: No. It removes absent-file entries only.
- Q: Does this record add a test? A: No new test function. No real gap exists in the working set.
- Q: Which pull request closes issue #2746? A: Only the final pull request uses `Closes #2746`.

## User Scenarios & Testing

### User Story 1 - Reconcile the 4xx backlog (Priority: P1)

A maintainer needs one accurate list of the `missing_fm_http_4xx` baseline entries. Each entry needs a class and evidence.

**Why this priority**: Every later step requires a correct count.

**Independent Test**: Run a complete report and compare each finding with the classes in `analysis.md`.

**Acceptance Scenarios**:

1. **Given** the baseline holds 38 `missing_fm_http_4xx` entries, **When** the record is reviewed, **Then** each entry has one class and one evidence line.
2. **Given** the complete report differs from the record, **When** the maintainer reviews it, **Then** the record changes before any baseline edit.

### User Story 2 - Remove class B entries without hiding findings (Priority: P1)

A maintainer removes class B entries that no finding matches. No new finding enters the baseline.

**Why this priority**: Class B entries keep the backlog false.

**Independent Test**: Run the test-quality gate after the removal. The gate reports zero new findings.

**Acceptance Scenarios**:

1. **Given** a class B entry has no finding in the complete report, **When** the entry is removed, **Then** the gate reports zero new findings.
2. **Given** the diff changes an entry that is not a `missing_fm_http_4xx` entry, **When** the diff is reviewed, **Then** the change is reverted.

### User Story 3 - Clear class A and class C findings upstream (Priority: P2)

A maintainer repairs the analyzer in misthelper-devtools, releases it, and pins the new commit. Class A and class C findings then leave the complete report.

**Why this priority**: No test in this repository can clear these findings.

**Independent Test**: After the pin change, the complete report omits each class A and class C finding.

**Acceptance Scenarios**:

1. **Given** a local opt-in marker is proposed, **When** the change is reviewed, **Then** the marker is rejected.
2. **Given** the released analyzer omits a finding, **When** its entry is removed, **Then** the gate reports zero new findings.

### User Story 4 - Add a test only for a real gap (Priority: P3)

A maintainer adds a test only when a product path has no 4xx test.

**Why this priority**: A duplicate test adds no coverage.

**Independent Test**: The new test fails when its checked failure behavior is removed.

**Acceptance Scenarios**:

1. **Given** no real gap exists, **When** this record runs, **Then** no new test module is added.
2. **Given** a real gap exists, **When** a test is added, **Then** the test uses a native 4xx response and asserts the failure result.

### Edge Cases

- The complete report count differs from the working set. The record changes before any removal.
- A baseline entry names a moved or absent file. The analyzer treats it as an absent-file entry.
- A test module imports a class that makes HTTP requests, but the test does not. The entry is class A.
- A product function returns a 4xx result as data. The test asserts the returned result.
- A test has no stable way to observe the failure result. The product change gets a separate issue.
- A removal introduces a new finding. The removal is reverted.

## Requirements

### Functional Requirements

- **FR-001**: The record MUST classify each of the 38 `missing_fm_http_4xx` baseline entries.
- **FR-002**: The record MUST route each class A and class C entry to an upstream repair.
- **FR-003**: The record MUST require one native 4xx test for each real gap in a product path.
- **FR-004**: The change MUST remove a class B entry only after a complete report omits its finding.
- **FR-005**: The change MUST NOT add an opt-in marker, an exclusion, a synthetic status object, or a baseline entry.
- **FR-006**: The change MUST NOT change production behavior or an existing test assertion.
- **FR-007**: A product defect found during verification MUST get a separate issue.
- **FR-008**: Each new test MUST fail when its checked failure behavior is removed.
- **FR-009**: Each decision MUST name its alternatives, its choice, its reason, and its risk.
- **FR-010**: Interim pull requests MUST use `Part of #2746`. Only the final pull request MUST use `Closes #2746`.

### Key Entities

- **Baseline entry**: One accepted finding. Its key holds category, rule identifier, file path, line number, and explanation.
- **Finding**: One analyzer result in a complete report.
- **Test module**: One Python test file. Its blob identifier on main confirms its content.
- **Upstream dependency**: The misthelper-devtools repository and its issue #67.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The record classifies 38 of 38 baseline entries with one class and one evidence line each.
- **SC-002**: The complete report shows zero new findings after the change.
- **SC-003**: The baseline diff contains removed `missing_fm_http_4xx` entries only.
- **SC-004**: The change adds zero markers, zero exclusions, and zero synthetic status objects.
- **SC-005**: The test-quality gate, the guard preflight, and the guardrail tests pass on the pull request head.

## Out of Scope

- `missing_fm_http_5xx` findings. Issue #2747 owns them.
- Changes to the misthelper-devtools repository. This record names that repository as a dependency only.
- Production code changes. Verification found no open product defect.
- A guard for unmatched entries. The analyzer contract owns that change.

## Assumptions

- The local checkout matches `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Three blob checks confirm the match.
- The installed analyzer equals the pinned analyzer. The installed direct URL file names commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Execution steps run the analyzer. This record phase does not run it.

## Dependencies

- misthelper-devtools issue #67, "SourceDrivenCoverageSlicer discards every fixture-driven test", is open.
- A misthelper-devtools release that carries the applicability repairs. Task T005 owns it.
