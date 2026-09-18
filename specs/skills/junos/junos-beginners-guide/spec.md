# Feature Specification: Day One: Beginner's Guide to Learning Junos skill package

**Feature Branch**: `feat/2925-juniper-skill-factory`

**Created**: 2026-09-18

**Status**: Generated

**Input**: Source document `C:\Users\jmorrison\Downloads\juniper-harvest-md\guides\junos-beginners-guide.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build the skill package (Priority: P1)

As an AI agent, I need a bounded skill package for `Day One: Beginner's Guide to Learning Junos`.
I can answer Junos questions with three file reads.

**Why this priority**: The skill must route before it can answer a question.

**Independent Test**: Generate the package and confirm that every required artifact exists.

**Acceptance Scenarios**:

1. **Given** the source Markdown exists, **When** the harness runs, **Then** it writes the full artifact set.
2. **Given** the package exists, **When** the Companion GUI reads it, **Then** context shows completed status.

### Edge Cases

- The harness records missing companion extension files in `analysis.md`.
- The harness records source drift by hash so a re-converted document can trigger a sync.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST write all required artifacts.
  The artifacts include spec, plan, tasks, checklist, analysis, and context.
- **FR-002**: The harness MUST reuse the installed SpecKit templates before it renders artifacts.
- **FR-003**: The harness MUST record source metadata for living-spec drift checks.
- **FR-004**: The harness MUST run a cross-artifact analysis that maps requirements to tasks.
- **FR-005**: The harness MUST report missing companion extension files.

### Key Entities

- **SkillDocument**: The source Markdown file, title, domain, page count, slug, and source hash.
- **SpecKitArtifactSet**: The generated specification, plan, tasks, checklist, analysis, and context files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The generated artifact set contains all six required files.
- **SC-002**: The analysis check reports zero critical issues for this generated package.
- **SC-003**: The context file contains `currentStep`, `status`, `phase`, `phaseStatus`, and `completionPercentage`.

## Assumptions

- The domain for this proof document is `junos`.
- The harness writes programmatic artifacts because 1,500 interactive runs are not practical.
