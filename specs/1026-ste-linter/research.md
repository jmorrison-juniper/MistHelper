# Research: Detection Methods and Scoring Model

**Feature**: 1026-ste-linter | **Phase**: 0

This document records the technical decisions for how each rule detects a problem
and how the tool turns violations into a 0 to 100 score.

## Decision 1: Two analysis backends behind one protocol

**Decision**: Define a `Backend` protocol that gives part-of-speech tags, lemmas,
and a passive-voice flag for a sentence. Ship a `HeuristicBackend` that uses the
standard library and an optional `SpacyBackend` that uses spaCy when it is
installed. A factory picks spaCy when the import succeeds, and the heuristic
backend otherwise.

**Rationale**: The repository values a small dependency footprint. The heuristic
backend keeps the core dependency-free. Teams that want higher accuracy install
spaCy and get better part-of-speech and tense detection with no code change.

**Alternatives rejected**: Require spaCy (adds a large model download and slows
first use). Use only heuristics (lower accuracy for passive voice and tense).

## Decision 2: Heuristic detection methods per rule

The heuristic backend uses word lists and simple patterns. Each method is a best
effort that favors few false alarms.

- **Sentence length**: Count words by the STE word rules (Decision 3). Compare to
  20 for procedural sentences and 25 for descriptive sentences.
- **Procedural or descriptive**: A sentence is procedural when it starts with a
  base-form verb (imperative) or when it is a numbered or lettered list item.
  Otherwise it is descriptive. A project can override the limit by configuration.
- **Passive voice**: Look for a form of "be" (am, is, are, was, were, be, been,
  being) followed within a short window by a past participle. The heuristic marks
  the past participle from a suffix list ("-ed", "-en") and an irregular list.
- **Complex tense**: Perfect is a form of "have" plus a past participle.
  Progressive is a form of "be" plus an "-ing" word. Report the simple form.
- **Semicolons**: Match the semicolon character outside code spans.
- **Latin abbreviations**: Match "e.g.", "i.e.", "etc.", "viz.", "et al.", and
  "N.B." with word boundaries and optional periods.
- **Multi-word noun clusters**: Find runs of adjectives and nouns longer than
  three words with the backend tags. The heuristic backend approximates nouns and
  adjectives from suffix and capitalization patterns and a stop-word list.
- **Phrasal verbs**: Match a curated map of common phrasal verbs to single-word
  verbs, for example "put out" to "extinguish".
- **-ing progressive verb**: Flag an "-ing" word that follows a form of "be" and
  is not part of a known technical noun list.
- **Contractions**: Match a curated list, for example "do not" for "don't".
- **Paragraph length**: Count sentences in a paragraph. Flag more than six.
- **Warnings**: Find a line that starts with "Warning" or "Caution". Flag it when
  it has no consequence clause, detected by the absence of a result cue such as
  "can cause", "results in", or "otherwise".
- **Gendered pronouns**: Flag "he", "she", "his", "her", "him" when the subject is
  a general person. The heuristic flags these pronouns and lets the writer confirm.

**Rationale**: These methods need no model and run fast. The tool marks each
heuristic finding with a severity so the score does not over-penalize a guess.

## Decision 3: STE word counting

**Decision**: A word counter tokenizes a sentence and counts these as one word
each: a number, a number joined to a unit, an acronym or initialism, an
alphanumeric identifier, a quoted span, and a hyphenated group. Paragraph and step
numbers do not count.

**Rationale**: The writing guide, Section 8, defines these counting rules. The
sentence-length rule depends on them, so the counter must match the guide.

**Method**: Protect quoted spans and inline-code spans first. Replace each number
with unit, identifier, and hyphenated group with a single placeholder token. Then
split on whitespace and count tokens.

## Decision 4: Deterministic scoring model

**Decision**: The score is a weighted average of per-section penalties, turned into
a percent.

For each rule R:

- `density(R) = min(1, violations(R) / max(1, eligible_units(R)))`
- `eligible_units(R)` is the number of sentences, words, or paragraphs the rule can
  apply to, based on the rule scope.

For each section S:

- `penalty(S) = sum over R in S of weight(R) * density(R) / sum over R in S of weight(R)`
- `penalty(S)` is between 0 and 1.

Overall:

- `penalty = sum over S of section_weight(S) * penalty(S) / sum over S of section_weight(S)`
- `score = round(100 * (1 - penalty))`

Each section score is `round(100 * (1 - penalty(S)))` for the breakdown.

**Rationale**: The model is deterministic, bounded between 0 and 100, and easy to
explain. A rule cannot push the score past its share because each density is capped
at 1 and each section is a weighted average. A mostly clean file scores high. A
file with dense violations scores low. Weights and section weights live in the
configuration, so a team can tune the emphasis without a code change.

**Alternatives rejected**: A flat "minus N points per violation" model is not
bounded and punishes long files unfairly. A pass or fail per rule loses the
gradient that helps writers improve.

## Decision 5: File parsing

**Decision**: Parse Markdown with a small tokenizer that removes fenced code,
inline code, link and image URLs, tables, and HTML, and keeps the prose with its
source line numbers. Parse Python with `ast` for docstrings and `tokenize` for
comments, and grade only that text.

**Rationale**: The linter grades prose, not code. Line numbers must survive the
parse so the report points to the right place. The standard library covers both
formats with no dependency.

**Alternatives rejected**: A full Markdown library adds a dependency for a small
need. A regular expression over the whole Python file would grade code as prose.

## Decision 6: Dictionary source and copyright

**Decision**: The engine supports full dictionary checks, but the dictionary data
is not in the repository. A tool reads a licensed ASD-STE100 PDF and writes
`data/ste_dictionary.json`, which git ignores. The linter loads the file when it is
present and skips the dictionary checks when it is absent.

**Rationale**: The ASD-STE100 dictionary is copyrighted. The repository must not
redistribute it. This design gives the full capability to a licensed user and keeps
the copyrighted data out of git, the same choice already made for the source PDF.

**Alternatives rejected**: Embed the dictionary in the code (redistributes
copyrighted data). Drop the dictionary checks (loses the depth the user asked for).
