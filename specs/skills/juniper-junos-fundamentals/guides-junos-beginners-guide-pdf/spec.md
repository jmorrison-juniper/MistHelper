# Feature Specification: Day One: Beginner's Guide to Learning Junos skill package

Command: speckit.specify

**Feature Branch**: `feat/2925-juniper-skill-factory`

**Created**: 2026-09-18

**Status**: Generated

**Input**: Source document `C:\Users\jmorrison\Downloads\juniper-harvest-md\guides\junos-beginners-guide.md`

## Document Measurements

Document title: Day One: Beginner's Guide to Learning Junos
Domain: juniper-junos-fundamentals
Category: guides
Page count: 356
Part count: 1
Topic count: 47
Life cycle spread: day0=4, day1=38, day2=39, day2plus=15
Guard result: not measured
STE result: not measured
Version status: unversioned
Superseded by: not measured
Source hash: cda62188c9779df067ba8a8bcc6201d8f37481dba227e8ebe166944ce02e4dc1
Package path: C:\Users\jmorrison\juniper-agent-skills\skills\juniper-junos-fundamentals\documents\junos-beginners-guide


## Document Subjects

Subjects: Overview, MX Series Routers, SRX Series, Transit Traffic and Exception Traffic, User Interface, The Interfaces Used to Manage Your Box, Method Four: The Management Port, CLI Keyboard Shortcuts, Filtering Output, CLI Help

Keywords: routers, transit, traffic, exception, user, interface, interfaces, used, manage, your, method, four, management, port, keyboard, shortcuts, filtering, output, help, finding

## Life Cycle Coverage

Covered stages: day0, day1, day2, day2plus.

Absent stages: none.

## Source Quality

Source defects: not measured.

Guard result: not measured.

STE result: not measured.

## Reader Expectations

- Do not expect complete vendor prose.
- Do not expect topics from absent life cycle stages.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer questions from this document (Priority: P1)

As an AI agent, I need topic routes for `Day One: Beginner's Guide to Learning Junos`.
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
- **SC-004**: The generated artifact set records 47 built topics.

## Assumptions

- The shared contract controls repeated harness behavior.
- This document specification controls the conversion audit for one PDF.
