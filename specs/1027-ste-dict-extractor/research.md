# Research: Extraction Method and Column Model

**Feature**: 1027-ste-dict-extractor | **Phase**: 0

This document records the decisions for how the tool reads the dictionary and how it
turns the page layout into correct entries. The decisions come from a probe of the
real PDF with pdfplumber.

## Decision 1: Read the PDF by word position, not flattened text

**Decision**: Use pdfplumber. For each page, read the words with their left and top
coordinates. Group words into rows by their top coordinate. Split each row into
columns by the left coordinate.

**Rationale**: The dictionary is a four-column table. pypdf flattens the columns
into one stream, so the columns interleave and a pattern match cannot separate them.
This is the exact cause of the current bad output. pdfplumber keeps the word
coordinates, so the columns can be rebuilt.

**Alternatives rejected**: Flattened text with a regex (the current, broken method).
pdfplumber table detection by ruled lines (the table has no borders).

## Decision 2: Read only the two left columns

**Decision**: Keep only column 1 (word and part of speech) and column 2 (approved
meaning or alternatives). Drop column 3 (STE example) and column 4 (non-STE
example).

**Rationale**: The linter needs only the keyword, the part of speech, the approved
flag, the alternatives, and the approved meaning. The example columns are not used.
The two left columns are the best separated, so dropping the example columns removes
the hardest part of the layout.

**Alternatives rejected**: Parse all four columns (more work, no benefit, and the
right columns drift the most).

## Decision 3: Classify approved status by letter case

**Decision**: A word is approved when it is printed in capital letters. A word is not
approved when it is printed in lower case.

**Rationale**: The standard prints approved words in capitals and not-approved words
in lower case. Case is a reliable, built-in signal that needs no extra data.

**Alternatives rejected**: A word list of approved words (that is the very data the
tool is trying to build).

## Decision 4: Extract alternatives by the part-of-speech suffix

**Decision**: In column 2, an alternative is an uppercase word or short phrase that
is followed by a part of speech in parentheses, for example "PRECISION (n)" or
"THE TWO (TN)". Extract every such match. Ignore uppercase words with no part of
speech suffix.

**Rationale**: Example words can leak into column 2 because an example sentence is in
capitals. But an example word is never followed by a part of speech in parentheses.
The part-of-speech suffix separates a real alternative from a leaked example word.
This is the key rule that makes the alternatives reliable.

**Alternatives rejected**: Take the first uppercase word in column 2 (the current
method, which grabs a leaked example word or the wrong word).

## Decision 5: Detect entry boundaries and continuations

**Decision**: A row starts a new entry when column 1 matches a word plus a part of
speech. A row with no column-1 header is a continuation, and its column-2 text joins
the current entry. Record the base word once, even when the entry lists several verb
or adjective forms.

**Rationale**: Entries span several rows. The meaning and the alternatives wrap
across lines. The header pattern marks where one entry ends and the next begins.

## Decision 6: Skip the intro and help pages

**Decision**: Start scanning at the page where the real alphabetical entries begin,
near page 155. Skip earlier pages. Also skip page headers, footers, and blank pages
by matching known header and footer text.

**Rationale**: The intro and help pages hold example tables that look like real
entries (for example the words that the guide uses to teach the rules). Those
examples are not real dictionary entries and must not enter the output. The real
entries run in alphabetical order from near page 155 to the end.

**Alternatives rejected**: Scan every page (pulls in the intro examples and pollutes
the output).

## Decision 7: Measure quality with a golden set and a harness

**Decision**: Build a small set of hand-verified entries. Write a harness that runs
the tool, compares each golden entry against the tool output, and reports a per-field
accuracy score plus every mismatch. Improve the parser until the score meets the
target.

**Rationale**: The user asked to iterate until near flawless. Iteration needs an
objective score. The harness turns "near flawless" into a number the parser can be
tuned against, and it prevents a fix for one entry from breaking another.

**Alternatives rejected**: Eyeball the output (not repeatable, and it misses
regressions).

## Known issues to iterate on (from the probe)

- The first prototype found 1846 entries against a target of 2149. The gap is mostly
  approved words. Likely causes to test: some headwords sit just past the column
  boundary, some entries split across a page break, and a long approved meaning can
  swallow the next header. The harness will show which entries are missing.
- The column boundary drifts between pages. A fixed boundary loses some words. Test a
  boundary that adapts per page, or widen the word column and use the header pattern
  to confirm the split.
