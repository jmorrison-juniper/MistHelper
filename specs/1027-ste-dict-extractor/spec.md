# Feature Specification: Near-Flawless ASD-STE100 Dictionary Extractor

**Feature Branch**: `1027-ste-dict-extractor`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User request: "Improve the extractor iteratively over and over with
SpecKit workflows until it is near flawless."

## Overview

The STE linter can check text against the approved ASD-STE100 vocabulary when a
local dictionary file is present. A tool builds that file from the licensed PDF.
The current tool uses a simple pattern match over flattened text and produces poor
data. This feature rewrites the tool to read the PDF by word position, so it
extracts the dictionary correctly. The tool improves through repeated measurement
against a set of known-correct entries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build an accurate dictionary from the PDF (Priority: P1)

An operator runs the extraction tool on a licensed ASD-STE100 PDF. The tool writes
a dictionary file with the correct words, parts of speech, approved status, and
approved alternatives. The linter then loads the file and checks vocabulary.

**Why this priority**: This is the whole point. A correct dictionary is the value.
Without it, the vocabulary checks are noise.

**Independent Test**: Run the tool on the PDF and confirm the output holds close to
2149 entries with a correct approved and not-approved split, and that a sample of
known entries is correct.

**Acceptance Scenarios**:

1. **Given** a licensed PDF, **When** the operator runs the tool, **Then** the
   output holds between 2106 and 2192 entries.
2. **Given** the output file, **When** a reviewer counts the approved entries,
   **Then** the count is near 875 and the not-approved count is near 1274.
3. **Given** the word "accuracy", **When** the reviewer reads its record, **Then**
   the record is not approved and names "precision" as the alternative.
4. **Given** any record, **When** the reviewer reads its keyword, **Then** the
   keyword is a single term of four words or fewer, never a sentence.

---

### User Story 2 - Measure extraction quality (Priority: P2)

A developer runs a quality harness. The harness compares the tool output against a
set of hand-verified entries and reports an accuracy score per field. The developer
uses the score to improve the parser.

**Why this priority**: The user asked to iterate until near flawless. Iteration
needs an objective score. The harness makes "near flawless" measurable.

**Independent Test**: Run the harness against the golden set and confirm it reports
a per-field accuracy score and lists every mismatch.

**Acceptance Scenarios**:

1. **Given** the golden set and the tool output, **When** the harness runs,
   **Then** it reports an accuracy score for keyword, part of speech, approved
   status, and alternatives.
2. **Given** a mismatch, **When** the harness runs, **Then** it names the keyword,
   the field, the expected value, and the actual value.
3. **Given** the final parser, **When** the harness runs, **Then** the field
   accuracy is 95 percent or higher.

---

### User Story 3 - Keep the copyrighted data out of the repository (Priority: P3)

The tool writes the dictionary to a path that git ignores. The repository ships the
tool and a small golden set of facts, never the full copyrighted dictionary.

**Why this priority**: The ASD-STE100 dictionary is copyrighted. The project must
not redistribute it. This rule already governs the source PDF.

**Independent Test**: Run the tool and confirm the output path is git-ignored and
that no full dictionary data is staged for commit.

**Acceptance Scenarios**:

1. **Given** the tool runs, **When** it writes the output, **Then** the output path
   is listed in the git ignore file.
2. **Given** the golden set, **When** a reviewer counts its entries, **Then** it
   holds about 35 facts, not the full dictionary.

### Edge Cases

- A page header, footer, or blank page must not become an entry.
- The intro and help pages hold example tables that look like real entries. The
  tool must not extract those examples.
- A verb entry lists several forms across lines (for example give, gives, gave,
  given). The tool records the base word once.
- An adjective entry shows comparative and superlative forms in parentheses. The
  tool records the base word once.
- A not-approved word can have several alternatives. The tool records each one.
- An example sentence in the approved-example column is in capitals. The tool must
  not mistake an example word for an alternative.
- A missing or unreadable PDF gives a clear error, not a stack trace.
- The pdfplumber library is not installed. The tool prints a clear install message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST read the PDF by word position with pdfplumber, not by
  flattened text.
- **FR-002**: The tool MUST read only the word column and the meaning-or-alternatives
  column. It MUST ignore the two example columns.
- **FR-003**: The tool MUST classify a word as approved when the word is printed in
  capital letters, and not approved otherwise.
- **FR-004**: The tool MUST record the part of speech from the set: noun, verb,
  adjective, adverb, preposition, pronoun, conjunction, article. It MUST also accept
  the technical-noun and technical-verb markers for alternatives.
- **FR-005**: The tool MUST extract an alternative only when an uppercase word is
  followed by a part of speech in parentheses. It MUST NOT treat an example word as
  an alternative.
- **FR-006**: The tool MUST record the approved meaning text for an approved word.
- **FR-007**: The tool MUST record several alternatives for a not-approved word when
  the dictionary lists several.
- **FR-008**: The tool MUST skip page headers, footers, blank pages, and the intro
  and help pages that precede the real entries.
- **FR-009**: The tool MUST record each keyword as a single term of four words or
  fewer. It MUST reject a sentence-length keyword.
- **FR-010**: The tool MUST write the output to a configurable, git-ignored path.
- **FR-011**: The tool MUST give a clear message when the PDF is missing, unreadable,
  or when pdfplumber is not installed.
- **FR-012**: The project MUST provide a golden set of hand-verified entries and a
  harness that scores the tool output against it.
- **FR-013**: The harness MUST report a per-field accuracy score and list every
  mismatch with the expected and actual values.
- **FR-014**: The tool MUST produce the same output for the same PDF every time it
  runs.

### Key Entities

- **Dictionary entry**: A record with the keyword, the part of speech, the approved
  flag, the list of alternatives, and the approved meaning.
- **Golden entry**: A hand-verified expected record used to measure accuracy.
- **Quality report**: The per-field accuracy scores and the list of mismatches.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The output holds between 2106 and 2192 entries.
- **SC-002**: The approved count is 875 plus or minus 40. The not-approved count is
  1274 plus or minus 40.
- **SC-003**: The golden-set field accuracy is 95 percent or higher.
- **SC-004**: No keyword is longer than four words.
- **SC-005**: Every alternative is an uppercase word with a valid part of speech.
- **SC-006**: The same PDF gives the same output on repeated runs.
- **SC-007**: Unit tests, ruff, black, mypy, radon, and the coverage gate pass.
- **SC-008**: No copyrighted dictionary data is committed.

## Assumptions

- The licensed PDF is ASD-STE100 Issue 9. The dictionary is Part 2.
- The real alphabetical entries start near page 155. The earlier pages hold the
  intro, the help categories, and example tables.
- pdfplumber gives reliable word positions for this PDF.
- The linter needs only the keyword, part of speech, approved flag, alternatives,
  and approved meaning. The example sentences are not needed.
- A golden set of about 35 entries is enough to measure field accuracy. The set is
  small facts, not the full copyrighted dictionary.
- "Near flawless" means the accuracy targets in the success criteria, not literal
  perfection, because the source is a scanned-style PDF with layout drift.
