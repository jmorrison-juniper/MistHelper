# Feature Specification: Analyzer Skip Reporting

**Feature Branch**: `1768-analyzer-skips`

**Created**: 2026-09-15

**Status**: Draft

**Input**: GitHub issue #1768: analyzers skip source areas silently, so a green report can be incomplete.

## User Scenarios & Testing

### User Story 1 - See the measured files (Priority: P1)

A maintainer runs an analyzer and sees the files that it read. The report also lists each skipped file or target, with the reason.

**Why this priority**: A green result must prove its measurement area.

**Independent Test**: Run each analyzer on a small target set and verify that the output names the read set and the skipped set.

**Acceptance Scenarios**:

1. **Given** a valid source file, **When** the analyzer runs, **Then** the report lists the file in the read set.
2. **Given** an excluded source file, **When** the analyzer runs, **Then** the report lists the file in the skipped set with a reason.

---

### User Story 2 - Fail on an unintended skip (Priority: P2)

A maintainer runs an analyzer with a target that should be measured. If the analyzer skips that explicit target, the run fails.

**Why this priority**: A silent skip can hide unmeasured code behind a green result.

**Independent Test**: Run an analyzer with an explicit target that an exclusion rule skips and verify a non-zero exit code.

**Acceptance Scenarios**:

1. **Given** an explicit Python file target under an excluded path, **When** the analyzer runs, **Then** it exits with code 2.
2. **Given** a missing target among valid targets, **When** the analyzer runs, **Then** it exits with code 2 and names the target.

---

### User Story 3 - Know when the repository is not fully measured (Priority: P3)

A maintainer can distinguish a full repository measurement from a partial measurement. The report states whether the run is complete or partial.

**Why this priority**: Partial runs are useful, but the output must not look like full coverage.

**Independent Test**: Run an analyzer with a narrow target and verify that the report marks the scope as partial.

**Acceptance Scenarios**:

1. **Given** a narrow target, **When** the analyzer runs, **Then** the report marks the scope as partial.
2. **Given** all supported roots, **When** the analyzer runs, **Then** the report marks the scope as complete for that analyzer.

### Edge Cases

- If a directory has no supported files, the analyzer records the directory as skipped.
- If git cannot answer an ignore query, the analyzer records no git-ignore skip and scans the collected files.
- If a test file cannot parse, the test quality analyzer records a parse error instead of a silent skip.
- If the STE linter receives an unsupported file type, it records the skip and fails with a usage error.

## Requirements

### Functional Requirements

- **FR-001**: Each analyzer MUST report the files that it read.
- **FR-002**: Each analyzer MUST report each skipped file or target with a reason.
- **FR-003**: Each analyzer MUST fail when an explicit target is skipped unintentionally.
- **FR-004**: Each analyzer MUST state whether the run measured the full supported repository scope or a partial scope.
- **FR-005**: The compliance analyzer MUST report default excludes, user excludes, missing targets, non-Python targets, and git-ignored files.
- **FR-006**: The refactor analyzer MUST report the entrypoint, module graph files, pinned candidates, and unresolved first-party imports.
- **FR-007**: The STE linter MUST report graded files, unsupported files, missing files, and dictionary absence.
- **FR-008**: The test quality analyzer MUST report analyzed files, skipped files, parse errors, and omitted test roots.
- **FR-009**: The repository MUST provide one documented command for whole-repository analyzer runs.
- **FR-010**: Bandit configuration MUST include `tools`, so the security analyzer measures analyzer packages.

### Key Entities

- **Analyzer coverage record**: One read file or one skipped target, including the reason.
- **Analyzer coverage summary**: The read count, skip count, scope status, and failure flag for one analyzer run.
- **Analyzer report**: The existing analyzer output plus the coverage summary.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each changed analyzer prints or writes a read count and a skip count.
- **SC-002**: A test proves that an explicit skipped compliance target exits with code 2.
- **SC-003**: A test proves that the test quality analyzer reports an omitted test root.
- **SC-004**: A repository-wide analyzer command exists and names the roots it measures.
- **SC-005**: The changed analyzer tests pass on Windows with Python 3.13.

## Assumptions

- The supported analyzer set is `compliance_analyzer`, `refactor_analyzer`, `ste_linter`, and `test_quality_analyzer`.
- A targeted scan can stay valid when the output clearly marks the scope as partial.
- Existing analyzer command names and exit codes remain compatible, except for explicit skipped targets.
