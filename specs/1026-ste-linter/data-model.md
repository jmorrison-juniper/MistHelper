# Data Model: STE Linter

**Feature**: 1026-ste-linter | **Phase**: 1

This document lists the main types the linter uses and how they relate. All types
are Python dataclasses or enums unless noted.

## Severity (enum)

The weight class of a violation.

- `ERROR`: A clear rule break. Default weight 3.
- `WARNING`: A likely rule break. Default weight 2.
- `INFO`: A heuristic guess the writer should confirm. Default weight 1.

## ProseSpan

One run of gradable prose taken from a file.

| Field | Type | Description |
| - | - | - |
| `text` | str | The prose text with code and links removed |
| `start_line` | int | The 1-based source line where the span starts |
| `kind` | str | "markdown", "docstring", or "comment" |

## Sentence

One sentence inside a ProseSpan.

| Field | Type | Description |
| - | - | - |
| `text` | str | The sentence text |
| `line` | int | The 1-based source line of the sentence start |
| `word_count` | int | The STE word count |
| `mode` | str | "procedural" or "descriptive" |

## Document

The parsed file, ready to grade.

| Field | Type | Description |
| - | - | - |
| `path` | str | The file path |
| `spans` | list[ProseSpan] | The gradable prose spans |
| `sentences` | list[Sentence] | All sentences across the spans |
| `paragraphs` | list[list[Sentence]] | Sentences grouped by paragraph |
| `word_count` | int | The total STE word count |

## Rule (base class)

One STE check. Subclasses live in the `rules` package.

| Member | Type | Description |
| - | - | - |
| `rule_id` | str | A stable identifier, for example "STE-S1-LEN" |
| `section` | str | The writing-guide section, for example "1-words" |
| `severity` | Severity | The default severity |
| `scope` | str | "sentence", "word", "paragraph", or "document" |
| `check(document, backend, config)` | method | Yields Violation objects |

## Violation

One rule failure at one place.

| Field | Type | Description |
| - | - | - |
| `rule_id` | str | The rule that failed |
| `section` | str | The writing-guide section |
| `severity` | Severity | The severity of this finding |
| `path` | str | The file path |
| `line` | int | The 1-based source line |
| `column` | int | The 1-based column, or 0 when not known |
| `message` | str | What is wrong, in plain STE prose |
| `suggestion` | str | How to fix it |

## SectionScore

The score for one writing-guide section.

| Field | Type | Description |
| - | - | - |
| `section` | str | The section name |
| `penalty` | float | The section penalty between 0 and 1 |
| `score` | int | The section score between 0 and 100 |
| `violation_count` | int | The number of violations in the section |

## Score

The final result for one file.

| Field | Type | Description |
| - | - | - |
| `path` | str | The file path |
| `score` | int | The overall score between 0 and 100 |
| `sections` | list[SectionScore] | The per-section breakdown |
| `violations` | list[Violation] | All violations, sorted by line |
| `dictionary_used` | bool | True when the dictionary checks ran |
| `word_count` | int | The graded word count |

## Dictionary and DictionaryEntry

Loaded from `data/ste_dictionary.json` when present.

`DictionaryEntry`:

| Field | Type | Description |
| - | - | - |
| `keyword` | str | The word |
| `part_of_speech` | str | The approved part of speech, or empty |
| `approved` | bool | True when the word is approved |
| `alternatives` | list[str] | Approved words to use instead |
| `approved_meaning` | str | The approved meaning, or empty |

`Dictionary` holds a map from a lower-case keyword to a list of `DictionaryEntry`
and gives a lookup method.

## Relationships

- A `Document` has many `ProseSpan` and many `Sentence`.
- A `Rule` reads a `Document` and yields `Violation` objects.
- The scoring model turns `Violation` objects and unit counts into a `Score` with
  many `SectionScore`.
- The `Dictionary` is optional input to the dictionary rules only.
