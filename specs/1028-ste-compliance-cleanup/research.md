# Research: Fix Categories and Safe-Edit Method

**Feature**: 1028-ste-compliance-cleanup | **Phase**: 0

This document records how the findings were grouped and how each group is fixed
without any risk to code behavior.

## Decision 1: Fix only comment and docstring prose

**Decision**: Every edit is to a comment or a docstring. No edit touches code, an
identifier, a variable name, or a string inside a logging or print call.

**Rationale**: The STE linter grades comments and docstrings only. The prose is the
target. Code text is not graded and must not change, because a change to code could
change behavior. The test suite proves behavior is unchanged after the edits.

## Decision 2: Group the findings by risk

**Decision**: Sort the findings into three groups by how much judgment each needs.

- **Mechanical (no judgment)**: Latin abbreviations, contractions, phrasal verbs,
  and comment semicolons. Each has one correct fix.
- **Small judgment (fixed map)**: The top unapproved words that have a clear
  approved replacement, applied from a fixed map.
- **Large judgment (deferred)**: Passive voice, noun clusters, and complex tense.
  Each needs a rewrite that changes sentence shape.

**Rationale**: The mechanical group is safe and the continuous integration gate can
verify it. The fixed-map group is safe when the map is small and each entry is
unambiguous. The large-judgment group is deferred because it carries more risk for
little score gain on source-code prose.

## Decision 3: Method for each mechanical fix

- **Latin abbreviations (20)**: Replace "e.g." with "for example", "i.e." with "that
  is", and "etc." with "and so on". Read the comment, confirm the abbreviation is
  prose and not part of a URL or an identifier, then replace it.
- **Contractions (34)**: Replace each contraction with its full form. The linter
  gives the exact replacement.
- **Phrasal verbs (2)**: Replace each with a single precise verb from the linter
  suggestion.
- **Comment semicolons (92)**: Rewrite the comment as two sentences. Keep the same
  meaning. Confirm the semicolon is not inside a code example.

## Decision 4: The four over-length sentences

**Decision**: Split each of the four flagged comment sentences into two shorter
sentences, each within the word limit. Wrap across lines so no line passes 120
characters.

**Rationale**: These are the only errors. Each is a single long comment that packs
several ideas. Splitting improves clarity and clears the error.

## Decision 5: The curated swap map

**Decision**: Build a fixed map of the top unambiguous unapproved words to approved
words, and apply it to comment prose only. See swap-map.md for the map.

**Rationale**: Of the 368 unique unapproved words, only a small number have a single
clear approved replacement that fits every use in a comment. The map holds only
those. Words with several senses (for example "present", which can be a verb or an
adjective) are left out to avoid a wrong change.

**Method**: For each comment, read the text. For each word in the map, replace the
whole-word prose use. Never change a word that is part of an identifier, a quoted
string, a URL, or a logging string. Review each file section after the pass.

## Decision 6: The technical-noun allowlist

**Decision**: Add an allowlist option to the dictionary rules. The linter skips a
word that is in the allowlist. Seed the allowlist with the common programming terms
that the report flags (for example "log", "file", "list", "call", "return").

**Rationale**: These words are correct in a software project. They are not prose
errors. The allowlist stops the linter from flagging them, which raises the signal
for every future run. This is a small, additive linter change with its own tests.

## Known limits

- Grading source-code prose stays noisy even after this work, because most
  programming words are not in the approved vocabulary. The goal is a clear
  improvement in the structural rules and the top dictionary words, not a perfect
  score.
- The continuous integration gate runs the structural rules only, because the
  dictionary is git-ignored. The dictionary swaps improve the local score and the
  readability, but the gate cannot measure them.
