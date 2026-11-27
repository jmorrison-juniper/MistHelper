# Feature Specification: Duplicate PDF Corpus

**Issue**: #2977

**Created**: 2026-11-26

**Status**: Draft

**Input**: Corpus harvest: 351 duplicate PDF files fill 11.8 percent of the corpus.

## Record Status

The prevention code is on `main`. Pull request #4311 merged on 2026-10-20. Pull request #4823 merged on 2026-11-19. Both files and seven tests exist on `main` (R02 to R06).

Three parts stay open. The historical corpus still holds the redundant copies. The manual sorter does not update stored paths. The copy run has no owner inputs yet.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep one stored PDF for each document (Priority: P1)

As a harvest operator, I need each PDF stored once, under any name or category. A later harvest then adds no second copy.

**Why this priority**: The prevention code protects every future harvest. It must stay correct after each change.

**Independent Test**: Run the content index tests with temporary files. Each test writes PDF bytes into a temporary folder and checks the file count.

**Acceptance Scenarios**:

1. **Given** a stored PDF under one name, **When** the same bytes arrive under another name, **Then** the harvest returns that path.
2. **Given** two distinct PDFs with the same byte size, **When** the harvest processes both, **Then** the harvest keeps two files.
3. **Given** a stored PDF that reclassification moved, **When** the same bytes arrive again, **Then** the harvest returns the current path.

---

### User Story 2 - Keep document paths valid after a manual sort (Priority: P1)

As a harvest operator, I need each stored path to match the disk after a manual sort. Later passes then find each document.

**Why this priority**: A stale path makes a document look missing. A later pass can then store a copy of it.

**Independent Test**: Run the manual sorter against a temporary database and temporary files. Check the file location and the stored path.

**Acceptance Scenarios**:

1. **Given** an uncategorized document that matches one folder rule, **When** the sorter applies the move, **Then** the document row names the new path.
2. **Given** the same input, **When** the sorter runs in dry-run mode, **Then** no file moves and no row changes.
3. **Given** a document row whose file is missing, **When** the sorter runs, **Then** the sorter counts the row as missing and leaves the row unchanged.

---

### User Story 3 - Verify the historical copies on a verified copy (Priority: P2)

As the owner, I need the redundant copies counted on a verified copy. The 351 figure must be proven before any action.

**Why this priority**: The figure drives the decision to delete files. The source corpus must stay unchanged until a human approves a deletion.

**Independent Test**: Run the copy verifier against a temporary source tree. Check the inventory, the copy comparison, and the source-unchanged check.

**Acceptance Scenarios**:

1. **Given** the owner records all five inputs, **When** the copy run starts, **Then** the verifier accepts the preconditions.
2. **Given** a verified copy, **When** the consolidator writes it into an empty library root, **Then** the verifier reports the duplicate count and passes the comparison.
3. **Given** a source tree that changes during the run, **When** the verifier checks it, **Then** the verifier reports a source change and fails the run.

### Edge Cases

- Two distinct PDFs with the same byte size must stay separate.
- An empty file under the output root must not count as a stored PDF.
- A canonical file removed from disk must not match a later download.
- A stored file that moves during classification must resolve to its current path.
- A manual sort row whose file is missing must not stop the pass.
- A manual sort database update that fails after a file move must leave the file in place and log both paths.
- A copy-run library root that equals or contains the source root must be refused.
- Two source files with the same name and different bytes must both appear in the library.
- A redundant download found by the same URL with different bytes is out of scope (D-5).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harvest MUST store one file for each distinct SHA256 digest under the output root, across all names and categories.
- **FR-002**: The harvest MUST return the existing canonical path and write no second file when a digest already exists.
- **FR-003**: The content index MUST keep distinct PDFs with equal byte sizes as separate entries.
- **FR-004**: The content index MUST NOT write, rename, or delete any file.
- **FR-005**: The content index MUST resolve a canonical file that reclassification moved to its current path.
- **FR-006**: The content index MUST resolve a remaining identical file when the canonical file no longer exists.
- **FR-007**: The manual document sorter MUST update the `local_path` of each document row that it moves.
- **FR-008**: The manual document sorter MUST change no file and no row in dry-run mode.
- **FR-009**: The consolidator MUST copy each unique document once into an empty library root and MUST NOT modify a source file.
- **FR-010**: The copy run MUST record the source inventory of relative path, size, and SHA256 digest before it copies.
- **FR-011**: The copy run MUST compare digest sets and check the duplicate count as scanned minus unique.
- **FR-012**: The copy run MUST NOT start until the owner records the source host, source path, copy path, output path, and target capacity.
- **FR-013**: This issue MUST NOT delete or rewrite any file in the historical corpus. Deletion needs a separate human decision (D-10).

### Key Entities

- **Stored PDF**: A PDF file under the output root. Its natural key is the SHA256 digest of its bytes.
- **Document row**: A row in table `documents` of `harvest_state.db`. Its natural key is `root_url`. It names the stored path in `local_path`.
- **Inventory row**: One line of a source inventory. Its natural key is the relative path under the source root. It holds the size and the SHA256 digest.
- **Library copy**: A file that the consolidator writes into the library root. It holds one document and one digest.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The eight content-index tests, the three manual-sorter tests, and the four consolidator tests pass in the CI run of the pull request. The five verifier tests pass as well.
- **SC-002**: After a manual sort, the document rows of the moved files name the new paths. The count of stale paths is zero.
- **SC-003**: The copy-run report shows zero missing digests and zero unmatched library files.
- **SC-004**: The report duplicate count equals the scanned count minus the unique count.
- **SC-005**: The source inventory before and after the copy run matches row for row.
- **SC-006**: The 351 figure is either reproduced from the authoritative inventory or recorded as not reproduced.

## Assumptions

- The harvester writes files under `data/juniper_corpus` on the owner machine (R12).
- The harvester stops before any copy run. No harvest writes during a copy run.
- The owner machine holds enough space for the library copy. The owner records the space before the run.
- Every test uses temporary files and synthetic bytes. No test reads a real PDF from the corpus.
- The owner decides the successor issue for the copy run before the pull request merges (D-11).

## Out of Scope

- Deleting or moving any file in the historical corpus (D-3, D-10).
- Changing the same-URL reuse rule (D-5).
- Routing `scripts/crawl_jvd.py` through the content index (D-6).
- Writing licensing or legal text (D-9).
- Changing any menu operation, any Mist API call, or any container.
- Changing the legacy record `specs\numbered\0\0\0\4\3\4\0\2\2977-harvest-index-moves`.

## Clarifications

### Session 2026-11-26

- Q: Does the source corpus exist in this worktree? A: No. Folder `data\juniper_corpus` is absent (L01). The source host and path remain unknown (issue comment of 2026-10-30).
- Q: May the agent delete a redundant copy? A: No. The owner decided on 2026-10-21 that the consolidator runs on a verified copy first. Deletion needs a human decision (D-10).
- Q: Which rule chooses the library copy? A: The most specific category wins. This rule differs from prevention, which keeps the first sorted path (D-2).
- Q: Does this pull request close #2977? A: Yes. The copy run moves to a successor issue (D-11). The owner must confirm before the pull request opens.
- Q: Does the manual sorter need a database write? A: Yes. The write sets `local_path` and `updated_at` only. It does not change the stage or the category (contract `manual-sort-update.md`).
- Q: May the copy run start when the owner records only some inputs? A: No. The verifier refuses a partial set (FR-012, test `test_preconditions_refuse_missing_or_overlapping_paths`).
