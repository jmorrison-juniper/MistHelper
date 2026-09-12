# Data Model: Dictionary Extractor

**Feature**: 1027-ste-dict-extractor | **Phase**: 1

## PositionedWord

One word read from the PDF with its position. This is the input the parser works
from.

| Field | Type | Description |
| - | - | - |
| `text` | str | The word as printed |
| `x0` | float | The left coordinate on the page |
| `top` | float | The top coordinate on the page |
| `page` | int | The 1-based page number |

## RawEntry

One entry as the parser builds it, before it becomes a record.

| Field | Type | Description |
| - | - | - |
| `keyword` | str | The headword |
| `part_of_speech` | str | The part of speech from column 1 |
| `approved` | bool | True when the word is printed in capitals |
| `column2_lines` | list[str] | The joined column-2 text across rows |
| `page` | int | The page where the entry starts |

## DictionaryRecord

The output record. It matches the shape the loader already reads.

| Field | Type | Description |
| - | - | - |
| `keyword` | str | The word, in lower case |
| `part_of_speech` | str | The part of speech |
| `approved` | bool | The approved flag |
| `alternatives` | list[str] | The approved words to use instead, in lower case |
| `approved_meaning` | str | The approved meaning, for an approved word |

The output file is a JSON object with a `version` and an `entries` list of these
records. This is the same shape `loader.py` reads today, so the linter needs no
change.

## GoldenEntry

One hand-verified expected record used to measure accuracy.

| Field | Type | Description |
| - | - | - |
| `keyword` | str | The word to look up in the output |
| `part_of_speech` | str | The expected part of speech |
| `approved` | bool | The expected approved flag |
| `alternatives` | list[str] | The expected alternatives, in lower case |

The golden set is a JSON list of these entries. It holds about 35 facts, not the
full dictionary.

## QualityReport

The result of the harness.

| Field | Type | Description |
| - | - | - |
| `total` | int | The number of golden entries checked |
| `keyword_found` | int | How many golden keywords appear in the output |
| `pos_correct` | int | How many parts of speech match |
| `approved_correct` | int | How many approved flags match |
| `alternatives_correct` | int | How many alternative lists match |
| `field_accuracy` | float | The average correctness across the fields, 0 to 1 |
| `mismatches` | list | Each mismatch with keyword, field, expected, actual |

## Relationships

- The parser reads many `PositionedWord` objects and builds `RawEntry` objects.
- Each `RawEntry` becomes one `DictionaryRecord`.
- The harness compares each `GoldenEntry` against the matching `DictionaryRecord`
  and produces one `QualityReport`.
