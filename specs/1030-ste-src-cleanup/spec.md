# Feature Specification: STE Compliance for src/ Comments and Docstrings

**Feature Branch**: `1030-ste-src-cleanup`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "use the linter on the python submodules for this
repo and build a new speckit workflow to address all of those results."

## Overview

The Simplified Technical English (STE) linter grades comments and docstrings.
Feature 1028 brought `MistHelper.py` into compliance. This feature applies the
same linter to the `src/` submodule tree and removes genuine STE violations.

The linter grades comments and docstrings only. It does not grade code or
logging strings. Every edit in this feature stays in comments and docstrings.
The code behavior does not change.

### Scan Baseline

The scan covered 359 files and 108,543 lines. Every file already passes the 80
percent score gate. This work reduces the count of real violations. It does not
fix a failure.

The scan found 67,161 raw violations. Most are false positives on code words.

| Rule | Count | Verdict |
| - | - | - |
| STE-S1-WORD | 51,966 | False positive. Code words. Out of scope. |
| STE-S1-POS | 7,028 | False positive. Out of scope. |
| STE-S2-NOUNCLUSTER | 3,883 | About 95 percent false positive. Out of scope. |
| STE-S8-SEMICOLON | 2,147 | In scope. Verify each file. |
| STE-S3-PASSIVE | 1,200 | In scope. Judgment. |
| STE-S4-LEN | 446 | In scope. Judgment. |
| STE-S3-TENSE | 182 | In scope. Judgment. |
| STE-S9-LATIN | 167 | In scope. Mechanical. |
| STE-S4-CONTRACTION | 117 | In scope. Mechanical. |
| STE-S7-WARNING | 10 | In scope. Mechanical. |
| STE-S9-PHRASAL | 9 | In scope. Mechanical. |
| STE-S6-PARA | 4 | In scope. Mechanical. |
| STE-S9-GENDER | 2 | In scope. Mechanical. |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove mechanical STE violations (Priority: P1)

A junior NOC engineer reads a docstring in `src/`. The text uses plain English.
It has no Latin abbreviations, no contractions, and no phrasal verbs. The
meaning is clear on the first read.

**Why this priority**: Mechanical rules are finite, unambiguous, and safe. Each
fix is a direct word swap. The result is CI-verifiable. This story removes 309
real violations and delivers the largest clear win.

**Independent Test**: Run the linter across `src/` with only the mechanical
rules active. Confirm zero violations for STE-S9-LATIN, STE-S4-CONTRACTION,
STE-S9-PHRASAL, STE-S9-GENDER, STE-S7-WARNING, and STE-S6-PARA.

**Acceptance Scenarios**:

1. **Given** a docstring with "e.g.", **When** the fix is applied, **Then** the
   text reads "for example" and the linter reports no STE-S9-LATIN violation.
2. **Given** a comment with "doesn't", **When** the fix is applied, **Then** the
   text reads "does not" and the linter reports no STE-S4-CONTRACTION violation.
3. **Given** the full `src/` tree, **When** the linter runs, **Then** the six
   mechanical rules report zero violations.

---

### User Story 2 - Reduce prose semicolons (Priority: P2)

A reader finds two short sentences where a semicolon joined two ideas before.
Code examples inside docstrings keep their semicolons, because those are shell
or Python syntax, not prose.

**Why this priority**: Semicolons are the largest judgment group at 2,147. Many
are code examples in docstrings, such as PowerShell one-liners. Each file needs
a check to separate prose semicolons from code semicolons. This story needs care
but gives a clear readability gain.

**Independent Test**: Run the linter with the semicolon rule active on the
changed files. Confirm prose semicolons are gone. Confirm code examples in
docstrings still work and still read correctly.

**Acceptance Scenarios**:

1. **Given** a docstring sentence joined by a prose semicolon, **When** the fix
   splits it into two sentences, **Then** the linter reports no STE-S8-SEMICOLON
   violation for that line.
2. **Given** a docstring with a PowerShell example that uses a semicolon,
   **When** the file is reviewed, **Then** the example is left unchanged.

---

### User Story 3 - Reduce passive, long, and past-tense sentences (Priority: P3)

A reader finds active-voice sentences that name the actor. Sentences are short.
Instructions use the present tense.

**Why this priority**: Passive voice (1,200), sentence length (446), and tense
(182) are judgment rules. Each fix needs a human decision to keep the meaning.
The gain is real but the effort per fix is higher. This story runs last and is
grouped by module.

**Independent Test**: Run the linter with the passive, length, and tense rules
active on the changed module. Confirm the counts drop and no meaning is lost.

**Acceptance Scenarios**:

1. **Given** a passive docstring sentence, **When** it is rewritten in active
   voice, **Then** the actor is named and the meaning is the same.
2. **Given** a sentence longer than the STE limit, **When** it is split, **Then**
   each new sentence states one idea.

---

### Edge Cases

- A semicolon appears inside a code example in a docstring. Keep it. It is
  shell or Python syntax, not prose.
- A word looks like a contraction but is a quoted identifier or string literal.
  Keep it. The linter does not grade code, so this is rare, but verify.
- A passive sentence has no clear actor. Rewrite only if the actor is known.
  If the actor is unknown, keep the sentence and note the reason.
- A fix would remove an inline comment from a code line. Do not remove the
  comment. Every touched code line keeps its inline comment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The six mechanical rules (STE-S9-LATIN, STE-S4-CONTRACTION,
  STE-S9-PHRASAL, STE-S9-GENDER, STE-S7-WARNING, STE-S6-PARA) MUST report zero
  violations across `src/` after Phase 1.
- **FR-002**: The system MUST edit comments and docstrings only. The code
  behavior MUST NOT change.
- **FR-003**: The system MUST keep code examples inside docstrings unchanged,
  including their semicolons.
- **FR-004**: The counts for STE-S1-WORD, STE-S1-POS, and STE-S2-NOUNCLUSTER
  MUST NOT be a target. These are false positives on code words. The team does
  not edit them.
- **FR-005**: Every code line that is touched MUST keep its inline comment.
- **FR-006**: All CI gates MUST pass: ruff, black, mypy, radon, pytest coverage,
  and CodeQL.
- **FR-007**: The work MUST be split into phases. Phase 1 is mechanical fixes.
  Later phases are judgment fixes grouped by module cluster.
- **FR-008**: Each phase MUST be a separate pull request to keep reviews small
  and to reduce merge conflicts on hot files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The six mechanical rules report zero violations across `src/`.
- **SC-002**: Prose semicolons in changed files drop to zero. Code examples in
  docstrings stay unchanged.
- **SC-003**: Passive, length, and tense counts drop in each changed module,
  with no loss of meaning.
- **SC-004**: STE-S1-WORD, STE-S1-POS, and STE-S2-NOUNCLUSTER counts do not
  change (no edits to false positives).
- **SC-005**: All CI gates stay green on every phase pull request.
- **SC-006**: No code behavior change. A reviewer can confirm each diff touches
  only comments and docstrings.

## Assumptions

- The STE linter and dictionary on `main` are the source of truth for grades.
- The allowlist in `pyproject.toml` `[tool.ste_linter].allowlist` stays as is.
  The team does not grow it to hide false positives.
- The reader audience is junior NOC engineers. Clear language is the goal, not a
  perfect score.
- `src/` has CI gates that `MistHelper.py` comments did not: coverage at 80
  percent, mypy on `src/`, and radon at CC 10 or less. Comment-only edits keep
  these gates green.
- The scope is Option C: mechanical rules plus all judgment rules. Dictionary
  and noun-cluster false positives are out of scope.
