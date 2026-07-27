# Feature Specification: ASD-STE100 Simplified Technical English Compliance Linter

**Feature Branch**: `1026-ste-linter`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "Take the ASD-STE100 PDF and create a complete,
comprehensive, deep Python linter that grades a file's compliance with the rules
and outputs a percent compliance score out of 100 percent. Use a SpecKit workflow."

## Overview

The linter reads a documentation or source file, checks the prose against the
Simplified Technical English (STE) rules in
`documentation/ASD-STE100_writing-guide.md`, and reports a compliance score from
0 to 100 percent. The report lists each rule violation with its location, the
reason, and a suggested fix. Writers, reviewers, continuous integration jobs, and
AI agents use the score to measure and improve writing quality.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Grade a file from the command line (Priority: P1)

A writer runs the linter on a Markdown or Python file. The tool prints a score
from 0 to 100 percent and a list of violations. Each violation shows the line
number, the rule, the problem, and a suggested fix. The writer edits the file to
raise the score.

**Why this priority**: This is the core value. Without a working command-line
grade and report, nothing else matters. This story alone is a usable product.

**Independent Test**: Run the tool on a sample file and confirm it prints a
numeric score and a violation list. No other feature is needed.

**Acceptance Scenarios**:

1. **Given** a Markdown file with prose, **When** the writer runs the linter on
   it, **Then** the tool prints an integer score from 0 to 100 and a violation
   report.
2. **Given** a Python file with docstrings and comments, **When** the writer runs
   the linter on it, **Then** the tool grades only the prose in docstrings and
   comments and ignores the code.
3. **Given** a file that follows the STE rules well, **When** the writer runs the
   linter, **Then** the score is high (90 or more).
4. **Given** a file that breaks many STE rules, **When** the writer runs the
   linter, **Then** the score is low (below 60) and each broken rule appears in
   the report.

---

### User Story 2 - Enforce a threshold in continuous integration (Priority: P2)

A continuous integration job runs the linter on changed documentation files with
a machine-readable output mode. The job fails when the score is below a set
threshold, so noncompliant text does not merge.

**Why this priority**: Automated enforcement keeps the standard from eroding over
time. It builds on the P1 engine and adds a gate.

**Independent Test**: Run the linter with the JSON output mode and a threshold on
a low-scoring file. Confirm the exit code is nonzero and the JSON holds the score
and the violations.

**Acceptance Scenarios**:

1. **Given** a file that scores below the threshold, **When** the linter runs with
   a threshold set, **Then** the exit code is nonzero.
2. **Given** a file that scores at or above the threshold, **When** the linter
   runs with a threshold set, **Then** the exit code is zero.
3. **Given** the JSON output mode, **When** the linter runs, **Then** the output
   is valid JSON with the score, the per-section breakdown, and the violation
   list.

---

### User Story 3 - Check writing before a commit (Priority: P3)

A contributor installs a pre-commit hook. The hook runs the linter on staged
Markdown and Python files and blocks the commit when a file scores below the
threshold.

**Why this priority**: Local, fast feedback stops problems before they reach the
pull request. It reuses the same engine and threshold as the continuous
integration gate.

**Independent Test**: Stage a low-scoring file, run the hook, and confirm it
blocks the commit and prints the report.

**Acceptance Scenarios**:

1. **Given** a staged file below the threshold, **When** the hook runs, **Then**
   the commit is blocked and the report is shown.
2. **Given** only compliant staged files, **When** the hook runs, **Then** the
   commit proceeds.

---

### User Story 4 - Check controlled vocabulary with the full dictionary (Priority: P4)

A writer generates the STE dictionary from a licensed copy of the ASD-STE100 PDF.
The linter then flags unapproved words, wrong parts of speech, and unapproved
meanings, and it suggests approved alternatives.

**Why this priority**: The dictionary rules add depth, but the structural rules
already deliver value. The dictionary depends on a licensed source, so it is
optional and loaded from a local file.

**Independent Test**: With a dictionary file present, run the linter on text that
uses an unapproved word and confirm the tool flags it and suggests an approved
word. With no dictionary file, confirm the tool skips the dictionary checks and
says so.

**Acceptance Scenarios**:

1. **Given** a dictionary file is present, **When** the text uses an unapproved
   word, **Then** the linter flags the word and names an approved alternative.
2. **Given** no dictionary file is present, **When** the linter runs, **Then** the
   structural rules still run and the report states that the dictionary checks
   were skipped.
3. **Given** the licensed PDF, **When** the writer runs the extraction tool,
   **Then** the tool writes a dictionary file to a path that git ignores.

### Edge Cases

- An empty file, or a file with no prose (only code, only tables, only links),
  scores 100 with a note that no gradable text was found.
- A Markdown file with fenced code blocks, inline code, tables, HTML, and link
  URLs grades only the prose and skips those spans.
- A Python file that fails to parse falls back to a comment and string scan and
  reports the parse problem.
- A very long sentence with numbers, units, identifiers, and quoted strings counts
  words by the STE rules (each number, unit pair, acronym, identifier, quoted
  span, and hyphenated group counts as one word).
- A file that mixes procedural steps and descriptive prose applies the correct
  sentence-length limit to each part.
- A dictionary file that is missing, empty, or malformed does not crash the linter.
  The tool reports reduced coverage and continues.
- The optional spaCy backend is not installed. The linter uses the heuristic
  backend and produces a score.

## Requirements *(mandatory)*

### Functional Requirements

#### Input and parsing

- **FR-001**: The linter MUST accept one or more file paths and grade each file.
- **FR-002**: The linter MUST grade Markdown files by extracting prose and skipping
  fenced code, inline code, link URLs, images, tables, and raw HTML.
- **FR-003**: The linter MUST grade Python files by extracting prose from
  docstrings and comments only, and MUST skip code.
- **FR-004**: The linter MUST segment prose into sentences and paragraphs with a
  method that handles common abbreviations.
- **FR-005**: The linter MUST count words by the STE rules, where a number, a
  number with a unit, an acronym, an alphanumeric identifier, a quoted span, and a
  hyphenated group each count as one word.

#### Structural rules (no dictionary needed)

- **FR-010**: The linter MUST flag procedural sentences longer than 20 words and
  descriptive sentences longer than 25 words.
- **FR-011**: The linter MUST flag passive voice, except where it cannot be avoided
  in descriptive text.
- **FR-012**: The linter MUST flag complex verb tenses (perfect and progressive
  forms) and report the simple form to use.
- **FR-013**: The linter MUST flag semicolons.
- **FR-014**: The linter MUST flag Latin abbreviations such as "e.g.", "i.e.", and
  "etc.".
- **FR-015**: The linter MUST flag multi-word noun clusters longer than three
  words.
- **FR-016**: The linter MUST flag phrasal verbs and suggest a single-word verb.
- **FR-017**: The linter MUST flag the "-ing" form used as a progressive verb.
- **FR-018**: The linter MUST flag contractions.
- **FR-019**: The linter MUST flag paragraphs longer than six sentences.
- **FR-020**: The linter MUST flag a warning or caution that has no signal word or
  no stated consequence.
- **FR-021**: The linter MUST flag gendered pronouns used for a general person.
- **FR-022**: The linter MUST let a project turn each rule on or off and set its
  weight through a configuration file.

#### Dictionary rules (need a local dictionary file)

- **FR-030**: The linter MUST load an STE dictionary from a configurable path when
  the file is present.
- **FR-031**: When a dictionary is loaded, the linter MUST flag unapproved words
  and name an approved alternative when the dictionary gives one.
- **FR-032**: When a dictionary is loaded, the linter MUST flag a word used as the
  wrong part of speech.
- **FR-033**: When no dictionary is present, the linter MUST run the structural
  rules and MUST report that the dictionary checks were skipped.
- **FR-034**: The project MUST provide a tool that reads a licensed ASD-STE100 PDF
  and writes a dictionary file.
- **FR-035**: The linter MUST NOT include the copyrighted dictionary data in the
  repository. The dictionary file path MUST be ignored by git.

#### Scoring and output

- **FR-040**: The linter MUST compute a compliance score from 0 to 100 percent with
  a deterministic, documented formula.
- **FR-041**: The linter MUST report a per-section score breakdown that maps to the
  writing guide sections.
- **FR-042**: The linter MUST list each violation with the file, the line, the
  rule identifier, the problem, and a suggested fix.
- **FR-043**: The linter MUST provide a human-readable text report and a
  machine-readable JSON report.
- **FR-044**: The linter MUST return a nonzero exit code when a file scores below a
  configured threshold, and zero otherwise.
- **FR-045**: The linter MUST produce the same score and report for the same input
  every time it runs.

#### Backends

- **FR-050**: The linter MUST run with the Python standard library only.
- **FR-051**: The linter MUST use a spaCy backend for part-of-speech and tense
  analysis when spaCy is installed, and MUST fall back to the heuristic backend
  when spaCy is absent.

### Key Entities

- **Document**: The parsed file. Holds the gradable prose spans with their source
  line numbers and a type (procedural or descriptive) per span.
- **Rule**: One STE check. Has an identifier, a section, a weight, a severity, and
  logic that inspects a unit and yields violations.
- **Violation**: One rule failure. Has the file, the line, the column, the rule
  identifier, the message, and a suggested fix.
- **Score**: The overall percent, the per-section breakdown, and the counts used to
  compute the percent.
- **Dictionary**: The approved and unapproved words with parts of speech, approved
  meanings, and alternatives. Loaded from a local, git-ignored file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The linter grades `documentation/ASD-STE100_writing-guide.md` at 90
  percent or higher.
- **SC-002**: The linter grades a deliberately noncompliant fixture below 60
  percent, and the report names each rule the fixture breaks.
- **SC-003**: The linter grades a typical documentation file (about 300 lines) in
  under five seconds with the heuristic backend.
- **SC-004**: The same input gives the same score and report on repeated runs.
- **SC-005**: Test coverage for the linter is at least 70 percent, and the ruff,
  Black, mypy, and radon gates pass.
- **SC-006**: No copyrighted dictionary data is committed to the repository.

## Assumptions

- The writing guide at `documentation/ASD-STE100_writing-guide.md` is the source of
  truth for the rules. The linter follows the guide, not the full PDF text.
- The dictionary (Part 2 of the standard) is copyrighted. The repository ships the
  engine and an extraction tool, not the dictionary data.
- Reasonable heuristics for passive voice, tense, and noun clusters are acceptable
  for the default backend. The optional spaCy backend improves accuracy.
- The classification of a sentence as procedural or descriptive uses a heuristic
  (imperative lead or numbered-list item means procedural). A project can override
  the default limit through configuration.
- The linter targets Python 3.13 or newer, in line with the repository standard.
- The scoring weights start from sensible defaults and can be tuned later without a
  change to the rule logic.
