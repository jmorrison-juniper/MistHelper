# Feature Specification: MistHelper.py Simplified Technical English Compliance Cleanup

**Feature Branch**: `1028-ste-compliance-cleanup`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User request: "Start a new issue and SpecKit workflow to use our new
report results to clean up our MistHelper file to bring it into compliance.
Please include the dictionary checks."

## Overview

The STE linter graded the comments and docstrings in `MistHelper.py` at 97 out of
100. This feature uses the linter report to clean up the prose so it follows
Simplified Technical English. The work changes comments and docstrings only. It
does not change any code, identifier, or logging string. The goal is a targeted,
measurable improvement, not a perfect score.

## Why a perfect score is not the goal

The linter reports 3369 findings. Most (2873) come from the dictionary rules,
because normal programming words such as "file", "list", and "dispatch" are not in
the ASD-STE100 approved vocabulary of about 875 words. A score of 100 would force
stilted prose and an allowlist of hundreds of technical terms, and it would make
the comments harder to read, not easier. So this feature fixes the high-value,
low-risk findings and a curated set of dictionary swaps, and it defers the rest.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix the mechanical structural findings (Priority: P1)

A maintainer fixes every Latin abbreviation, contraction, phrasal verb, and comment
semicolon, and splits the four over-length sentences. These are unambiguous text
edits with no judgment and no code risk.

**Why this priority**: These are the clearest wins. Each has one correct fix, the
continuous integration STE gate can verify them, and they carry no risk to code
behavior.

**Independent Test**: Run the linter on the file before and after. Confirm the
counts for STE-S9-LATIN, STE-S4-CONTRACTION, STE-S9-PHRASAL, STE-S8-SEMICOLON, and
STE-S4-LEN all reach zero.

**Acceptance Scenarios**:

1. **Given** a comment with "e.g.", **When** the maintainer fixes it, **Then** the
   comment reads "for example".
2. **Given** a comment with "can't", **When** the maintainer fixes it, **Then** the
   comment reads "cannot".
3. **Given** a comment with a semicolon, **When** the maintainer fixes it, **Then**
   the comment is two sentences with no semicolon.
4. **Given** an over-length comment sentence, **When** the maintainer fixes it,
   **Then** the comment is two shorter sentences, each within the word limit.

---

### User Story 2 - Apply curated dictionary swaps in comments (Priority: P2)

A maintainer applies a small, curated map of unapproved words to approved words in
comment prose only. For example "via" becomes "by" and "attempt" becomes "try". The
maintainer does not touch identifiers, variable names, or logging strings.

**Why this priority**: This adds real clarity, but each swap needs judgment to keep
the meaning. It builds on the mechanical pass and uses a fixed map to stay safe.

**Independent Test**: Run the linter before and after. Confirm the unapproved-word
count for the mapped words drops, and confirm no code line changed.

**Acceptance Scenarios**:

1. **Given** the word "via" in a comment, **When** the maintainer applies the swap,
   **Then** the comment reads "by" or "through" and the meaning is the same.
2. **Given** the word "via" inside an identifier or a logging string, **When** the
   maintainer runs the pass, **Then** that word is not changed.
3. **Given** the curated map, **When** a word is not in the map, **Then** the
   maintainer does not change it.

---

### User Story 3 - Add a technical-noun allowlist (Priority: P3)

A maintainer adds an allowlist of legitimate technical terms (for example "API",
"URL", "MAC", "log", "file") to the linter configuration, so the linter stops
flagging them. This raises the signal from the dictionary rules for every future
run, not only this file.

**Why this priority**: The allowlist is a durable improvement, but it is a
configuration change that needs a linter feature, so it comes after the direct
text fixes.

**Independent Test**: Add a term to the allowlist, run the linter, and confirm that
term is no longer flagged while other unapproved words still are.

**Acceptance Scenarios**:

1. **Given** "API" in the allowlist, **When** the linter runs, **Then** "API" is
   not flagged as unapproved.
2. **Given** a word not in the allowlist, **When** the linter runs, **Then** that
   word is still flagged.

### Edge Cases

- A word appears both as an identifier and as a prose word in the same comment. The
  maintainer changes only the prose use.
- A semicolon appears inside a code example in a docstring. The maintainer does not
  change code examples.
- A contraction appears inside a quoted string in a docstring. The maintainer does
  not change quoted text.
- Splitting a long sentence must not push the line past the 120-character limit. The
  maintainer wraps the comment across lines when needed.
- A Latin abbreviation appears inside a URL or an identifier. The maintainer does
  not change it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST modify comments and docstrings only. It MUST NOT
  change code, identifiers, variable names, or the string text inside logging and
  print calls.
- **FR-002**: The change MUST replace every Latin abbreviation in comments with plain
  English ("e.g." to "for example", "i.e." to "that is", "etc." to "and so on").
- **FR-003**: The change MUST replace every contraction in comments with its full
  form ("can't" to "cannot", "it's" to "it is", "do not" for "don't").
- **FR-004**: The change MUST replace every phrasal verb in comments with a single
  precise verb.
- **FR-005**: The change MUST rewrite every comment semicolon as two sentences.
- **FR-006**: The change MUST split the four over-length comment sentences into
  shorter sentences within the word limit.
- **FR-007**: The change MUST apply a curated word-swap map to comment prose only,
  for the top unambiguous unapproved words.
- **FR-008**: The change MUST NOT apply a swap to a word that is part of an
  identifier, a quoted string, a URL, or a logging string.
- **FR-009**: The change MUST add a technical-noun allowlist to the linter
  configuration so legitimate terms are not flagged.
- **FR-010**: Every touched line MUST keep its inline comment per the project
  standard.
- **FR-011**: The change MUST keep the file valid. `python -m py_compile
  MistHelper.py` MUST pass.
- **FR-012**: The test suite MUST still pass, which proves the code behavior did not
  change.

### Key Entities

- **Swap map**: A fixed map from an unapproved word to its approved replacement,
  used for comment prose only.
- **Technical-noun allowlist**: A list of approved technical terms the linter must
  not flag.
- **Linter report**: The before and after findings used to measure progress.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The counts for Latin abbreviations, contractions, phrasal verbs, and
  comment semicolons reach zero.
- **SC-002**: The four over-length sentence errors reach zero.
- **SC-003**: The total structural findings (all rules except the two dictionary
  rules) drop by at least 60 percent from the baseline of 496.
- **SC-004**: The overall linter score rises from 97 toward the high nineties with
  the dictionary active, and the structural-only score rises measurably.
- **SC-005**: The test suite passes, which proves no code behavior changed.
- **SC-006**: Ruff, black, mypy, radon, and the coverage gate pass. `py_compile`
  passes.
- **SC-007**: No identifier, variable name, or logging string is changed.

## Assumptions

- The linter report is the source of truth for the findings and their lines.
- The dictionary file is present locally, so the dictionary rules run during the
  work. The continuous integration gate runs the structural rules only, because the
  dictionary is git-ignored.
- The passive-voice, noun-cluster, and complex-tense rewrites are out of scope for
  this feature and are tracked for a later pass.
- The file is the designated hot file, so this work holds the only open pull request
  that modifies it while it is in progress.
- The 120-character line limit and the inline-comment rule from the project standard
  apply to every edit.
