# Feature Specification: Keep the Harvest Index Current

**Issue**: #2977

**Created**: 2026-11-13

**Status**: Draft

**Input**: Keep the PDF content index current when reclassification moves a PDF.

## User Scenarios & Testing

### User Story 1 - Reuse a moved document (Priority: P1)

As a harvest operator, I need a repeated document to resolve to its current stored path after reclassification, so the harvest does not create a second copy.

**Why this priority**: A stale path can make a later matching document appear new.

**Independent Test**: Move a temporary PDF to its classified folder, then process the same bytes from another source URL.

**Acceptance Scenarios**:

1. **Given** a stored PDF moved during reclassification, **When** another source returns the same content, **Then** the harvest reuses the moved file.
2. **Given** the original path no longer exists, **When** a matching file exists at its new path, **Then** the recorded path names the existing file.

### User Story 2 - Keep distinct documents (Priority: P2)

As a harvest operator, I need distinct documents to remain separate when their file sizes match.

**Why this priority**: File size alone cannot identify document content.

**Independent Test**: Process two different temporary PDFs with the same byte count.

**Acceptance Scenarios**:

1. **Given** two different PDFs with the same size, **When** the harvest processes both, **Then** it stores both documents.

### Edge Cases

- If the moved file is the only copy and is then removed, the next matching download must create a new file.
- If another matching file remains after the original path disappears, the harvest must reuse a path that exists.
- This feature must not read or change the historical source corpus.

## Requirements

### Functional Requirements

- **FR-001**: The harvest MUST find a stored PDF at its current path after reclassification moves it.
- **FR-002**: The harvest MUST reuse a remaining file when the previous stored path no longer exists.
- **FR-003**: The harvest MUST store a new PDF when no stored file has the same content.
- **FR-004**: The harvest MUST keep distinct PDFs separate even when their file sizes match.
- **FR-005**: The harvest MUST leave files outside its configured output directory unchanged.

### Key Entities

- **Stored PDF**: A document file in the harvest output. Its path can change during classification.
- **Source record**: A harvested web document that refers to a resolved PDF and its stored path.

## Success Criteria

### Measurable Outcomes

- **SC-001**: After a temporary PDF moves, a repeated matching download creates zero extra PDF files.
- **SC-002**: The repeated source record points to an existing file after the move.
- **SC-003**: Two different PDFs with the same size remain as two files.
- **SC-004**: Tests use temporary files only and make no changes outside their temporary output.

## Assumptions

- The harvest already reuses files with identical content when their indexed paths remain valid.
- Classification can move a PDF while the same harvest is running.
- This change does not consolidate existing duplicate files.
