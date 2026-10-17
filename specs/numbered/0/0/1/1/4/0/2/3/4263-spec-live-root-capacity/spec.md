# Feature Specification: Bounded live timestamp records

**Feature Branch**: `jmorrison-juniper-spec-live-root-capacity`

**Created**: 2026-10-17

**Status**: Process increment implemented. The approved #4202 move is verified. Shared task discovery and Redis integration remain blocked.

**Input**: [Issue #4263](https://github.com/jmorrison-juniper/MistHelper/issues/4263) requires bounded timestamp groups before Redis planning PR #4223 can proceed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a bounded timestamp record (Priority: P1)

A maintainer creates a timestamp record without exceeding five children or placing a feature inside another feature.

**Why this priority**: The full live root blocks another migration plan.

**Independent Test**: Create six timestamp records in an isolated tree. Verify valid groups and reject a sixth child at each structural level.

**Acceptance Scenarios**:

1. **Given** five direct records, **When** a maintainer prepares the approved migration, **Then** all records receive independent grouped locations.
2. **Given** a full group, **When** another record is requested, **Then** allocation selects another bounded group or fails before writing.
3. **Given** a feature directory, **When** allocation selects a parent, **Then** it never selects that feature directory.

### User Story 2 - Select the same feature after grouping (Priority: P1)

A maintainer selects a feature and its tasks through its explicit directory before and after migration.

**Why this priority**: A valid directory tree is insufficient if commands select another feature.

**Independent Test**: Resolve numbered, direct timestamp, and grouped timestamp fixtures through each feature consumer.

**Acceptance Scenarios**:

1. **Given** a grouped record, **When** a command selects its directory, **Then** specification, plan, and tasks belong to that record.
2. **Given** a missing or ambiguous selection, **When** a command runs, **Then** it fails with the examined count and cause.
3. **Given** two worktrees, **When** one selects a feature, **Then** the other worktree retains its selection.

### User Story 3 - Preserve records during migration (Priority: P2)

Record owners approve moves only after the migration manifest proves complete preservation and updated references.

**Why this priority**: Grouping must not discard another migration's work.

**Independent Test**: Compare file paths, file hashes, ownership, and references against the approved pre-move manifest.

**Acceptance Scenarios**:

1. **Given** an approved move set, **When** relocation completes, **Then** every original file has the same content and owner.
2. **Given** an open overlapping PR, **When** migration preparation starts, **Then** the move waits for its owner's handover.
3. **Given** PR #4223, **When** the process fix merges, **Then** its owner rebases and places its record in the approved grouped route.

### Edge Cases

- Reject duplicate record names, occupied destinations, missing inputs, unreadable directories, and symlink escapes before any move.
- Reject the sixth structural child at the root, intermediate group, and terminal bucket.
- Reject a record beneath a feature even when the parent contains fewer than five children.
- Reject unsupported or exhausted allocation ranges without partial records.
- Preserve direct timestamp discovery during migration without creating new direct timestamp records.
- Preserve established feature artifact layouts. Do not use this issue to restructure their internal files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Timestamp records MUST remain under `specs/live/` in independent structural groups.
- **FR-002**: Each new structural directory MUST contain at most five direct children, including files.
- **FR-003**: Allocation MUST reject feature parents and unsafe, duplicate, occupied, or exhausted destinations before writing.
- **FR-004**: Discovery and task selection MUST support numbered, current direct timestamp, and grouped timestamp records during migration.
- **FR-005**: Invalid, unreadable, absent, or ambiguous selection MUST fail explicitly and report examined counts.
- **FR-006**: Each moved record MUST retain every artifact byte, its identity, and its owner through an approved migration manifest.
- **FR-007**: Each affected reference and selector MUST resolve the intended record after migration.
- **FR-008**: The process guard MUST remain enabled, retain the five-child threshold, and test valid and invalid nested structures.
- **FR-009**: Feature selection MUST remain local to the active worktree or command.
- **FR-010**: Migration MUST coordinate open PR ownership and require fresh checks on PR #4223 after its base changes.
- **FR-011**: The initial planning phase MUST modify only its new numeric Spec Kit artifacts. Product runtime code remains outside this issue.

### Key Entities

- **Feature record**: One identity, owner, and complete set of planning artifacts.
- **Structural group**: A container for groups or records, never a feature.
- **Migration manifest**: Source, destination, owner approval, file inventory, and preservation evidence for each move.
- **Feature selection**: An explicit directory associated with one command or worktree.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every new structural directory has five children or fewer, including a fixture with six feature records.
- **SC-002**: All selected migration files retain identical content and ownership, with zero missing or duplicate files.
- **SC-003**: Every supported selection fixture returns the expected record and tasks. Every invalid fixture fails explicitly.
- **SC-004**: All affected links resolve, with zero stale source-path references after the approved moves.
- **SC-005**: The process checks pass for the migrated tree and the rebased Redis plan without exclusions or threshold changes.
- **SC-006**: The initial planning phase changes zero existing records, product files, shared selectors, or live-root children.

## Assumptions

- Work proceeds serially. The initial request stopped after analysis. Subsequent issue authorization permits bounded process implementation.
- Existing feature-internal layouts remain unchanged. This issue bounds structural grouping, not historical artifact counts within features.
- This new numeric record also uses at most five children per directory.
- Owner approval is a prerequisite for each move. Subsequent user authorization permits only the #4202 move and two reference-only replacements.
- The approved reference replacements are the only exceptions to byte-identical preservation under FR-006 and SC-002.
- Existing numbered routing remains fixed at eight base-5 levels.
- The linked issue stays open until implementation and Redis-plan integration satisfy its remaining acceptance criteria.
- [Design decisions](design/research.md) define the proposed route and the process tools that need changes.
