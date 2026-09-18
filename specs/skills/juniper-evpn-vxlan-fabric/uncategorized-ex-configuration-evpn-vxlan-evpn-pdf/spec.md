# Feature Specification: Junos® OS EVPN User Guide skill package

Command: speckit.specify

**Feature Branch**: `feat/2925-juniper-skill-factory`

**Created**: 2026-09-18

**Status**: Generated

**Input**: Source document `C:\Users\jmorrison\Downloads\juniper-harvest-md\uncategorized\ex__configuration__evpn-vxlan\evpn.md`

## Document Measurements

Document title: Junos® OS EVPN User Guide
Domain: juniper-evpn-vxlan-fabric
Category: uncategorized
Page count: 2220
Part count: 1
Topic count: not measured
Life cycle spread: not measured
Guard result: not measured
STE result: not measured
Version status: unversioned
Superseded by: not measured
Source hash: 1d0b0aab50c589679d4d1889528defd54a6e0c54002b68bbffbe180db194f474
Package path: not measured


## Document Subjects

Subjects: not measured

Keywords: not measured

## Life Cycle Coverage

Life cycle coverage is not measured.

## Source Quality

Source defects: not measured.

Guard result: not measured.

STE result: not measured.

## Reader Expectations

- Do not expect complete vendor prose.
- Do not expect topics from absent life cycle stages.
- Do not use the topic count until the installed package exists.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer questions from this document (Priority: P1)

As an AI agent, I need topic routes for `Junos® OS EVPN User Guide`.
I can select the correct topic and cite the source page range.

**Why this priority**: The package must answer questions about this document, not about the harness.

**Independent Test**: Read the installed package and confirm the measured topics and life cycles.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST cover the measured subjects listed in this specification.
- **FR-002**: The package MUST state which life cycle stages are covered and which stages are absent.
- **FR-003**: The package MUST record the source part structure and source quality findings.
- **FR-004**: The package MUST record version status and superseded status from the factory database.
- **FR-005**: The package MUST report guard and STE measurements without invented values.
- **FR-006**: The package MUST reference the shared SpecKit conversion contract.

### Key Entities

- **SkillDocument**: The source Markdown file, title, domain, page count, slug, and source hash.
- **SpecKitArtifactSet**: The generated specification, plan, tasks, checklist, analysis, and context files.
- **Shared Contract**: The common harness rules in `specs/skills/CONTRACT.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The measured topic count matches the installed package.
- **SC-002**: The analysis check reports zero critical issues for this generated package.
- **SC-003**: The context file contains the source path and source hash.
- **SC-004**: The generated artifact set records not measured built topics.

## Assumptions

- The shared contract controls repeated harness behavior.
- This document specification controls the conversion audit for one PDF.
